open Lwt
module H = HelperSupervisor
module W = SemanticWorkers
module A = SemanticAdmission
module I = IoAdmission
let assertions = ref 0
let check condition reason = incr assertions; if not condition then failwith reason
let run = Lwt_unix.run
let selected = Sys.argv.(1)
let operation = Sys.argv.(2)
let initial_wait = Sys.argv.(3)
let timers = int_of_string Sys.argv.(4)
let negative = Array.exists ((=) "negative") Sys.argv
let source = "source.bin"
let contents = String.init 8192 (fun i -> Char.chr ((i*73+19) land 255))
let write path data =
  let output=open_out_bin path in
  Fun.protect ~finally:(fun () -> close_out output) (fun () -> output_string output data)
let read path =
  let input=open_in_bin path in
  Fun.protect ~finally:(fun () -> close_in input)
    (fun () -> really_input_string input (in_channel_length input))
let rec until_started remaining =
  if Atomic.get Fault.entered then return ()
  else if remaining=0 then fail (Failure "actual worker did not reach its callback")
  else Lwt_unix.sleep 0.001 >>= fun () -> until_started (remaining-1)
let outcome promise = try match Lwt.poll promise with
  | None -> `Sleeping | Some result -> `Returned result
  with error -> `Failed error
let cost : A.cost = {payload_bytes=4096;descriptors=3}

let () =
  write source contents;
  let initial=Fault.fd_count () in
  let input=Unix.openfile source [Unix.O_RDONLY;Unix.O_CLOEXEC] 0 in
  let original=Unix.LargeFile.fstat input in
  let cpu=H.create ~cpu_permits:1 ~max_children:1 ~max_pending:8 in
  let io=I.create ~per_device:1 ~max_pending:8 in
  let pool=W.create_with_io ~io ~workers:1 ~max_pending:8 ~budget:cpu in
  let admission=A.create ~source_headroom:None ~max_transactions:1
    ~max_payload_bytes:4096 ~max_descriptors:3 ~max_pending:8 in
  let owner=A.make_reservation admission ~role:A.Consumer ~cost in
  let cancellation=H.cancellation () and next_cancel=H.cancellation ()
  and device_cancel=H.cancellation () and holder_cancel=H.cancellation () in
  let holder_release=Lwt.wait () in
  let device=I.devices_of_fds [input] in
  let base=Fault.fd_count () in
  let cleanup () =
    Atomic.set Fault.released true;
    H.cancel cancellation;H.cancel next_cancel;H.cancel device_cancel;
    H.cancel holder_cancel;
    (try match Lwt.poll holder_release with None -> Lwt.wakeup holder_release () | Some _ -> () with _ -> ());
    (try A.retire owner with _ -> ());
    (try ignore (run (W.shutdown pool)) with _ -> ());
    Unix.close input in
  Fun.protect ~finally:cleanup (fun () ->
    let holder = match initial_wait with
      | "cpu" -> H.with_cpu_permits cpu ~weight:1 holder_cancel
          (fun () -> holder_release) >>= fun _ -> return ()
      | "io" -> I.with_devices io holder_cancel ~devices:device
          (fun () -> holder_release) >>= fun _ -> return ()
      | "immediate" -> return ()
      | _ -> invalid_arg "unknown initial waiter" in
    Fault.configure selected timers;
    check (run (A.acquire owner cancellation)) "first resource reservation was not admitted";
    let module Recognizer = struct
      let format="worker-settlement-private/1"
      let identify file =
        ignore (SemanticFile.read file 0L 4);
        Fault.pause ();
        if operation="error" then raise (Unix.Unix_error (Unix.EIO,"worker-result","fixture"));
        FormatRecognition.Not_matched
    end in
    let recognizer=FormatRecognition.trusted (module Recognizer) in
    let first=A.with_borrow owner ~cost (fun () ->
      W.identify pool cancellation ~recognizers:[recognizer,false] input) in
    let ticks=ref 0 in
    let rec pulse n = if n=0 then return () else
      Lwt_unix.sleep 0.002 >>= fun () -> incr ticks;pulse (n-1) in
    if initial_wait<>"immediate" then begin
      ignore (run (pulse 2));
      check (not (Atomic.get Fault.entered) && Fault.fd_count ()=base+1 &&
             (W.usage pool).pending=1 && (W.usage pool).running=0 &&
             (A.usage admission).transactions=1)
        "queued first work lost its borrowed descriptor/reservation or executed before gate release";
      if initial_wait="cpu" then
        check (H.usage cpu=(1,0) && (I.usage io).active_jobs=1 && !(Fault.slots) ()=1)
          "queued CPU work did not retain its device and domain slot"
      else check (H.usage cpu=(0,0) && (I.usage io).active_jobs=1 &&
                  (I.usage io).pending=1 && !(Fault.slots) ()=0)
        "queued I/O work occupied CPU/domain slot or lost device wait";
      Lwt.wakeup holder_release ();ignore (run holder)
    end;
    ignore (run (until_started 3000));
    ignore (run (pulse 3));
    check (!ticks>=3 && Atomic.get Fault.entered && not (Atomic.get Fault.left))
      "owner-loop ticker did not progress alongside the actual paused domain";
    check (Fault.fd_count ()=base+2 && (W.usage pool).running=1)
      "fixture did not observe both actual worker-owned input/channel descriptors";
    if selected<>"normal" then begin
      check (!(Fault.failures)=2) "the two designated waiter faults did not fire";
      check !(Fault.captured) "fault target was not an actual captured promise";
      check (!(Fault.timer_failures)=timers) "finite post-waiter polling timer faults did not execute"
    end;
    (* Retire before checking accounting. The independent kernel FD census and
       active domain marker make premature envelope release observable. *)
    A.retire owner;
    let admitted=A.usage admission in
    let workers=W.usage pool and devices=I.usage io in
    check (admitted.transactions=1 && admitted.descriptors=3 && admitted.payload_bytes=4096 &&
           workers.pending=1 && !(Fault.slots) ()=1 && H.usage cpu=(1,0) &&
           devices.active_jobs=1 && devices.devices<>[] && outcome first=`Sleeping)
      "DESIGNATED active worker descriptors escaped retained workspace/CPU/IO/slot admission";
    let next_entered=ref false and device_entered=ref false in
    let next=A.with_lease admission next_cancel ~role:A.Consumer ~cost (fun () ->
      next_entered:=true;W.digest pool next_cancel input) in
    let same_device=I.with_devices io device_cancel ~devices:device
      (fun () -> device_entered:=true;return ()) in
    ignore (run (pulse 3));
    check (not !next_entered && not !device_entered &&
           (A.usage admission).pending=1 && (I.usage io).pending=1)
      "next consumer or same-device callback started while first worker retained descriptors";
    if operation="cancel" then H.cancel cancellation;
    ignore (run (pulse 3));
    check (Fault.fd_count ()=base+2 && (W.usage pool).running=1 &&
           (W.usage pool).pending=1 && !(Fault.slots) ()=1 && H.usage cpu=(1,0) &&
           (I.usage io).active_jobs=1 && (A.usage admission).transactions=1 &&
           not !next_entered && not !device_entered && outcome first=`Sleeping)
      "cancellation or retirement released borrowed worker resources before settlement";
    Atomic.set Fault.released true;
    let completed=try Ok (run first) with error -> Error error in
    if selected="normal" then
      (match operation,completed with
       | "cancel",Ok None -> ()
       | "success",Ok (Some result) -> check (result.W.formats=[] && result.fingerprint=None) "normal recognition changed"
       | "error",Error (W.Failed _) -> ()
       | _ -> failwith "normal worker success/error/cancellation outcome changed")
    else check (completed=Error Fault.primary) "secondary fault/cancellation replaced the first waiter exception";
    check (Atomic.get Fault.left) "caller returned before actual callback left";
    (match run next with
     | Some (Some fingerprint) -> check (fingerprint.W.digest=SemanticHash.string contents) "exact follow-up digest changed"
     | _ -> failwith "queued next consumer failed exact reuse");
    check (run same_device=Some () && !next_entered && !device_entered)
      "settled worker stranded resource or device waiter";
    ignore (run (Lwt_unix.yield ()));
    let a=A.usage admission and w=W.usage pool and i=I.usage io in
    check (a.transactions=0 && a.pending=0 && a.descriptors=0 && a.payload_bytes=0 &&
           w.pending=0 && w.running=0 && !(Fault.slots) ()=0 && H.usage cpu=(0,0) &&
           i.active_jobs=0 && i.pending=0 && i.devices=[] && Fault.fd_count ()=base)
      "worker completion did not settle actual descriptors and every admission ledger";
    let now=Unix.LargeFile.fstat input in
    check (now.Unix.LargeFile.st_dev=original.Unix.LargeFile.st_dev &&
           now.st_ino=original.st_ino && now.st_size=original.st_size && read source=contents)
      "worker failure changed/closed borrowed source";
    check (not negative) "negative participant unexpectedly passed current accounting invariant";
    Printf.printf "PASS settlement phase=%s operation=%s wait=%s attempts=%d faults=%d timer_faults=%d ticker=%d assertions=%d\n%!"
      selected operation initial_wait !(Fault.attempts) !(Fault.failures)
      !(Fault.timer_failures) !ticks !assertions);
  check (Fault.fd_count ()=initial) "pool shutdown leaked descriptors";
  Printf.printf "PASS exact reuse/shutdown phase=%s\n%!" selected
