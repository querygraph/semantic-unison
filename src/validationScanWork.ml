open Lwt
exception Cleanup_failed of exn option * exn
let invalid reason=raise (Util.Transient ("Unchanged scan validation: "^reason))
let same a b=a.Unix.LargeFile.st_dev=b.Unix.LargeFile.st_dev && a.Unix.LargeFile.st_ino=b.Unix.LargeFile.st_ino
let directory name =
  let info=Unix.LargeFile.lstat name in
  if info.Unix.LargeFile.st_kind<>Unix.S_DIR || info.st_uid<>Unix.getuid () then
    invalid "owned nonsymlink staging directory required";
  info
let outside roots base =
  let roots=List.map (fun p -> Unix.LargeFile.stat (Fspath.toString p)) roots in
  let rec ancestors remaining path =
    if remaining=0 then invalid "staging ancestry limit exceeded";
    let info=Unix.LargeFile.stat path in
    if List.exists (same info) roots then invalid "staging directory is inside a replica";
    let parent=Filename.dirname path in
    if parent<>path then ancestors (remaining-1) parent in
  ancestors 4096 (Fspath.toString base)
let create base roots =
  let parent=Fspath.toString base in
  let before=directory parent in
  if before.Unix.LargeFile.st_perm land 0o022<>0 then invalid "writable staging base refused";
  outside roots base;
  let rec attempt remaining =
    if remaining=0 then invalid "private staging name collision limit exceeded";
    let name=Name.fromString (Printf.sprintf "validation-scan-%d-%08x-%08x"
      (Unix.getpid ()) (Random.bits ()) (Random.bits ())) in
    let path=Fspath.child base name in
    match Unix.mkdir (Fspath.toString path) 0o700 with
    | () -> path
    | exception Unix.Unix_error (Unix.EEXIST,_,_) -> attempt (remaining-1) in
  let path=attempt 8 in
  (* Failure before recording the new identity leaves the fresh private name
     for inspection; never remove an unbound/replacement directory. *)
  let info=directory (Fspath.toString path) in
  if not (same before (directory parent)) || info.Unix.LargeFile.st_perm<>0o700 then
    invalid ("private staging preparation changed: "^Fspath.toString path);
  path,info
let run_with_validators ~validators ~staging_base ~roots ~root ~paths ~max_bytes =
  if max_bytes<0L then invalid_arg "ValidationScanWork.max_bytes";
  if paths=[] || validators=[] then return () else
  let roots=root::roots in
  let staging_base=Fspath.resolve_existing (Fspath.toString staging_base) in
  let staging_directory,identity=create staging_base roots in
  let name=Fspath.toString staging_directory and retired=ref false
  and cleanup_error=ref None in
  let check_directory () =
    let current=directory name in
    if not (same identity current) || current.Unix.LargeFile.st_perm<>0o700 then
      invalid "private staging directory rebound" in
  let finish failure =
    if not !retired then begin
      retired:=true;
      (try check_directory ();Unix.rmdir name
       with error -> cleanup_error:=Some error)
    end;
    match !cleanup_error,failure with
    | Some error,_ -> fail (Cleanup_failed (failure,error))
    | None,None -> return ()
    | None,Some error -> fail error in
  let validate path =
    Abort.checkAll ();check_directory ();
    let logical=Fspath.concat root path in
    let resolve () =
      if Fileinfo.getType true root path<>`FILE then invalid "selected regular file changed kind";
      Fspath.resolve_existing (Fspath.toString logical) in
    let source=resolve () in
    let guard () =
      check_directory ();
      if Fspath.compare source (resolve ())<>0 then invalid "selected followed path retargeted" in
    guard ();
    BorrowedWork.try_bind
      (fun () -> CandidateValidation.unchanged_file_with_validators ~validators
        ~staging_directory ~source ~destination:path ~max_bytes)
      (fun () -> guard ();return ())
      (fun error ->
        try guard ();fail error
        with changed -> fail (Cleanup_failed (Some error,changed))) in
  let rec consume = function
    | [] -> return ()
    | path::rest -> BorrowedWork.bind (fun () -> validate path) (fun () -> consume rest) in
  BorrowedWork.try_bind (fun () -> consume paths) (fun () -> finish None)
    (fun error -> finish (Some error))

let run ~staging_base ~roots ~root ~paths ~max_bytes =
  if paths=[] then return () else
  run_with_validators ~validators:(CandidateValidators.selected ())
    ~staging_base ~roots ~root ~paths ~max_bytes
