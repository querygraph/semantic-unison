(* Original deterministic callback barrier; no scheduling stress or helper. *)
open Lwt
module H=HelperSupervisor
module W=SemanticWorkers
external times : string -> int64 * int * int64 * int = "unison_publication_test_exact_times"
let entered=Atomic.make false
let released=Atomic.make false
let check value reason=if not value then failwith reason
module Recognizer=struct
 let format="test.same-size-source-mutation/1"
 let identify file=
  check(SemanticFile.read file 0L 4="MUT0") "wrong initial original fixture";
  Atomic.set entered true;
  while not(Atomic.get released) do Unix.sleepf 0.0001 done;
  FormatRecognition.Recognized
end
let ()=
 let initial="MUT0 owned source" and changed="MUT1 owned source" in
 check(String.length initial=String.length changed) "fixture sizes differ";
 let out=open_out_bin "source.bin" in output_string out initial;close_out out;
 Unix.utimes "source.bin" 1700000000. 1700000000.;
 let ms,mn,cs,cn=times "source.bin" in
 let baseline=Array.length(Sys.readdir "/dev/fd") in
 let source=Unix.openfile "source.bin" [Unix.O_RDONLY;Unix.O_CLOEXEC] 0 in
 let before=Unix.LargeFile.fstat source in
 let cpu=H.create ~cpu_permits:1 ~max_children:1 ~max_pending:4 in
 let io=IoAdmission.create ~per_device:1 ~max_pending:4 in
 let pool=W.create_with_io ~io ~workers:1 ~max_pending:4 ~budget:cpu in
 let cancellation=H.cancellation() in
 let job=W.identify pool cancellation ~recognizers:[FormatRecognition.trusted(module Recognizer),false] source in
 let rec started n=if Atomic.get entered then return() else if n=0 then fail(Failure "worker never entered original recognizer") else Lwt_unix.sleep 0.001 >>= fun()->started(n-1) in
 Fun.protect ~finally:(fun()->Atomic.set released true) (fun()->
  Lwt_unix.run(started 2000);Unix.sleepf 0.01;
  let writer=Unix.openfile "source.bin" [Unix.O_WRONLY;Unix.O_CLOEXEC] 0 in
  Fun.protect ~finally:(fun()->Unix.close writer) (fun()->
   let written=Unix.write_substring writer changed 0(String.length changed) in check(written=String.length changed) "short original mutation");
  Unix.utimes "source.bin" 1700000000. 1700000000.;
  let ms2,mn2,cs2,cn2=times "source.bin" in
  check(ms=1700000000L && mn=0 && ms2=ms && mn2=mn && (cs<>cs2 || cn<>cn2)) "exact native mtime-restored/ctime-changed fixture not achieved");
 let failed=try ignore(Lwt_unix.run job);false with W.Failed _->true in
 check(failed && not(H.is_cancelled cancellation)) "mutated recognizer returned stale result or cancellation hid error";
 Lwt_unix.run(W.shutdown pool);
 check(H.usage cpu=(0,0) && (W.usage pool).running=0 && (W.usage pool).pending=0 && (IoAdmission.usage io).active_jobs=0 && (IoAdmission.usage io).pending=0) "mutation failure released before settlement or leaked accounting";
 let after=Unix.LargeFile.fstat source in
 check(after.st_dev=before.st_dev && after.st_ino=before.st_ino && after.st_size=before.st_size && after.st_mtime=before.st_mtime) "caller descriptor or original identity changed unexpectedly";
 check(SemanticFile.with_fd source(fun file->SemanticFile.read file 0L(String.length changed))=changed) "caller descriptor was closed or rebound";
 Unix.close source;check(Array.length(Sys.readdir "/dev/fd")=baseline) "source mutation test leaked descriptors";
 Printf.printf "PASS active worker same-size mutation with exact restored native mtime refused; callerFD/accounting settled\n%!"
