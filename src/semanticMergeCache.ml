(* This private owner store has the same trust boundary as local Unison state.
   Its checksums detect corruption; they are not authentication against its UID. *)
let preference = Prefs.createBool "semanticmergebasecache" false ~local:true
  ~send_value:(fun _ -> false) ~category:(`Advanced `Syncprocess)
  "retain compact common DNG XMP bases for built-in scalar merging"
  "Opt-in local private metadata bases bound to the previous common archive. \
   Does not replace original preservation or enable merging without a merge rule."
let enabled () = Prefs.read preference && Sys.os_type <> "Win32"
let fail reason = raise (Util.Transient ("DNG metadata base cache: " ^ reason))
let directory () =
  let path = Util.fileInUnisonDir "semantic-merge-bases-v0" in
  (try Unix.mkdir path 0o700 with Unix.Unix_error (Unix.EEXIST,_,_) -> ());
  let stat = Unix.lstat path in
  if stat.Unix.st_kind <> Unix.S_DIR || stat.st_uid <> Unix.getuid () ||
     stat.st_perm land 0o777 <> 0o700 then fail "private owned directory required";
  path
let shard dir identity =
  let path = Filename.concat dir (String.sub (SemanticHash.hex identity) 0 3) in
  (try Unix.mkdir path 0o700 with Unix.Unix_error (Unix.EEXIST,_,_) -> ());
  let stat=Unix.lstat path in
  if stat.Unix.st_kind<>Unix.S_DIR || stat.st_uid<>Unix.getuid () ||
     stat.st_perm land 0o777<>0o700 then fail "private owned shard required";
  path
let key ~root ~path ~fingerprint =
  if Os.isPseudoFingerprint fingerprint then fail "pseudo archive fingerprint";
  let fields = ["SBC/0";Fspath.toString root;Path.toString path;
    Os.fullfingerprint_to_string fingerprint;XmpMerge.policy;"parser=1"] in
  SemanticHash.string (String.concat "" (List.map (fun value ->
    Printf.sprintf "%d:" (String.length value) ^ value) fields))
let same a b = a.Unix.st_dev=b.Unix.st_dev && a.st_ino=b.st_ino &&
  a.st_size=b.st_size && a.st_mtime=b.st_mtime && a.st_ctime=b.st_ctime
let read filename =
  let before = Unix.lstat filename in
  if before.Unix.st_kind <> Unix.S_REG || before.st_uid <> Unix.getuid () ||
     before.st_perm land 0o777 <> 0o600 || before.st_nlink <> 1 ||
     before.st_size < 72 || before.st_size > SemanticDelta.max_base_cache_size+72 then
    fail "untrusted or oversized record";
  let fd = Unix.openfile filename [Unix.O_RDONLY;Unix.O_CLOEXEC;Unix.O_NONBLOCK] 0 in
  (* Exception patterns install protection before evaluating the body. Unlike
     allocating Fun.protect callbacks here, no setup allocation follows open. *)
  match
    if not (same before (Unix.fstat fd)) then fail "record name changed";
    let bytes = Bytes.create before.st_size in
    let rec fill position = if position < Bytes.length bytes then
      let count = Unix.read fd bytes position (Bytes.length bytes-position) in
      if count=0 then fail "truncated record" else fill (position+count) in
    fill 0;
    if not (same before (Unix.fstat fd) && same before (Unix.lstat filename)) then
      fail "record changed during read";
    Bytes.to_string bytes
  with
  | value -> Unix.close fd; value
  | exception error -> Unix.close fd; raise error
let body identity proof =
  let payload = "SBC\000\000\000\000\000" ^ identity ^ SemanticDelta.encode_base_cache proof in
  payload ^ SemanticHash.string payload
let unpack identity encoded =
  let length=String.length encoded in
  if length<72 || String.sub encoded 0 8 <> "SBC\000\000\000\000\000" ||
     String.sub encoded 8 32 <> identity then fail "archive/path binding mismatch";
  let payload=String.sub encoded 0 (length-32) in
  if SemanticHash.string payload <> String.sub encoded (length-32) 32 then
    fail "record checksum mismatch";
  match SemanticDelta.decode_base_cache (String.sub encoded 40 (length-72)) with
  | Ok proof -> proof | Error reason -> fail reason
let store ~root ~path ~fingerprint proof =
  if enabled () then begin
    let identity=key ~root ~path ~fingerprint in
    let dir=shard (directory ()) identity in
    let filename=Filename.concat dir (SemanticHash.hex identity) in
    let encoded=body identity proof in
    let present = try Some (read filename) with Unix.Unix_error (Unix.ENOENT,_,_) -> None in
    match present with
    | Some existing -> if existing<>encoded then fail "common fingerprint already has another base"
    | None ->
      (* Bounded scan; refuse new entries when full. Retain earlier bases for
         partial-commit recovery instead of silently evicting their authority. *)
      let handle=Unix.opendir dir in
      (match
        let rec count total =
          if total>=4096 then fail "entry capacity reached";
          match Unix.readdir handle with
          | "." | ".." -> count total
          | _ -> count (total+1)
          | exception End_of_file -> () in count 0
       with
       | () -> Unix.closedir handle
       | exception error -> Unix.closedir handle; raise error);
      (* Prepare names, flags and close state before acquiring the descriptor.
         O_EXCL makes a collision a decline, never authority to remove a peer's
         file. Random names are collision avoidance inside an owned directory,
         not a security token. Avoid open_temp_file's post-open channel/tuple
         allocations by using a raw descriptor and a protected partial-write loop. *)
      let temporary=Filename.concat dir (Printf.sprintf ".base-%d-%08x-%08x.tmp"
        (Unix.getpid ()) (Random.bits ()) (Random.bits ())) in
      let flags=[Unix.O_WRONLY;Unix.O_CREAT;Unix.O_EXCL;Unix.O_CLOEXEC;Unix.O_NONBLOCK] in
      let closed=ref false in
      let fd=Unix.openfile temporary flags 0o600 in
      match
        Unix.fchmod fd 0o600;
        let rec write position =
          if position < String.length encoded then begin
            let count = try Unix.write_substring fd encoded position
              (min 65536 (String.length encoded-position))
              with Unix.Unix_error (Unix.EINTR,_,_) -> -1 in
            if count=0 then fail "zero-length record write";
            write (if count<0 then position else position+count)
          end in
        write 0;
        Unix.fsync fd;
        (* Never retry a failed close on a possibly reused descriptor number. *)
        closed:=true; Unix.close fd;
        (* No replacement: a concurrent capture may only publish equal bytes. *)
        (try Unix.link temporary filename with
         | Unix.Unix_error (Unix.EEXIST,_,_) ->
             if read filename<>encoded then fail "concurrent base differs");
        Unix.unlink temporary
      with
      | () -> ()
      | exception error ->
          if not !closed then (closed:=true; try Unix.close fd with _ -> ());
          (try Unix.unlink temporary with Unix.Unix_error (Unix.ENOENT,_,_) -> ());
          raise error
  end
let load ~root ~path ~fingerprint =
  if not (enabled ()) then None else
  try
    let identity=key ~root ~path ~fingerprint in
    let filename=Filename.concat (shard (directory ()) identity) (SemanticHash.hex identity) in
    Some (unpack identity (read filename))
  with Util.Transient _ | Unix.Unix_error _ | Invalid_argument _ -> None
