open Lwt
let require yes why=if not yes then failwith why
let () =
 let mode=Sys.argv.(1) in NonceFault.mode:=mode;
 Prefs.loadStrings["semanticdng = true";"semanticworkers = 1";"semanticmaxinflight = 4";"semanticpayloadbudget = 64"];
 let before=Array.length(Sys.readdir "/dev/fd") in
 let result=SemanticRuntime.with_admission (HelperSupervisor.cancellation ())
   ~payload_bytes:4096 ~descriptors:2 (fun () -> return(NonceFixture.nonce ())) in
 let unknown=mode="before" || mode="after" || mode="read-close" in
 if unknown then begin
  require((try Lwt.poll result=None with _ -> false)) "DESIGNATED uncertain nonce released caller";
  require((SemanticRuntime.admission_usage ()).transactions=1 && (SemanticRuntime.admission_usage ()).descriptors=2) "uncertain nonce released transaction";
  require(NotificationPipe.retained_count ()=1 && !(NonceFault.closes)=1) "nonce owner lost/retried";
  RetainedOwnership.iter(fun entry -> match RetainedOwnership.cause entry with
    | NotificationPipe.Uncertain owner ->
      require(Option.is_some(NotificationPipe.read_cause owner)) "nonce close cause missing";
      require(NotificationPipe.operation_cause owner=(if mode="read-close" then Some NonceFault.Read_failed else None)) "nonce read cause lost";
      (match NotificationPipe.read_identity owner with Some stat -> require(stat.Unix.LargeFile.st_kind=Unix.S_CHR) "nonce identity kind" | None -> failwith "nonce identity missing")
    | _ -> failwith "unexpected nonce carrier");
  Gc.full_major ();
  List.iter(fun fd -> ignore(Unix.fstat fd)) !(NonceFault.recycled);
  List.iter(fun fd -> ignore(Unix.fstat fd)) !(NonceFault.unclosed)
 end else begin
  if mode="read-error" then (try ignore(Lwt.poll result);failwith "missing read error" with NonceFault.Read_failed -> ())
  else if mode="empty" then (try ignore(Lwt.poll result);failwith "missing empty read rejection" with Util.Transient _ -> ())
  else (match Lwt.poll result with Some value -> require(String.length value=32) "nonce length changed" | None -> failwith "known nonce slept");
  require((SemanticRuntime.admission_usage ()).transactions=0 && NotificationPipe.retained_count ()=0 && !(NonceFault.closes)=1) "known nonce did not close/release";
  require(Array.length(Sys.readdir "/dev/fd")=before) "known nonce FD leak";
  if mode="interrupt" then require(!(NonceFault.reads)=2) "EINTR read not retried once"
 end;
 Printf.printf "PASS actual nonce body %s: single close authority; unknown process-exit settlement only\n%!" mode
