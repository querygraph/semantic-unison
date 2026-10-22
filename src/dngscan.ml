(* unison-dngscan: read-only survey of DNG files against the built-in merge.

   Walks the given paths, and for every *.dng file runs the same inspectors the
   merge uses: dng-xmp /0, /1 and the merge-only /2, then an identity XmpMerge of
   the embedded packet at its fixed length. A file that passes both can take a
   built-in merge. For any other file the /2 grammar is walked once more to list
   every field it does not know, not just the first. Files are opened read-only
   and only their TIFF directories and XMP packet are read; nothing is written
   under the scanned paths. Work is sharded over forked worker processes. *)

type verdict = Mergeable | Xmp_unsupported of string | Declined of string | Error of string

type record = {
  path : string; size : int64;
  v0 : bool; v1 : bool; v2 : bool; verdict : verdict;
  unknown : (string * int * int * int64) list;
}

let usage = "usage: unison-dngscan [-j WORKERS] [-cache WALK] [-admit IFD:TAG:TYPE]... [-tags REVIEW.tsv] [-o REPORT.jsonl [-resume]] PATH..."

let is_dng name =
  String.lowercase_ascii (Filename.extension name) = ".dng"

(* A directory's cached listing: its subdirectories and regular *.dng files.
   Adding, removing or renaming an entry changes the directory's mtime, so the
   listing is reused only while device, inode and mtime are all unchanged. *)
type listing = { dev : int; ino : int; mtime : float; subdirs : string list; dngs : string list }
let cache_format = "unison-dngscan-walk/1"

let load_cache path =
  try
    let ch = open_in_bin path in
    Fun.protect ~finally:(fun () -> close_in ch) (fun () ->
      match (Marshal.from_channel ch : string * (string, listing) Hashtbl.t) with
      | format, table when format = cache_format -> table
      | _ -> Hashtbl.create 0)
  with Sys_error _ | End_of_file | Failure _ -> Hashtbl.create 0

let save_cache path table =
  let temp = path ^ ".tmp" in
  let ch = open_out_bin temp in
  Marshal.to_channel ch (cache_format, table) [];
  close_out ch;
  Sys.rename temp path

(* Depth-first, no symlinks followed, unreadable directories reported. With a
   cache, unchanged directories are listed from it without reading their entries.
   A directory modified in the last few seconds, or with an unreadable entry, is
   not cached. Returns the files, the errors, and directories (listed, reused). *)
let walk ?cache roots =
  let old = match cache with Some path -> load_cache path | None -> Hashtbl.create 0 in
  let fresh = Hashtbl.create (max 16 (Hashtbl.length old)) in
  let now = Unix.gettimeofday () in
  let files = ref [] and walk_errors = ref [] and listed = ref 0 and reused = ref 0 in
  let error path e = walk_errors := (path, Unix.error_message e) :: !walk_errors in
  let rec visit path =
    match Unix.LargeFile.lstat path with
    | exception Unix.Unix_error (e, _, _) -> error path e
    | {Unix.LargeFile.st_kind = Unix.S_REG; _} -> if is_dng path then files := path :: !files
    | {Unix.LargeFile.st_kind = Unix.S_DIR; st_dev; st_ino; st_mtime; _} ->
        let listing = match Hashtbl.find_opt old path with
          | Some l when l.dev = st_dev && l.ino = st_ino && l.mtime = st_mtime -> incr reused; Some l
          | _ -> list path st_dev st_ino st_mtime in
        Option.iter (fun l ->
          if cache <> None then Hashtbl.replace fresh path l;
          List.iter (fun name -> files := Filename.concat path name :: !files) l.dngs;
          List.iter (fun name -> visit (Filename.concat path name)) l.subdirs) listing
    | _ -> ()
  and list path dev ino mtime =
    match Unix.opendir path with
    | exception Unix.Unix_error (e, _, _) -> error path e; None
    | dir ->
        incr listed;
        let names = ref [] in
        (try while true do
           let name = Unix.readdir dir in
           if name <> "." && name <> ".." then names := name :: !names
         done with End_of_file -> ());
        Unix.closedir dir;
        let subdirs = ref [] and dngs = ref [] and complete = ref true in
        List.iter (fun name ->
          let child = Filename.concat path name in
          match Unix.LargeFile.lstat child with
          | exception Unix.Unix_error (e, _, _) -> error child e; complete := false
          | {Unix.LargeFile.st_kind = Unix.S_DIR; _} -> subdirs := name :: !subdirs
          | {Unix.LargeFile.st_kind = Unix.S_REG; _} when is_dng name -> dngs := name :: !dngs
          | _ -> ()) (List.sort compare !names);
        let l = {dev; ino; mtime; subdirs = List.rev !subdirs; dngs = List.rev !dngs} in
        if !complete && mtime < now -. 5. then Some l
        else begin
          (* Still walked now, but left out of the cache. *)
          List.iter (fun name -> files := Filename.concat path name :: !files) l.dngs;
          List.iter (fun name -> visit (Filename.concat path name)) l.subdirs;
          None
        end in
  List.iter visit roots;
  Option.iter (fun path -> save_cache path fresh) cache;
  Array.of_list (List.rev !files), List.rev !walk_errors, (!listed, !reused)

