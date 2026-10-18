open Lwt
exception Original_error
let require yes reason=if not yes then failwith reason
let () =
  let mode=Sys.argv.(1) and ownership=Sys.argv.(2) in
  Prefs.loadStrings ["semanticdng = true";"rsrc = false";"semanticworkers = 2";
    "semanticmaxinflight = 4";"semanticpayloadbudget = 64"];
  let source="synthetic-reader" in
  let channel=open_out_bin source in output_string channel "synthetic";close_out channel;
  let fd=Unix.openfile source [Unix.O_RDONLY;Unix.O_CLOEXEC] 0 in
  let cancellation=HelperSupervisor.cancellation () in
  let cost=SemanticAdmission.{payload_bytes=4096;descriptors=2} in
  let gate=SemanticAdmission.create ~source_headroom:None ~max_transactions:2
    ~max_payload_bytes:8192 ~max_descriptors:4 ~max_pending:2 in
  let reservation=SemanticAdmission.make_reservation gate ~role:SemanticAdmission.Consumer ~cost in
  let explicit=ownership="explicit" in
  if explicit then require(Lwt.poll(SemanticAdmission.acquire reservation cancellation)=Some true) "acquire";
  let usage ()=if explicit then SemanticAdmission.usage gate else SemanticRuntime.admission_usage () in
  let uncertain=mode<>"known" && mode<>"known-error" in
  if uncertain then ReaderCloseFault.arm ~install:(mode="install");
  let operation ()=SemanticFile.with_fd fd (fun file ->
    require(SemanticFile.read file 0L 1="s") "wrong source";
    if mode="error" || mode="known-error" then raise Original_error;
    17) in
  let trigger=Lwt.wait () in
  let work ()=if mode="async" then trigger >>= fun () -> return(operation ()) else return(operation ()) in
  let result=SemanticRuntime.with_admission ?reservation:(if explicit then Some reservation else None)
    cancellation ~payload_bytes:cost.payload_bytes ~descriptors:cost.descriptors work in
  if explicit then SemanticAdmission.retire reservation;
  if mode="async" then Lwt.wakeup trigger ();
  if uncertain then begin
    require((try Lwt.poll result=None with _ -> false)) "DESIGNATED runtime released uncertain reader reply";
    require(SemanticRuntime.retained_ownership_count ()=1) "runtime did not root carrier";
    let u=usage () in require(u.transactions=1 && u.descriptors=2 && u.payload_bytes=4096) "runtime released reservation";
    HelperSupervisor.cancel cancellation;
    if explicit then SemanticAdmission.retire reservation;
    Gc.full_major ();
    require(Lwt.poll result=None && (usage ()).transactions=1) "cancellation/GC released unknown";
    require(ReaderCloseFault.attempts ()=1) "numeric close retry";
    List.iter(fun replacement -> ignore(Unix.fstat replacement)) (ReaderCloseFault.replacements ());
    RetainedOwnership.iter(fun entry -> match RetainedOwnership.cause entry with
      | SemanticFile.Close_uncertain issue ->
        require(SemanticFile.close_issue_descriptor issue<>fd) "borrowed input closed";
        if mode="error" then require(SemanticFile.close_issue_operation_error issue=Some Original_error) "original error lost"
      | _ -> failwith "wrong retained cause")
  end else begin
    if mode="known" then require(Lwt.poll result=Some 17) "known result"
    else (try ignore(Lwt.poll result);failwith "expected error" with Original_error -> ());
    require((usage ()).transactions=0 && (usage ()).descriptors=0) "known resources not retired";
    require(SemanticRuntime.retained_ownership_count ()=0) "false retention";
    Unix.close fd
  end;
  Printf.printf "PASS actual Runtime %s/%s; uncertain cases settle only at process exit\n%!" ownership mode
