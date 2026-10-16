type slot = {
  mutable fd : Unix.file_descr; mutable owned : bool; mutable uncertain : bool;
  mutable before : Unix.LargeFile.stats option; mutable error : exn option;
}
type uncertain_close = {
  descriptor : Unix.file_descr; before_close : Unix.LargeFile.stats option; error : exn option;
}
type t = {
  directory : string; source_name : string; stage_name : string;
  parent : slot; source : slot; output : slot;
  mutable parent_stats : Unix.LargeFile.stats option;
  mutable source_stats : Unix.LargeFile.stats option;
  mutable source_native : FileObservation.t option;
  mutable stage_stats : Unix.LargeFile.stats option;
  mutable unlink_attempted : bool; mutable cleanup_error : exn option;
  mutable failure : exn option;
}
exception Unresolved_ownership of t
exception Cleanup_failed of exn
exception Preparation_failed of exn * exn
let invalid reason=raise (SemanticFile.Invalid reason)
let slot ()={fd=Unix.stdin;owned=false;uncertain=false;before=None;error=None}
let same a b=a.Unix.LargeFile.st_dev=b.Unix.LargeFile.st_dev && a.Unix.LargeFile.st_ino=b.Unix.LargeFile.st_ino
let stable a b={a with Unix.LargeFile.st_atime=0.}={b with Unix.LargeFile.st_atime=0.}
let native fd=try Some (FileObservation.observe fd) with
  | Unix.Unix_error (Unix.ENOSYS,"file_observation.platform",_) -> None
let get=function Some value -> value | None -> invalid "snapshot owner is not prepared"
let live owner=List.for_all (fun s -> s.owned && not s.uncertain) [owner.parent;owner.source;owner.output]
let check_parent owner =
  let held=Unix.LargeFile.fstat owner.parent.fd and visible=Unix.LargeFile.lstat owner.directory in
  let expected=get owner.parent_stats in
  if not (same held expected && same visible expected) ||
     visible.Unix.LargeFile.st_kind<>Unix.S_DIR || visible.Unix.LargeFile.st_uid<>Unix.getuid () ||
     visible.Unix.LargeFile.st_perm<>0o700 then invalid "snapshot private parent rebound or untrusted"
let check_source owner =
  let expected=get owner.source_stats in
  if not (stable expected (Unix.LargeFile.fstat owner.source.fd)) ||
     not (stable expected (Unix.LargeFile.lstat owner.source_name)) ||
     native owner.source.fd<>owner.source_native then invalid "snapshot original name/epoch changed"
let check_stage owner =
  let expected=get owner.stage_stats in
  let held=Unix.LargeFile.fstat owner.output.fd and visible=Unix.LargeFile.lstat owner.stage_name in
  if not (same expected held && same expected visible) ||
     held.Unix.LargeFile.st_kind<>Unix.S_REG || held.Unix.LargeFile.st_nlink<>1 ||
     visible.Unix.LargeFile.st_kind<>Unix.S_REG || visible.Unix.LargeFile.st_nlink<>1 ||
     visible.Unix.LargeFile.st_uid<>Unix.getuid () || visible.Unix.LargeFile.st_perm<>0o600 then
    invalid "snapshot stage name/inode changed"
let check owner=
  if List.exists (fun s -> s.uncertain) [owner.output;owner.source;owner.parent] then
    raise (Unresolved_ownership owner);
  if not (live owner) || owner.unlink_attempted then invalid "snapshot owner no longer live";
  check_parent owner;check_source owner;check_stage owner
let descriptors owner=check owner;owner.source.fd,owner.output.fd
let path owner=check owner;owner.stage_name
let uncertain_closes owner=List.filter_map (fun s ->
  if s.uncertain then Some {descriptor=s.fd;before_close=s.before;error=s.error} else None)
  [owner.output;owner.source;owner.parent]
