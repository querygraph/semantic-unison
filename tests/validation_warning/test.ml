open Lwt
module H = HelperSupervisor
module W = SemanticWorkers
module R = SemanticRuntime
module A = SemanticAdmission
module I = IoAdmission
module P = Probe
let assertions = ref 0
let check condition message = incr assertions; if not condition then failwith message
let run = Lwt_unix.run
let case = Sys.argv.(1)
let negative = Array.length Sys.argv > 3
let helper = Sys.argv.(2)
let candidate = Filename.concat (Sys.getcwd ()) "candidate.dng"
let original = "SYNTHETIC-WARNING-CANDIDATE\000" ^ String.make 8192 'q'
let write path bytes =
  let channel = open_out_bin path in
  Fun.protect ~finally:(fun () -> close_out channel) (fun () -> output_string channel bytes)
let read path =
  let channel = open_in_bin path in
  Fun.protect ~finally:(fun () -> close_in channel) (fun () ->
    really_input_string channel (in_channel_length channel))
let has text part =
  let n = String.length part in
  let rec find index = index + n <= String.length text &&
    (String.sub text index n = part || find (index + 1)) in
  find 0
let inspect runtime cancellation path =
  let fd = Unix.openfile path [Unix.O_RDONLY; Unix.O_CLOEXEC; Unix.O_NONBLOCK] 0 in
  let closed = ref false in
  let close () = if not !closed then begin closed := true; Unix.close fd end in
  try BorrowedWork.try_bind (fun () -> W.digest runtime.R.pool cancellation fd)
    (fun result -> close (); match result with
      | None -> fail (Util.Transient "private inspection cancelled")
      | Some fingerprint ->
          let st = fingerprint.W.stats in
          return {CandidateValidator.sha256 = SemanticHash.hex fingerprint.digest;
            size = st.Unix.LargeFile.st_size;
            identity = Printf.sprintf "%d:%d:%Ld:%.17g:%.17g:%d:%d"
              st.Unix.LargeFile.st_dev st.st_ino st.st_size st.st_mtime st.st_ctime
              st.st_perm st.st_nlink})
    (fun error -> close (); fail error)
  with error -> close (); raise error
let ledgers_settled runtime =
  let a = R.admission_usage () and i = I.usage runtime.R.io
  and w = W.usage runtime.R.pool in
  check (a.A.transactions = 0 && a.pending = 0 && a.payload_bytes = 0 &&
    a.descriptors = 0 && i.I.active_jobs = 0 && i.pending = 0 && i.devices = [] &&
    w.W.pending = 0 && w.running = 0 && H.usage runtime.supervisor = (0, 0))
    "warning control left an active helper/worker/resource ledger"
