(* Unison file synchronizer: src/skeleton.ml *)
(* Skeletons: what makes an earlier version of a file rebuildable from a later
   version of it.

   A metadata edit (a rating, develop settings, IPTC) rewrites a file's small
   structures and carries its large blocks over unchanged, perhaps to other
   offsets.  A skeleton of a file is every byte outside its blocks, with a map
   of where each block goes; the blocks themselves are not part of it.

   The cutting rules are those of the dng-compare archive specification,
   section 13.1 ("Blocks and the skeleton"), and this module is adapted from
   that project's OCaml implementation (ocaml-archive/lib/skeleton.ml,
   Copyright (c) 2026 FirstPair contributors, MIT License), so that the cuts
   agree with it byte for byte.  The store that keeps skeleton versions is
   SkeletonStore; see docs/skeleton-versions.md. *)

(* An out-of-line TIFF value or JPEG segment this large is a block. *)
let block_min = 512
(* A run this long that no tag points at is a block. *)
let gap = 65536
(* A block's mark hashes this many bytes from each end (the whole block when
   it is no longer than twice this). *)
let mark_bytes = 4096
(* Strips or tiles of one image this close together are one block. *)
let pad = 3
(* A file without a walker is its own skeleton up to this size. *)
let whole = 1 lsl 20

(* XMP, IPTC and Photoshop resources: what editors rewrite, kept in the skeleton. *)
let volatile = [700; 33723; 34377]
(* SubIFDs, Exif, GPS and Interoperability. *)
let pointers = [330; 34665; 34853; 40965]

type block = { at : int; len : int; mark : string; role : string }

(* A file's skeleton: its format ("tiff", "jpeg" or "whole"), size, blocks in
   file order, and every byte outside them, concatenated in file order. *)
type t = { format : string; size : int; blocks : block list; bytes : string }

let no_walker = "no skeleton walker for this format"

(* Up to [len] bytes at [at]; fewer at the end of the file. *)
let read_at fd at len =
  if len <= 0 then "" else begin
    ignore (Unix.LargeFile.lseek fd (Int64.of_int at) Unix.SEEK_SET);
    let chunk = Bytes.create (min len 1048576) in
    let b = Buffer.create (min len 1048576) in
    let rec go left =
      if left > 0 then
        match Unix.read fd chunk 0 (min left (Bytes.length chunk)) with
        | 0 -> ()
        | n -> Buffer.add_subbytes b chunk 0 n; go (left - n)
        | exception Unix.Unix_error (Unix.EINTR, _, _) -> go left in
    go len;
    Buffer.contents b
  end

let with_file path f =
  let fd =
    try Unix.openfile path [Unix.O_RDONLY; Unix.O_CLOEXEC] 0
    with Unix.Unix_error (e, _, _) -> failwith (path ^ ": " ^ Unix.error_message e) in
  Fun.protect ~finally:(fun () -> try Unix.close fd with Unix.Unix_error _ -> ())
    (fun () -> f fd (Int64.to_int (Unix.LargeFile.fstat fd).Unix.LargeFile.st_size))

let rd16 le s o = if le then String.get_uint16_le s o else String.get_uint16_be s o
let rd32 le s o =
  Int32.to_int (if le then String.get_int32_le s o else String.get_int32_be s o)
  land 0xFFFFFFFF

type entry = { tag : int; typ : int; raw : string; total : int }

let type_size = function 3 | 8 -> 2 | 4 | 9 | 11 | 13 -> 4 | 5 | 10 | 12 -> 8 | _ -> 1