let original_failure owner=owner.failure
let retire ?failure owner =
  (match failure,owner.failure with Some error,None -> owner.failure<-Some error | _ -> ());
  if not owner.unlink_attempted then begin
    owner.unlink_attempted<-true;
    if owner.output.owned && not owner.output.uncertain then
      (try
        check_parent owner;
        let held=Unix.LargeFile.fstat owner.output.fd in
        (match Unix.LargeFile.lstat owner.stage_name with
         | visible ->
           if not (same held visible) || visible.Unix.LargeFile.st_kind<>Unix.S_REG then
             invalid "refusing to remove replaced snapshot name";
           Unix.unlink owner.stage_name
         | exception Unix.Unix_error (Unix.ENOENT,_,_) -> ())
       with error -> owner.cleanup_error<-Some error)
  end;
  List.iter (fun s -> if s.owned && not s.uncertain then begin
    s.before<-(try Some (Unix.LargeFile.fstat s.fd) with _ -> None);
    (* Mark uncertain BEFORE attempting close. Never inspect/retry this number
       if close raises, even when independent slots can be retired. *)
    s.owned<-false;s.uncertain<-true;
    try Unix.close s.fd;s.uncertain<-false with error -> s.error<-Some error
  end) [owner.output;owner.source;owner.parent];
  if List.exists (fun s -> s.uncertain) [owner.output;owner.source;owner.parent] then
    raise (Unresolved_ownership owner);
  match owner.cleanup_error with None -> () | Some error -> raise (Cleanup_failed error)
let create ~directory ~source ~max_bytes =
  if max_bytes<0L || Filename.is_relative directory || Filename.is_relative source then
    invalid_arg "ValidationStage absolute paths/nonnegative budget required";
  let a=Random.bits () in let b=Random.bits () in
  let name=Filename.concat directory (Printf.sprintf ".validation-%d-%08x-%08x.dng"
    (Unix.getpid ()) a b) in
  let owner={directory;source_name=source;stage_name=name;parent=slot ();source=slot ();output=slot ();
    parent_stats=None;source_stats=None;source_native=None;stage_stats=None;
    unlink_attempted=false;cleanup_error=None;failure=None} in
  let open_slot slot path flags mode =
    let fd=Unix.openfile path flags mode in slot.fd<-fd;slot.owned<-true in
  try
    let parent=Unix.LargeFile.lstat directory in
    if parent.Unix.LargeFile.st_kind<>Unix.S_DIR || parent.Unix.LargeFile.st_uid<>Unix.getuid () ||
       parent.Unix.LargeFile.st_perm<>0o700 then invalid "owned mode0700 snapshot directory required";
    owner.parent_stats<-Some parent;
    open_slot owner.parent directory [Unix.O_RDONLY;Unix.O_CLOEXEC;Unix.O_NONBLOCK] 0;
    check_parent owner;
    let initial=Unix.LargeFile.lstat source in
    if initial.Unix.LargeFile.st_kind<>Unix.S_REG || initial.Unix.LargeFile.st_size<0L ||
       initial.Unix.LargeFile.st_size>max_bytes then invalid "snapshot source kind/size refused";
    owner.source_stats<-Some initial;
    open_slot owner.source source [Unix.O_RDONLY;Unix.O_CLOEXEC;Unix.O_NONBLOCK] 0;
    owner.source_native<-native owner.source.fd;
    check_source owner;
    open_slot owner.output name [Unix.O_RDWR;Unix.O_CREAT;Unix.O_EXCL;Unix.O_CLOEXEC;Unix.O_NONBLOCK] 0o600;
    owner.stage_stats<-Some (Unix.LargeFile.fstat owner.output.fd);
    check owner;owner
  with error ->
    owner.failure<-Some error;
    (try retire owner with
     | Unresolved_ownership _ as uncertain -> raise uncertain
     | cleanup -> raise (Preparation_failed (error,cleanup)));
    raise error
