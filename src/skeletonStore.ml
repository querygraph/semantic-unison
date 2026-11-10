(* Unison file synchronizer: src/skeletonStore.ml *)
(* Skeleton versions: the last few replaced versions of a file, each kept as
   its skeleton (Skeleton) instead of a whole copy.  See
   docs/skeleton-versions.md for the design and its limits.

   Per file there is one directory:

     index            the chain: one line per kept version, oldest first
     N.full           version N's record (block map and skeleton bytes)
     N.delta          the same, as a SkeletonDelta against a newer record
     N.whole          version N kept as a whole file
     N.pending        a replaced file not yet settled
     blocks/SHA256    a block no later version of the file holds any more

   This module works on plain path names and knows nothing of Unison's
   preferences; Stasher drives it during a synchronization and the
   unison-skeleton tool reads it. *)

type kind = Skel | Whole
type stored = Full | Delta of int | File

type version = {
  seq : int;            (* the version's number; never reused for a path *)
  time : float;         (* when it was replaced *)
  size : int;
  sha256 : string;      (* of the content, in hex *)
  kind : kind;
  format : string;      (* "tiff", "jpeg" or "whole"; "-" for a whole file *)
  record_sha256 : string;
  record_bytes : int;
  stored : stored;
  stored_bytes : int;   (* bytes of N.full, N.delta or N.whole *)
}

type chain = {
  path : string;
  next : int;
  pending : (int * float) option;
  versions : version list;   (* oldest first *)
}

type xblock = { b : Skeleton.block; sha : string }   (* sha: of the whole block *)
type record = { format : string; size : int; blocks : xblock list; bytes : string }

(* ---- Small helpers ---- *)

let ( // ) = Filename.concat
let hex_of s = SemanticHash.hex (SemanticHash.string s)
let key s = String.sub (hex_of s) 0 32

let rec mkdir_p dir =
  if not (Sys.file_exists dir) then begin
    mkdir_p (Filename.dirname dir);
    try Unix.mkdir dir 0o700 with Unix.Unix_error (Unix.EEXIST, _, _) -> ()
  end

let remove_noerr file = try Sys.remove file with Sys_error _ -> ()

let is_regular file =
  match Unix.LargeFile.stat file with
  | st -> st.Unix.LargeFile.st_kind = Unix.S_REG
  | exception Unix.Unix_error _ -> false

let file_size file = Int64.to_int (Unix.LargeFile.stat file).Unix.LargeFile.st_size

let read_file file =
  let ic = open_in_bin file in
  Fun.protect ~finally:(fun () -> close_in_noerr ic)
    (fun () -> really_input_string ic (in_channel_length ic))

let rec write_all fd s o n =
  if n > 0 then
    match Unix.write_substring fd s o n with
    | k -> write_all fd s (o + k) (n - k)
    | exception Unix.Unix_error (Unix.EINTR, _, _) -> write_all fd s o n

(* Write a file under a temporary name, flush it to disk, then rename it. *)
let write_atomic file fill =
  let tmp = file ^ ".tmp" in
  let fd = Unix.openfile tmp [Unix.O_WRONLY; Unix.O_CREAT; Unix.O_TRUNC; Unix.O_CLOEXEC] 0o600 in
  (try
     fill fd;
     (try Unix.fsync fd with Unix.Unix_error _ -> ());
     Unix.close fd
   with e -> (try Unix.close fd with _ -> ()); remove_noerr tmp; raise e);
  Unix.rename tmp file

let write_string_atomic file s = write_atomic file (fun fd -> write_all fd s 0 (String.length s))

(* [len] bytes of [fd] from [at], given to each of [use] in pieces. *)
let pump fd at len use =
  ignore (Unix.LargeFile.lseek fd (Int64.of_int at) Unix.SEEK_SET);
  let buf = Bytes.create (max 1 (min len 1048576)) in
  let left = ref len in
  while !left > 0 do
    match Unix.read fd buf 0 (min !left (Bytes.length buf)) with
    | 0 -> failwith "a file ended before its recorded size"
    | k -> use buf k; left := !left - k
    | exception Unix.Unix_error (Unix.EINTR, _, _) -> ()
  done

let copy_file src dst =
  Skeleton.with_file src (fun fd size ->
    write_atomic dst (fun out ->
      pump fd 0 size (fun buf k -> write_all out (Bytes.unsafe_to_string buf) 0 k)))

let sha_of_range fd at len =
  let c = SemanticHash.create () in
  pump fd at len (fun buf k -> SemanticHash.feed c buf 0 k);
  SemanticHash.hex (SemanticHash.finish c)

let sha_of_file file = Skeleton.with_file file (fun fd size -> sha_of_range fd 0 size)

(* ---- Layout ---- *)

type loc = { rootdir : string; dir : string; marker : string; lpath : string }

let root_dir ~store ~root = store // key root

let locate ~store ~root ~path =
  let rootdir = root_dir ~store ~root in
  let k = key path in
  { rootdir; dir = rootdir // "p" // String.sub k 0 2 // k; marker = rootdir // "pending" // k; lpath = path }

let file_of loc seq ext = loc.dir // Printf.sprintf "%d.%s" seq ext
let block_file loc sha = loc.dir // "blocks" // sha

(* ---- The index ---- *)

let header = "unison-skeleton-chain 1"

let write_index loc (chain : chain) =
  let b = Buffer.create 512 in
  Printf.bprintf b "%s\npath %s\nnext %d\n" header (String.escaped chain.path) chain.next;
  (match chain.pending with
   | Some (seq, time) -> Printf.bprintf b "pending %d %.6f\n" seq time
   | None -> ());
  List.iter (fun v ->
    Printf.bprintf b "version %d %.6f %d %s %s %s %s %d %s %d\n" v.seq v.time v.size v.sha256
      (match v.kind with Skel -> "skeleton" | Whole -> "whole")
      v.format v.record_sha256 v.record_bytes
      (match v.stored with Full -> "full" | Delta base -> Printf.sprintf "delta:%d" base | File -> "file")
      v.stored_bytes) chain.versions;
  mkdir_p loc.dir;
  write_string_atomic (loc.dir // "index") (Buffer.contents b)

let read_index loc =
  let file = loc.dir // "index" in
  if not (Sys.file_exists file) then { path = loc.lpath; next = 1; pending = None; versions = [] }
  else begin
    let bad () = failwith (file ^ ": not a skeleton chain this version reads") in
    let num s = match int_of_string_opt s with Some n when n >= 0 -> n | _ -> bad () in
    let time s = match float_of_string_opt s with Some t -> t | None -> bad () in
    match String.split_on_char '\n' (read_file file) with
    | first :: lines when first = header ->
        List.fold_left (fun chain line ->
          match String.split_on_char ' ' line with
          | [ "" ] -> chain
          | "path" :: _ ->
              let escaped = String.sub line 5 (String.length line - 5) in
              { chain with path = (try Scanf.unescaped escaped with _ -> bad ()) }
          | [ "next"; n ] -> { chain with next = num n }
          | [ "pending"; seq; t ] -> { chain with pending = Some (num seq, time t) }
          | [ "version"; seq; t; size; sha256; kind; format; rsha; rbytes; stored; sbytes ] ->
              let kind = match kind with "skeleton" -> Skel | "whole" -> Whole | _ -> bad () in
              let stored = match stored with
                | "full" -> Full
                | "file" -> File
                | s when String.length s > 6 && String.sub s 0 6 = "delta:" ->
                    Delta (num (String.sub s 6 (String.length s - 6)))
                | _ -> bad () in
              let v = { seq = num seq; time = time t; size = num size; sha256; kind; format;
                        record_sha256 = rsha; record_bytes = num rbytes; stored;
                        stored_bytes = num sbytes } in
              { chain with versions = chain.versions @ [ v ] }
          | _ -> bad ())
          { path = loc.lpath; next = 1; pending = None; versions = [] } lines
    | _ -> bad ()
  end

(* ---- Records: a version's block map and skeleton bytes as one string ---- *)

let record_magic = "SKR1"

let unhex s =
  String.init (String.length s / 2) (fun i -> Char.chr (int_of_string ("0x" ^ String.sub s (2 * i) 2)))

let encode_record (r : record) =
  let b = Buffer.create (String.length r.bytes + 256) in
  let num = SkeletonDelta.add_varint b in
  let str s = num (String.length s); Buffer.add_string b s in
  Buffer.add_string b record_magic;
  str r.format;
  num r.size;
  num (List.length r.blocks);
  List.iter (fun x ->
    (* The offset first: it is what a metadata edit changes, and the rest of
       the entry then matches the next version's as one run. *)
    num x.b.Skeleton.at; num x.b.Skeleton.len; str x.b.Skeleton.role;
    Buffer.add_string b (unhex x.b.Skeleton.mark);
    Buffer.add_string b (unhex x.sha)) r.blocks;
  str r.bytes;
  Buffer.contents b

let decode_record s =
  let bad why = failwith ("bad skeleton record: " ^ why) in
  if String.length s < 4 || String.sub s 0 4 <> record_magic then bad "magic";
  let pos = ref 4 in
  let num () = try SkeletonDelta.read_varint s pos with SkeletonDelta.Corrupt m -> bad m in
  let raw n =
    if n < 0 || n > String.length s - !pos then bad "truncated";
    let v = String.sub s !pos n in
    pos := !pos + n; v in
  let str () = raw (num ()) in
  let format = str () in
  let size = num () in
  let count = num () in
  if count > String.length s then bad "block count";
  let blocks = List.init count (fun _ ->
      let at = num () in
      let len = num () in
      let role = str () in
      let mark = SemanticHash.hex (raw 16) in
      let sha = SemanticHash.hex (raw 32) in
      { b = { Skeleton.at; len; mark; role }; sha }) in
  let bytes = str () in
  if !pos <> String.length s then bad "trailing bytes";
  ignore (List.fold_left (fun stop x ->
    if x.b.Skeleton.at < stop || x.b.Skeleton.at + x.b.Skeleton.len > size then bad "blocks out of order";
    x.b.Skeleton.at + x.b.Skeleton.len) 0 blocks);
  let outside = size - List.fold_left (fun n x -> n + x.b.Skeleton.len) 0 blocks in
  if String.length bytes <> outside then bad "skeleton length";
  { format; size; blocks; bytes }

(* A version's record, through its chain of deltas, each checked against its
   own SHA-256. *)
let rec load_encoded loc chain v =
  let text = match v.stored with
    | Full -> read_file (file_of loc v.seq "full")
    | Delta base_seq ->
        let base = match List.find_opt (fun b -> b.seq = base_seq) chain.versions with
          | Some b when b.kind = Skel && b.seq > v.seq -> load_encoded loc chain b
          | _ -> failwith (Printf.sprintf "version %d needs version %d, which is not kept" v.seq base_seq) in
        (try SkeletonDelta.apply ~base ~delta:(read_file (file_of loc v.seq "delta"))
         with SkeletonDelta.Corrupt m -> failwith (Printf.sprintf "version %d: %s" v.seq m))
    | File -> failwith "a whole version has no skeleton record" in
  if hex_of text <> v.record_sha256 then
    failwith (Printf.sprintf "the stored skeleton of version %d does not match its SHA-256" v.seq);
  text

let load_record loc chain v = decode_record (load_encoded loc chain v)

(* ---- Rebuilding ---- *)

(* Files that may hold blocks, in the order they are asked. *)
type sources = {
  files : string list;
  tables : (string, (int * string, int) Hashtbl.t) Hashtbl.t;   (* (len, mark) -> offsets *)
  shas : (string * int * int, string) Hashtbl.t;                (* whole-block SHA-256 *)
}

let make_sources files = { files; tables = Hashtbl.create 4; shas = Hashtbl.create 16 }

let table sources file =
  match Hashtbl.find_opt sources.tables file with
  | Some t -> t
  | None ->
      let t = Hashtbl.create 16 in
      (try
         Skeleton.with_file file (fun fd size ->
           (* Hashtbl.find_all gives the latest first: add in reverse file order. *)
           List.iter (fun (len, mark, at) -> Hashtbl.add t (len, mark) at)
             (List.rev (Skeleton.marked_blocks fd size)))
       with Failure _ | Unix.Unix_error _ -> ());
      Hashtbl.replace sources.tables file t;
      t

let block_sha sources file at len =
  match Hashtbl.find_opt sources.shas (file, at, len) with
  | Some s -> s
  | None ->
      let s = Skeleton.with_file file (fun fd _ -> sha_of_range fd at len) in
      Hashtbl.replace sources.shas (file, at, len) s;
      s

(* Where a block's bytes are: (file, offset).  A candidate is a block of a
   source file with the same length and mark; a mark covers only a block's two
   ends, so with [exact] a candidate counts only when its whole SHA-256 is the
   block's.  A kept block is named by that SHA-256. *)
let find_block loc sources ~exact x =
  let len = x.b.Skeleton.len in
  let in_file file =
    List.find_map (fun at ->
        if not exact || block_sha sources file at len = x.sha then Some (file, at) else None)
      (Hashtbl.find_all (table sources file) (len, x.b.Skeleton.mark)) in
  match List.find_map in_file sources.files with
  | Some found -> Some found
  | None ->
      let kept = block_file loc x.sha in
      if is_regular kept && file_size kept = len then Some (kept, 0) else None

exception Missing of string

(* Write a record's content with [write]; the SHA-256 of what was written. *)
let rebuild loc sources ~exact (r : record) write =
  let h = SemanticHash.create () in
  let put s o n = SemanticHash.feed h (Bytes.unsafe_of_string s) o n; write s o n in
  let pos = ref 0 and skel = ref 0 in
  List.iter (fun x ->
    let n = x.b.Skeleton.at - !pos in
    put r.bytes !skel n;
    skel := !skel + n;
    (match find_block loc sources ~exact x with
     | None ->
         raise (Missing (Printf.sprintf "block %s (%d bytes) is in no later version and not kept"
                           x.b.Skeleton.role x.b.Skeleton.len))
     | Some (file, at) ->
         Skeleton.with_file file (fun fd _ ->
           pump fd at x.b.Skeleton.len (fun buf k -> put (Bytes.unsafe_to_string buf) 0 k)));
    pos := x.b.Skeleton.at + x.b.Skeleton.len) r.blocks;
  put r.bytes !skel (String.length r.bytes - !skel);
  SemanticHash.hex (SemanticHash.finish h)

(* The files a version's blocks may come from: the current file, a pending
   replaced file, and the chain's whole versions. *)
let source_files loc chain ~live ~with_pending =
  (match live with Some f when is_regular f -> [ f ] | _ -> [])
  @ (match chain.pending with
     | Some (seq, _) when with_pending && is_regular (file_of loc seq "pending") ->
         [ file_of loc seq "pending" ]
     | _ -> [])
  @ List.rev (List.filter_map (fun v ->
      if v.kind = Whole then Some (file_of loc v.seq "whole") else None) chain.versions)

(* Write version [v]'s content: [write] receives it in pieces, [reset] is
   called when what was written so far has to be discarded.  Fails unless the
   SHA-256 of the result is the version's. *)
let produce loc chain sources v ~write ~reset =
  match v.kind with
  | Whole ->
      let h = SemanticHash.create () in
      Skeleton.with_file (file_of loc v.seq "whole") (fun fd size ->
        pump fd 0 size (fun buf k ->
          SemanticHash.feed h buf 0 k; write (Bytes.unsafe_to_string buf) 0 k));
      if SemanticHash.hex (SemanticHash.finish h) <> v.sha256 then
        failwith (Printf.sprintf "the whole file kept for version %d does not match its SHA-256" v.seq)
  | Skel ->
      let r = load_record loc chain v in
      (* First by marks alone; when that gives another content (a block
         changed between its two ends), again with whole-block checks. *)
      let first = try rebuild loc sources ~exact:false r write with Missing _ -> "" in
      if first <> v.sha256 then begin
        reset ();
        let second = rebuild loc sources ~exact:true r write in
        if second <> v.sha256 then
          failwith (Printf.sprintf "version %d rebuilt to another SHA-256" v.seq)
      end

(* ---- Adding a version, pruning, sweeping ---- *)

let version_files v =
  match v.kind, v.stored with
  | Whole, _ -> [ Printf.sprintf "%d.whole" v.seq ]
  | Skel, Delta _ -> [ Printf.sprintf "%d.delta" v.seq ]
  | Skel, _ -> [ Printf.sprintf "%d.full" v.seq ]

let rmdir_noerr dir = try Unix.rmdir dir with Unix.Unix_error _ -> ()

(* Remove what the index no longer names: replaced and pruned files, and kept
   blocks no kept version has.  Leaves everything when a record cannot be
   read. *)
let sweep loc chain =
  let keep = "index" :: "blocks"
             :: (match chain.pending with Some (seq, _) -> [ Printf.sprintf "%d.pending" seq ] | None -> [])
             @ List.concat_map version_files chain.versions in
  let names dir = try Array.to_list (Sys.readdir dir) with Sys_error _ -> [] in
  List.iter (fun name -> if not (List.mem name keep) then remove_noerr (loc.dir // name)) (names loc.dir);
  let blocks = loc.dir // "blocks" in
  (match names blocks with
   | [] -> ()
   | kept ->
       (match
          List.concat_map (fun v ->
            if v.kind = Skel then List.map (fun x -> x.sha) (load_record loc chain v).blocks else [])
            chain.versions
        with
        | needed -> List.iter (fun name -> if not (List.mem name needed) then remove_noerr (blocks // name)) kept
        | exception (Failure _ | Sys_error _ | Unix.Unix_error _) -> ()));
  rmdir_noerr blocks;
  if chain.versions = [] && chain.pending = None then begin
    remove_noerr (loc.dir // "index");
    rmdir_noerr loc.dir;
    rmdir_noerr (Filename.dirname loc.dir)
  end

let rec drop_oldest depth versions =
  if List.length versions > max depth 0 then drop_oldest depth (List.tl versions) else versions

(* ---- Settling a pending replaced file ---- *)

type outcome =
  | Nothing            (* there was no pending file *)
  | Unchanged          (* the file was not replaced after all: no version *)
  | Kept_skeleton of int * int   (* version, bytes of kept blocks it added *)
  | Kept_whole of int * string   (* version, why it is not a skeleton *)

(* The SHA-256 of an open file and of each of its blocks, in one pass. *)
let hash_with_blocks fd size (blocks : Skeleton.block list) =
  let whole = SemanticHash.create () in
  let pos = ref 0 in
  let shas = List.map (fun (b : Skeleton.block) ->
      pump fd !pos (b.Skeleton.at - !pos) (fun buf k -> SemanticHash.feed whole buf 0 k);
      let c = SemanticHash.create () in
      pump fd b.Skeleton.at b.Skeleton.len (fun buf k ->
        SemanticHash.feed whole buf 0 k; SemanticHash.feed c buf 0 k);
      pos := b.Skeleton.at + b.Skeleton.len;
      SemanticHash.hex (SemanticHash.finish c)) blocks in
  pump fd !pos (size - !pos) (fun buf k -> SemanticHash.feed whole buf 0 k);
  SemanticHash.hex (SemanticHash.finish whole), shas

exception Whole_instead of string

(* A skeleton larger than this is not worth keeping as one. *)
let max_skeleton = 16 * 1024 * 1024

(* For tests: called just before a new skeleton version is rebuilt and
   checked; raising [Failure] there stands for a version whose skeleton does
   not rebuild it. *)
let before_check : (unit -> unit) ref = ref (fun () -> ())

let remove_marker loc =
  remove_noerr loc.marker;
  rmdir_noerr (Filename.dirname loc.marker)

(* Settle the path's pending file against [live], the file now at the path
   (or nothing, when [gone]).  The pending file is deleted only after the
   version it becomes has been rebuilt from the store and [live] and its
   SHA-256 checked; otherwise it is kept whole. *)
let settle_loc loc ~live ~gone ~depth =
  let chain = read_index loc in
  match chain.pending with
  | None ->
      (* A marker without a pending item: a run stopped after writing the
         index.  Remove what it left behind. *)
      if Sys.file_exists loc.marker then sweep loc chain;
      remove_marker loc; Nothing
  | Some (seq, time) ->
      let pfile = file_of loc seq "pending" in
      (* A run that stopped between renaming the pending file to a whole
         version and writing the index: take it back and settle it again. *)
      if not (is_regular pfile) && is_regular (file_of loc seq "whole") then
        Unix.rename (file_of loc seq "whole") pfile;
      if not (is_regular pfile) then begin
        (* The index named it but the file was never taken. *)
        let chain = { chain with pending = None } in
        write_index loc chain; sweep loc chain; remove_marker loc; Nothing
      end else begin
        let live = if (not gone) && is_regular live then Some live else None in
        let psize = file_size pfile in
        let sk = try Some (Skeleton.build pfile) with Failure _ | Unix.Unix_error _ -> None in
        let psha, block_shas =
          Skeleton.with_file pfile (fun fd size ->
            hash_with_blocks fd size (match sk with Some s -> s.Skeleton.blocks | None -> [])) in
        let same = match live with
          | Some f -> file_size f = psize && sha_of_file f = psha
          | None -> false in
        if same then begin
          let chain = { chain with pending = None } in
          write_index loc chain; sweep loc chain; remove_marker loc; Unchanged
        end else begin
          let sources = make_sources (source_files loc { chain with pending = None } ~live ~with_pending:false) in
          let as_skeleton () =
            let sk = match sk with
              | Some s -> s
              | None -> raise (Whole_instead "no walker for this format and larger than 1 MiB") in
            if sk.Skeleton.blocks <> [] && live = None then
              raise (Whole_instead "no later file to hold its blocks");
            (* A file whose structure leaves most of it outside any block
               gains nothing from a skeleton. *)
            if String.length sk.Skeleton.bytes > max_skeleton then
              raise (Whole_instead "its skeleton would be larger than 16 MiB");
            let blocks = List.map2 (fun b sha -> { b; sha }) sk.Skeleton.blocks block_shas in
            let r = { format = sk.Skeleton.format; size = sk.Skeleton.size; blocks; bytes = sk.Skeleton.bytes } in
            (* Keep every block the later file does not hold, byte for byte. *)
            let captured = ref 0 in
            List.iter (fun x ->
              let held = match live with
                | Some f ->
                    List.exists (fun at -> block_sha sources f at x.b.Skeleton.len = x.sha)
                      (Hashtbl.find_all (table sources f) (x.b.Skeleton.len, x.b.Skeleton.mark))
                | None -> false in
              let kept = block_file loc x.sha in
              if not held && not (is_regular kept && file_size kept = x.b.Skeleton.len) then begin
                mkdir_p (Filename.dirname kept);
                Skeleton.with_file pfile (fun fd _ ->
                  write_atomic kept (fun out ->
                    pump fd x.b.Skeleton.at x.b.Skeleton.len (fun buf k ->
                      write_all out (Bytes.unsafe_to_string buf) 0 k)));
                captured := !captured + x.b.Skeleton.len
              end) blocks;
            let text = encode_record r in
            write_string_atomic (file_of loc seq "full") text;
            (* The check that counts: rebuild it from what will remain. *)
            let v = { seq; time; size = psize; sha256 = psha; kind = Skel; format = r.format;
                      record_sha256 = hex_of text; record_bytes = String.length text;
                      stored = Full; stored_bytes = String.length text } in
            let probe = { chain with pending = None; versions = chain.versions @ [ v ] } in
            (try !before_check (); produce loc probe sources v ~write:(fun _ _ _ -> ()) ~reset:(fun () -> ())
             with Failure m | Missing m -> raise (Whole_instead ("its skeleton did not rebuild it: " ^ m)));
            (* The previous newest skeleton becomes a delta against this one. *)
            let newest_skeleton =
              List.fold_left (fun found p -> if p.kind = Skel then Some p else found) None chain.versions in
            let versions = match newest_skeleton with
              | Some prev when prev.stored = Full ->
                  let prev' =
                    try
                      let base = load_encoded loc chain prev in
                      let delta = SkeletonDelta.make ~base:text ~target:base in
                      if String.length delta < String.length base
                         && SkeletonDelta.apply ~base:text ~delta = base then begin
                        write_string_atomic (file_of loc prev.seq "delta") delta;
                        { prev with stored = Delta seq; stored_bytes = String.length delta }
                      end else prev
                    with Failure _ | Sys_error _ | SkeletonDelta.Corrupt _ -> prev in
                  List.map (fun p -> if p.seq = prev.seq then prev' else p) chain.versions
              | _ -> chain.versions in
            versions @ [ v ], Kept_skeleton (seq, !captured) in
          let versions, outcome =
            try as_skeleton ()
            with
            | Whole_instead why | Failure why ->
                remove_noerr (file_of loc seq "full");
                Unix.rename pfile (file_of loc seq "whole");
                let v = { seq; time; size = psize; sha256 = psha; kind = Whole; format = "-";
                          record_sha256 = "-"; record_bytes = 0; stored = File; stored_bytes = psize } in
                chain.versions @ [ v ], Kept_whole (seq, why) in
          let chain = { chain with pending = None; versions = drop_oldest depth versions } in
          write_index loc chain;
          sweep loc chain;
          remove_marker loc;
          outcome
        end
      end

let settle ~store ~root ~path ~live ?(gone = false) ~depth () =
  settle_loc (locate ~store ~root ~path) ~live ~gone ~depth

(* ---- Stashing a file that is about to be replaced or deleted ---- *)

let note_root ~store ~root =
  let dir = root_dir ~store ~root in
  if not (Sys.file_exists (dir // "root")) then begin
    mkdir_p dir;
    write_string_atomic (dir // "root") (root ^ "\n")
  end

(* Take [file], the current content of [path], as a pending item: by renaming
   it away ([`Move], for a file being deleted) or by copying it ([`Copy];
   [clone] may make the copy and say so).  A pending item left by an earlier
   run is settled first.  Returns whether the file was moved away. *)
let stash ~store ~root ~path ~file ~how ?(clone = fun _ _ -> false) ~depth () =
  let loc = locate ~store ~root ~path in
  ignore (settle_loc loc ~live:file ~gone:false ~depth);
  note_root ~store ~root;
  let chain = read_index loc in
  let seq = chain.next in
  mkdir_p (Filename.dirname loc.marker);
  write_string_atomic loc.marker (String.escaped path ^ "\n");
  write_index loc { chain with next = seq + 1; pending = Some (seq, Unix.gettimeofday ()) };
  let dst = file_of loc seq "pending" in
  let copy () =
    let cloned = try clone file dst with _ -> false in
    if not (cloned && is_regular dst) then begin remove_noerr dst; copy_file file dst end in
  match how with
  | `Copy -> copy (); false
  | `Move ->
      (try Unix.rename file dst; true
       with Unix.Unix_error _ -> copy (); false)

(* Pending items of a root, as their paths. *)
let pending_paths ~store ~root =
  let dir = root_dir ~store ~root // "pending" in
  let names = try Array.to_list (Sys.readdir dir) with Sys_error _ -> [] in
  List.filter_map (fun name ->
    if Filename.check_suffix name ".tmp" then None
    else try Some (Scanf.unescaped (String.trim (read_file (dir // name)))) with _ -> None) names

(* Settle the pending items of a root: all of them, or those at or under
   [under].  [live] maps a path to the file now there.  Returns the outcomes,
   and the paths that could not be settled with the reason; those stay
   pending. *)
let settle_all ~store ~root ?under ~live ~depth () =
  let wanted path = match under with
    | None -> true
    | Some "" -> true
    | Some u ->
        path = u || (String.length path > String.length u
                     && String.sub path 0 (String.length u + 1) = u ^ "/") in
  List.fold_left (fun (done_, failed) path ->
    if not (wanted path) then (done_, failed)
    else
      match settle ~store ~root ~path ~live:(live path) ~depth () with
      | outcome -> ((path, outcome) :: done_, failed)
      | exception (Failure m | Sys_error m) -> (done_, (path, m) :: failed)
      | exception Unix.Unix_error (e, f, _) -> (done_, (path, f ^ ": " ^ Unix.error_message e) :: failed))
    ([], []) (pending_paths ~store ~root)

(* ---- Reading the store ---- *)

let chain ~store ~root ~path =
  let loc = locate ~store ~root ~path in
  if Sys.file_exists (loc.dir // "index") then Some (read_index loc) else None

(* Every path of a root that has a chain, sorted. *)
let paths ~store ~root =
  let p = root_dir ~store ~root // "p" in
  let names dir = try List.sort compare (Array.to_list (Sys.readdir dir)) with Sys_error _ -> [] in
  List.sort compare
    (List.concat_map (fun fan ->
       List.filter_map (fun k ->
         let dir = p // fan // k in
         if Sys.file_exists (dir // "index") then
           (try Some (read_index { rootdir = ""; dir; marker = ""; lpath = "" }).path with Failure _ -> None)
         else None) (names (p // fan))) (names p))

(* Bytes the store holds for a path: (index and records, kept blocks, whole
   and pending files). *)
let stored_bytes ~store ~root ~path =
  let loc = locate ~store ~root ~path in
  let size f = try file_size f with Unix.Unix_error _ -> 0 in
  let names dir = try Array.to_list (Sys.readdir dir) with Sys_error _ -> [] in
  List.fold_left (fun (records, blocks, wholes) name ->
    if name = "blocks" then
      (records, List.fold_left (fun n b -> n + size (loc.dir // "blocks" // b)) blocks (names (loc.dir // "blocks")), wholes)
    else if Filename.check_suffix name ".whole" || Filename.check_suffix name ".pending" then
      (records, blocks, wholes + size (loc.dir // name))
    else (records + size (loc.dir // name), blocks, wholes)) (0, 0, 0) (names loc.dir)

(* Write a kept version's content with [write], checked against its SHA-256;
   [reset] discards what was written so far.  [live] is the file now at the
   path, when there is one. *)
let restore ~store ~root ~path ~live ~seq ~write ~reset =
  let loc = locate ~store ~root ~path in
  let chain = read_index loc in
  match List.find_opt (fun v -> v.seq = seq) chain.versions with
  | None -> failwith (Printf.sprintf "version %d of %s is not kept" seq path)
  | Some v ->
      let sources = make_sources (source_files loc chain ~live ~with_pending:true) in
      (try produce loc chain sources v ~write ~reset
       with Missing m -> failwith (Printf.sprintf "version %d: %s" seq m))

(* Rebuild every kept version of a path to nowhere; each with its result. *)
let verify ~store ~root ~path ~live =
  let loc = locate ~store ~root ~path in
  let chain = read_index loc in
  let sources = make_sources (source_files loc chain ~live ~with_pending:true) in
  List.map (fun v ->
    v,
    (match produce loc chain sources v ~write:(fun _ _ _ -> ()) ~reset:(fun () -> ()) with
     | () -> None
     | exception (Failure m | Missing m | Sys_error m) -> Some m
     | exception Unix.Unix_error (e, f, _) -> Some (f ^ ": " ^ Unix.error_message e)))
    chain.versions