(* An entry's unsigned integer values (BYTE, SHORT, LONG, IFD). *)
let values fd le size e =
  match (match e.typ with 1 -> 1 | 3 -> 2 | 4 | 13 -> 4 | _ -> 0) with
  | 0 -> []
  | width ->
      let buf =
        if e.total <= 4 then String.sub e.raw 0 e.total
        else
          let at = rd32 le e.raw 0 in
          if at + e.total > size then "" else read_at fd at e.total in
      if String.length buf <> e.total then []
      else List.init (e.total / width) (fun k ->
          let o = k * width in
          match width with
          | 1 -> Char.code buf.[o] | 2 -> rd16 le buf o | _ -> rd32 le buf o)

(* (offset, length, role) *)
type extent = int * int * string

let tiff fd size : extent list =
  let h = read_at fd 0 8 in
  let le = match if String.length h >= 2 then String.sub h 0 2 else "" with
    | "II" -> true | "MM" -> false | _ -> failwith "not a TIFF" in
  if String.length h < 8 || rd16 le h 2 <> 42 then failwith "not a classic TIFF";
  let blocks = ref [] and claims = ref [ (0, 8) ] in
  let seen = Hashtbl.create 16 in
  let queue = Queue.create () in
  Queue.add (rd32 le h 4, "0") queue;
  while not (Queue.is_empty queue) do
    let first, role = Queue.pop queue in
    let off = ref first and n = ref 0 and going = ref true in
    while !going && !off <> 0 && !off + 6 <= size && not (Hashtbl.mem seen !off) do
      Hashtbl.replace seen !off ();
      let head = read_at fd !off 2 in
      if String.length head < 2 then going := false
      else begin
        let cnt = rd16 le head 0 in
        let data = read_at fd (!off + 2) (cnt * 12 + 4) in
        if String.length data < cnt * 12 + 4 then going := false
        else begin
          let r = if !n = 0 then role else Printf.sprintf "%s+%d" role !n in
          claims := (!off, 6 + cnt * 12) :: !claims;
          let entries = List.init cnt (fun k ->
              let o = k * 12 in
              let typ = rd16 le data (o + 2) in
              { tag = rd16 le data o; typ; raw = String.sub data (o + 8) 4;
                total = type_size typ * rd32 le data (o + 4) }) in
          let find tag = List.find_opt (fun e -> e.tag = tag) entries in
          let add o c name =
            if c > 0 && o + c <= size then blocks := (o, c, r ^ "/" ^ name) :: !blocks in
          List.iter (fun (otag, ctag, name) ->
            match find otag, find ctag with
            | Some o, Some c ->
                let rec zip os cs = match os, cs with
                  | o :: os, c :: cs -> add o c name; zip os cs
                  | _ -> () in
                let os = values fd le size o in
                zip os (values fd le size c)
            | _ -> ()) [ (273, 279, "strips"); (324, 325, "tiles") ];
          (match find 513, find 514 with
           | Some o, Some c ->
               let os = values fd le size o in
               (match os, values fd le size c with
                | o :: _, c :: _ -> add o c "jpeg"
                | _ -> ())
           | _ -> ());
          List.iter (fun e ->
            if e.total > 4 then begin
              let at = rd32 le e.raw 0 in
              if at + e.total <= size then begin
                claims := (at, e.total) :: !claims;
                if e.total >= block_min && not (List.mem e.tag volatile)
                   && not (List.mem e.tag pointers)
                   && not (List.mem e.tag [273; 279; 324; 325]) then
                  blocks := (at, e.total, Printf.sprintf "%s/tag%d" r e.tag) :: !blocks
              end
            end) entries;
          List.iter (fun tag ->
            match find tag with
            | Some e ->
                List.iteri (fun k o ->
                  Queue.add (o, Printf.sprintf "%s/%d.%d" r tag k) queue)
                  (values fd le size e)
            | None -> ()) pointers;
          off := rd32 le data (cnt * 12);
          incr n
        end
      end
    done
  done;
  (* Data only a maker's own structures reach: no tag points at it, and an
     edit carries it over as it is. *)
  let all =
    List.sort compare
      ((size, 0) :: !claims @ List.map (fun (o, l, _) -> (o, l)) !blocks) in
  let pos = ref 0 in
  List.iter (fun (o, l) ->
    if o > !pos && o - !pos >= gap then blocks := (!pos, o - !pos, "gap") :: !blocks;
    pos := max !pos (o + l)) all;
  !blocks

let jpeg fd size : extent list =
  let blocks = ref [] in
  let pos = ref 2 and going = ref true in
  while !going && !pos + 4 <= size do
    let m = read_at fd !pos 4 in
    if String.length m < 4 || m.[0] <> '\xff' then going := false
    else begin
      let marker = Char.code m.[1] in
      if marker = 0xff then incr pos
      (* Start of scan, or a marker without a length: the image runs from here. *)
      else if marker = 0xda || marker = 0x00 || marker = 0x01
              || (marker >= 0xd0 && marker <= 0xd9) then going := false
      else begin
        let seg = rd16 false m 2 + 2 in
        if seg < 4 || !pos + seg > size then going := false
        else begin
          (* Exif and XMP (APP1), IPTC (APP13) and comments stay in the skeleton. *)
          if not (List.mem marker [0xe1; 0xed; 0xfe]) && seg >= block_min then
            blocks := (!pos, seg, Printf.sprintf "seg%02x" marker) :: !blocks;
          pos := !pos + seg
        end
      end
    end
  done;
  if !pos < size then blocks := (!pos, size - !pos, "scan") :: !blocks;
  !blocks

let ends_with ~suffix s =
  let n = String.length suffix and m = String.length s in
  m >= n && String.sub s (m - n) n = suffix

(* Sorted, without overlaps; the strips or tiles of one image merged when no
   more than [pad] bytes apart. *)
let normalize (blocks : extent list) : extent list =
  let out = List.fold_left (fun out (o, l, role) ->
    match out with
    | (lo, ll, lrole) :: rest ->
        let stop = lo + ll in
        if o < stop then out
        else if role = lrole
                && (ends_with ~suffix:"strips" role || ends_with ~suffix:"tiles" role)
                && o - stop <= pad then
          (lo, o + l - lo, lrole) :: rest
        else (o, l, role) :: out
    | [] -> [ (o, l, role) ]) [] (List.sort_uniq compare blocks) in
  List.rev out

(* A file's format and blocks, decided by its first bytes. *)
let walk fd size =
  let magic = read_at fd 0 4 in
  if magic = "II*\000" || magic = "MM\000*" then "tiff", normalize (tiff fd size)
  else if String.length magic >= 2 && String.sub magic 0 2 = "\xff\xd8" then
    "jpeg", normalize (jpeg fd size)
  else failwith no_walker

let sha_add c s = SemanticHash.feed c (Bytes.unsafe_of_string s) 0 (String.length s)

(* The first 32 hex digits of the SHA-256 of a block's two ends. *)
let mark fd at len =
  let c = SemanticHash.create () in
  if len <= 2 * mark_bytes then sha_add c (read_at fd at len)
  else begin
    sha_add c (read_at fd at mark_bytes);
    sha_add c (read_at fd (at + len - mark_bytes) mark_bytes)
  end;
  String.sub (SemanticHash.hex (SemanticHash.finish c)) 0 32

(* The skeleton of the open file [fd] of [size] bytes.  Reads its structures,
   the bytes outside its blocks, and each block's two ends; never a whole
   block.  Fails when the file has no walker and is larger than [whole]. *)
let build_fd fd size =
  let format, extents = match walk fd size with
    | w -> w
    | exception (Failure _ | Unix.Unix_error _ | Invalid_argument _) when size <= whole ->
        "whole", [] in
  let bytes = Buffer.create 65536 in
  let pos = ref 0 in
  let blocks = List.map (fun (at, len, role) ->
      Buffer.add_string bytes (read_at fd !pos (at - !pos));
      pos := at + len;
      { at; len; mark = mark fd at len; role }) extents in
  Buffer.add_string bytes (read_at fd !pos (size - !pos));
  let outside = size - List.fold_left (fun n b -> n + b.len) 0 blocks in
  if Buffer.length bytes <> outside then failwith "file changed while its skeleton was read";
  { format; size; blocks; bytes = Buffer.contents bytes }

let build path = with_file path build_fd

(* The blocks of a file as (len, mark, at), in file order; none for a file
   without a walker. *)
let marked_blocks fd size =
  match walk fd size with
  | _, extents -> List.map (fun (at, len, _) -> (len, mark fd at len, at)) extents
  | exception (Failure _ | Unix.Unix_error _ | Invalid_argument _) -> []
