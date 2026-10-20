module C=SemanticMergeCacheForOwner
module D=DirectoryOwnerForCache
module S=SemanticSyncForCache
let check b s=if not b then failwith s
let ()=
 let requested=Sys.argv.(1) in
 let capture=String.starts_with ~prefix:"capture-" requested and merge=String.starts_with ~prefix:"merge-" requested in
 let mode=if capture then String.sub requested 8 (String.length requested-8) else if merge then String.sub requested 6 (String.length requested-6) else requested in
 Prefs.loadStrings["semanticmergebasecache = true";"semanticdng = true";"semanticworkers = 1";"semanticvolumejobs = 1"];
 Features.setEnabled(Features.all());
 let root=Fspath.canonize(Some(Sys.getcwd())) and path=Path.fromString "base.dng" in
 let fingerprint=Os.data_only_fingerprint(Fingerprint.file root path) in
 let fd=Unix.openfile "base.dng" [Unix.O_RDONLY;Unix.O_CLOEXEC] 0 in
 let proof=SemanticFile.with_fd fd(fun file->match SemanticDelta.inspect(module DngSemantic)file with Ok p->p | Error e->failwith e) in Unix.close fd;
 let store ()=C.store ~root ~path ~fingerprint proof in
 let read=String.starts_with ~prefix:"read-" mode in
 if read then store();
 let runtime=SemanticRuntime.get () in
 let before=SemanticRuntime.admission_usage () in
 CacheJointFault.mode:=mode;
 let pending=if capture then S.capture_common_base_async ~root ~path ~source:(Fspath.concat root path)
 else if merge then Lwt.bind(S.merge_local_async_with_cache ~cache:(root,path) ~base_fingerprint:fingerprint
  ~base:(Fspath.concat root(Path.fromString "absent")) ~left:(Fspath.concat root path) ~right:(Fspath.concat root path) ~output:(Fspath.concat root path))(fun _->Lwt.return ())
 else SemanticRuntime.with_transaction ~max_payload:4096(fun _->
  if read then begin ignore(C.load ~root ~path ~fingerprint);Lwt.return () end
  else begin store();Lwt.return () end) in
 if capture then begin
  let rec await n=if C.retained()<>[] || (try Lwt.poll pending<>None with _->true) then Lwt.return ()
   else if n=0 then Lwt.fail(Failure "capture retention deadline") else Lwt.bind(Lwt_unix.sleep 0.005)(fun()->await(n-1)) in
  Lwt_unix.run(await 1000)
 end;
 if mode="known" || mode="temporary-interrupt" then begin
  if mode="known" then Lwt_unix.run pending else
   check((try Lwt_unix.run pending;false with CacheJointFault.Original_error->true)) "interruption failure lost";
  check(C.retained()=[]) "known store retained";
  if mode="known" then check(Option.is_some(C.load ~root ~path ~fingerprint)) "known cache load failed"
  else begin
   let cache=Util.fileInUnisonDir "semantic-merge-bases-v1" in
   Array.iter(fun shard->let p=Filename.concat cache shard in if Sys.is_directory p then
    check(not(Array.exists(fun n->String.starts_with ~prefix:".base-" n)(Sys.readdir p))) "interrupted created name leaked") (Sys.readdir cache)
  end;
  check((SemanticRuntime.admission_usage()).transactions=before.transactions) "known admission leak"
 end else begin
  check((try Lwt.poll pending=None with _->false)) "DESIGNATED cache uncertainty escaped";
  check((SemanticRuntime.admission_usage()).transactions=before.transactions+1) "cache admission released";
  let owner=match C.retained() with [x]->x|_->failwith "joint retained scope missing" in
  if capture || merge then begin
   let inputs=match S.retained_inputs() with [x]->x|_->failwith "outer capture/merge input scope lost" in
   check(S.retained_input_count inputs=(if capture then 1 else 4)) "outer slot count wrong";
   for i=0 to S.retained_input_count inputs-1 do
    check(NotificationPipe.read_held(S.retained_input_slot inputs i)=capture) "outer input closed or premature merge open"
   done
  end;
  let files=C.files owner and dirs=C.directories owner in
  let file_errors=List.filter(fun(_,s)->Option.is_some(NotificationPipe.read_cause s))files in
  let directory_errors=List.filter(fun s->D.phase s=D.Close_uncertain)dirs in
  let tmp,phase,identity=C.temporary owner in
  if read || String.starts_with ~prefix:"quota-" mode || String.starts_with ~prefix:"temporary-" mode || mode="error-quota-dir" then begin
   check(List.length file_errors=1) "file close evidence missing";
   List.iter(fun(_,s)->check(Option.is_some(NotificationPipe.read_identity s)) "file preclose identity missing")file_errors
  end;
  if List.mem mode ["directory-before";"directory-after";"root-after";"inner-shard-after";"error-quota-dir"] then
   check(List.length directory_errors=1) "directory close evidence missing";
  if mode="root-after" || mode="inner-shard-after" then begin
   check(List.exists(fun(name,s)->Filename.basename name=".quota-v1" && NotificationPipe.read_held s)files) "quota lock closed behind directory uncertainty";
   check(not(List.mem "quota" !(CacheJointFault.file_calls))) "quota close attempted behind directory uncertainty"
  end;
  if mode="inner-shard-after" then check(List.exists(fun d->D.phase d=D.Held)dirs) "outer scan lost behind inner uncertainty";
  if mode="temporary-interrupt-close" then check(C.operation_cause owner=Some CacheJointFault.Original_error) "interrupted original error lost";
  if mode="error-quota-dir" then begin
   check(C.operation_cause owner=Some CacheJointFault.Original_error) "original work error lost";
   check(List.length file_errors=1 && List.length directory_errors=1) "combined failures collapsed";
   List.iter(fun(_,file)->check(NotificationPipe.operation_cause file=Some CacheJointFault.Original_error) "file original error lost")file_errors;
   List.iter(fun directory->check(D.operation_cause directory=Some CacheJointFault.Original_error) "directory original error lost")directory_errors
  end;
  if String.starts_with ~prefix:"temporary-" mode then begin
   check(phase=C.Temporary_owned && Sys.file_exists tmp && Option.is_some identity) "temporary removed behind descriptor uncertainty";
   check(!(CacheJointFault.unlink_calls)=0) "uncertain temporary unlink attempted"
  end;
  if String.starts_with ~prefix:"unlink-" mode then begin
   check(phase=C.Unlink_uncertain && Option.is_some(C.temporary_cause owner)) "unlink uncertainty lost";
   check(Sys.file_exists tmp=(mode<>"unlink-after")) "unlink physical effect mismatch";
   if mode="unlink-rebound" then begin
    check((Unix.lstat tmp).Unix.st_ino<>(Option.get identity).Unix.st_ino) "peer replacement not observed";
    check(!(CacheJointFault.unlink_calls)=0) "replacement unlink attempted"
   end else check(!(CacheJointFault.unlink_calls)=1) "unlink attempt count wrong"
  end;
  let acquired=List.length !(CacheJointFault.bindings) in
  check((try ignore(C.load ~root ~path ~fingerprint);false with NotificationPipe.Uncertain _->true)) "retained cache permitted new load";
  check((try store();false with NotificationPipe.Uncertain _->true)) "retained cache permitted new capture";
  check(List.length !(CacheJointFault.bindings)=acquired && List.length(C.retained())=1) "retained cache acquired new resources";
  let f= !(CacheJointFault.file_calls) and d= !(CacheJointFault.directory_calls) and u= !(CacheJointFault.unlink_calls) in
  (try C.settle_owner owner with NotificationPipe.Uncertain _->());Gc.full_major();
  check(f= !(CacheJointFault.file_calls) && d= !(CacheJointFault.directory_calls) && u= !(CacheJointFault.unlink_calls)) "uncertain cleanup retried";
  check((try Lwt.poll pending=None with _->false)) "retained reply settled"
 end;
 Printf.printf "PASS joint cache %s\n%!" requested
