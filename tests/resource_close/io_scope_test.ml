open Lwt
exception Original_error
let require yes why=if not yes then failwith why
let () =
 let mode=Sys.argv.(1) in
 Prefs.loadStrings ["semanticdng = true";"semanticworkers = 1";"semanticmaxinflight = 4";"semanticpayloadbudget = 64"];
 let initial=Array.length(Sys.readdir "/dev/fd") in
 let ch=open_out_bin "source" in output_string ch "synthetic";close_out ch;
 let original=Unix.LargeFile.stat "source" in
 let runtime=SemanticRuntime.get () in
 let cancellation=HelperSupervisor.cancellation () in
 let nested=if mode="nested" then begin
  let owner=NotificationPipe.prepare () in
  let fd=Unix.openfile "source" [Unix.O_RDONLY;Unix.O_CLOEXEC] 0 in
  NotificationPipe.adopt_read owner fd;IoScopeFault.armed:=true;
  try NotificationPipe.close_all owner;assert false with NotificationPipe.Uncertain _ as error -> Some error
 end else None in
 IoScopeFault.armed:=(mode="close" || mode="error-close" || mode="nested");
 let callback=Lwt.wait () in
 let work ()=match nested with
  | Some error -> fail error
  | None when mode="cancel" -> callback
  | None when mode="error" || mode="error-close" -> fail Original_error
  | None -> return 17 in
 let result=SemanticRuntime.with_admission cancellation ~payload_bytes:4096 ~descriptors:2 (fun () ->
   SemanticRuntime.with_io_file cancellation "source" work) in
 if mode="cancel" then begin
  HelperSupervisor.cancel cancellation;
  require(Lwt.poll result=None && (IoAdmission.usage runtime.io).active_jobs=1 && (SemanticRuntime.admission_usage ()).transactions=1 && !(IoScopeFault.attempts)=0) "active cancellation released scope";
  Lwt.wakeup callback 17
 end;
 let unknown=mode="close" || mode="error-close" || mode="nested" in
 if unknown then begin
  require(Lwt.poll result=None) "DESIGNATED uncertain I/O scope settled";
  require((IoAdmission.usage runtime.io).active_jobs=1 && (SemanticRuntime.admission_usage ()).transactions=1) "DESIGNATED uncertain I/O scope released reservations";
  require(!(IoScopeFault.attempts)=1) "numeric close retry";
  HelperSupervisor.cancel cancellation;Gc.full_major ();
  require(Lwt.poll result=None && (IoAdmission.usage runtime.io).active_jobs=1) "uncertainty lost after cancel/GC";
  if mode="nested" then begin
   let info=Unix.LargeFile.fstat !(IoScopeFault.candidate) in
   require(info.st_ino=original.st_ino && info.st_dev=original.st_dev) "nested error closed outer descriptor";
   require(NotificationPipe.retained_count ()=2) "outer descriptor not rooted"
  end else RetainedOwnership.iter(fun entry -> match RetainedOwnership.cause entry with
   | NotificationPipe.Uncertain issue ->
     require(Option.is_some(NotificationPipe.read_cause issue)) "close cause missing";
     require(NotificationPipe.operation_cause issue=(if mode="error-close" then Some Original_error else None)) "original operation cause lost";
     (match NotificationPipe.read_identity issue with Some stat -> require(stat.st_ino=original.st_ino) "preclose identity lost" | None -> failwith "missing identity")
   | _ -> failwith "unexpected retained carrier");
  List.iter(fun fd -> ignore(Unix.fstat fd)) !(IoScopeFault.replacements)
 end else begin
  if mode="error" then (try ignore(Lwt.poll result);failwith "missing callback error" with Original_error -> ())
  else require(Lwt.poll result=Some 17) "known result changed";
  require((IoAdmission.usage runtime.io).active_jobs=0 && (SemanticRuntime.admission_usage ()).transactions=0 && !(IoScopeFault.attempts)=1) "known I/O scope did not close/release";
  Lwt_unix.run(SemanticWorkers.shutdown runtime.pool);
  require(Array.length(Sys.readdir "/dev/fd")=initial) "known I/O scope leaked descriptors"
 end;
 Printf.printf "PASS actual I/O scope %s; unknown cases settle at process exit only\n%!" mode