let main () =
  Unix.mkdir Util.unisonDir 0o700;
  write candidate original;
  let mode = if case = "warn-mutation" then "mutate"
    else if case = "warn-active-cancel" then "hang"
    else if case = "warn-pass" then "pass" else "error" in
  write (candidate ^ ".control") mode;
  let policy = if case = "require-error" then "require" else if case = "off" then "off" else "warn" in
  Prefs.loadStrings ["log = false"; "semanticworkers = 1";
    "semanticmaxinflight = 1"; "semanticpayloadbudget = 1";
    "semanticdescriptorbudget = 24"; "semanticvolumejobs = 1";
    "adobevalidate = " ^ policy; "adobevalidator = " ^ helper;
    "adobevalidatorhash = " ^ SemanticHash.hex (SemanticHash.string (read helper));
    "adobevalidatorbuild = validation-warning-synthetic-1";
    "adobevalidatorthreads = 1"; "adobevalidatetimeout = 10"];
  Features.setEnabled (Features.all ());
  Trace.sendLogMsgsToStderr := false;
  let runtime = R.get () and cancellation = H.cancellation () in
  let notices = ref [] and calls = ref 0 and sibling = ref None in
  let expected = run (inspect runtime cancellation candidate) in
  let context_inspect path =
    incr calls;
    if case = "warn-inspection-error" && !calls = 1 then
      fail (Unix.Unix_error (Unix.EIO, "private warning inspection", path))
    else BorrowedWork.bind (fun () -> inspect runtime cancellation path) (fun snapshot ->
      if !calls = 4 then begin
        (* This continuation executes inside the actual final tool-digest
           dispatch. The warning must leave that dispatch and rearm its pump. *)
        check (!P.dispatch_depth > 0) "final inspected tool did not use actual worker dispatch";
        check (H.usage runtime.supervisor = (0, 0)) "validation CPU/helper credits not settled before notice";
        P.anchor ();
        sibling := Some (inspect runtime (H.cancellation ()) candidate);
        if case = "warn-before-delivery-cancel" then H.cancel cancellation
      end;
      return snapshot) in
  Util.warnPrinter := Some (fun message ->
    notices := message :: !notices;
    check (!P.dispatch_depth = 0 && !P.pump_rearms > !P.warning_anchor)
      "DESIGNATED warning delivered inside unrearmed worker dispatch";
    let a = R.admission_usage () in
    check (a.A.transactions = 1 && a.payload_bytes = 1048576 && a.descriptors = 9)
      "candidate workspace retired before warning delivery";
    (* Model the existing remote warning printer's nested owner-loop wait.
       This is a real sibling hash, requiring the real pump to consume it. *)
    (match !sibling with
      | None -> failwith "warning did not retain its independently launched sibling"
      | Some job -> check ((run job).CandidateValidator.sha256 = expected.sha256)
          "nested warning delivery did not consume actual sibling hash");
    if case = "warn-delivery-cancel" then H.cancel cancellation;
    if case = "warn-delivery-abort" then Abort.all ();
    if case = "warn-printer-error" then failwith "private warning printer failure");
  let context = {CandidateValidator.supervisor = runtime.supervisor; cancellation;
    cpu_budget = runtime.cpu_budget; candidate; expected; inspect = context_inspect;
    execute = R.with_io_file cancellation candidate} in
  let rec cancel_active left =
    if Sys.file_exists (candidate ^ ".calls") then (H.cancel cancellation; return ())
    else if left = 0 then fail (Failure "synthetic helper did not enter active cancellation")
    else Lwt_unix.sleep 0.001 >>= fun () -> cancel_active (left - 1) in
  if case = "warn-active-cancel" then Lwt.ignore_result (cancel_active 5000);
  let cleanup () =
    H.cancel cancellation;
    (match !sibling with None -> () | Some job -> (try ignore (run job) with _ -> ()));
    ignore (run (W.shutdown runtime.pool)); Abort.reset () in
  Fun.protect ~finally:cleanup (fun () ->
    let work = R.with_admission cancellation ~payload_bytes:1048576 ~descriptors:9 (fun () ->
      match DngCandidateValidation.select () with
      | None -> return ()
      | Some validate -> validate context) in
    let verdict = try run work; Ok () with error -> Error error in
    if negative && case = "warn-error" then begin
      match verdict with
      | Error (Failure message) when has message "DESIGNATED" -> failwith message
      | _ -> check (List.length !notices = 1)
          "DESIGNATED allowed validation finding never reached visible warning channel"
    end;
    let should_pass = List.mem case ["warn-error"; "warn-pass"; "off"] in
    check ((match verdict with Ok () -> true | Error _ -> false) = should_pass)
      "companion warning policy produced incorrect success/rejection";
    let should_warn = List.mem case ["warn-error"; "warn-delivery-cancel";
      "warn-delivery-abort"; "warn-printer-error"] in
    check (List.length !notices = if should_warn then 1 else 0)
      "companion emitted an absent, duplicate or forbidden warning";
    List.iter (fun message -> check (has message "Adobe DNG validation warning" &&
      has message candidate && has message "validation errors") "visible warning lost candidate/finding") !notices;
    let helper_calls = if Sys.file_exists (candidate ^ ".calls") then
      List.filter ((<>) "") (String.split_on_char '\n' (read (candidate ^ ".calls"))) else [] in
    let expected_helpers = if case = "off" || case = "warn-inspection-error" then 0 else 1 in
    check (List.length helper_calls = expected_helpers) "unexpected helper invocation count";
    List.iter (fun line ->
      let pid = int_of_string (List.hd (String.split_on_char '\t' line)) in
      check (try ignore (Unix.waitpid [Unix.WNOHANG] pid); false
        with Unix.Unix_error (Unix.ECHILD, _, _) -> true)
        "synthetic helper was still owned/unreaped after companion returned") helper_calls;
    check ((read candidate <> original) = (case = "warn-mutation"))
      "candidate bytes changed outside explicit helper mutation control";
    (match !sibling with None -> () | Some job -> ignore (run job));
    ledgers_settled runtime;
    check (not negative) "designated negative unexpectedly passed";
    Printf.printf "PASS case=%s warnings=%d helper_calls=%d dispatch_depth=%d rearmed=%d assertions=%d\n%!"
      case (List.length !notices) (List.length helper_calls) !P.dispatch_depth !P.pump_rearms !assertions)
let () =
  try main () with Failure message when has message "DESIGNATED" ->
    Printf.eprintf "%s\n%!" message; exit 2
