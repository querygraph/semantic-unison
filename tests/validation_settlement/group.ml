(* Runner inserts Group.all backed by actual fixed BorrowedWork.all or the
   parent's exact legacy Lwt_util.iter launch/join implementation. *)
open Lwt
module H = HelperSupervisor
module A = SemanticAdmission
module I = IoAdmission
let phase = Sys.argv.(1)
let active = if phase = "launch-one" then 1 else 2
let helper = Sys.argv.(2)
let timer_errors = if Array.length Sys.argv>3 && Sys.argv.(3)<>"negative"
  then int_of_string Sys.argv.(3) else 0
let negative = Array.exists ((=) "negative") Sys.argv
let assertions = ref 0
let check yes message = incr assertions; if not yes then failwith message
let write path text = let channel = open_out_bin path in
  Fun.protect ~finally:(fun () -> close_out channel) (fun () -> output_string channel text)
let pids () = Fault.pids ()
let sleeping p = try Lwt.poll p = None with _ -> false
let alive pid = match Unix.waitpid [Unix.WNOHANG] pid with 0, _ -> true | _ -> false
let reaped pid = try ignore (Unix.waitpid [Unix.WNOHANG] pid); false
  with Unix.Unix_error (Unix.ECHILD, _, _) -> true
let rec until_paths paths n =
  if List.for_all Sys.file_exists paths then return ()
  else if n = 0 then fail (Failure "two actual consumers did not become ready")
  else Lwt_unix.sleep 0.002 >>= fun () -> until_paths paths (n - 1)
let pulse () = Lwt_unix.run (Lwt_unix.sleep 0.01)
let cost : A.cost = { payload_bytes = 4096; descriptors = 3 }
let () =
  let cpu = H.create ~cpu_permits:2 ~max_children:2 ~max_pending:8 in
  let io = I.create ~per_device:2 ~max_pending:8 in
  let admission = A.create ~source_headroom:None ~max_transactions:2
    ~max_payload_bytes:8192 ~max_descriptors:6 ~max_pending:8 in
  let cancellations = Array.init 2 (fun _ -> H.cancellation ()) in
  let gates = Array.init 2 (fun i -> Filename.concat (Sys.getcwd ()) ("consumer-" ^ string_of_int i ^ ".control")) in
  let ready = List.init active (fun index -> Filename.chop_extension gates.(index) ^ ".ready.json") in
  let candidate = Filename.concat (Sys.getcwd ()) "candidate.dng" in
  let bytes = "actual independently gated directory-consumer fixture" in
  write candidate bytes;
  let hash = SemanticHash.hex (SemanticHash.string bytes) in
  let inputs = Array.init 2 (fun _ -> Unix.openfile candidate [Unix.O_RDONLY;Unix.O_CLOEXEC] 0) in
  let device = I.devices_of_fds [inputs.(0)] in
  let started = ref 0 and completed = ref 0 and remembered = ref None in
  Fault.reset_native (); Fault.configure ~timer_errors (if phase = "join" then "group-first" else "normal");
  let cleanup () =
    Array.iter (fun path -> try write path "release\n" with _ -> ()) gates;
    Array.iter H.cancel_and_cleanup cancellations;
    Array.iter Unix.close inputs in
  Fun.protect ~finally:cleanup (fun () ->
    let start index () =
      if (phase="launch-one" && index=1) || index=2 then raise Fault.Primary_waiter;
      incr started;
      let cancellation = cancellations.(index) in
      let promise = BorrowedWork.try_bind
        (fun () -> A.with_lease admission cancellation ~role:A.Consumer ~cost (fun () ->
        BorrowedWork.try_bind (fun () -> I.with_devices io cancellation ~devices:device (fun () ->
          H.run cpu ~weight:1 cancellation
            ~limits:{H.timeout=10.;terminate_grace=0.3;stdout_bytes=4096;stderr_bytes=4096}
            ~executable:helper ~environment:[||]
            ~arguments:[|gates.(index);"pass";"--unison-dng-validation-v1";
              "--expected-sha256";hash;"--expected-size";string_of_int (String.length bytes);
              "--threads";"1";"--";candidate|]))
          (function Some child ->
            check (child.H.status = Some (Unix.WEXITED 0)) "actual consumer child failed";
            incr completed; return ()
          | None -> fail (Failure "device acquisition cancelled")) fail))
        (function Some () -> return () | None -> fail (Failure "workspace acquisition cancelled")) fail in
      if index = 0 then Fault.watch "group-first" promise else promise in
    let count = if phase="launch" || phase="launch-one" then 3 else 2 in
    let promise = try Group.all ~on_error:(fun error -> if !remembered=None then remembered:=Some error)
      (List.init count start) with error -> Lwt.fail error in
    Lwt_unix.run (until_paths ready 2000);
    pulse ();
    check (!started=active && !completed=0 && List.length (pids ())=active && List.for_all alive (pids ()))
      "directory fixture did not run the designated actual children concurrently";
    let a=A.usage admission and i=I.usage io in
    check (sleeping promise && a.transactions=active && a.payload_bytes=4096*active && a.descriptors=3*active &&
           H.usage cpu=(active,active) && i.active_jobs=active)
      "DESIGNATED aggregate reported failure with an actual live sibling consumer";
    write gates.(0) "release\n";
    pulse ();
    let rec first_done n =
      if !completed=1 then return () else if n=0 then fail (Failure "first consumer did not settle")
      else Lwt_unix.sleep 0.002 >>= fun () -> first_done (n-1) in
    Lwt_unix.run (first_done 2000);
    if active=2 then begin
    check (sleeping promise && !completed=1 && reaped (List.hd (pids ())) &&
           alive (List.nth (pids ()) 1) && (A.usage admission).transactions=1 &&
           H.usage cpu=(1,1) && (I.usage io).active_jobs=1)
      "aggregate failure stopped draining after its first participant";
    write gates.(1) "release\n";
    end;
    let result = try ignore (Lwt_unix.run promise); Ok () with error -> Error error in
    if phase="normal" then check (result=Ok ()) "normal group changed its result"
    else check (result=Error Fault.Primary_waiter && !remembered=Some Fault.Primary_waiter)
      "aggregate replaced its first setup error";
    check (!completed=active && !started=active && List.for_all reaped (pids ()))
      "aggregate returned before every actual child was stopped/reaped or retried a task";
    let a=A.usage admission and i=I.usage io in
    check (a.transactions=0 && a.pending=0 && a.payload_bytes=0 && a.descriptors=0 &&
           H.usage cpu=(0,0) && i.active_jobs=0 && i.pending=0)
      "aggregate leaked retained resources";
    check (not negative) "negative aggregate unexpectedly retained all active participants";
    check (!(Fault.timer_failures)=timer_errors) "aggregate finite drain timer faults were not exercised";
    Printf.printf "PASS directory aggregate phase=%s actual_consumers=%d completed=%d waiter_faults=%d assertions=%d\n%!"
      phase !started !completed !(Fault.failures) !assertions)
