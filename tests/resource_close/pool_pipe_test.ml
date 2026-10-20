open Lwt
let require yes why=if not yes then failwith why
let () =
 let mode=Sys.argv.(1) in PoolPipeFault.mode:=mode;
 let budget=HelperSupervisor.create ~cpu_permits:1 ~max_children:1 ~max_pending:4 in
 let creation=mode="creation-raw" || mode="creation-wrapped" in
 if creation then begin
  let issue=try ignore(SemanticWorkers.create ~workers:1 ~max_pending:4 ~budget);failwith "expected creation carrier"
    with NotificationPipe.Uncertain issue -> issue in
  require(NotificationPipe.operation_cause issue=Some PoolPipeFault.Creation_failed) "primary failure lost";
  require(Option.is_some(NotificationPipe.read_cause issue) && Option.is_some(NotificationPipe.write_cause issue)) "combined pipe errors lost";
  require(NotificationPipe.retained_count ()=1) "creation ledger not rooted"
 end else begin
  let pool=SemanticWorkers.create ~workers:1 ~max_pending:4 ~budget in
  let shutdown=SemanticWorkers.shutdown pool in
  Lwt_unix.run(Lwt_unix.sleep 0.03);
  if mode="known" then require(Lwt.poll shutdown=Some ()) "known shutdown unsettled"
  else begin
   require(Lwt.poll shutdown=None) "DESIGNATED uncertain pipe falsely settled shutdown";
   require(NotificationPipe.retained_count ()=1) "pipe ledger not rooted";
   require(SemanticWorkers.shutdown pool==shutdown) "shutdown did not reuse owner"
  end
 end;
 require(!(PipeFault.read_calls)=1 && !(PipeFault.write_calls)=1) "missing or repeated endpoint closes";
 require(HelperSupervisor.usage budget=(0,0)) "unexpected job CPU permit";
 Gc.full_major ();
 List.iter(fun fd -> ignore(Unix.fstat fd)) !(PipeFault.replacements);
 Printf.printf "PASS actual pool pipe %s; uncertainty process-exit settlement only\n%!" mode
