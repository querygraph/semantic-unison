open Lwt
let require yes why=if not yes then failwith why
let pipe_still_owned () =
 ignore(Unix.fstat !(PipeFault.read_fd));ignore(Unix.fstat !(PipeFault.write_fd));
 require(!(PipeFault.read_calls)=0 && !(PipeFault.write_calls)=0) "uncertain lifecycle closed pipe";
 require(NotificationPipe.retained_count ()=1) "unknown pool not rooted"
let () =
 let mode=Sys.argv.(1) in PoolLifecycleFault.mode:=mode;
 if String.starts_with ~prefix:"publication-" mode then begin
  let budget=HelperSupervisor.create ~cpu_permits:2 ~max_children:1 ~max_pending:4 in
  let failed=try ignore(SemanticWorkers.create ~workers:2 ~max_pending:4 ~budget);false
    with PoolLifecycleFault.Publication_failed -> true in
  require failed "publication failure lost";
  require(!(PoolLifecycleFault.joins)=(if mode="publication-first" then 1 else 2)) "published handles not joined";
  require(!(PipeFault.read_calls)=1 && !(PipeFault.write_calls)=1) "known cleanup missed pipe close";
  require(NotificationPipe.retained_count ()=0) "known joins falsely retained"
 end else if mode="handoff" then begin
  Prefs.loadStrings ["semanticdng = true";"semanticworkers = 1";"semanticmaxinflight = 4";"semanticpayloadbudget = 64"];
  let failure ()=try ignore(SemanticRuntime.get ());failwith "expected handoff refusal"
    with NotificationPipe.Uncertain issue -> issue
    | _ -> failwith "DESIGNATED runtime lost unpublished pool owner" in
  let first=failure () in
  require(NotificationPipe.operation_cause first=Some PoolLifecycleFault.Publication_failed) "publication cause missing";
  require(failure ()==first && !(PoolLifecycleFault.pipes)=1) "runtime silently created replacement pool";
  pipe_still_owned ()
 end else begin
  let budget=HelperSupervisor.create ~cpu_permits:1 ~max_children:1 ~max_pending:4 in
  if String.starts_with ~prefix:"creation-" mode then begin
   let issue=try ignore(SemanticWorkers.create ~workers:1 ~max_pending:4 ~budget);failwith "expected creation retention"
     with NotificationPipe.Uncertain issue -> issue in
   require(NotificationPipe.operation_cause issue=Some PoolLifecycleFault.Publication_failed) "creation primary missing";
   require((match NotificationPipe.lifecycle_cause issue with
     | Some PoolLifecycleFault.Stop_failed -> mode="creation-stop"
     | Some(DomainOwner.Join_uncertain slot) -> DomainOwner.cause slot=Some PoolLifecycleFault.Join_failed
     | _ -> false)) "lifecycle cause missing";
   pipe_still_owned ()
  end else begin
   let pool=SemanticWorkers.create ~workers:1 ~max_pending:4 ~budget in
   let result=SemanticWorkers.shutdown pool in
   Lwt_unix.run(Lwt_unix.sleep 0.02);
   require(Lwt.poll result=None) "DESIGNATED lifecycle failure settled shutdown";
   let joins= !(PoolLifecycleFault.joins) and stops= !(PoolLifecycleFault.stops) in
   require(SemanticWorkers.shutdown pool==result) "new shutdown owner";
   require(!(PoolLifecycleFault.joins)=joins && !(PoolLifecycleFault.stops)=stops) "lifecycle action retried";
   pipe_still_owned ()
  end
 end;
 Gc.full_major ();
 if not(String.starts_with ~prefix:"publication-" mode) then pipe_still_owned ();
 Printf.printf "PASS actual pool lifecycle %s; unresolved domains settle only at process exit\n%!" mode
