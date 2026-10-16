(* Link the actual registered preferences/runtime from a matched private Make
   snapshot. Each configuration runs in a new process: runtime budgets freeze. *)
open Lwt
module H = HelperSupervisor
module I = IoAdmission
module R = SemanticRuntime
let assertions = ref 0
let check value reason = incr assertions; if not value then failwith reason
let run promise = Lwt_unix.run promise
let descriptors () = Array.length (Sys.readdir "/dev/fd")
let write path contents =
  let channel = open_out_bin path in output_string channel contents; close_out channel
let wire entries = Umarshal.from_string Prefs.mdumpedPrefs
  (Umarshal.to_string Umarshal.(list (prod3 string bool string id id)) entries) 0
let outgoing_absent () =
  let raw = Umarshal.from_string Umarshal.(list (prod3 string bool string id id))
    (Umarshal.to_string Prefs.mdumpedPrefs (Prefs.dump 1)) 0 in
  check (not (List.exists (fun (name,_,_) -> name="semanticvolumejobs") raw))
    "actual semanticvolumejobs was transmitted to peer"
let malformed_incoming_ignored () =
  Prefs.load (wire ["semanticvolumejobs",false,"invalid encoded integer"]) 999
let settled runtime =
  let u = I.usage runtime.R.io in
  check (u.active_jobs=0 && u.pending=0 && u.devices=[]) "runtime I/O credits leaked"
let shutdown runtime =
  run (SemanticWorkers.shutdown runtime.R.pool);
  check (H.usage runtime.R.supervisor=(0,0)) "runtime shutdown leaked CPU permits";
  settled runtime
let assert_limit runtime expected =
  let releases = List.init expected (fun _ -> Lwt.wait ()) in
  let held = List.map (fun release -> I.with_devices runtime.R.io (H.cancellation ())
    ~devices:[123] (fun () -> release)) releases in
  check ((I.usage runtime.R.io).active_jobs=expected) "configured filesystem limit admitted fewer jobs";
  let cancellation = H.cancellation () and started = ref false in
  let waiting = I.with_devices runtime.R.io cancellation ~devices:[123]
    (fun () -> started := true; return ()) in
  check (not !started && (I.usage runtime.R.io).pending=1) "configured filesystem limit admitted extra job";
  H.cancel cancellation;
  check (run waiting=None && not !started) "cancelled runtime limit waiter executed";
  List.iter (fun release -> Lwt.wakeup release ()) releases;
  List.iter (fun promise -> check (run promise=Some ()) "held runtime lease lost result") held;
  settled runtime
let expect_failure expected f =
  let matched = try ignore (run (f ())); false with error -> expected error in
  check matched "expected candidate failure was lost or replaced"
