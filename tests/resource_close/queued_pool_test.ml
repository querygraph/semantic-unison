open Lwt
module W=SemanticWorkers
module H=HelperSupervisor
module I=IoAdmission
external fd_count : unit -> int = "resource_fixture_fd_count"
let entered=Atomic.make false
let released=Atomic.make false
let left=Atomic.make false
let require yes why=if not yes then failwith why
let rec await condition n =
 if condition () then return () else if n=0 then fail(Failure "queued pool control deadline")
 else Lwt_unix.sleep 0.002 >>= fun () -> await condition (n-1)
let run=Lwt_unix.run
module Recognizer = struct
 let format="queued-pool-fixed/1"
 let identify file =
  ignore(SemanticFile.read file 0L 1);
  Atomic.set entered true;
  while not(Atomic.get released) do Domain.cpu_relax () done;
  Atomic.set left true;
  FormatRecognition.Not_matched
end
let () =
 let mode=Sys.argv.(1) in
 let initial=fd_count () in
 let data=String.make 4096 'q' in
 let ch=open_out_bin "source" in output_string ch data;close_out ch;
 let fd=Unix.openfile "source" [Unix.O_RDONLY;Unix.O_CLOEXEC] 0 in
 let identity=Unix.LargeFile.fstat fd in
 let cpu=H.create ~cpu_permits:1 ~max_children:1 ~max_pending:8 in
 let io=I.create ~per_device:1 ~max_pending:8 in
 let pool=W.create_with_io ~io ~workers:1 ~max_pending:8 ~budget:cpu in
 let base=fd_count () in
 let c1=H.cancellation () and c2=H.cancellation () and c3=H.cancellation () in
 let holder_done=Lwt.wait () in
 let holder=if mode="queued-cpu" then H.with_cpu_permits cpu ~weight:1 (H.cancellation ()) (fun () -> holder_done)
   else if mode="queued-io" then I.with_devices io (H.cancellation ()) ~devices:(I.devices_of_fds [fd]) (fun () -> holder_done)
   else return(Some ()) in
 let first=W.recognize pool c1 ~recognizers:[FormatRecognition.trusted(module Recognizer),false] fd in
 if mode="queued-cpu" || mode="queued-io" then begin
  run(Lwt_unix.sleep 0.01);
  require(not(Atomic.get entered) && (W.usage pool).pending=1) "first started past held gate"
 end else run(await(fun () -> Atomic.get entered) 1000);
 let cancelled=W.digest pool c2 fd in
 let third=W.digest pool c3 fd in
 H.cancel c2;
 run(await(fun () -> Lwt.poll cancelled=Some None) 1000);
 require((W.usage pool).pending=2 && fd_count ()=(if Atomic.get entered then base+3 else base+2)) "queued cancellation lost ownership accounting";
 if mode="queued-cpu" || mode="queued-io" then begin
  Lwt.wakeup holder_done ();ignore(run holder);
  run(await(fun () -> Atomic.get entered) 1000)
 end;
 require((W.usage pool).pending=2 && (W.usage pool).running=1 && H.usage cpu=(1,0) && (I.usage io).active_jobs=1) "running/queued accounting";
 require(fd_count ()=base+3 && Lwt.poll first=None && Lwt.poll third=None) "active or queued descriptors released early";
 let shutdown=if mode="shutdown-active" then Some(W.shutdown pool) else None in
 if mode="cancel-active" then H.cancel c1;
 run(Lwt_unix.sleep 0.03);
 require(not(Atomic.get left) && Lwt.poll first=None && H.usage cpu=(1,0) && (I.usage io).active_jobs=1) "cancel/shutdown released active callback";
 (match shutdown with Some promise -> require(Lwt.poll promise=None && Lwt.poll third=Some None) "shutdown ignored active/queued work" | None -> ());
 Atomic.set released true;
 let first_result=run first in
 require(Atomic.get left) "reply preceded worker exit";
 if mode="cancel-active" || mode="shutdown-active" then require(first_result=None) "cancelled first result changed"
 else require(Option.is_some first_result) "known first result missing";
 if mode<>"shutdown-active" then begin
  match run third with
  | Some fingerprint -> require(fingerprint.W.digest=SemanticHash.string data) "queued digest changed"
  | None -> failwith "third job lost"
 end;
 let closing=match shutdown with Some p -> p | None -> W.shutdown pool in
 run closing;require(W.shutdown pool==closing) "shutdown owner replaced";
 require((W.usage pool).pending=0 && (W.usage pool).running=0 && (W.usage pool).retained=0 && H.usage cpu=(0,0) && (I.usage io).active_jobs=0 && (I.usage io).pending=0) "known completion left accounting";
 let after=Unix.LargeFile.fstat fd in
 require(identity.st_ino=after.st_ino && identity.st_dev=after.st_dev && identity.st_size=after.st_size) "borrowed source changed";
 Unix.close fd;
 require(fd_count ()=initial) "known shutdown did not restore descriptor census";
 Printf.printf "PASS actual queued pool %s: known joins/pipe closes and baseline FD census\n%!" mode