let read_packet file (region : FormatExtension.region) =
  let buffer = Buffer.create region.length in
  let rec loop at left =
    if left > 0 then begin
      let n = min left 1048576 in
      Buffer.add_string buffer (SemanticFile.read file at n);
      loop (Int64.add at (Int64.of_int n)) (left - n)
    end in
  loop region.offset region.length;
  Buffer.contents buffer

let ok = function Ok _ -> true | Result.Error _ -> false

let inspect path =
  let blank = {path; size = 0L; v0 = false; v1 = false; v2 = false;
               verdict = Error ""; unknown = []} in
  match Unix.openfile path [Unix.O_RDONLY; Unix.O_CLOEXEC] 0 with
  | exception Unix.Unix_error (e, _, _) -> {blank with verdict = Error (Unix.error_message e)}
  | fd ->
      Fun.protect ~finally:(fun () -> Unix.close fd) (fun () ->
        try
          SemanticFile.with_borrowed_fd fd (fun file ->
            let size = SemanticFile.size file in
            let v0 = ok (DngSemantic.inspect file) and v1 = ok (DngSemantic.inspect_extended file) in
            match DngSemantic.inspect_opaque_maker file with
            | Ok {FormatExtension.regions = [region]} ->
                let packet = read_packet file region in
                let verdict = match XmpMerge.merge ~base:packet ~left:packet ~right:packet with
                  | Ok merged when String.length merged = String.length packet -> Mergeable
                  | Ok _ -> Xmp_unsupported "identity merge changes packet length"
                  | Result.Error reason -> Xmp_unsupported reason in
                {blank with size; v0; v1; v2 = true; verdict}
            | Ok _ -> {blank with size; v0; v1; v2 = true; verdict = Xmp_unsupported "not one XMP region"}
            | Result.Error reason ->
                let unknown, _ = DngSemantic.unknown_fields file in
                {blank with size; v0; v1; verdict = Declined reason; unknown})
        with
        | SemanticFile.Invalid reason -> {blank with verdict = Error reason}
        | Unix.Unix_error (e, _, _) -> {blank with verdict = Error (Unix.error_message e)})

(* Worker k takes files k, k+workers, ... and marshals one record per file. *)
let run_worker files workers k out =
  let channel = Unix.out_channel_of_descr out in
  let i = ref k in
  while !i < Array.length files do
    Marshal.to_channel channel (inspect files.(!i) : record) [];
    flush channel;
    i := !i + workers
  done;
  close_out channel

let json_string s =
  let b = Buffer.create (String.length s + 2) in
  Buffer.add_char b '"';
  String.iter (fun c -> match c with
    | '"' -> Buffer.add_string b "\\\"" | '\\' -> Buffer.add_string b "\\\\"
    | '\n' -> Buffer.add_string b "\\n" | '\t' -> Buffer.add_string b "\\t"
    | c when Char.code c < 0x20 -> Buffer.add_string b (Printf.sprintf "\\u%04x" (Char.code c))
    | c -> Buffer.add_char b c) s;
  Buffer.add_char b '"';
  Buffer.contents b

let verdict_fields = function
  | Mergeable -> "mergeable", ""
  | Xmp_unsupported r -> "xmp-unsupported", r
  | Declined r -> "declined", r
  | Error r -> "error", r

let json r =
  let kind, reason = verdict_fields r.verdict in
  Printf.sprintf "{\"path\":%s,\"size\":%Ld,\"dng-xmp/0\":%b,\"dng-xmp/1\":%b,\"dng-xmp/2\":%b,\"verdict\":%s,\"reason\":%s,\"unknown\":[%s]}"
    (json_string r.path) r.size r.v0 r.v1 r.v2 (json_string kind) (json_string reason)
    (String.concat "," (List.map (fun (d, tag, typ, n) ->
       Printf.sprintf "{\"ifd\":%s,\"tag\":%d,\"type\":%d,\"count\":%Ld}" (json_string d) tag typ n) r.unknown))

