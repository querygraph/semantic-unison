open Lwt
let require yes why=if not yes then failwith why
let write path data=let channel=open_out_bin path in output_string channel data;close_out channel
let read path=let channel=open_in_bin path in let data=really_input_string channel(in_channel_length channel) in close_in channel;data
let () =
 let consumer=Sys.argv.(1) and mode=Sys.argv.(2) in
 Prefs.loadStrings ["semanticworkers = 1";"semanticmaxinflight = 4";"semanticpayloadbudget = 64";"log = false"];
 Features.setEnabled(Features.all());Case.init false false;Props.init false;
 let initial=Array.length(Sys.readdir "/dev/fd") in
 Unix.mkdir "entries" 0o700;
 let originals=List.map(fun name->let path="entries/"^name in write path ("original tiny "^name);path,Unix.LargeFile.stat path,read path)
   ["alpha.entry";"zeta.entry";".hidden"] in
 write "guard.entry" "original scheduling fence";
 let directory=Fspath.canonize(Some(Sys.getcwd())) in
 let relative=Path.fromString(if mode="missing" then "absent" else "entries") in
 let absolute=Fspath.concat directory relative in
 DirectoryConsumerFault.target_path:=System.extendedPath(Fspath.toString absolute);
 let runtime=SemanticRuntime.get () and cancellation=HelperSupervisor.cancellation () in
 DirectoryConsumerFault.mode:=mode;DirectoryConsumerFault.armed:=true;
 let invoke ()=if consumer="os" then Os.childrenOf directory relative |> List.map Name.toString |> List.sort String.compare
  else if consumer="files" then Files.ls !(DirectoryConsumerFault.target_path) "*.entry"
  else invalid_arg "consumer" in
 let result=SemanticRuntime.with_admission cancellation ~payload_bytes:4096 ~descriptors:3 (fun ()->
  SemanticRuntime.with_io_file cancellation "guard.entry" (fun ()->return(invoke ()))) in
 let unknown=List.mem mode ["close-before";"close-after";"read-before";"read-after";"publish-after"] in
 if unknown then begin
  require((try Lwt.poll result=None with _->false)) "DESIGNATED directory consumer released uncertain borrower";
  require((SemanticRuntime.admission_usage()).transactions=1 && (IoAdmission.usage runtime.io).active_jobs=1) "consumer released admission/device before settlement";
  require(DirectoryOwner.retained_count()=1 && !(DirectoryConsumerFault.closes)=1) "opaque consumer owner lost/retried";
  require(NotificationPipe.retained_count()>0) "outer scheduling descriptor not rooted";
  let owner=ref None in DirectoryOwner.iter_retained(fun value->owner:=Some value);
  let owner=match !owner with Some owner->owner | None->failwith "missing opaque consumer owner" in
  require(Option.is_some(DirectoryOwner.close_cause owner)) "consumer close cause lost";
  if List.mem mode ["read-before";"read-after";"publish-after"] then
   require(DirectoryOwner.operation_cause owner=Some DirectoryConsumerFault.Original_error) "consumer original failure lost";
  for _=1 to 3 do (try DirectoryOwner.close owner with DirectoryOwner.Uncertain other->require(other==owner) "changed directory owner") done;
  HelperSupervisor.cancel cancellation;Gc.full_major ();
  require(!(DirectoryConsumerFault.closes)=1 && (try Lwt.poll result=None with _->false)) "cleanup retried or released consumer";
  (match !(DirectoryConsumerFault.target) with Some handle when List.mem mode ["close-before";"read-before"] ->
    require(DirectoryConsumerFault.readable handle) "live opaque directory lost" | _->());
  List.iter(fun handle->require(DirectoryConsumerFault.readable handle) "replacement opaque directory closed") !(DirectoryConsumerFault.replacements)
 end else begin
  let absent=mode="missing" || mode="open-error" in
  if mode="known" || (consumer="os" && absent) then begin
   let expected=if absent then [] else if consumer="os" then [".hidden";"alpha.entry";"zeta.entry"] else ["alpha.entry";"zeta.entry"] in
   require(Lwt.poll result=Some expected) "directory names/missing behavior changed"
  end else begin
   let failed=try ignore(Lwt.poll result);false with
    | DirectoryConsumerFault.Original_error -> List.mem mode ["read-error";"wrapper";"publish"]
    | Util.Transient _ -> mode="read-enoent" || (consumer="files" && absent) in
   require failed "consumer read error mistaken for missing directory"
  end;
  require(!(DirectoryConsumerFault.closes)=(if absent || mode="wrapper" then 0 else 1)) "known consumer close multiplicity";
  require(DirectoryOwner.retained_count()=0 && (SemanticRuntime.admission_usage()).transactions=0 && (IoAdmission.usage runtime.io).active_jobs=0) "known consumer scope leaked";
  DirectoryConsumerFault.armed:=false;
  Lwt_unix.run(SemanticWorkers.shutdown runtime.pool);
  require(Array.length(Sys.readdir "/dev/fd")=initial) "known consumer descriptors leaked"
 end;
 List.iter(fun(path,before,data)->let after=Unix.LargeFile.stat path in
  require({after with Unix.LargeFile.st_atime=before.Unix.LargeFile.st_atime}=before && read path=data) "synthetic originals changed") originals;
 require(read "guard.entry"="original scheduling fence") "scheduling source changed";
 Printf.printf "PASS actual %s directory consumer %s; unknowns settle at process exit only\n%!" consumer mode
