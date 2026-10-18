open Lwt
module H=HelperSupervisor
module W=SemanticWorkers
let require condition message=if not condition then failwith message
let rec await predicate count =
  if predicate () then return () else if count=0 then fail(Failure "reader worker deadline")
  else Lwt_unix.sleep 0.005 >>= fun () -> await predicate (count-1)
let () =
  let mode=Sys.argv.(1) in
  let ch=open_out_bin "source" in output_string ch (String.make 64 'x');close_out ch;
  let source=Unix.openfile "source" [Unix.O_RDONLY;Unix.O_CLOEXEC] 0 in
  let budget=H.create ~cpu_permits:1 ~max_children:1 ~max_pending:4 in
  let pool=W.create ~workers:1 ~max_pending:4 ~budget in
  ReaderCloseFault.arm ~install:(mode="install");
  let cancellation=H.cancellation () in
  let job=W.digest pool cancellation source in
  Lwt_unix.run(await(fun () -> ReaderCloseFault.attempts ()>0 && (W.usage pool).running=0) 400);
  Lwt_unix.run(Lwt_unix.sleep 0.02);
  let sleeping=try Lwt.poll job=None with _ -> false in
  require sleeping "expected-reader-retained-reply";
  require((W.usage pool).retained=1 && (W.usage pool).pending=1 && H.usage budget=(1,0)) "reader failure released admission";
  H.cancel cancellation;
  let shutdown=W.shutdown pool in
  Lwt_unix.run(Lwt_unix.sleep 0.02);
  require(Lwt.poll shutdown=None && Lwt.poll job=None && H.usage budget=(1,0)) "reader uncertainty lost at shutdown";
  require(ReaderCloseFault.attempts ()=1) "reader close retried";
  List.iter(fun fd -> ignore(Unix.fstat fd)) (ReaderCloseFault.replacements ());
  Printf.printf "PASS reader-worker %s: nested carrier retains borrowed admission; process-exit settlement only\n%!" mode;
  exit 0
