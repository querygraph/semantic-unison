module C=CopyForOwned
external mode : int -> unit = "owned_fixture_mode"
external closes : unit -> int = "owned_fixture_closes"
let require yes why=if not yes then failwith why
let write path bytes=let out=open_out_bin path in output_string out bytes;close_out out
let read path=let input=open_in_bin path in let s=really_input_string input(in_channel_length input)in close_in input;s
let identity path=let s=Unix.LargeFile.lstat path in
 s.Unix.LargeFile.st_dev,s.st_ino,s.st_kind,s.st_perm,s.st_nlink,s.st_uid,s.st_gid,s.st_size,s.st_mtime,s.st_ctime
let marker=Failure "original ordinary writer error"
let ()=
 let folder=Sys.argv.(1) and phase=Sys.argv.(2) in
 Prefs.loadStrings["rsrc = false";"adobevalidate = off";"semanticworkers = 2";"log = false"];
 Case.init true Osx.isMacOSX;Props.init false;Osx.init Osx.isMacOSX;Fileinfo.init false;
 let root=Fspath.canonize(Some folder) in
 let path name=Filename.concat folder name and local=Path.fromString in
 let original=String.make 8192 'A' and incoming=String.make 8192 'B' in
 write(path "basis") original;write(path "source") incoming;write(path "live") "OLD LIVE";
 let basis_identity=identity(path "basis") and source_identity=identity(path "source") and live_identity=identity(path "live") in
 let before=SemanticRuntime.admission_usage() in
 let token=match Lwt_unix.run(TargetBinding.prepare_admitted ~require_producer:true ~logical_root:root
  ~local_path:(local "live") ~working_dir:root ~candidate:(local "normal") ~target:(local "live")
  ~normalize:false ~check_apple_double:false())with Some t->t|_->failwith "native ticket unavailable" in
 mode(if phase="adopt-close" then 1 else if phase="disarm-close" then 8 else 0);
 let writes=ref 0 in
 let pending=C.withProducer None root (local "live") root (local "normal") (local "live") token
  (fun producer ->
   let copied=if phase="source-copy" then
     C.copyByPath ~producer ~expected_length:8192L root (local "source") root (local "normal")
    else if phase="receiver-copy" then
     C.copyLocalCloned ~producer (Fspath.resolve_existing(path "source")) (Fspath.resolve_existing(path "basis"))
       root (local "normal") (Uutil.Filesize.ofInt 8192) None
    else C.copyBoundClone ~expected_length:8192L (Some producer)
    (Fspath.resolve_existing(path "basis")) root (local "normal") "-owned-test"
    (fun _ output -> incr writes;output_string output incoming;
     if phase="writer-close" then begin mode(-1);raise marker end) in
   require copied "bound clone declined";
   C.freezeProducer(Some producer);
   TargetBinding.record_fingerprint producer.binding(Os.fingerprint root (local "normal") `FILE);
   Lwt.return()) in
 if phase="normal" || phase="source-copy" || phase="receiver-copy" then begin
  let _,completion=Lwt_unix.run pending in
  require(completion=TargetBinding.Guarded_producer && !writes=(if phase="normal" then 1 else 0) && read(path "normal")=incoming)
   "ordinary clone bytes/producer completion wrong";
  TargetBinding.release_ticket ~logical_root:root ~token();
  let after=SemanticRuntime.admission_usage() in
  require(after.transactions=before.transactions && after.descriptors=before.descriptors) "normal ticket reservation leaked"
 end else begin
  Lwt_unix.run(Lwt_unix.sleep 0.02);
  require(Lwt.poll pending=None) "unknown ordinary clone escaped producer guard";
  let owner=match C.retained_clones()with [owner]->owner|_->failwith "missing retained ordinary clone owner" in
  let native=match C.retained_clone_native owner with Some owner->owner|_->failwith "missing native owner" in
  let known=C.retained_clone_descriptors owner in
  require(List.length known=2) "remaining raw/channel pair lost";
  List.iter(fun fd->ignore(Unix.fstat fd))known;
  let held=SemanticRuntime.admission_usage() in
  require(held.transactions=before.transactions+1 && held.descriptors>before.descriptors && held.payload_bytes>before.payload_bytes)
   "unknown ordinary clone retired producer reservation";
  if phase="writer-close" then require(C.retained_clone_cause owner==marker) "writer cause overwritten by close error";
  require(!writes=(if phase="adopt-close" then 0 else 1)) "writer repeated/omitted";
  if phase="disarm-close" then require(read(path "normal")=incoming) "unknown disarm unlinked published candidate";
  let evidence=StagePublication.owned_evidence native and count=closes() in
  TargetBinding.release_ticket ~logical_root:root ~token();
  Remote.clientCloseRootConnection(Common.Local,root);
  Lwt_unix.run(Lwt_unix.sleep 0.02);
  require(Lwt.poll pending=None && StagePublication.owned_evidence native=evidence && closes()=count)
   "connection cleanup retried native owner or settled unknown producer";
  List.iter(fun fd->ignore(Unix.fstat fd))known;
  let after=SemanticRuntime.admission_usage() in
  require(after.transactions=held.transactions && after.descriptors=held.descriptors && after.payload_bytes=held.payload_bytes)
   "connection cleanup retired reservation under unknown native ownership";
  if phase="disarm-close" then require(read(path "normal")=incoming) "connection cleanup removed held published candidate"
 end;
 require(read(path "basis")=original && read(path "live")="OLD LIVE") "ordinary clone changed source/live target";
 require(identity(path "basis")=basis_identity && identity(path "source")=source_identity && identity(path "live")=live_identity) "source/live identity or metadata changed";
 Printf.printf "PASS ordinary bound clone %s; actual ticket/channel/native ownership\n%!" phase
