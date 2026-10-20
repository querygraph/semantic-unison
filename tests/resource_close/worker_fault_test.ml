open Lwt
module H=HelperSupervisor
module W=SemanticWorkers
let require condition message = if not condition then failwith message
let rec wait_until predicate remaining =
  if predicate () then return ()
  else if remaining=0 then fail (Failure "worker observation deadline")
  else Lwt_unix.sleep 0.005 >>= fun () -> wait_until predicate (remaining-1)
let () =
  let mode=Sys.argv.(1) in
  let channel=open_out_bin "source" in output_string channel (String.make 64 'a');close_out channel;
  let source=Unix.openfile "source" [(if mode="error" then Unix.O_WRONLY else Unix.O_RDONLY);Unix.O_CLOEXEC] 0 in
  let output=Unix.openfile "output" [Unix.O_RDWR;Unix.O_CREAT;Unix.O_EXCL;Unix.O_CLOEXEC] 0o600 in
  let budget=H.create ~cpu_permits:1 ~max_children:1 ~max_pending:4 in
  let pool=W.create ~workers:1 ~max_pending:4 ~budget in
  let cancellation=H.cancellation () in
  if mode<>"known" then WorkerCloseFault.arm ();
  let job=if mode="dual" then
      W.snapshot pool cancellation ~max_bytes:64L ~source ~output >>= fun result ->
      return (Option.is_some result)
    else W.digest pool cancellation source >>= fun result -> return (Option.is_some result) in
  if mode="known" then begin
    require (Lwt_unix.run job) "known digest result missing";
    Lwt_unix.run (W.shutdown pool);
    require (H.usage budget=(0,0) && (W.usage pool).pending=0 && (W.usage pool).retained=0) "known release failed";
    Unix.close source;Unix.close output;
    print_endline "PASS known worker digest/shutdown settled"
  end else begin
    Lwt_unix.run (wait_until (fun () -> WorkerCloseFault.attempts ()>0 && (W.usage pool).running=0) 400);
    (* Drain the completion notification, without completing the borrowed job. *)
    Lwt_unix.run (Lwt_unix.sleep 0.02);
    let sleeping=try Lwt.poll job=None with _ -> false in
    require sleeping "expected-retained-reply";
    require ((W.usage pool).retained=1 && (W.usage pool).pending=1 && H.usage budget=(1,0)) "expected-retained-accounting";
    require (WorkerCloseFault.attempts ()=(if mode="dual" then 2 else 1)) "close attempt count differs";
    H.cancel cancellation;
    let shutdown=W.shutdown pool in
    require (shutdown==W.shutdown pool) "shutdown not idempotent";
    Lwt_unix.run (Lwt_unix.sleep 0.02);
    require (Lwt.poll shutdown=None && Lwt.poll job=None && H.usage budget=(1,0)) "cancellation or shutdown released unknown";
    let refused=W.digest pool (H.cancellation ()) source in
    let closed=try ignore(Lwt.poll refused);false with W.Failed _ -> true in
    require closed "new work admitted after uncertainty";
    List.iter (fun fd -> ignore(Unix.fstat fd)) (WorkerCloseFault.replacements ());
    require (WorkerCloseFault.attempts ()=(if mode="dual" then 2 else 1)) "numeric close retried";
    Printf.printf "PASS %s: reply/admission/shutdown retained; replacement descriptors live; process-exit settlement only\n%!" mode;
    (* The intentionally unresolved pool cannot claim shutdown. This original
       fixture has no subprocesses; its external owner waits for actual exit. *)
    exit 0
  end