(* Reader for this command's own report lines, used by -resume. Lines that do
   not parse, such as one cut short when a run was stopped, are dropped and their
   files scanned again. *)
type value = Str of string | Num of string | Bool of bool | Arr of value list | Obj of (string * value) list

exception Bad_line

let parse_line line =
  let i = ref 0 and n = String.length line in
  let peek () = if !i < n then line.[!i] else raise Bad_line in
  let expect c = if peek () <> c then raise Bad_line; incr i in
  let rec value () = match peek () with
    | '"' -> Str (string ())
    | '{' ->
        incr i;
        if peek () = '}' then (incr i; Obj []) else
        let rec fields acc =
          let k = string () in expect ':';
          let v = value () in
          match peek () with
          | ',' -> incr i; fields ((k, v) :: acc)
          | '}' -> incr i; Obj (List.rev ((k, v) :: acc))
          | _ -> raise Bad_line in
        fields []
    | '[' ->
        incr i;
        if peek () = ']' then (incr i; Arr []) else
        let rec items acc =
          let v = value () in
          match peek () with
          | ',' -> incr i; items (v :: acc)
          | ']' -> incr i; Arr (List.rev (v :: acc))
          | _ -> raise Bad_line in
        items []
    | 't' when !i + 4 <= n && String.sub line !i 4 = "true" -> i := !i + 4; Bool true
    | 'f' when !i + 5 <= n && String.sub line !i 5 = "false" -> i := !i + 5; Bool false
    | '-' | '0'..'9' ->
        let start = !i in
        while !i < n && (match line.[!i] with '-' | '0'..'9' -> true | _ -> false) do incr i done;
        Num (String.sub line start (!i - start))
    | _ -> raise Bad_line
  and string () =
    expect '"';
    let b = Buffer.create 64 in
    let rec loop () = match peek () with
      | '"' -> incr i
      | '\\' ->
          incr i;
          (match peek () with
           | '"' -> Buffer.add_char b '"' | '\\' -> Buffer.add_char b '\\'
           | 'n' -> Buffer.add_char b '\n' | 't' -> Buffer.add_char b '\t'
           | 'u' when !i + 5 <= n ->
               Buffer.add_char b (Char.chr (int_of_string ("0x" ^ String.sub line (!i + 1) 4) land 0xff));
               i := !i + 4
           | _ -> raise Bad_line);
          incr i; loop ()
      | c -> Buffer.add_char b c; incr i; loop () in
    loop (); Buffer.contents b in
  let v = value () in
  if !i <> n then raise Bad_line;
  v

let record_of_line line =
  match parse_line line with
  | Obj fields ->
      let get k = try List.assoc k fields with Not_found -> raise Bad_line in
      let str k = match get k with Str s -> s | _ -> raise Bad_line in
      let bool k = match get k with Bool b -> b | _ -> raise Bad_line in
      let num v = match v with Num s -> Int64.of_string s | _ -> raise Bad_line in
      let reason = str "reason" in
      let verdict = match str "verdict" with
        | "mergeable" -> Mergeable | "xmp-unsupported" -> Xmp_unsupported reason
        | "declined" -> Declined reason | "error" -> Error reason | _ -> raise Bad_line in
      let unknown = match get "unknown" with
        | Arr items -> List.map (function
            | Obj f ->
                let g k = try List.assoc k f with Not_found -> raise Bad_line in
                (match g "ifd" with Str d -> d | _ -> raise Bad_line),
                Int64.to_int (num (g "tag")), Int64.to_int (num (g "type")), num (g "count")
            | _ -> raise Bad_line) items
        | _ -> raise Bad_line in
      {path = str "path"; size = num (get "size"); v0 = bool "dng-xmp/0";
       v1 = bool "dng-xmp/1"; v2 = bool "dng-xmp/2"; verdict; unknown}
  | _ -> raise Bad_line
  | exception (Failure _ | Invalid_argument _) -> raise Bad_line

(* Complete report lines from an earlier run, rewritten so the report ends on a
   whole line before new results are appended. *)
let load_report path =
  if not (Sys.file_exists path) then [] else begin
    let ch = open_in_bin path in
    let kept = ref [] in
    (try while true do
       let line = input_line ch in
       match record_of_line line with
       | r -> kept := (r, line) :: !kept
       | exception Bad_line -> ()
     done with End_of_file -> ());
    close_in ch;
    let kept = List.rev !kept in
    let temp = path ^ ".resume" in
    let out = open_out_bin temp in
    List.iter (fun (_, line) -> output_string out line; output_char out '\n') kept;
    close_out out;
    Sys.rename temp path;
    List.map fst kept
  end

