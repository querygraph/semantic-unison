(* This private owner store has the same trust boundary as local Unison state.
   Its checksums detect corruption; they are not authentication against its UID. *)
let preference = Prefs.createBool "semanticmergebasecache" false ~local:true
  ~send_value:(fun _ -> false) ~category:(`Advanced `Syncprocess)
  "retain compact common DNG XMP bases for built-in scalar merging"
  "Opt-in local private metadata bases bound to the previous common archive. \
   Does not replace original preservation or enable merging without a merge rule."
let enabled () = Prefs.read preference && Sys.os_type <> "Win32"
let max_mib = Prefs.makeEndpointLocal (Prefs.createInt "semanticmergecachemaxmib" 1024
  ~local:true ~category:(`Advanced `Syncprocess)
  "maximum charged compact merge-base payload in MiB"
  "Endpoint-local monotonic capture reservations, 1..65536 MiB. Existing \
   recovery bases are never evicted; abandoned reservations can exhaust capacity.")
let max_entries = Prefs.makeEndpointLocal (Prefs.createInt "semanticmergecachemaxentries" 1048576
  ~local:true ~category:(`Advanced `Syncprocess)
  "maximum compact merge-base capture reservations"
  "Endpoint-local monotonic reservation count, 1..16777216. Cooperating \
   processes sharing one state directory must use the same quota settings.")
let fail reason = raise (Util.Transient ("DNG metadata base cache: " ^ reason))
(* Joint synchronous cache scope. Every node is linked before acquisition; the
   existing uncertainty carrier lets earlier runtime layers retain admission
   without a dependency cycle on this module. *)
type file_owner = { file:NotificationPipe.t; filename:string; next_file:file_owner option }
type directory_owner = { directory:DirectoryOwner.t; next_directory:directory_owner option }
type temporary_phase = No_temporary | Temporary_opening | Temporary_owned | Unlink_attempted | Temporary_removed | Unlink_uncertain
type ownership = {
  anchor:NotificationPipe.t;
  mutable files:file_owner option; mutable directories:directory_owner option;
  mutable temporary:string; mutable temporary_phase:temporary_phase;
  mutable temporary_owner:file_owner option;
  mutable temporary_identity:Unix.stats option;
  mutable temporary_error:exn; mutable temporary_failed:bool;
  mutable operation_error:exn; mutable operation_failed:bool;
  mutable unknown_error:exn; mutable retained:bool;
  mutable previous:ownership option; mutable next:ownership option;
  link:ownership option;
}
let owners=ref None
let prepare_owner () =
  let anchor=NotificationPipe.prepare () in
  let rec owner={anchor;files=None;directories=None;temporary="";temporary_phase=No_temporary;
    temporary_owner=None;temporary_identity=None;temporary_error=Exit;temporary_failed=false;
    operation_error=Exit;operation_failed=false;unknown_error=Exit;retained=false;
    previous=None;next=None;link=Some owner} in
  NotificationPipe.keep_owner anchor (fun()->ignore(Sys.opaque_identity owner));
  owner.next<- !owners;
  (match !owners with None->() | Some first->first.previous<-owner.link);
  owners:=owner.link;owner
let forget_owner owner =
  (match owner.previous with None->owners:=owner.next | Some p->p.next<-owner.next);
  (match owner.next with None->() | Some n->n.previous<-owner.previous);
  owner.previous<-None;owner.next<-None
let note_unknown owner error =
  if not owner.retained then owner.unknown_error<-error;
  owner.retained<-true
let raise_unknown owner = NotificationPipe.retain_unsettled owner.anchor owner.unknown_error
let uncertain = function
  | NotificationPipe.Uncertain _ | DirectoryOwner.Uncertain _
  | SemanticFile.Close_uncertain _ | DngComponents.Cache_ownership_uncertain _
  | StagePublication.Ownership_uncertain _ -> true | _ -> false
let rec remember_files error = function
  | None->() | Some node->NotificationPipe.remember_failure node.file error;remember_files error node.next_file
let rec remember_directories error = function
  | None->() | Some node->DirectoryOwner.remember_failure node.directory error;remember_directories error node.next_directory
let remember_owner owner error =
  if not owner.operation_failed then begin owner.operation_error<-error;owner.operation_failed<-true end;
  NotificationPipe.remember_failure owner.anchor error;
  remember_files error owner.files;remember_directories error owner.directories
let open_file ?(temporary=false) owner filename flags mode =
  let file=NotificationPipe.prepare () in
  NotificationPipe.keep_owner file (fun()->ignore(Sys.opaque_identity owner));
  let node={file;filename;next_file=owner.files} in
  owner.files<-Some node;
  if temporary then begin owner.temporary_owner<-Some node;owner.temporary_phase<-Temporary_opening end;
  let fd=Unix.openfile filename flags mode in
  NotificationPipe.adopt_read file fd;
  if temporary then owner.temporary_phase<-Temporary_owned;
  node
