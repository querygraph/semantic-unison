(* unison-dngscan -semdiff: is every file under one left root (a shuttle disk
   such as Kolobok) safely kept on one or more long-term roots (Photo, Bumer)?

   The left root is walked; the right roots are only matched. A left file is
   matched on each right root by the same relative path first, then by the same
   file name anywhere under that root; a name found more than once is reported
   as ambiguous, never guessed. Size is not a match criterion. Equal-size pairs
   are compared by SHA-256; any other pair, or one whose hashes differ, gets:

   - for DNGs, the encoded raw image compared by SHA-256 over its strips or
     tiles (the largest image directory), and the other image directories
     (previews) compared as a set;
   - for JPEGs, the image compared by SHA-256 over every segment except APPn and
     COM metadata, through the first EOI; bytes after it are the previews;
   - for files the exiftool-rs engine reads, a metadata difference list in
     dng-compare's batch-row form, from dng-compare's own exiftool-rs worker.

   With -sameview a pair is "same view" when its raw image is byte-identical
   and every changed tag is listed as non-rendering in dng-compare's shared
   metadata_rules.json. That is a metadata rule, not a comparison of rendered
   images, and anything not listed counts as possibly rendering.

   Nothing under any root is written. Reports are JSON lines; -summarize reads
   one or more of them, says whether the left root is safe to wipe, and writes
   the catch-up list that `unison LEFT RIGHT -semcatchupfrom LIST` copies with
   creation only. -db stores the differences in a dng-compare archive and runs
   dng-compare's own indexer. *)

open ScanCommon

let system name = name = ".DS_Store" || (String.length name > 2 && String.sub name 0 2 = "._")
(* The default -preserve archive lives under the long-term root; never compare it. *)
let archive_dir = ".dng-compare"

(* dng-compare's shared tag rules. *)
type rules = {
  copy : string; (* group_copy is ^PREFIX[0-9]+$ *)
  never : string list * string list; volatile : string list * string list;
  filesystem : string list; plain : string list * string list;
  layout : string list; (* tag names: file positions *)
  mirrors : (string * string list) list; (* XMP copy -> source tag names *)
}

let starts prefix s = String.length s >= String.length prefix && String.sub s 0 (String.length prefix) = prefix
let rule_match (exact, prefixes) tag = List.mem tag exact || List.exists (fun p -> starts p tag) prefixes

let load_rules path =
  let text = In_channel.with_open_bin path In_channel.input_all in
  let j = try parse text with Bad_json -> failwith (path ^ ": not JSON") in
  let str = function Str s -> s | _ -> failwith (path ^ ": bad rules") in
  let strs = function Some (Arr l) -> List.map str l | _ -> failwith (path ^ ": bad rules") in
  let pair k = match member k j with
    | Some o -> strs (member "exact" o), strs (member "prefixes" o)
    | None -> failwith (path ^ ": missing " ^ k) in
  if member "format" j <> Some (Str "dng-compare-metadata-rules/1") then
    failwith (path ^ ": unsupported metadata rules format");
  let copy = match member "group_copy" j with
    | Some (Str s) when String.length s > 7 && starts "^" s &&
                        String.sub s (String.length s - 7) 7 = "[0-9]+$" -> String.sub s 1 (String.length s - 8)
    | _ -> failwith (path ^ ": group_copy must be ^PREFIX[0-9]+$") in
  { copy;
    never = pair "never_compared"; volatile = pair "volatile";
    filesystem = strs (member "filesystem_prefixes" j); plain = pair "non_rendering";
    layout = (match member "layout_names" j with None -> [] | l -> strs l);
    mirrors = (match member "mirrors" j with
      | Some (Obj l) -> List.map (fun (k, v) -> k, strs (Some v)) l
      | None -> [] | Some _ -> failwith (path ^ ": bad mirrors")) }

let normalize rules tag =
  let n = String.length rules.copy in
  let copy part = String.length part > n && starts rules.copy part &&
    String.for_all (function '0'..'9' -> true | _ -> false) (String.sub part n (String.length part - n)) in
  String.concat ":" (List.filter (fun part -> not (copy part)) (String.split_on_char ':' tag))
let compared rules tag = not (rule_match rules.never tag || rule_match rules.volatile tag)
let category rules tag = if List.exists (fun p -> starts p tag) rules.filesystem then "filesystem" else "embedded"
let non_rendering rules tag = rule_match rules.plain (normalize rules tag)
let tag_name tag = match String.rindex_opt tag ':' with
  | Some i -> String.sub tag (i + 1) (String.length tag - i - 1) | None -> tag
(* A strip, tile or preview offset: moves with the metadata, and cannot change
   rendering once the image data compare identical. *)
let layout rules tag = (starts "EXIF:" tag || starts "MakerNotes:" tag) && List.mem (tag_name tag) rules.layout

(* One right root's view of one left file. *)
type diff = { tag : string; kind : string; left_value : json option; right_value : json option; cat : string }
type target = {
  root : string; matched : string; how : string; (* path | name | ambiguous | none | unavailable *)
  msize : int64; mmtime : float;
  status : string; (* identical | metadata-only | image-differs | differs | missing | ambiguous | unavailable | error *)
  image : string; previews : string; (* same | differs | unknown | "" *)
  sameview : bool option; reason : string; differences : diff list;
  left_meta : json option; right_meta : json option; (* kept in memory for -db only *)
}
type record = { path : string; rel : string; size : int64; mtime : float; ino : int; targets : target list }

type options = {
  rules : rules option; exiftool : string; want_sameview : bool; keep_meta : bool;
}

let blank_target root = {root; matched = ""; how = "none"; msize = 0L; mmtime = 0.; status = "missing";
  image = ""; previews = ""; sameview = None; reason = ""; differences = []; left_meta = None; right_meta = None}

(* One reader per spinning disk. A root whose device diskutil does not report as
   solid state is read by one stream at a time, across all workers and their
   helpers, through a lock file per device; SSDs keep their parallel readers. *)
let spinning = ref ([] : (int * int) list) (* device, readers *)

(* diskutil's fields for the volume holding [path]: "Solid State", "Volume UUID". *)
let disk_info path =
  try
    let ic = Unix.open_process_args_in "df" [|"df"; "-P"; path|] in
    let lines = In_channel.input_lines ic in
    ignore (Unix.close_process_in ic);
    match lines with
    | _ :: line :: _ ->
        let device = List.hd (String.split_on_char ' ' line) in
        let ic = Unix.open_process_args_in "diskutil" [|"diskutil"; "info"; device|] in
        let info = In_channel.input_lines ic in
        ignore (Unix.close_process_in ic);
        List.filter_map (fun l -> match String.index_opt l ':' with
          | Some i -> Some (String.trim (String.sub l 0 i), String.trim (String.sub l (i + 1) (String.length l - i - 1)))
          | None -> None) info
    | _ -> []
  with Unix.Unix_error _ | Sys_error _ | Failure _ -> []

(* A disk's kind given with -hdd or -ssd lives on the disk itself, in
   MOUNT-POINT/.semantic-unison ("disk = hdd" or "disk = ssd"), so it holds for
   every later run, on any Mac, whichever folder of the disk is synchronized. *)
let settings_file mount = Filename.concat mount ".semantic-unison"

let mount_point path = List.assoc_opt "Mount Point" (disk_info path)

let read_settings mount =
  try List.filter_map (fun l -> match String.index_opt l '=' with
      | Some i -> Some (String.trim (String.sub l 0 i), String.trim (String.sub l (i + 1) (String.length l - i - 1)))
      | None -> None)
      (In_channel.with_open_bin (settings_file mount) In_channel.input_lines)
  with Sys_error _ -> []

let recorded_kind mount = match List.assoc_opt "disk" (read_settings mount) with
  | Some ("hdd" | "ssd" as k) -> Some k | _ -> None
let recorded_readers mount =
  Option.bind (List.assoc_opt "readers" (read_settings mount)) int_of_string_opt

(* Set KEY = VALUE lines in the disk's settings file, keeping every other line. *)
let record_settings path updates =
  match mount_point path with
  | None -> Printf.eprintf "semdiff: %s: no mount point from diskutil; applies to this run only\n%!" path
  | Some mount when List.for_all (fun (k, v) -> List.assoc_opt k (read_settings mount) = Some v) updates -> ()
  | Some mount ->
      let file = settings_file mount in
      let others = try List.filter (fun l -> match String.index_opt l '=' with
          | Some i -> not (List.mem_assoc (String.trim (String.sub l 0 i)) updates) | None -> true)
          (In_channel.with_open_bin file In_channel.input_lines) with Sys_error _ -> [] in
      (try
         let temp = file ^ ".tmp" in
         Out_channel.with_open_bin temp (fun ch ->
           List.iter (fun l -> output_string ch l; output_char ch '\n') others;
           List.iter (fun (k, v) -> Printf.fprintf ch "%s = %s\n" k v) updates);
         Sys.rename temp file;
         Printf.eprintf "semdiff: recorded %s in %s\n%!"
           (String.concat ", " (List.map (fun (k, v) -> k ^ " = " ^ v) updates)) file
       with Sys_error e -> Printf.eprintf "semdiff: cannot record disk settings (%s); they apply to this run only\n%!" e)

let record_kind ?readers kind path =
  record_settings path (("disk", kind) :: match readers with Some n -> [("readers", string_of_int n)] | None -> [])

(* Limited readers for this root's disk? An explicit or recorded kind wins over
   diskutil; a disk not reported as solid state is spinning. A spinning disk
   gets the explicit, else the recorded, else one reader. *)
let note_disk ?kind ?readers root =
  match Unix.LargeFile.stat root with
  | exception Unix.Unix_error _ -> None
  | s when List.mem_assoc s.st_dev !spinning -> None
  | s ->
      let info = disk_info root in
      let mount = List.assoc_opt "Mount Point" info in
      let recorded = Option.bind mount recorded_kind in
      let kind = match kind, recorded with
        | Some k, _ -> Some (k, "-" ^ k)
        | None, Some k -> Some (k, "recorded as " ^ k)
        | None, None -> None in
      let one = match kind with
        | Some ("hdd", _) -> true
        | Some _ -> false
        (* UNISON_SEMDIFF_ONE_READER=all treats every disk as spinning (tests). *)
        | None -> Sys.getenv_opt "UNISON_SEMDIFF_ONE_READER" = Some "all" ||
                  List.assoc_opt "Solid State" info <> Some "Yes" in
      if one then begin
        let n = match readers with
          | Some n -> n | None -> Option.value (Option.bind mount recorded_readers) ~default:1 in
        let n = max 1 (min 64 n) in
        spinning := (s.st_dev, n) :: !spinning;
        Some (Printf.sprintf "%s, %s at a time"
          (match kind with Some (_, why) -> why | None -> "not reported as solid state")
          (if n = 1 then "one reader" else string_of_int n ^ " readers"))
      end else None

(* A reader slot is one lock file of the device's [readers]: take any free
   slot, else wait on one. Locks belong to processes, so workers and their
   helpers share the slots. *)
let one_reader path f =
  match Unix.LargeFile.lstat path with
  | s when List.mem_assoc s.st_dev !spinning ->
      let n = List.assoc s.st_dev !spinning in
      let slot k = Filename.concat (Filename.get_temp_dir_name ())
          (Printf.sprintf "unison-semdiff-disk-%d-%d.lock" s.st_dev k) in
      let open_slot k = Unix.openfile (slot k) [Unix.O_RDWR; Unix.O_CREAT; Unix.O_CLOEXEC] 0o600 in
      let rec try_slots k =
        if k = n then None else
        let fd = open_slot k in
        match Unix.lockf fd Unix.F_TLOCK 0 with
        | () -> Some fd
        | exception Unix.Unix_error ((Unix.EAGAIN | Unix.EACCES | Unix.EWOULDBLOCK), _, _) ->
            Unix.close fd; try_slots (k + 1) in
      let fd = match try_slots 0 with
        | Some fd -> fd
        | None -> let fd = open_slot (Unix.getpid () mod n) in Unix.lockf fd Unix.F_LOCK 0; fd in
      Fun.protect ~finally:(fun () -> Unix.close fd) (fun () -> f path)
  | _ -> f path
  | exception Unix.Unix_error _ -> f path

let hash_file path = one_reader path @@ fun path ->
  let fd = Unix.openfile path [Unix.O_RDONLY; Unix.O_CLOEXEC] 0 in
  Fun.protect ~finally:(fun () -> Unix.close fd) (fun () ->
    let h = SemanticHash.create () and buf = Bytes.create 4194304 in
    let rec loop () = match Unix.read fd buf 0 (Bytes.length buf) with
      | 0 -> SemanticHash.finish h
      | n -> SemanticHash.feed h buf 0 n; loop () in
    loop ())

(* [f a] here and [f b] in a forked helper at the same time, so the two files
   of a pair are read from their two disks concurrently. An exception in the
   helper is raised here as Failure. *)
let both f a b =
  let input, output = Unix.pipe ~cloexec:true () in
  match Unix.fork () with
  | 0 ->
      Unix.close input;
      let result = try Ok (f b) with e -> Error (Printexc.to_string e) in
      let ch = Unix.out_channel_of_descr output in
      Marshal.to_channel ch result []; close_out ch;
      Unix._exit 0
  | pid ->
      Unix.close output;
      let mine = try Ok (f a) with e -> Error e in
      let ch = Unix.in_channel_of_descr input in
      let theirs = try Marshal.from_channel ch with End_of_file -> Error "helper exited" in
      close_in ch;
      ignore (Unix.waitpid [] pid);
      match mine, theirs with
      | Ok x, Ok y -> x, y
      | Error e, _ -> raise e
      | _, Error e -> failwith (b ^ ": " ^ e)

(* Encoded image directories of a DNG, each hashed over its strips or tiles in
   order: the largest is the raw image, the rest are previews. *)
let image_units path = one_reader path @@ fun path ->
  let fd = Unix.openfile path [Unix.O_RDONLY; Unix.O_CLOEXEC] 0 in
  Fun.protect ~finally:(fun () -> Unix.close fd) (fun () ->
    SemanticFile.with_borrowed_fd fd (fun file ->
      match DngSemantic.component_regions file with
      | Result.Error reason -> Result.Error reason
      | Ok regions ->
          let groups = Hashtbl.create 8 and order = ref [] in
          List.iter (fun (r : DngSemantic.component_region) ->
            if r.role = DngSemantic.Image_bytes then begin
              (* "DIRECTORY/image/TAG/N": group a directory's units. *)
              let id = r.logical_id and marker = "/image/" in
              let rec find i = if i + String.length marker > String.length id then String.length id
                else if String.sub id i (String.length marker) = marker then i else find (i + 1) in
              let dir = String.sub id 0 (find 0) in
              if not (Hashtbl.mem groups dir) then begin
                Hashtbl.replace groups dir (SemanticHash.create (), ref 0L); order := dir :: !order end;
              let h, total = Hashtbl.find groups dir in
              let rec feed at left =
                if left > 0L then begin
                  let n = Int64.to_int (min left 1048576L) in
                  let chunk = SemanticFile.read file at n in
                  SemanticHash.feed h (Bytes.unsafe_of_string chunk) 0 n;
                  feed (Int64.add at (Int64.of_int n)) (Int64.sub left (Int64.of_int n))
                end in
              feed r.offset r.length;
              total := Int64.add !total r.length
            end) regions;
          let units = List.map (fun dir -> let h, total = Hashtbl.find groups dir in !total, SemanticHash.finish h)
              (List.rev !order) in
          match List.sort (fun a b -> compare b a) units with
          | [] -> Result.Error "no encoded image"
          | raw :: previews -> Ok (raw, List.sort compare previews)))

(* A JPEG's image is every segment before the first scan except APPn and COM
   metadata, then the scans through the first EOI (entropy-coded data stuffs
   every 0xFF it contains, so the first FF D9 after a scan starts is the EOI).
   Bytes after the EOI, such as MPF secondary images, are the previews. *)
let jpeg_units path = one_reader path @@ fun path ->
  let data = In_channel.with_open_bin path In_channel.input_all in
  let n = String.length data in
  let byte i = Char.code data.[i] in
  if n < 4 || byte 0 <> 0xff || byte 1 <> 0xd8 then Result.Error "not a JPEG" else
  let image = SemanticHash.create () in
  let feed first last = SemanticHash.feed image (Bytes.unsafe_of_string data) first (last - first) in
  feed 0 2;
  let rec segments i =
    if i + 4 > n || byte i <> 0xff then Result.Error "malformed JPEG segment" else
    let marker = byte (i + 1) in
    if marker = 0xff then segments (i + 1)
    else if marker = 0xda then scan i (i + 2)
    else if marker = 0xd9 then Result.Error "JPEG without a scan" else
    let length = (byte (i + 2) lsl 8) lor byte (i + 3) in
    if length < 2 || i + 2 + length > n then Result.Error "truncated JPEG segment" else begin
      if not ((marker >= 0xe0 && marker <= 0xef) || marker = 0xfe) then feed i (i + 2 + length);
      segments (i + 2 + length)
    end
  and scan start i =
    if i + 1 >= n then Result.Error "JPEG without EOI"
    else if byte i = 0xff && byte (i + 1) = 0xd9 then begin
      feed start (i + 2);
      let image_hash = SemanticHash.finish image in
      let rest = String.sub data (i + 2) (n - i - 2) in
      Ok ((Int64.of_int (i + 2 - start), image_hash),
          if rest = "" then [] else [Int64.of_int (String.length rest), SemanticHash.string rest])
    end else scan start (i + 1) in
  segments 2

(* dng-compare's exiftool-rs worker: NUL-separated paths in, a JSON array of
   records in input order out. *)
let extract exiftool paths =
  let in_r, in_w = Unix.pipe ~cloexec:true () and out_r, out_w = Unix.pipe ~cloexec:true () in
  let pid = Unix.create_process exiftool [|exiftool; "1"|] in_r out_w Unix.stderr in
  Unix.close in_r; Unix.close out_w;
  let oc = Unix.out_channel_of_descr in_w in
  List.iter (fun p -> output_string oc p; output_char oc '\000') paths;
  close_out oc;
  let ic = Unix.in_channel_of_descr out_r in
  let text = In_channel.input_all ic in
  close_in ic;
  match Unix.waitpid [] pid, (try parse text with Bad_json -> Null) with
  | (_, Unix.WEXITED 0), Arr records when List.length records = List.length paths -> Ok records
  | (_, Unix.WEXITED 0), _ -> Result.Error "exiftool-rs worker printed no records"
  | _ -> Result.Error "exiftool-rs worker failed"

let fields = function Obj l -> l | _ -> []

let differences rules left right =
  let l = fields left and r = fields right in
  let keys = List.sort_uniq compare (List.map fst l @ List.map fst r) in
  List.filter_map (fun tag ->
    if not (compared rules tag) then None else
    match List.assoc_opt tag l, List.assoc_opt tag r with
    | Some a, Some b when a = b -> None
    | a, b ->
        let kind = match a, b with
          | Some _, Some _ -> "changed_in_bumer" | None, _ -> "added_in_bumer" | _, None -> "missing_in_bumer" in
        Some {tag; kind; left_value = a; right_value = b; cat = category rules tag}) keys

(* Copy groups are positions, not values: compare each tag's values as a set.
   Returns the changed tags that may affect rendering, develop settings first.
   An XMP copy of EXIF or maker-notes data (Lightroom's aux:Lens) is not a
   change while each of its values equals a source value in the same file; a
   source missing from [left] or [right] counts as a change (fail closed). *)
let rendering_changes rules left right =
  let text = function Str s -> s | v -> to_string v in
  let table side =
    let t = Hashtbl.create 256 in
    List.iter (fun (tag, v) -> if compared rules tag then begin
      let k = normalize rules tag in
      (* TIFF text is padded with spaces or NULs; padding is not a change. *)
      let v = match v with
        | Str s -> let n = ref (String.length s) in
            while !n > 0 && (s.[!n - 1] = ' ' || s.[!n - 1] = '\000') do decr n done; Str (String.sub s 0 !n)
        | v -> v in
      Hashtbl.replace t k (text v :: (try Hashtbl.find t k with Not_found -> [])) end) (fields side);
    Hashtbl.filter_map_inplace (fun _ vs -> Some (List.sort compare vs)) t; t in
  let a = table left and b = table right in
  let mirrored t k = match List.assoc_opt k rules.mirrors with
    | None -> false
    | Some names ->
        let sources = Hashtbl.fold (fun k' vs acc ->
          if not (starts "XMP:" k') && List.mem (tag_name k') names then vs @ acc else acc) t [] in
        List.for_all (fun v -> List.mem v sources) (try Hashtbl.find t k with Not_found -> []) in
  let keys = List.sort_uniq compare (Hashtbl.fold (fun k _ l -> k :: l) a (Hashtbl.fold (fun k _ l -> k :: l) b [])) in
  let changed = List.filter (fun k -> Hashtbl.find_opt a k <> Hashtbl.find_opt b k &&
    not (non_rendering rules k || layout rules k || (mirrored a k && mirrored b k))) keys in
  let rank k = if starts "XMP:XMP-crs:" k || starts "XMP:XMP-crd:" k then 0
    else if tag_name k = "Orientation" then 1 else 2 in
  List.stable_sort (fun x y -> compare (rank x) (rank y)) changed

let rendering_reason = function
  | [] -> ""
  | [tag] -> "rendering tag changed: " ^ tag
  | tag :: more -> Printf.sprintf "rendering tag changed: %s and %d more" tag (List.length more)

(* Same view again from a report's stored differences, under the current rules:
   tags equal on both sides cancel out of the value sets, so the differences
   alone decide, except for a mirror whose unchanged source was not stored. *)
let reclassify rules t =
  (* Only pairs whose metadata was compared: a failed extraction stays as it was. *)
  if t.status <> "metadata-only" || t.sameview = None ||
     not (t.reason = "" || starts "rendering tag changed: " t.reason) then t else
  let side f = Obj (List.filter_map (fun d -> Option.map (fun v -> d.tag, v) (f d)) t.differences) in
  let changes = rendering_changes rules (side (fun d -> d.left_value)) (side (fun d -> d.right_value)) in
  {t with sameview = Some (changes = []); reason = rendering_reason changes}

let compare_pair opts left matched t =
  let ext = String.lowercase_ascii (Filename.extension left) in
  let lsize = (Unix.LargeFile.stat left).st_size and msize = t.msize in
  if lsize = msize && (let h, h' = both hash_file left matched in h = h') then
    {t with status = "identical"; image = "same"; previews = "same";
            sameview = if opts.want_sameview then Some true else None}
  else begin
    let image, previews, image_note =
      let units = match ext with
        | ".dng" -> Some image_units | ".jpg" | ".jpeg" -> Some jpeg_units | _ -> None in
      match units with
      | None -> "unknown", "unknown", ""
      | Some units ->
      match both units left matched with
      | Ok (raw, p), Ok (raw', p') ->
          (if raw = raw' then "same" else "differs"), (if p = p' then "same" else "differs"), ""
      | Result.Error e, _ | _, Result.Error e -> "unknown", "unknown", "image not compared: " ^ e
      | exception Unix.Unix_error (e, _, _) -> "unknown", "unknown", "image not readable: " ^ Unix.error_message e
      | exception SemanticFile.Invalid r -> "unknown", "unknown", "image not readable: " ^ r
      | exception Failure r -> "unknown", "unknown", "image not readable: " ^ r in
    let meta = if opts.rules = None then Result.Error "no metadata rules" else extract opts.exiftool [left; matched] in
    let status = match image with "same" -> "metadata-only" | "differs" -> "image-differs" | _ -> "differs" in
    match meta, opts.rules with
    | Ok [l; r], Some rules ->
        let differences = differences rules l r in
        let blocking = rendering_changes rules l r in
        let sameview = if not opts.want_sameview then None
          else Some (image = "same" && blocking = []) in
        let reason = match image with
          | "same" -> rendering_reason blocking
          | "differs" -> "raw image differs"
          | _ -> image_note in
        {t with status; image; previews; sameview; reason; differences;
                left_meta = if opts.keep_meta then Some l else None;
                right_meta = if opts.keep_meta then Some r else None}
    | Ok _, _ -> {t with status; image; previews; sameview = if opts.want_sameview then Some false else None;
                         reason = "unexpected exiftool-rs output"}
    | Result.Error e, _ ->
        {t with status; image; previews; sameview = if opts.want_sameview then Some false else None;
                reason = String.concat "; " (List.filter ((<>) "") [image_note; e])}
  end

type job = { jpath : string; jrel : string; jsize : int64; jmtime : float; jino : int; jtargets : target list }

let run_job opts j =
  let targets = List.map (fun t ->
    if t.how <> "path" && t.how <> "name" then t else
    try compare_pair opts j.jpath t.matched t
    with Unix.Unix_error (e, _, p) -> {t with status = "error"; reason = p ^ ": " ^ Unix.error_message e}
       | SemanticFile.Invalid r | Failure r -> {t with status = "error"; reason = r}) j.jtargets in
  {path = j.jpath; rel = j.jrel; size = j.jsize; mtime = j.jmtime; ino = j.jino; targets}

(* Report lines. *)
let opt_json = function None -> [] | Some v -> [v]
let diff_json d =
  Obj ([("tag", Str d.tag); ("kind", Str d.kind)] @
       List.map (fun v -> "apo", v) (opt_json d.left_value) @
       List.map (fun v -> "bumer", v) (opt_json d.right_value) @ [("category", Str d.cat)])
let num_i64 n = Num (Int64.to_string n)
let num_f f = Num (Printf.sprintf "%.17g" f)
let target_json t =
  Obj [("root", Str t.root); ("match", Str t.matched); ("how", Str t.how); ("size", num_i64 t.msize);
       ("mtime", num_f t.mmtime); ("status", Str t.status); ("image", Str t.image);
       ("previews", Str t.previews);
       ("sameview", match t.sameview with None -> Null | Some b -> Bool b);
       ("reason", Str t.reason); ("differences", Arr (List.map diff_json t.differences))]
let record_json r =
  to_string (Obj [("semdiff", Num "1"); ("path", Str r.path); ("rel", Str r.rel); ("size", num_i64 r.size);
                  ("mtime", num_f r.mtime); ("ino", Num (string_of_int r.ino));
                  ("targets", Arr (List.map target_json r.targets))])

exception Bad_record
let record_of_line line =
  let j = try parse line with Bad_json -> raise Bad_record in
  let get o k = match member k o with Some v -> v | None -> raise Bad_record in
  let str o k = match get o k with Str s -> s | _ -> raise Bad_record in
  let i64 o k = match get o k with Num s -> (try Int64.of_string s with Failure _ -> raise Bad_record) | _ -> raise Bad_record in
  let flt o k = match get o k with Num s -> (try float_of_string s with Failure _ -> raise Bad_record) | _ -> raise Bad_record in
  if member "semdiff" j <> Some (Num "1") then raise Bad_record;
  let target o =
    let diffs = match get o "differences" with
      | Arr l -> List.map (fun d -> {tag = str d "tag"; kind = str d "kind"; left_value = member "apo" d;
                                     right_value = member "bumer" d; cat = str d "category"}) l
      | _ -> raise Bad_record in
    {root = str o "root"; matched = str o "match"; how = str o "how"; msize = i64 o "size"; mmtime = flt o "mtime";
     status = str o "status"; image = str o "image"; previews = str o "previews";
     sameview = (match get o "sameview" with Bool b -> Some b | _ -> None);
     reason = str o "reason"; differences = diffs; left_meta = None; right_meta = None} in
  {path = str j "path"; rel = str j "rel"; size = i64 j "size"; mtime = flt j "mtime";
   ino = Int64.to_int (i64 j "ino");
   targets = (match get j "targets" with Arr l -> List.map target l | _ -> raise Bad_record)}

let load_records path =
  if not (Sys.file_exists path) then [] else
  In_channel.with_open_bin path (fun ch ->
    let rec loop acc = match In_channel.input_line ch with
      | None -> List.rev acc
      | Some line -> loop (match record_of_line line with r -> r :: acc | exception Bad_record -> acc) in
    loop [])

let lstat_opt p = try Some (Unix.LargeFile.lstat p) with Unix.Unix_error _ -> None
let is_dir p = match lstat_opt p with Some {Unix.LargeFile.st_kind = Unix.S_DIR; _} -> true | _ -> false
let unchanged_left r = match lstat_opt r.path with
  | Some s -> s.st_size = r.size && s.st_mtime = r.mtime && s.st_ino = r.ino | None -> false

(* A result is reused only while both files are unchanged and the pair was
   actually compared; missing, ambiguous, unavailable and failed pairs are
   always looked at again. *)
let reusable ~sameview roots r =
  unchanged_left r &&
  List.length r.targets = List.length roots &&
  List.for_all2 (fun root t -> t.root = root &&
    List.mem t.status ["identical"; "metadata-only"; "image-differs"; "differs"] &&
    (not sameview || t.sameview <> None) &&
    (match lstat_opt t.matched with Some s -> s.st_size = t.msize && s.st_mtime = t.mmtime | None -> false))
    roots r.targets

let strip_slash p = if String.length p > 1 && p.[String.length p - 1] = '/' then String.sub p 0 (String.length p - 1) else p

let name_of root =
  let parts = List.filter ((<>) "") (String.split_on_char '/' root) in
  match List.rev parts with
  | a :: b :: _ -> b ^ "-" ^ a | [a] -> a | [] -> "root"

(* Where the shuttle's version of a file whose content differs on a long-term
   root R (such as /Volumes/Photo/foto) is kept: in a tree beside R, under R's
   own name and the same relative path (R/../review/foto/REL by default, or
   -tree NAME), so roots side by side (foto/, jpg/) never collide; or with -suffix
   beside the long-term file itself, as NAME_2.EXT, NAME_3.EXT, ... or
   NAME_SUF.EXT. The default -preserve archive is R/../dng-compare/SHUTTLE.
   Tree and archive lie outside R, as dng-compare requires of an archive. *)
type placement = Tree of string | Suffix of string (* "" numbers the copies *)

let default_archive ~left root =
  Filename.concat (Filename.concat (Filename.dirname root) "dng-compare") (name_of left)

let utc_stamp () =
  let t = Unix.gmtime (Unix.time ()) in
  Printf.sprintf "%04d%02d%02dT%02d%02d%02dZ" (t.tm_year + 1900) (t.tm_mon + 1) t.tm_mday t.tm_hour t.tm_min t.tm_sec

(* The preservation manifest, written by dng-archive or by dng-compare's
   preserve_apo: relative path -> [ino, size, mtime_ns, ctime_ns]. *)
let preserved archive =
  let t = Hashtbl.create 256 in
  let manifest = Filename.concat archive "manifest.jsonl" in
  if Sys.file_exists manifest then
    In_channel.with_open_bin manifest (fun ch ->
      let rec loop () = match In_channel.input_line ch with
        | None -> ()
        | Some line ->
            (match parse line with
             | j -> (match member "relative_path" j, member "source_identity" j with
                 | Some (Str rel), Some (Arr [Num ino; Num size; Num mtime; _]) ->
                     Hashtbl.replace t rel (ino, size, mtime)
                 | _ -> ())
             | exception Bad_json -> ());
            loop () in
      loop ());
  t
let preserved_unchanged table (r : record) = match Hashtbl.find_opt table r.rel, lstat_opt r.path with
  | Some (ino, size, mtime), Some s ->
      ino = string_of_int s.st_ino && size = Int64.to_string s.st_size &&
      (try Float.abs (float_of_string mtime /. 1e9 -. s.st_mtime) < 1e-6 with Failure _ -> false)
  | _ -> false

(* Candidate places for a conflict copy; an existing identical copy is reused. *)
let conflict_candidates placement (r : record) (t : target) =
  match placement with
  | Tree name -> [List.fold_left Filename.concat (Filename.dirname t.root) [name; Filename.basename t.root; r.rel]]
  | Suffix suf ->
      let dir = Filename.dirname t.matched and base = Filename.basename t.matched in
      let ext = Filename.extension base in
      let stem = Filename.remove_extension base in
      if suf <> "" then [Filename.concat dir (stem ^ "_" ^ suf ^ ext)]
      else List.init 98 (fun i -> Filename.concat dir (Printf.sprintf "%s_%d%s" stem (i + 2) ext))

let same_content a b =
  match lstat_opt a, lstat_opt b with
  | Some x, Some y -> x.st_size = y.st_size && hash_file a = hash_file b
  | _ -> false

let conflict_kept placement r t =
  List.exists (fun c -> same_content c r.path) (conflict_candidates placement r t)

(* Copy, verify the copy's SHA-256 against the source's, then link it into
   place, which fails rather than replace anything already there. *)
let copy_verified src dst =
  let mkdirp d = if Sys.command ("mkdir -p " ^ Filename.quote d) <> 0 then failwith ("cannot create " ^ d) in
  mkdirp (Filename.dirname dst);
  let temp = dst ^ ".semdiff-partial" in
  (try Sys.remove temp with Sys_error _ -> ());
  let st = Unix.LargeFile.stat src in
  let fd_in = Unix.openfile src [Unix.O_RDONLY; Unix.O_CLOEXEC] 0 in
  let fd_out = Unix.openfile temp [Unix.O_WRONLY; Unix.O_CREAT; Unix.O_EXCL; Unix.O_CLOEXEC] 0o600 in
  let h = SemanticHash.create () and buf = Bytes.create 4194304 in
  Fun.protect ~finally:(fun () -> Unix.close fd_in; Unix.close fd_out) (fun () ->
    let rec loop () = match Unix.read fd_in buf 0 (Bytes.length buf) with
      | 0 -> ()
      | n ->
          SemanticHash.feed h buf 0 n;
          let rec write off = if off < n then write (off + Unix.write fd_out buf off (n - off)) in
          write 0; loop () in
    loop ();
    Unix.fsync fd_out);
  let expected = SemanticHash.finish h in
  if hash_file temp <> expected || hash_file src <> expected then begin
    Sys.remove temp; failwith (src ^ " changed or the copy differs; nothing kept") end;
  Unix.chmod temp (st.st_perm land 0o777);
  Unix.utimes temp st.st_atime st.st_mtime;
  (match Unix.link temp dst with
   | () -> Sys.remove temp
   | exception Unix.Unix_error ((Unix.EPERM | Unix.EOPNOTSUPP | Unix.EXDEV | Unix.ENOSYS), _, _)
     when not (Sys.file_exists dst) -> Sys.rename temp dst
   | exception e -> Sys.remove temp; raise e)

(* Keep the shuttle's version of every pair whose content differs. *)
let keep_conflicts placement ~root records =
  let copied = ref 0 and kept = ref 0 and failed = ref 0 in
  List.iter (fun (r : record) ->
    match List.find_opt (fun t -> t.root = root) r.targets with
    | Some t when List.mem t.status ["image-differs"; "differs"] && unchanged_left r ->
        (try
           let candidates = conflict_candidates placement r t in
           if List.exists (fun c -> same_content c r.path) candidates then incr kept
           else match List.find_opt (fun c -> not (Sys.file_exists c)) candidates with
             | Some dst -> copy_verified r.path dst; incr copied
             | None -> failwith ("no free name for " ^ r.rel ^ " (each candidate exists and differs)")
         with Failure e | Sys_error e -> incr failed; Printf.printf "  not kept: %s\n" e
            | Unix.Unix_error (e, _, p) -> incr failed; Printf.printf "  not kept: %s: %s\n" p (Unix.error_message e))
    | _ -> ()) records;
  let where = match placement with
    | Tree name -> List.fold_left Filename.concat (Filename.dirname root) [name; Filename.basename root]
    | Suffix "" -> "numbered copies beside the files in " ^ root
    | Suffix suf -> Printf.sprintf "_%s copies beside the files in %s" suf root in
  Printf.printf "\nfiles whose content differs: %d copied to %s, %d already there, %d not kept\n"
    !copied where !kept !failed

(* Summary and catch-up list. [records] may come from several reports; the
   newest record of a left file for a root wins. A left file is safe to wipe when
   it is byte-identical on a long-term root, byte-identical in that root's
   review tree, or preserved by -preservefull, and unchanged since. *)
let catchup_format = "unison-semcatchup/1"

let write_list file ~left ~right paths =
  Out_channel.with_open_bin file (fun ch ->
    Printf.fprintf ch "%s\nleft\t%s\nright\t%s\n" catchup_format left right;
    List.iter (fun p -> Printf.fprintf ch "path\t%s\n" p) paths)

let usable_path p = not (String.contains p '\n' || String.contains p '\t')

let summarize ?catchup ~left ~archives ~placement records =
  let latest = Hashtbl.create 1024 in
  List.iter (fun r -> List.iter (fun t -> Hashtbl.replace latest (r.path, t.root) (r, t)) r.targets) records;
  let paths = List.sort_uniq compare (List.map (fun r -> r.path) records) in
  let roots = List.sort_uniq compare (List.concat_map (fun r -> List.map (fun t -> t.root) r.targets) records) in
  Printf.printf "semdiff: %d files under %s, compared with %s\n" (List.length paths) left (String.concat ", " roots);
  List.iter (fun root ->
    let counts = Hashtbl.create 8 and same = ref 0 in
    Hashtbl.iter (fun (_, root') (_, t) -> if root' = root then begin
      Hashtbl.replace counts t.status (1 + try Hashtbl.find counts t.status with Not_found -> 0);
      if t.sameview = Some true && t.status <> "identical" then incr same end) latest;
    Printf.printf "\n%s:\n" root;
    List.iter (fun s -> match Hashtbl.find_opt counts s with
      | Some n -> Printf.printf "  %8d  %s%s\n" n s
          (if s = "metadata-only" && !same > 0 then Printf.sprintf " (%d same view)" !same else "")
      | None -> ())
      ["identical"; "metadata-only"; "image-differs"; "differs"; "missing"; "ambiguous"; "unavailable"; "error"]) roots;
  let manifests = List.map (fun (root, archive) -> root, preserved archive) archives in
  let in_review r t = try conflict_kept placement r t with Unix.Unix_error _ -> false in
  let by_path = Hashtbl.create 1024 in
  Hashtbl.iter (fun (p, _) (r, t) -> Hashtbl.replace by_path p ((r, t) :: try Hashtbl.find by_path p with Not_found -> [])) latest;
  let identical = ref 0 and kept_full = ref 0 and kept_review = ref 0 and gone = ref 0 in
  let blockers = Hashtbl.create 16 in
  let block why (r : record) =
    (* Report by session directory: at most the first three components. *)
    let parts = String.split_on_char '/' r.rel in
    let parts = List.filteri (fun i _ -> i < List.length parts - 1 && i < 3) parts in
    let dir = if parts = [] then "." else String.concat "/" parts in
    let n, dirs = try Hashtbl.find blockers why with Not_found -> 0, [] in
    Hashtbl.replace blockers why (n + 1, if List.mem dir dirs then dirs else dir :: dirs) in
  List.iter (fun p ->
    let entries = Hashtbl.find by_path p in
    let r = fst (List.hd entries) in
    if not (Sys.file_exists p) then incr gone
    else if List.exists (fun (r, t) -> t.status = "identical" && unchanged_left r) entries then incr identical
    else if not (List.for_all (fun (r, _) -> unchanged_left r) entries) then block "changed since the report" r
    else if List.exists (fun (r, (t : target)) -> t.status = "metadata-only" &&
              (match List.assoc_opt t.root manifests with Some m -> preserved_unchanged m r | None -> false)) entries
    then incr kept_full
    else if List.exists (fun (r, t) -> List.mem t.status ["image-differs"; "differs"] && in_review r t) entries
    then incr kept_review
    else begin
      let statuses = List.map (fun (_, t) -> t.status) entries in
      let why = if List.mem "metadata-only" statuses then
          (if List.exists (fun (_, t) -> t.sameview = Some true) entries
           then "metadata differs (same view; -preservefull keeps it)"
           else "metadata differs (-preservefull keeps it)")
        else if List.mem "image-differs" statuses then "image differs (-preserve keeps a copy)"
        else if List.mem "differs" statuses then "content differs (-preserve keeps a copy)"
        else if List.mem "ambiguous" statuses then "name ambiguous"
        else if List.for_all (fun s -> s = "unavailable") statuses then "no long-term root available"
        else if List.mem "error" statuses then "error"
        else "missing on every long-term root" in
      block why r
    end) paths;
  let safe = !identical + !kept_full + !kept_review in
  Printf.printf "\nsafe to wipe: %d of %d files (%d byte-identical, %d preserved in full, %d kept as conflict copies)\n"
    safe (List.length paths - !gone) !identical !kept_full !kept_review;
  if !gone > 0 then Printf.printf "  %d files in the reports are no longer on the left root\n" !gone;
  Hashtbl.iter (fun why (n, dirs) ->
    let dirs = List.rev dirs in
    Printf.printf "  not safe: %d %s, in %s%s\n" n why
      (String.concat ", " (List.filteri (fun i _ -> i < 6) dirs))
      (if List.length dirs > 6 then Printf.sprintf " and %d more" (List.length dirs - 6) else "")) blockers;
  let all_safe = Hashtbl.length blockers = 0 in
  (* Catch-up: files missing on the chosen root, collapsed to the shallowest
     absent directory when nothing under it was found there by name. *)
  all_safe, match catchup with
  | None -> None
  | Some (root, file) ->
      let entries = Hashtbl.fold (fun _ (r, t) l -> if t.root = root then (r, t) :: l else l) latest [] in
      let missing = List.filter (fun ((r : record), t) -> t.how = "none" && unchanged_left r) entries in
      let found_dirs = Hashtbl.create 64 in
      let ancestors rel =
        let parts = String.split_on_char '/' rel in
        List.init (List.length parts - 1) (fun i -> String.concat "/" (List.filteri (fun j _ -> j <= i) parts)) in
      List.iter (fun ((r : record), t) -> if t.how <> "none" then
        List.iter (fun d -> Hashtbl.replace found_dirs d ()) (ancestors r.rel)) entries;
      let absent = Hashtbl.create 64 in
      let absent_dir d = match Hashtbl.find_opt absent d with
        | Some b -> b | None -> let b = not (is_dir (Filename.concat root d)) in Hashtbl.replace absent d b; b in
      let out = Hashtbl.create 256 in
      List.iter (fun ((r : record), _) ->
        let path = match List.find_opt (fun d -> absent_dir d && not (Hashtbl.mem found_dirs d)) (ancestors r.rel) with
          | Some d -> d | None -> r.rel in
        Hashtbl.replace out path ()) missing;
      let list = List.sort compare (Hashtbl.fold (fun p () l -> p :: l) out []) in
      let bad = List.filter (fun p -> not (usable_path p)) list in
      let list = List.filter usable_path list in
      write_list file ~left ~right:root list;
      Printf.printf "\ncatch-up for %s: %d files missing, %d paths written to %s\n" root
        (List.length missing) (List.length list) file;
      if bad <> [] then Printf.printf "  %d paths with a tab or newline left out: copy them by hand\n" (List.length bad);
      Some (root, list)

(* dng-compare archive. Batch rows are only ever added: each run writes new
   batches for pairs the archive does not hold yet, so files from earlier
   shuttle cycles stay recorded after the shuttle is wiped. Then dng-compare's
   own indexer, which is idempotent per batch. An existing directory is used
   only if an earlier -preserve run created it. *)
let tool_id = "unison-dngscan -semdiff"

(* A shuttle file's version key: its size and modification time. A wiped and
   refilled shuttle with new contents at an old path gives a new key. *)
let source_stamp (r : record) = Printf.sprintf "%Ld:%.6f" r.size r.mtime

(* Relative path -> version keys already in the archive's batches. *)
let archive_rels batches =
  let t = Hashtbl.create 1024 in
  Array.iter (fun f -> if Filename.check_suffix f ".jsonl.gz" then begin
    let ic = Unix.open_process_args_in "gzip" [|"gzip"; "-dc"; Filename.concat batches f|] in
    let rec loop () = match In_channel.input_line ic with
      | None -> ()
      | Some line -> (match parse line with
          | j -> (match member "relative_path" j with
              | Some (Str rel) ->
                  let stamp = match member "source_stamp" j with Some (Str s) -> s | _ -> "" in
                  Hashtbl.replace t rel (stamp :: try Hashtbl.find t rel with Not_found -> [])
              | _ -> ())
          | exception Bad_json -> ()); loop () in
    loop ();
    if Unix.close_process_in ic <> Unix.WEXITED 0 then failwith ("unreadable batch " ^ f) end)
    (try Sys.readdir batches with Sys_error _ -> [||]);
  t

let write_archive ~archive ~archiver ~exiftool ~left records root =
  let prov = Filename.concat archive "provenance.json" in
  let ours () = Sys.file_exists prov &&
    (match parse (In_channel.with_open_bin prov In_channel.input_all) with
     | j -> member "tool" j = Some (Str tool_id) | exception Bad_json -> false) in
  if Sys.file_exists archive && Sys.readdir archive <> [||] && not (ours ()) then
    failwith (archive ^ " exists and was not created by " ^ tool_id ^ "; choose another -preservedb");
  let batches = Filename.concat archive "metadata/batches" in
  if Sys.command ("mkdir -p " ^ Filename.quote batches) <> 0 then failwith ("cannot create " ^ batches);
  let engine = try
      let ic = Unix.open_process_args_in exiftool [|exiftool; "--engine-version"|] in
      let v = String.trim (In_channel.input_all ic) in ignore (Unix.close_process_in ic); v
    with _ -> "unknown" in
  if not (Sys.file_exists prov) then
    Out_channel.with_open_bin prov (fun ch ->
      output_string ch (to_string (Obj [
        ("tool", Str tool_id); ("source", Str left); ("reference", Str root); ("engine", Str engine);
        ("scope", Str "metadata differences of compared pairs, added run by run; see runs.jsonl")]));
      output_char ch '\n');
  let known = archive_rels batches in
  let stamp = utc_stamp () in
  (* A path is recorded once per version: a new version of a recorded path gets
     this run's stamp as its dng-compare version. *)
  let recorded (r : record) = match Hashtbl.find_opt known r.rel with
    | None -> false
    | Some stamps -> List.mem (source_stamp r) stamps in
  let rows = List.filter_map (fun r ->
    match List.find_opt (fun t -> t.root = root) r.targets with
    | Some t when List.mem t.status ["identical"; "metadata-only"; "image-differs"; "differs"]
                 && not (recorded r) ->
        let version = if Hashtbl.mem known r.rel then stamp else "" in
        Some (to_string (Obj [
          ("relative_path", Str r.rel); ("version", Str version); ("source_stamp", Str (source_stamp r));
          ("apo", Str r.path); ("bumer", Str t.matched);
          ("apo_metadata", Option.value t.left_meta ~default:(Obj []));
          ("bumer_metadata", Option.value t.right_meta ~default:(Obj []));
          ("differences", Arr (List.map diff_json t.differences));
          ("errors", Arr []); ("warnings", Arr [])]))
    | _ -> None) records in
  let rec chunks n = function [] -> [] | l ->
    List.filteri (fun i _ -> i < n) l :: chunks n (List.filteri (fun i _ -> i >= n) l) in
  (* Batches are write-once: a name is never reused, even by two runs in one second. *)
  let rec fresh_name i n =
    let f = Filename.concat batches (Printf.sprintf "%s-%d-%06d%s.jsonl.gz" stamp (Unix.getpid ()) i
        (if n = 0 then "" else Printf.sprintf "-%d" n)) in
    if Sys.file_exists f || Sys.file_exists (f ^ ".tmp") then fresh_name i (n + 1) else f in
  List.iteri (fun i rows ->
    let file = fresh_name i 0 in
    let temp = file ^ ".tmp" in
    let oc = Unix.open_process_out ("gzip -n -c > " ^ Filename.quote temp) in
    List.iter (fun row -> output_string oc row; output_char oc '\n') rows;
    if Unix.close_process_out oc <> Unix.WEXITED 0 then failwith "gzip failed";
    Sys.rename temp file) (chunks 1000 rows);
  let runs = open_out_gen [Open_wronly; Open_creat; Open_append; Open_binary] 0o644 (Filename.concat archive "runs.jsonl") in
  output_string runs (to_string (Obj [("run", Str stamp); ("source", Str left); ("reference", Str root);
    ("engine", Str engine); ("rows_added", Num (string_of_int (List.length rows)));
    ("paths_recorded_earlier", Num (string_of_int (Hashtbl.length known)))]));
  output_char runs '\n'; close_out runs;
  let cmd = Printf.sprintf "%s index %s" (Filename.quote archiver) (Filename.quote archive) in
  Printf.printf "\ndng-compare archive %s: %d rows added (%d paths recorded earlier); indexing with %s\n%!"
    archive (List.length rows) (Hashtbl.length known) archiver;
  if Sys.command cmd <> 0 then
    Printf.printf "  indexing failed; the batches are kept, rerun: %s\n" cmd

(* -preservefull: dng-archive keeps each metadata-only file as a
   verified VCDIFF delta against its match, rebuildable to the exact SHA-256. *)
let preserve_full ?(verbose = false) ~archive ~archiver ~workers ~left records root =
  let done_ = preserved archive in
  (* The archive keeps one record per relative path: never replace the record
     of another version. *)
  let other = ref [] in
  let pairs = List.filter_map (fun r ->
    match List.find_opt (fun t -> t.root = root) r.targets with
    | Some t when t.status = "metadata-only" && unchanged_left r && not (preserved_unchanged done_ r) ->
        if Hashtbl.mem done_ r.rel then (other := r.rel :: !other; None)
        else Some (to_string (Obj [("source", Str r.path); ("reference", Str t.matched)]))
    | _ -> None) records in
  if !other <> [] then
    Printf.printf "\nnot preserved in full: %d files whose path already holds another version in %s, e.g. %s\n"
      (List.length !other) archive (List.hd !other);
  if pairs = [] then Printf.printf "\npreserved in full: nothing new for %s\n" archive else begin
    let file = Filename.concat archive (Printf.sprintf "pairs-%s-%d.jsonl" (utc_stamp ()) (Unix.getpid ())) in
    Out_channel.with_open_bin file (fun ch -> List.iter (fun l -> output_string ch l; output_char ch '\n') pairs);
    let cmd = Printf.sprintf "%s preserve %s %s %s --delta --pairs %s --workers %d"
        (Filename.quote archiver) (Filename.quote left) (Filename.quote root) (Filename.quote archive)
        (Filename.quote file) (max 1 (min 36 workers)) in
    Printf.printf "\npreserving %d metadata-only files in full with %s\n%!" (List.length pairs) archiver;
    let cmd = if verbose then cmd ^ " 2>&1 | tee " ^ Filename.quote (file ^ ".log") ^ "; exit ${PIPESTATUS[0]}"
      else cmd ^ " > " ^ Filename.quote (file ^ ".log") ^ " 2>&1" in
    if Sys.command ("bash -c " ^ Filename.quote cmd) <> 0 then
      Printf.printf "  preservation incomplete; see %s.log and rerun\n" file
  end

(* Command line for the -semdiff, -summarize and -review modes. *)
type config = {
  left_roots : string list; right_roots : string list; workers : int; report : string; resume : bool;
  cache : string; sameview_flag : bool; summarize : bool; reports : string list;
  catchup : bool; catchup_to : string; catchup_file : string; review : bool; placement : placement;
  db : bool; db_archive : string; preserve_full : bool; rules_path : string; exiftool_path : string;
  dng_compare_home : string; unison_path : string; unison_args : string list; verbose : bool;
  disk_kinds : (string * string) list; (* -hdd / -ssd PATH, recorded for later runs *)
  readers : int option; (* -readers N for the -hdd disks, recorded too *)
}

let human bytes =
  let b = Int64.to_float bytes in
  if b >= 1099511627776. then Printf.sprintf "%.2f TiB" (b /. 1099511627776.)
  else if b >= 1073741824. then Printf.sprintf "%.1f GiB" (b /. 1073741824.)
  else Printf.sprintf "%.0f MiB" (b /. 1048576.)

(* -v: walk progress every minute. *)
let walk_progress c what =
  if not c.verbose then None else begin
    let last = ref (Unix.gettimeofday ()) in
    Some (fun listed reused files ->
      let now = Unix.gettimeofday () in
      if now -. !last >= 60. then begin
        last := now;
        Printf.eprintf "semdiff: listing %s: %d directories read, %d from cache, %d files\n%!" what listed reused files
      end)
  end

let home () = try Sys.getenv "HOME" with Not_found -> "/"
let dng_compare_default () = try Sys.getenv "DNG_COMPARE_HOME" with Not_found -> Filename.concat (home ()) "src/dng-compare"

let find_program name extra =
  let dirs = (try String.split_on_char ':' (Sys.getenv "PATH") with Not_found -> []) @ extra in
  match List.find_opt (fun d -> Sys.file_exists (Filename.concat d name)) dirs with
  | Some d -> Filename.concat d name | None -> name

let scan c ~left ~roots ~rules ~exiftool =
  let started = Unix.gettimeofday () in
  let cache_of tag = if c.cache = "" then None
    else Some (if tag = "" then c.cache else c.cache ^ "." ^ Digest.to_hex (Digest.string tag)) in
  if c.verbose then Printf.eprintf "semdiff: listing %s\n%!" left;
  let files, walk_errors, (listed, reused) =
    walk ?cache:(cache_of "") ?progress:(walk_progress c left) ~format:"unison-dngscan-walk/1-all"
      ~keep:(fun n -> not (system n)) [left] in
  List.iter (fun (p, e) -> Printf.eprintf "semdiff: unreadable %s: %s\n" p e) walk_errors;
  (* Name indexes of the right roots: listings only, no file contents. *)
  let indexes = List.map (fun root ->
    if not (is_dir root) then root, None else begin
      if c.verbose then Printf.eprintf "semdiff: listing %s for matches by name\n%!" root;
      let found, _, (l, r) = walk ?cache:(cache_of root) ?progress:(walk_progress c root)
          ~format:"unison-dngscan-walk/1-all" ~keep:(fun n -> not (system n)) [root] in
      if c.verbose then Printf.eprintf "semdiff: %s: %d files (%d directories read, %d from cache)\n%!"
          root (Array.length found) l r;
      let t = Hashtbl.create (Array.length found) in
      Array.iter (fun p -> let k = String.lowercase_ascii (Filename.basename p) in
        Hashtbl.replace t k (p :: try Hashtbl.find t k with Not_found -> [])) found;
      root, Some t end) roots in
  Printf.eprintf "semdiff: %d files under %s in %.0fs (%d directories read, %d from cache)\n%!"
    (Array.length files) left (Unix.gettimeofday () -. started) listed reused;
  let earlier = if c.resume then load_records c.report else [] in
  let reused_records = List.filter (reusable ~sameview:c.sameview_flag roots) earlier in
  let reused_records = match rules with
    | Some rules -> List.map (fun r -> {r with targets = List.map (reclassify rules) r.targets}) reused_records
    | None -> reused_records in
  let done_ = Hashtbl.create 1024 in
  List.iter (fun r -> Hashtbl.replace done_ r.path ()) reused_records;
  let prefix = left ^ "/" in
  let jobs = Array.of_list (List.filter_map (fun p ->
    if Hashtbl.mem done_ p then None else
    match lstat_opt p with
    | None -> None
    | Some s ->
        let rel = String.sub p (String.length prefix) (String.length p - String.length prefix) in
        let targets = List.map (fun (root, index) ->
          let t = blank_target root in
          match index with
          | None -> {t with how = "unavailable"; status = "unavailable"; reason = root ^ " is not mounted"}
          | Some index ->
              let direct = Filename.concat root rel in
              let hit how m = match lstat_opt m with
                | Some ms -> {t with matched = m; how; msize = ms.st_size; mmtime = ms.st_mtime}
                | None -> t in
              (match lstat_opt direct with
               | Some {Unix.LargeFile.st_kind = Unix.S_REG; _} -> hit "path" direct
               | _ -> match Hashtbl.find_opt index (String.lowercase_ascii (Filename.basename p)) with
                 | Some [m] -> hit "name" m
                 | Some (_ :: _ as ms) -> {t with how = "ambiguous"; status = "ambiguous";
                     reason = String.concat " | " (List.filteri (fun i _ -> i < 4) (List.sort compare ms))}
                 | _ -> t)) indexes in
        Some {jpath = p; jrel = rel; jsize = s.st_size; jmtime = s.st_mtime; jino = s.st_ino; jtargets = targets})
    (Array.to_list files)) in
  Printf.eprintf "semdiff: %d results reused, comparing %d files with %d workers\n%!"
    (List.length reused_records) (Array.length jobs) c.workers;
  List.iter (fun (kind, path) ->
    record_kind ?readers:(if kind = "hdd" then c.readers else None) kind path) c.disk_kinds;
  List.iter (fun (kind, path) -> match note_disk ~kind ?readers:(if kind = "hdd" then c.readers else None) path with
    | Some why -> Printf.eprintf "semdiff: %s: %s\n%!" path why | None -> ()) c.disk_kinds;
  List.iter (fun root -> match note_disk root with
    | Some why -> Printf.eprintf "semdiff: %s: %s\n%!" root why | None -> ()) (left :: roots);
  let out = if c.report = "" then None else begin
    (* Rewrite the report to the reused lines, then append. *)
    let temp = c.report ^ ".resume" in
    Out_channel.with_open_bin temp (fun ch ->
      List.iter (fun r -> output_string ch (record_json r); output_char ch '\n') reused_records);
    Sys.rename temp c.report;
    Some (open_out_gen [Open_wronly; Open_append; Open_binary] 0o644 c.report) end in
  let opts = {rules; exiftool; want_sameview = c.sameview_flag; keep_meta = c.db} in
  let collected = ref reused_records and last_flush = ref (Unix.gettimeofday ()) in
  (* Progress by bytes that are actually read: shuttle files with a match.
     Missing files cost nothing and are left out. The rate is the last ten
     minutes', so the estimate follows what the disks deliver now. *)
  let compared j = List.exists (fun t -> t.how = "path" || t.how = "name") j.jtargets in
  let total = Array.fold_left (fun n j -> if compared j then Int64.add n j.jsize else n) 0L jobs in
  let total_files = Array.fold_left (fun n j -> if compared j then n + 1 else n) 0 jobs in
  let done_bytes = ref 0L and done_files = ref 0 and samples = Queue.create () in
  Queue.add (Unix.gettimeofday (), 0, 0L) samples;
  let counts = Hashtbl.create 8 in
  (* Time left = files left x seconds per file + bytes left x seconds per byte,
     both fitted by least squares over the last 15 one-minute intervals: small
     sidecars cost a seek each, large DNGs cost their bytes. *)
  let status _ =
    let now = Unix.gettimeofday () in
    Queue.add (now, !done_files, !done_bytes) samples;
    while Queue.length samples > 16 do ignore (Queue.pop samples) done;
    let points = Queue.fold (fun (acc, prev) (t, f, b) ->
      (match prev with
       | Some (t', f', b') when t > t' -> (float (f - f'), Int64.to_float (Int64.sub b b'), t -. t') :: acc
       | _ -> acc), Some (t, f, b)) ([], None) samples |> fst in
    let sum g = List.fold_left (fun a p -> a +. g p) 0. points in
    let ff = sum (fun (f, _, _) -> f *. f) and bb = sum (fun (_, b, _) -> b *. b)
    and fb = sum (fun (f, b, _) -> f *. b) and ft = sum (fun (f, _, t) -> f *. t)
    and bt = sum (fun (_, b, t) -> b *. t) in
    let det = ff *. bb -. fb *. fb in
    let per_file, per_byte =
      let only_files () = (if ff > 0. then ft /. ff else 0.), 0.
      and only_bytes () = 0., (if bb > 0. then bt /. bb else 0.) in
      if List.length points >= 2 && det > 1e-9 *. ff *. bb then
        let a = (ft *. bb -. bt *. fb) /. det and b = (ff *. bt -. fb *. ft) /. det in
        if a >= 0. && b >= 0. then a, b
        else if a < 0. then only_bytes () else only_files ()
      else only_bytes () in
    let span = sum (fun (_, _, t) -> t) in
    let rate = if span > 0. then sum (fun (_, b, _) -> b) /. span else 0. in
    let files_rate = if span > 0. then sum (fun (f, _, _) -> f) /. span else 0. in
    let left = float (total_files - !done_files) *. per_file
               +. Int64.to_float (Int64.sub total !done_bytes) *. per_byte in
    Printf.sprintf "%s of %s, %.0f MiB/s, %.0f files/s, %s; %s" (human !done_bytes) (human total)
      (rate /. 1048576.) files_rate
      (if per_file = 0. && per_byte = 0. then "estimating time left"
       else Printf.sprintf "about %.0f min left" (left /. 60.))
      (String.concat ", " (List.filter_map (fun s -> Option.map (fun n -> Printf.sprintf "%s %d" s n)
         (Hashtbl.find_opt counts s))
         ["identical"; "metadata-only"; "image-differs"; "differs"; "missing"; "ambiguous"; "unavailable"; "error"])) in
  let failed = run_pool ~interval:60. ~status ~label:"semdiff" ~workers:c.workers jobs
      (run_job opts) (fun (r : record) ->
    collected := r :: !collected;
    if List.exists (fun t -> t.how = "path" || t.how = "name") r.targets then begin
      done_bytes := Int64.add !done_bytes r.size; incr done_files end;
    List.iter (fun t ->
      Hashtbl.replace counts t.status (1 + try Hashtbl.find counts t.status with Not_found -> 0);
      if c.verbose && t.status <> "identical" then
        Printf.eprintf "semdiff: %-13s %s%s%s\n%!" t.status r.rel
          (if t.how = "name" then "  (found as " ^ t.matched ^ ")" else "")
          (match t.sameview, t.reason with
           | Some true, _ -> "  same view"
           | _, "" -> "" | _, why -> "  " ^ why)) r.targets;
    Option.iter (fun ch ->
      output_string ch (record_json r); output_char ch '\n';
      if Unix.gettimeofday () -. !last_flush >= 30. then (last_flush := Unix.gettimeofday (); flush ch)) out) in
  Option.iter close_out out;
  if failed > 0 then Printf.printf "INCOMPLETE: %d workers failed\n" failed;
  if walk_errors <> [] then Printf.printf "INCOMPLETE: %d paths under %s unreadable\n" (List.length walk_errors) left;
  List.sort (fun a b -> compare a.path b.path) !collected

let exec_unison c ~left ~right ~list =
  let unison = if c.unison_path <> "" then c.unison_path
    else let sibling = Filename.concat (Filename.dirname Sys.executable_name) "unison" in
      if Sys.file_exists sibling then sibling else "unison" in
  let args = [unison; left; right; "-semcatchupfrom"; list] @ c.unison_args in
  Printf.printf "\nrunning: %s\n%!" (String.concat " " (List.map Filename.quote args));
  Unix.execvp unison (Array.of_list args)

let run c =
  let roots = List.map strip_slash c.right_roots in
  let rules = try Some (load_rules c.rules_path) with Sys_error e | Failure e ->
    Printf.eprintf "semdiff: metadata rules unavailable (%s): metadata is not compared\n%!" e; None in
  let exiftool = if c.exiftool_path <> "" then c.exiftool_path else
    find_program "metadata-extract-exiftool-rs-oxcaml"
      (List.map (fun sw -> Filename.concat (home ()) (".opam/" ^ sw ^ "/bin")) ["default"; "5.2.0+ox"]) in
  (* dng-compare's OCaml archive tool: index, preserve, restore. *)
  let archiver = match Sys.getenv_opt "DNG_ARCHIVE" with
    | Some p when p <> "" -> p
    | _ -> find_program "dng-archive"
             (List.map (fun sw -> Filename.concat (home ()) (".opam/" ^ sw ^ "/bin")) ["5.2.0+ox"; "default"]) in
  let from_reports = c.summarize || c.review in
  let records =
    if from_reports then
      let records = List.concat_map load_records ((if c.report <> "" then [c.report] else []) @ c.reports) in
      match rules with
      | Some rules -> List.map (fun r -> {r with targets = List.map (reclassify rules) r.targets}) records
      | None -> records
    else begin
      let left = match List.map strip_slash c.left_roots with
        | [l] -> l | _ -> prerr_endline "unison-dngscan -semdiff: give exactly one left root"; exit 2 in
      scan c ~left ~roots ~rules ~exiftool
    end in
  let left = match List.map strip_slash c.left_roots, records with
    | [l], _ -> l
    | _, r :: _ -> String.sub r.path 0 (String.length r.path - String.length r.rel - 1)
    | _ -> prerr_endline "semdiff: no records"; exit 2 in
  let catchup_root = if c.catchup_to <> "" then strip_slash c.catchup_to
    else match roots, records with
      | r :: _, _ -> r | [], r :: _ -> (match r.targets with t :: _ -> t.root | [] -> "") | _ -> "" in
  let list_file suffix = if c.catchup_file <> "" then c.catchup_file
    else if c.report <> "" then c.report ^ suffix
    else match c.reports with r :: _ -> r ^ suffix | [] -> "semdiff" ^ suffix in
  let targets = List.sort_uniq compare (List.concat_map (fun r -> List.map (fun t -> t.root) r.targets) records) in
  let archive_of root = if c.db_archive = "" then default_archive ~left root
    else if List.length targets > 1 then Filename.concat c.db_archive (name_of root)
    else c.db_archive in
  let existing_archives () = List.filter_map (fun root ->
    let a = archive_of root in if Sys.file_exists a then Some (root, a) else None) targets in
  if c.review then begin
    (* Only the conflicts from the earlier report: no scan, no catch-up. *)
    if catchup_root = "" then (prerr_endline "semdiff -review: no long-term root"; exit 2);
    keep_conflicts c.placement ~root:catchup_root records;
    print_endline "\n(as of the last -semdiff scan; files caught up since then are still listed as missing)";
    let all_safe, _ = summarize ~left ~archives:(existing_archives ()) ~placement:c.placement records in
    exit (if all_safe then 0 else 1)
  end;
  if c.db || c.preserve_full then
    List.iter (fun root ->
      let archive = archive_of root in
      try
        write_archive ~archive ~archiver ~exiftool ~left records root;
        if c.preserve_full then preserve_full ~verbose:c.verbose ~archive ~archiver ~workers:c.workers ~left records root
      with Failure e | Sys_error e -> Printf.printf "dng-compare archive not written: %s\n" e) targets;
  if c.db && catchup_root <> "" then keep_conflicts c.placement ~root:catchup_root records;
  let archives = existing_archives () in
  let all_safe, result = summarize ~left ~archives ~placement:c.placement
      ?catchup:(if catchup_root = "" then None else Some (catchup_root, list_file ".catchup")) records in
  match c.catchup, result with
  | true, Some (root, paths) ->
      if paths = [] then (print_endline "nothing to catch up"; exit 0);
      exec_unison c ~left ~right:root ~list:(list_file ".catchup")
  | _ -> exit (if all_safe then 0 else 1)
