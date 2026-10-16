open Lwt
module H=HelperSupervisor
module W=SemanticWorkers
let check x why=if not x then failwith why
let () =
  let baseline=Array.length(Sys.readdir "/dev/fd") in
  let b=H.create ~cpu_permits:1 ~max_children:1 ~max_pending:8 in
  let pool=W.create ~workers:2 ~max_pending:1 ~budget:b in
  let fd=Unix.openfile "input.bin" [Unix.O_RDONLY;Unix.O_CLOEXEC] 0 in
  let first=W.digest pool (H.cancellation()) fd in
  (* Stop ticking Lwt while the actual worker finishes. Completions retain
     transaction/CPU ownership until the owner dispatches their receipts. *)
  let deadline=Unix.gettimeofday()+.5. in
  let rec completed ()=
    let jobs,results=W.test_mailboxes pool in
    if results.SemanticMailbox.pending=1 then jobs,results
    else if Unix.gettimeofday()>=deadline then failwith "no queued completion"
    else (Unix.sleepf 0.001;completed ()) in
  let jobs,results=completed() in
  check(jobs.pending=0 && results.pending=1 && results.capacity=1) "unbounded completion";
  check((W.usage pool).pending=1 && (W.usage pool).running=0 && H.usage b=(1,0)) "early ownership release";
  let attempted=W.digest pool (H.cancellation()) fd in
  check(try ignore(Lwt.poll attempted);false with W.Failed _ -> true) "full pool dispatched another job";
  check((W.test_mailboxes pool |> snd).pending=1) "full rejection stole completion";
  let result=Lwt_unix.run first in
  check(match result with Some r -> r.W.digest=SemanticHash.string(String.make 4194304 'p') | None -> false) "completed hash mismatch";
  check((W.usage pool).pending=0 && H.usage b=(0,0)) "completed ownership not settled";
  ignore(Unix.fstat fd);Unix.close fd;
  Lwt_unix.run(W.shutdown pool);
  let jobs,results=W.test_mailboxes pool in
  check(jobs.closed && results.closed && jobs.pending=0 && results.pending=0) "shutdown queues not closed/drained";
  check(Array.length(Sys.readdir "/dev/fd")=baseline) "pressure test leaked descriptors";
  print_endline "PASS actual queued completion retains CPU/admission, rejects overflow and settles/drains"