let descriptor node=fst(NotificationPipe.descriptors node.file)
let close_file owner node =
  try NotificationPipe.close_all node.file
  with NotificationPipe.Uncertain _ as error->note_unknown owner error;raise_unknown owner
let open_directory owner path =
  let directory=DirectoryOwner.prepare () in
  let node={directory;next_directory=owner.directories} in
  owner.directories<-Some node;
  DirectoryOwner.open_with directory path (fun()->());directory
let close_directory owner directory =
  try DirectoryOwner.close directory
  with DirectoryOwner.Uncertain _ as error->note_unknown owner error;raise_unknown owner
let rec close_files owner = function
  | None->() | Some node->
    (try NotificationPipe.close_all node.file with NotificationPipe.Uncertain _ as error->note_unknown owner error);
    close_files owner node.next_file
let rec close_directories owner = function
  | None->() | Some node->
    (try DirectoryOwner.close node.directory with DirectoryOwner.Uncertain _ as error->note_unknown owner error);
    close_directories owner node.next_directory
let remove_temporary owner =
  if owner.temporary_phase=Temporary_owned then begin
    try
      let expected=match owner.temporary_identity with Some s->s | None->fail "temporary identity unavailable" in
      let current=try Some(Unix.lstat owner.temporary) with Unix.Unix_error(Unix.ENOENT,_,_)->None in
      (match current with
       | None->owner.temporary_phase<-Temporary_removed
       | Some current->
          if current.Unix.st_dev<>expected.Unix.st_dev || current.st_ino<>expected.st_ino || current.st_kind<>Unix.S_REG then
            fail "temporary name no longer owned";
          owner.temporary_phase<-Unlink_attempted;
          Unix.unlink owner.temporary;owner.temporary_phase<-Temporary_removed)
    with error->
      owner.temporary_error<-error;owner.temporary_failed<-true;
      owner.temporary_phase<-Unlink_uncertain;note_unknown owner error;raise_unknown owner
  end
let reconcile_temporary owner =
  if owner.temporary_phase=Temporary_opening then begin
    match owner.temporary_owner with
    | Some node when NotificationPipe.read_held node.file ->
        (* An interruption after adoption but before the caller resumes cannot
           turn a created name into an unowned collision. Observe before close. *)
        owner.temporary_phase<-Temporary_owned;
        (try owner.temporary_identity<-Some(Unix.fstat(descriptor node))
         with error->owner.temporary_error<-error;owner.temporary_failed<-true;
           note_unknown owner error;raise_unknown owner)
    | Some node when NotificationPipe.settled node.file ->
        owner.temporary_phase<-No_temporary
    | _->note_unknown owner owner.unknown_error;raise_unknown owner
  end
let settle_owner owner =
  if owner.retained then raise_unknown owner;
  reconcile_temporary owner;
  close_files owner owner.files;close_directories owner owner.directories;
  if owner.retained then raise_unknown owner;
  remove_temporary owner;forget_owner owner
let rec refuse_retained = function
  | None->()
  | Some owner->if owner.retained then raise_unknown owner else refuse_retained owner.next
let with_owner work =
  (* A new same-process cache open/close must not interfere with the retained
     quota/namespace lifetime. Refuse before allocating or acquiring a scope. *)
  refuse_retained !owners;
  let owner=prepare_owner () in
  match work owner with
  | result->settle_owner owner;result
  | exception error->
      if uncertain error then begin note_unknown owner error;raise_unknown owner end;
      remember_owner owner error;settle_owner owner;raise error
let retained () =
  let rec loop acc=function None->List.rev acc | Some owner->loop(if owner.retained then owner::acc else acc)owner.next in
  loop [] !owners
let operation_cause owner=if owner.operation_failed then Some owner.operation_error else None
let uncertainty_cause owner=owner.unknown_error
let files owner=
  let rec loop acc=function None->List.rev acc | Some node->loop((node.filename,node.file)::acc)node.next_file in
  loop [] owner.files
let directories owner=
  let rec loop acc=function None->List.rev acc | Some node->loop(node.directory::acc)node.next_directory in
  loop [] owner.directories
let temporary owner=owner.temporary,owner.temporary_phase,owner.temporary_identity
let temporary_cause owner=if owner.temporary_failed then Some owner.temporary_error else None
let directory ?(legacy=false) () =
  let path = Util.fileInUnisonDir
    (if legacy then "semantic-merge-bases-v0" else "semantic-merge-bases-v1") in
  if not legacy then
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
(* Cooperative process owners reserve payload bytes before creating a record.
   Charges are monotonic: failed/interrupted captures can waste capacity, never
   make it available twice. This is not a bound on filesystem metadata or RSS. *)