let bump table key example =
  match Hashtbl.find_opt table key with
  | Some (n, e) -> Hashtbl.replace table key (n + 1, e)
  | None -> Hashtbl.replace table key (1, example)

let sorted table =
  List.sort (fun (k, (a, _)) (k', (b, _)) -> compare (b, k) (a, k')) (Hashtbl.fold (fun k v l -> (k, v) :: l) table [])

let () =
  let workers = ref 8 and report = ref "" and resume = ref false and cache = ref "" and roots = ref [] in
  let admit = ref [] and tags = ref "" in
  Arg.parse [
    "-j", Arg.Set_int workers, "N  worker processes, up to 256 (default 8); the scan is I/O bound";
    "-o", Arg.Set_string report, "FILE  write one JSON line per DNG as results arrive";
    "-cache", Arg.Set_string cache, "FILE  reuse and update directory listings whose mtime is unchanged";
    "-admit", Arg.String (fun spec -> match DngSemantic.parse_admission spec with
      | Ok field -> admit := !admit @ [field]
      | Error reason -> raise (Arg.Bad reason)),
      "IFD:TAG:TYPE  also admit this field in /2, as the dngmergeadmit preference does";
    "-tags", Arg.Set_string tags, "FILE  write the fields outside /2 as a review table with admit specs";
    "-resume", Arg.Set resume, " keep the complete lines already in the -o report, skip those files and append";
  ] (fun p -> roots := p :: !roots) usage;
  if !roots = [] || !workers < 1 || !workers > 256 || (!resume && !report = "") then
    (prerr_endline usage; exit 2);
  DngSemantic.admit_fields !admit;
  let started = Unix.gettimeofday () in
  let all_files, walk_errors, (listed, reused) =
    walk ?cache:(if !cache = "" then None else Some !cache) (List.rev !roots) in
  (* Earlier results count only for files this walk found again. *)
  let found = Hashtbl.create (Array.length all_files) in
  Array.iter (fun p -> Hashtbl.replace found p ()) all_files;
  let earlier = if !resume then load_report !report else [] in
  let earlier = List.filter (fun r -> Hashtbl.mem found r.path && (Hashtbl.remove found r.path; true)) earlier in
  let files = List.filter (fun p -> Hashtbl.mem found p) (Array.to_list all_files) |> Array.of_list in
  Printf.eprintf "dngscan: %d DNG files found in %.0fs (%d directories read, %d from cache), %d already in the report; scanning %d with %d workers\n%!"
    (Array.length all_files) (Unix.gettimeofday () -. started) listed reused (List.length earlier)
    (Array.length files) !workers;
  let workers = max 1 (min !workers (Array.length files)) in
  let children = List.init workers (fun k ->
    let input, output = Unix.pipe ~cloexec:true () in
    match Unix.fork () with
    | 0 -> Unix.close input; run_worker files workers k output; Unix._exit 0
    | pid -> Unix.close output; pid, Unix.in_channel_of_descr input) in
  (* Records arrive in any order and carry their path; a pipe at EOF is retired.
     Report lines are written as they arrive, so a partial report is readable. *)
  let out = if !report = "" then None
    else Some (open_out_gen [Open_wronly; Open_creat; Open_binary; if !resume then Open_append else Open_trunc] 0o644 !report) in
  let collected = ref earlier and received = ref 0 and last = ref (Unix.gettimeofday ()) in
  let scan_started = !last in
  let pending = ref (List.map snd children) in
  while !pending <> [] do
    let ready, _, _ = Unix.select (List.map Unix.descr_of_in_channel !pending) [] [] (-1.) in
    pending := List.filter (fun ch ->
      if not (List.mem (Unix.descr_of_in_channel ch) ready) then true else
      match (Marshal.from_channel ch : record) with
      | r ->
          collected := r :: !collected; incr received;
          Option.iter (fun ch -> output_string ch (json r); output_char ch '\n') out;
          let now = Unix.gettimeofday () in
          if now -. !last >= 30. then begin
            last := now;
            Option.iter flush out;
            let rate = float !received /. (now -. scan_started) in
            Printf.eprintf "dngscan: %d/%d files, %.0f/s, about %.0f min left\n%!" !received
              (Array.length files) rate (float (Array.length files - !received) /. rate /. 60.)
          end;
          true
      | exception End_of_file -> close_in ch; false) !pending
  done;
  let results = List.sort (fun a b -> compare a.path b.path) !collected in
  let missing = Array.length all_files - List.length results in
  let failed_workers = List.filter (fun (pid, _) -> match Unix.waitpid [] pid with
    | _, Unix.WEXITED 0 -> false | _ -> true) children in
  let verdicts = Hashtbl.create 8 and reasons = Hashtbl.create 32 and unknown = Hashtbl.create 64 in
  let profiles = Array.make 3 0 and bytes = ref 0L in
  List.iter (fun r ->
        bytes := Int64.add !bytes r.size;
        if r.v0 then profiles.(0) <- profiles.(0) + 1;
        if r.v1 then profiles.(1) <- profiles.(1) + 1;
        if r.v2 then profiles.(2) <- profiles.(2) + 1;
        let kind, reason = verdict_fields r.verdict in
        bump verdicts kind r.path;
        if reason <> "" then bump reasons (kind ^ ": " ^ reason) r.path;
        List.iter (fun (d, tag, typ, n) ->
          bump unknown (Printf.sprintf "%s tag %d type %d count %s" d tag typ
            (if n = 1L then "1" else "n")) r.path)
          (List.sort_uniq compare (List.map (fun (d, t, ty, n) -> d, t, ty, if n = 1L then 1L else 2L) r.unknown)))
    results;
  Option.iter close_out out;
  Printf.printf "DNG files: %d (%.1f GiB) in %.0fs\n" (Array.length all_files)
    (Int64.to_float !bytes /. 1073741824.) (Unix.gettimeofday () -. started);
  Printf.printf "accepted by inspector: dng-xmp/0 %d, /1 %d, /2 %d\n" profiles.(0) profiles.(1) profiles.(2);
  Printf.printf "\nverdicts:\n";
  List.iter (fun (k, (n, _)) -> Printf.printf "  %8d  %s\n" n k) (sorted verdicts);
  if Hashtbl.length reasons > 0 then begin
    Printf.printf "\nreasons (first stop of the real inspector or XMP merge):\n";
    List.iter (fun (k, (n, e)) -> Printf.printf "  %8d  %s\n            e.g. %s\n" n k e) (sorted reasons)
  end;
  (* Review table: one row per directory, tag and type, with the files that
     carry it and the spec that would admit it. *)
  let review = Hashtbl.create 64 in
  List.iter (fun r ->
    List.iter (fun (d, tag, typ) -> bump review (d, tag, typ) r.path)
      (List.sort_uniq compare (List.map (fun (d, t, ty, _) -> d, t, ty) r.unknown))) results;
  let review = List.sort (fun ((_, (a, _)) as x) ((_, (b, _)) as y) -> compare (b, fst x) (a, fst y))
      (Hashtbl.fold (fun k v l -> (k, v) :: l) review []) in
  if !tags <> "" then begin
    let ch = open_out_bin !tags in
    output_string ch "ifd\ttag\ttype\tfiles\tadmit\texample\n";
    List.iter (fun ((d, tag, typ), (n, e)) ->
      Printf.fprintf ch "%s\t%d\t%d\t%d\t%s:%d:%d\t%s\n" d tag typ n d tag typ e) review;
    close_out ch
  end;
  if !admit <> [] then
    Printf.printf "\nadmitted with -admit: %s\n" (String.concat " "
      (List.map (fun (d, t, ty) -> Printf.sprintf "%s:%d:%d" d t ty) !admit));
  if Hashtbl.length unknown > 0 then begin
    Printf.printf "\nfields outside dng-xmp/2 (files containing each):\n";
    List.iter (fun (k, (n, e)) -> Printf.printf "  %8d  %s\n            e.g. %s\n" n k e) (sorted unknown);
    Printf.printf "\nto try them, after review: %s\n" (String.concat " "
      (List.map (fun ((d, t, ty), _) -> Printf.sprintf "-admit %s:%d:%d" d t ty) review))
  end;
  if walk_errors <> [] then begin
    Printf.printf "\nunreadable paths: %d\n" (List.length walk_errors);
    List.iter (fun (p, e) -> Printf.printf "  %s: %s\n" p e) walk_errors
  end;
  if missing > 0 || failed_workers <> [] then
    Printf.printf "\nINCOMPLETE: %d files without a result, %d workers failed\n" missing (List.length failed_workers);
  let all_mergeable = Hashtbl.length verdicts = 1 && Hashtbl.mem verdicts "mergeable" in
  exit (if missing > 0 || failed_workers <> [] || walk_errors <> [] then 2
        else if all_mergeable then 0 else 1)
