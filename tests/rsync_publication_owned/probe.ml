module C=CopyForStream
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
 Prefs.loadStrings["rsrc = false";"adobevalidate = off";"semanticworkers = 2";"log = false";"rsync = true"];
 Case.init true Osx.isMacOSX;Props.init false;Osx.init Osx.isMacOSX;Fileinfo.init false;
 let root=Fspath.canonize(Some folder) in
 let path name=Filename.concat folder name and local=Path.fromString in
 let original=String.init 8192(fun i->Char.chr((i*17+i/1024) land 255)) in
 let incoming=if phase="growth" then "owned-prefix"^original else if phase="shrink" then String.sub original 0 4096
  else if phase="inherited" then original else
  let b=Bytes.of_string original in Bytes.set b 3073 'X';Bytes.to_string b in
 write(path "basis") original;write(path "source") incoming;write(path "live") original;
 let basis_identity=identity(path "basis") and source_identity=identity(path "source") and live_identity=identity(path "live") in
 let before=SemanticRuntime.admission_usage() in
 let token=match Lwt_unix.run(TargetBinding.prepare_admitted ~require_producer:true ~logical_root:root
  ~local_path:(local "live") ~working_dir:root ~candidate:(local "normal") ~target:(local "live")
  ~normalize:false ~check_apple_double:false())with Some t->t|_->failwith "native ticket unavailable" in
 mode(if phase="adopt-close" then 1 else if phase="disarm-close" then 8 else 0);
 let progress=ref false in
 let pending=C.withProducer None root (local "live") root (local "normal") (local "live") token
  (fun producer ->
   if phase="progress-close" || phase="progress-cancel" then Uutil.setProgressPrinter(fun _ _ _ ->
    if not !progress then begin
     progress:=true;
     let owner=match producer.clone_scope.publications with Some owner->owner|_->failwith "no active receiver" in
     require(owner.borrowers>0) "decoder did not hold native/channel borrower";
     mode(if phase="progress-close" then -1 else 0);
     let count=closes() in
     Remote.clientCloseRootConnection(Common.Local,root);
     require(closes()=count) "native cleanup ran under decoder borrower";
     (match owner.range_lease with Some lease->
       require((match CloneLease.observe lease with Error(CloneLease.Invalidated _)->true|_->false))
         "connection cleanup did not invalidate range authority before borrower settlement"
      |None->failwith "receiver range lease missing");
     ignore(Unix.fstat(Unix.descr_of_in_channel owner.input));
     ignore(Unix.fstat(Unix.descr_of_out_channel owner.output))
    end);
   let sending=C.transferFileContents ~producer (Obj.magic 0) root (local "source") root (local "normal") (local "live")
    (`Update(Uutil.Filesize.ofInt 8192,Uutil.Filesize.zero)) `DATA (Uutil.Filesize.ofInt(String.length incoming))
    (if phase="progress-close" || phase="progress-cancel" then Uutil.File.ofLine 0 else Uutil.File.dummy) in
   Lwt.bind sending(fun()->
    C.freezeProducer(Some producer);
    TargetBinding.record_fingerprint producer.binding(Os.fingerprint root (local "normal") `FILE);
    Lwt.return())) in
 if List.mem phase ["normal";"growth";"shrink";"inherited"] then begin
  let _,completion=Lwt_unix.run pending in
  require(completion=TargetBinding.Guarded_producer && read(path "normal")=incoming)
   "streaming rsync bytes/producer completion wrong";
  TargetBinding.release_ticket ~logical_root:root ~token();
  let after=SemanticRuntime.admission_usage() in
  require(after.transactions=before.transactions && after.descriptors=before.descriptors) "normal streaming ticket reservation leaked"
 end else if phase="progress-cancel" then begin
  let failed=try ignore(Lwt_unix.run pending);false with Util.Transient _ | Not_found ->true in
  require(failed && !progress) "known interrupted decoder did not fail normally";
  require(C.retained_clones()=[] && !(C.active_owned_clones)=None) "known cancellation retained native/channel owner";
  let after=SemanticRuntime.admission_usage() in
  require(after.transactions=before.transactions && after.descriptors=before.descriptors && after.payload_bytes=before.payload_bytes)
   "known cancellation failed to retire producer reservation"
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
  if phase="progress-close" then require(!progress) "progress cancellation hook did not run";
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
 require(read(path "basis")=original && read(path "live")=original) "ordinary clone changed source/live target";
 require(identity(path "basis")=basis_identity && identity(path "source")=source_identity && identity(path "live")=live_identity) "source/live identity or metadata changed";
 Printf.printf "PASS streaming receiver rsync %s; actual ticket/channel/native ownership\n%!" phase