let quota_limits () =
  let mib=Prefs.read max_mib and entries=Prefs.read max_entries in
  if mib<1 || mib>65536 || entries<1 || entries>16777216 then fail "invalid quota settings";
  Int64.mul (Int64.of_int mib) 1048576L,Int64.of_int entries
let quota_encode entries bytes =
  let payload=Printf.sprintf "SBQ1 %020Ld %020Ld\n" entries bytes in
  payload ^ SemanticHash.string payload
let quota_decode encoded =
  if String.length encoded<>79 then fail "quota ledger framing";
  let payload=String.sub encoded 0 47 in
  if SemanticHash.string payload<>String.sub encoded 47 32 ||
     String.sub payload 0 5<>"SBQ1 " || payload.[25]<>' ' || payload.[46]<>'\n' then
    fail "quota ledger checksum/format";
  let number offset =
    let text=String.sub payload offset 20 in
    String.iter (fun c -> if c<'0' || c>'9' then fail "quota counter syntax") text;
    try Int64.of_string text with Failure _ -> fail "quota counter overflow" in
  let entries=number 5 and bytes=number 26 in
  if entries<0L || entries>16777216L || bytes<0L || bytes>68719476736L then
    fail "quota counter range";
  entries,bytes
let empty_directory owner path =
  let handle=open_directory owner path in
  match
    let rec loop () = match DirectoryOwner.read handle with
    | "." | ".." -> loop ()
    | _ -> false
    | exception End_of_file -> true in loop ()
  with
  | value -> close_directory owner handle; value
  | exception error -> raise error
let reserve owner dir size =
  let quota_bytes,quota_entries=quota_limits () in
  let filename=Filename.concat dir ".quota-v1" in
  let before = try Some (Unix.lstat filename)
    with Unix.Unix_error (Unix.ENOENT,_,_) -> None in
  let trusted stat = stat.Unix.st_kind=Unix.S_REG && stat.st_uid=Unix.getuid () &&
    stat.st_perm land 0o777=0o600 && stat.st_nlink=1 && (stat.st_size=0 || stat.st_size=79) in
  (match before with Some stat when not(trusted stat) -> fail "untrusted quota ledger" | _ -> ());
  let flags = match before with
    | None -> [Unix.O_RDWR;Unix.O_CREAT;Unix.O_EXCL;Unix.O_CLOEXEC;Unix.O_NONBLOCK]
    | Some _ -> [Unix.O_RDWR;Unix.O_CLOEXEC;Unix.O_NONBLOCK] in
  let node=open_file owner filename flags 0o600 in
  let fd=descriptor node in
  match
    (match before with None -> Unix.fchmod fd 0o600 | Some _ -> ());
    let stat=Unix.fstat fd in
    if not(trusted stat) || not(same stat (Unix.lstat filename)) ||
       (match before with Some old -> not(same old stat) | None -> false) then
      fail "quota ledger changed";
    (* Never block the sole Lwt/archive owner behind another process. The caller
       treats a busy capture as best effort, exactly like other cache misses. *)
    Unix.lockf fd Unix.F_TLOCK 0;
    let stat=Unix.fstat fd in
    if not(same stat (Unix.lstat filename)) then fail "quota name changed";
    let entries,used = if stat.st_size=0 then begin
      (* A lost ledger never grants new capacity over surviving records. Only
         an empty managed tree can initialize; ambiguous state fails closed. *)
      let handle=open_directory owner dir in
      (match
        let rec loop count =
          if count>4096 then fail "quota initialization scan capacity";
          match DirectoryOwner.read handle with
          | "." | ".." | ".quota-v1" -> loop count
          | name ->
              if String.length name<>3 ||
                 not(String.for_all (fun c -> (c>='0' && c<='9') || (c>='a' && c<='f')) name) then
                fail "unknown managed cache entry";
              let path=Filename.concat dir name in
              let s=Unix.lstat path in
              if s.st_kind<>Unix.S_DIR || s.st_uid<>Unix.getuid () ||
                 s.st_perm land 0o777<>0o700 || not(empty_directory owner path) then
                fail "missing ledger with retained records";
              loop (count+1)
          | exception End_of_file -> () in loop 0
       with
       | () -> close_directory owner handle
       | exception error -> raise error);
      0L,0L
    end else begin
      let data=Bytes.create 79 in
      let rec fill offset = if offset<79 then
        let count=try Unix.read fd data offset (79-offset)
          with Unix.Unix_error (Unix.EINTR,_,_) -> -1 in
        if count=0 then fail "truncated quota ledger"
        else fill (if count<0 then offset else offset+count) in
      fill 0;quota_decode(Bytes.to_string data)
    end in
    let bytes=Int64.of_int size in
    if entries>=quota_entries || bytes>Int64.sub quota_bytes used then
      fail "global payload/entry reservation capacity reached";
    let encoded=quota_encode (Int64.succ entries) (Int64.add used bytes) in
    ignore(Unix.lseek fd 0 Unix.SEEK_SET);
    let rec write offset = if offset<String.length encoded then
      let count=try Unix.write_substring fd encoded offset (String.length encoded-offset)
        with Unix.Unix_error (Unix.EINTR,_,_) -> -1 in
      if count=0 then fail "zero-length quota write"
      else write (if count<0 then offset else offset+count) in
    write 0;Unix.fsync fd;
    close_file owner node
  with
  | () -> ()
  | exception error -> raise error