let candidate_checks runtime =
  let candidate = Filename.concat (Sys.getcwd ()) "candidate.bin" in
  write candidate "synthetic runtime IO candidate";
  let base = descriptors () in
  let expected_contents = "synthetic runtime IO candidate" in
  let callback_seen = ref false in
  check (run (R.with_io_file (H.cancellation ()) candidate (fun () ->
    callback_seen := true;
    check ((I.usage runtime.R.io).active_jobs=1) "candidate callback lacks I/O lease";
    check (descriptors ()=base+1) "candidate descriptor not retained during execution";
    return 17))=17 && !callback_seen) "candidate success result lost";
  check (descriptors ()=base) "candidate success leaked descriptor";
  settled runtime;
  List.iter (fun f ->
    expect_failure (function Failure message -> message="injected execution" | _ -> false)
      (fun () -> R.with_io_file (H.cancellation ()) candidate f);
    check (descriptors ()=base) "candidate execution failure leaked descriptor";
    settled runtime)
    [(fun () -> failwith "injected execution");
     (fun () -> Lwt_unix.sleep 0.002 >>= fun () -> fail (Failure "injected execution"))];
  (* A failed callback releases on the owner but deliberately defers starts.
     Drain that scheduled yield before asserting a newly active holder. *)
  ignore (run (Lwt_unix.yield ()));
  let release = Lwt.wait () and cancellation = H.cancellation () in
  let active = R.with_io_file cancellation candidate (fun () -> release) in
  let queued_cancel = H.cancellation () and queued_started = ref false in
  let waiting = R.with_io_file queued_cancel candidate
    (fun () -> queued_started := true; return ()) in
  check (descriptors ()=base+2 && (I.usage runtime.R.io).pending=1)
    "queued candidate descriptor/lease lifetime wrong";
  H.cancel queued_cancel;
  expect_failure (function Util.Transient _ -> true | _ -> false) (fun () -> waiting);
  check (not !queued_started && descriptors ()=base+1) "queued cancellation leaked/reused candidate descriptor";
  H.cancel_and_cleanup cancellation;
  check (descriptors ()=base+1 && (I.usage runtime.R.io).active_jobs=1)
    "active candidate cancellation freed a borrowed descriptor/lease early";
  Lwt.wakeup release ();
  ignore (run active);
  check (descriptors ()=base) "active candidate settlement leaked descriptor";
  settled runtime;
  let cancelled = H.cancellation () in
  H.cancel cancelled;
  expect_failure (function Util.Transient _ -> true | _ -> false)
    (fun () -> R.with_io_file cancelled candidate (fun () -> failwith "already-cancelled callback executed"));
  check (descriptors ()=base) "already-cancelled candidate leaked descriptor";
  let fifo = Filename.concat (Sys.getcwd ()) "candidate.fifo"
  and directory = Filename.concat (Sys.getcwd ()) "candidate.directory" in
  Unix.mkfifo fifo 0o600; Unix.mkdir directory 0o700;
  List.iter (fun path ->
    let called = ref false in
    let started = Unix.gettimeofday () in
    expect_failure (function Unix.Unix_error (Unix.EINVAL,"filesystem I/O candidate",_) -> true | _ -> false)
      (fun () -> R.with_io_file (H.cancellation ()) path (fun () -> called := true; return ()));
    check (not !called && Unix.gettimeofday () -. started < 1.) "nonregular candidate invoked callback or blocked";
    check (descriptors ()=base) "nonregular rejection leaked descriptor";
    settled runtime) [fifo;directory];
  expect_failure (function Unix.Unix_error (Unix.ENOENT,_,_) -> true | _ -> false)
    (fun () -> R.with_io_file (H.cancellation ()) (candidate ^ ".absent")
      (fun () -> failwith "absent candidate callback executed"));
  check (descriptors ()=base) "missing candidate error changed descriptor ownership";
  (* Repeated use catches accumulated leaks and a poisoned gate after failure. *)
  for index = 1 to 12 do
    check (run (R.with_io_file (H.cancellation ()) candidate (fun () -> return index))=index)
      "failed candidate poisoned exact follow-up";
    check (descriptors ()=base) "repeated candidate operation leaked descriptor"
  done;
  let input = open_in_bin candidate in
  let contents = really_input_string input (in_channel_length input) in
  close_in input;
  check (contents=expected_contents) "runtime scheduling changed candidate bytes";
  Sys.remove candidate; Sys.remove fifo; Unix.rmdir directory;
  settled runtime
let () =
  Unix.mkdir Util.unisonDir 0o700;
  let scenario = Sys.getenv "UNISON_IO_RUNTIME_CASE" in
  Prefs.loadStrings ["semanticworkers = 3"];
  outgoing_absent ();
  (match scenario with
  | "default" -> Prefs.loadEndpointLocal "I/O runtime qualification"
  | "endpoint" | "cli" | "candidate" ->
      write (Prefs.profilePathname ~add_ext:false "endpoint.prf") "semanticvolumejobs = 1\n";
      Prefs.loadEndpointLocal "I/O runtime qualification"
  | "negative" -> Prefs.loadStrings ["semanticvolumejobs = -1"]
  | "fault" -> ()
  | _ -> failwith "unknown runtime qualification scenario");
  malformed_incoming_ignored (); outgoing_absent ();
  (match scenario with
  | "negative" ->
      let base = descriptors () in
      let rejected = try ignore (R.get ()); false with
        Util.Fatal message -> message="semanticvolumejobs must be zero or positive" in
      check rejected "negative filesystem budget did not reject before runtime creation";
      check (descriptors ()=base) "negative configuration created native resources"
  | "fault" ->
      (* The runner injects a private Out_of_memory immediately after open,
         inside the production outer ownership guard. No actual OOM occurs. *)
      let candidate = Filename.concat (Sys.getcwd ()) "fault-candidate" in
      write candidate "fault ownership fixture";
      let base = descriptors () in
      let called = ref false in
      expect_failure (function Out_of_memory -> true | _ -> false)
        (fun () -> R.with_io_file (H.cancellation ()) candidate
          (fun () -> called := true; return ()));
      check (not !called) "allocation injection reached execution";
      check (descriptors ()=base) "first ownership-closure allocation leaked candidate descriptor";
      Sys.remove candidate
  | _ ->
      let runtime = R.get () in
      check (runtime.R.cpu_budget=3) "test CPU budget differs from requested endpoint runtime";
      let expected = match scenario with "default" -> runtime.R.cpu_budget | "cli" -> 2 | _ -> 1 in
      assert_limit runtime expected;
      if scenario="candidate" then candidate_checks runtime;
      shutdown runtime);
  Printf.printf "PASS actual endpoint/runtime %s (%d assertions)\n%!" scenario !assertions
