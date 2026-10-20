open Lwt
module H=HelperSupervisor
module W=SemanticWorkers
let check value reason=if not value then failwith reason
let run=Lwt_unix.run
let entered=Atomic.make false
let released=Atomic.make false
module Recognizer=struct
  let format="test.completed-before-owner/1"
  let identify file =
    check (SemanticFile.read file 0L 4="LATE") "wrong private source";
    Atomic.set entered true;
    while not (Atomic.get released) do Unix.sleepf 0.0001 done;
    FormatRecognition.Recognized
end
let () =
  let out=open_out_bin "source.bin" in output_string out "LATE owned fixture";close_out out;
  let baseline=Array.length(Sys.readdir "/dev/fd") in
  List.iter (fun mode ->
    Atomic.set entered false;Atomic.set released false;
    let source=Unix.openfile "source.bin" [Unix.O_RDONLY;Unix.O_CLOEXEC] 0 in
    let original=Unix.LargeFile.fstat source in
    let cpu=H.create ~cpu_permits:1 ~max_children:1 ~max_pending:4 in
    let io=IoAdmission.create ~per_device:1 ~max_pending:4 in
    let pool=W.create_with_io ~io ~workers:1 ~max_pending:4 ~budget:cpu in
    let cancellation=H.cancellation () in
    let recognizer=FormatRecognition.trusted (module Recognizer) in
    let result=W.identify pool cancellation ~recognizers:[recognizer,false] source in
    let rec started tries =
      if Atomic.get entered then return ()
      else if tries=0 then fail(Failure "worker callback never started")
      else Lwt_unix.sleep 0.001 >>= fun () -> started (tries-1) in
    run(started 2000);
    Atomic.set released true;
    (* No Lwt run/tick here: running reaches zero inside the same mutex that
       publishes the completion, before the owner can consume its reply. *)
    let until=Unix.gettimeofday () +. 2. in
    while (W.usage pool).running<>0 && Unix.gettimeofday ()<until do Unix.sleepf 0.0001 done;
    check ((W.usage pool).running=0) "worker did not finish before owner delivery";
    check (Lwt.poll result=None) "owner consumed completion while event loop stopped";
    check ((W.usage pool).pending=1 && H.usage cpu=(1,0) &&
           (IoAdmission.usage io).active_jobs=1) "completed reply lost retained accounting";
    let shutdown=if mode="shutdown" then Some(W.shutdown pool) else None in
    if mode="cancel" then H.cancel cancellation;
    let actual=run result in
    check ((actual=None)=(mode<>"success")) "late cancellation/shutdown returned stale result";
    check (H.is_cancelled cancellation=(mode="cancel")) "shutdown changed caller cancellation";
    (match shutdown with None->run(W.shutdown pool) | Some p->run p);
    check (H.usage cpu=(0,0) && (W.usage pool).pending=0 &&
           (W.usage pool).running=0 && (IoAdmission.usage io).active_jobs=0 &&
           (IoAdmission.usage io).pending=0) "completed reply leaked resources";
    let after=Unix.LargeFile.fstat source in
    check (after.Unix.LargeFile.st_dev=original.st_dev && after.st_ino=original.st_ino &&
           after.st_size=original.st_size && after.st_mtime=original.st_mtime &&
           after.st_ctime=original.st_ctime && after.st_perm=original.st_perm &&
           after.st_nlink=original.st_nlink) "worker changed caller source";
    Unix.close source;
    check (Array.length(Sys.readdir "/dev/fd")=baseline) "late result leaked descriptor";
    Printf.printf "PASS completed-before-owner %s: reply queued/accounting held/settlement closed\n%!" mode)
    ["success";"cancel";"shutdown"]