let read owner filename =
  let before = Unix.lstat filename in
  if before.Unix.st_kind <> Unix.S_REG || before.st_uid <> Unix.getuid () ||
     before.st_perm land 0o777 <> 0o600 || before.st_nlink <> 1 ||
     before.st_size < 72 || before.st_size > SemanticDelta.max_base_cache_size+72 then
    fail "untrusted or oversized record";
  let node=open_file owner filename [Unix.O_RDONLY;Unix.O_CLOEXEC;Unix.O_NONBLOCK] 0 in
  let fd=descriptor node in
  (* The enclosing joint scope already owns this node. Body failures leave it
     for scope cleanup; uncertainty cannot be converted into a cache miss. *)
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
  | value -> close_file owner node; value
  | exception error -> remember_owner owner error;raise error
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
  if enabled () then with_owner (fun scope ->
    let identity=key ~root ~path ~fingerprint in
    let cache_root=directory () in
    let dir=shard cache_root identity in
    let filename=Filename.concat dir (SemanticHash.hex identity) in
    let encoded=body identity proof in
    let present = try Some (read scope filename) with Unix.Unix_error (Unix.ENOENT,_,_) -> None in
    match present with
    | Some existing -> if existing<>encoded then fail "common fingerprint already has another base"
    | None ->
      (* Bounded scan; refuse new entries when full. Retain earlier bases for
         partial-commit recovery instead of silently evicting their authority. *)
      let handle=open_directory scope dir in
      (match
        let rec count total =
          if total>=4096 then fail "entry capacity reached";
          match DirectoryOwner.read handle with
          | "." | ".." -> count total
          | _ -> count (total+1)
          | exception End_of_file -> () in count 0
       with
       | () -> close_directory scope handle
       | exception error -> raise error);
      reserve scope cache_root (String.length encoded);
      (* Prepare names, flags and close state before acquiring the descriptor.
         O_EXCL makes a collision a decline, never authority to remove a peer's
         file. Random names are collision avoidance inside an owned directory,
         not a security token. Avoid open_temp_file's post-open channel/tuple
         allocations by using a raw descriptor and a protected partial-write loop. *)
      let temporary=Filename.concat dir (Printf.sprintf ".base-%d-%08x-%08x.tmp"
        (Unix.getpid ()) (Random.bits ()) (Random.bits ())) in
      let flags=[Unix.O_WRONLY;Unix.O_CREAT;Unix.O_EXCL;Unix.O_CLOEXEC;Unix.O_NONBLOCK] in
      scope.temporary<-temporary;
      let node=open_file ~temporary:true scope temporary flags 0o600 in
      let fd=descriptor node in
      scope.temporary_identity<-Some(Unix.fstat fd);
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
        close_file scope node;
        (* No replacement: a concurrent capture may only publish equal bytes. *)
        (try Unix.link temporary filename with
         | Unix.Unix_error (Unix.EEXIST,_,_) ->
             if read scope filename<>encoded then fail "concurrent base differs");
        remove_temporary scope
      with
      | () -> ()
      | exception error -> raise error
  )
let load ~root ~path ~fingerprint =
  if not (enabled ()) then None else with_owner (fun scope ->
  try
    let identity=key ~root ~path ~fingerprint in
    let lookup legacy =
      let dir=directory ~legacy () in
      let part=if legacy then Filename.concat dir (String.sub (SemanticHash.hex identity) 0 3)
        else shard dir identity in
      let stat=Unix.lstat part in
      if stat.st_kind<>Unix.S_DIR || stat.st_uid<>Unix.getuid () ||
         stat.st_perm land 0o777<>0o700 then fail "untrusted lookup shard";
      unpack identity (read scope (Filename.concat part (SemanticHash.hex identity))) in
    let value = try Some(lookup false)
      with Util.Transient _ | Unix.Unix_error _ | Invalid_argument _ -> None in
    (match value with Some _ -> value | None -> Some(lookup true))
  with Util.Transient _ | Unix.Unix_error _ | Invalid_argument _ -> None)
