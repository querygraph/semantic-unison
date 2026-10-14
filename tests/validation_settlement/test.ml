open Lwt
module H = HelperSupervisor
module V = DngValidation
module A = SemanticAdmission
module I = IoAdmission
let phase = Sys.argv.(1)
let action = Sys.argv.(2)
let policy = match Sys.argv.(3) with "warn" -> V.Warn | "require" -> V.Require
  | "off" -> V.Off | _ -> invalid_arg "policy"
let cancel = Sys.argv.(4) = "cancel"
let negative = Array.exists ((=) "negative") Sys.argv
let helper = Sys.argv.(5)
let timer_errors = if Array.length Sys.argv > 6 && Sys.argv.(6) <> "negative"
  then int_of_string Sys.argv.(6) else 0
let directory = Sys.getcwd ()
let candidate = Filename.concat directory "candidate.dng"
let gate = Filename.concat directory "release.control"
let ready = Filename.chop_extension gate ^ ".ready.json"
let assertions = ref 0
let check condition message = incr assertions; if not condition then failwith message
let write path contents =
  let channel = open_out_bin path in
  Fun.protect ~finally:(fun () -> close_out channel)
    (fun () -> output_string channel contents)
let read path =
  let channel = open_in_bin path in
  Fun.protect ~finally:(fun () -> close_in channel)
    (fun () -> really_input_string channel (in_channel_length channel))
let sha contents = SemanticHash.hex (SemanticHash.string contents)
let inspect path =
  let before = Unix.LargeFile.stat path in
  let digest = sha (read path) in
  let after = Unix.LargeFile.stat path in
  if {before with Unix.LargeFile.st_atime = 0.} <> {after with Unix.LargeFile.st_atime = 0.}
  then failwith "synthetic inspection changed during hashing";
  return { V.sha256 = digest; size = before.Unix.LargeFile.st_size;
    identity = Printf.sprintf "%d:%d:%Ld:%.17g:%.17g:%d"
      before.st_dev before.st_ino before.st_size before.st_mtime before.st_ctime before.st_perm }
let outcome promise = try match Lwt.poll promise with None -> `Sleeping | Some result -> `Returned result
  with error -> `Failed error
let rec until_ready n =
  if Sys.file_exists ready then return ()
  else if n = 0 then fail (Failure "actual gated helper did not become ready")
  else Lwt_unix.sleep 0.002 >>= fun () -> until_ready (n - 1)
let pulse n =
  let rec go n = if n = 0 then return () else Lwt_unix.sleep 0.002 >>= fun () -> go (n - 1)
  in Lwt_unix.run (go n)
let unreaped_alive pid =
  match Unix.waitpid [Unix.WNOHANG] pid with 0, _ -> true | _ -> false
let reaped pid =
  try ignore (Unix.waitpid [Unix.WNOHANG] pid); false
  with Unix.Unix_error (Unix.ECHILD, _, _) -> true
let has text part =
  let rec loop offset = offset + String.length part <= String.length text &&
    (String.sub text offset (String.length part) = part || loop (offset + 1)) in
  loop 0
let result_message = function V.Warning (message, _) | V.Rejected (message, _) -> message
  | _ -> ""
let cost : A.cost = { payload_bytes = 4096; descriptors = 3 }

let () =
  let original = "owned synthetic DNG validation candidate; no Adobe pixels" in
  write candidate original;
  let helper_original = read helper in
  let expected = Lwt_unix.run (inspect candidate) in
  let cpu = H.create ~cpu_permits:1 ~max_children:1 ~max_pending:8 in
  let io = I.create ~per_device:1 ~max_pending:8 in
  let admission = A.create ~source_headroom:None ~max_transactions:1
    ~max_payload_bytes:4096 ~max_descriptors:3 ~max_pending:8 in
  let owner = A.make_reservation admission ~role:A.Consumer ~cost in
  let cancellation = H.cancellation () in
  let next_cancel = H.cancellation () and device_cancel = H.cancellation () in
  let input = Unix.openfile candidate [Unix.O_RDONLY; Unix.O_CLOEXEC] 0 in
  let device = I.devices_of_fds [input] in
  let cleanup () =
    (try write gate "release\n" with _ -> ());
    H.cancel_and_cleanup cancellation;
    H.cancel_and_cleanup next_cancel; H.cancel_and_cleanup device_cancel;
    A.retire owner;
    Unix.close input;
    if read helper <> helper_original then write helper helper_original in
  Fun.protect ~finally:cleanup (fun () ->
    check (Lwt_unix.run (A.acquire owner cancellation)) "resource envelope was not admitted";
    Fault.reset_native (); Fault.configure ~timer_errors phase;
    let executions = ref 0 and inspections = ref 0 in
    let inspected path =
      incr inspections;
      if policy=V.Off then failwith "off invoked candidate/tool inspection";
      inspect path in
    let execute run =
      incr executions;
      let pending = BorrowedWork.try_bind
        (fun () -> I.with_devices io cancellation ~devices:device run)
        (function Some child -> return child | None -> fail (Failure "cancelled before helper")) fail in
      Fault.watch "execute" pending in
    let tool = { V.executable = helper; executable_sha256 = sha helper_original;
      build_id = "validation-settlement-synthetic-1"; arguments = [|gate; action|];
      environment = [||]; cpu_weight = 1;
      limits = { H.timeout = 10.; terminate_grace = 0.3; stdout_bytes = 4096; stderr_bytes = 4096 } } in
    let validation = A.with_borrow owner ~cost (fun () ->
      V.validate_with_execution ~execute cpu cancellation ~policy ~tool:(Some tool)
        ~inspect:inspected ~candidate ~expected) in
    if policy = V.Off then begin
      check (Lwt_unix.run validation = V.Skipped) "off changed its verdict";
      check (!inspections = 0 && !executions = 0 && Fault.pids () = []) "off inspected/executed a helper";
      A.retire owner;
      check ((A.usage admission).transactions = 0 && H.usage cpu = (0, 0) &&
             (I.usage io).active_jobs = 0) "off retained resources";
      Printf.printf "PASS validation off assertions=%d\n%!" !assertions
    end else begin
      Lwt_unix.run (until_ready 2000);
      let pids = Fault.pids () in
      check (List.length pids = 1) "not exactly one native child";
      let pid = List.hd pids in
      pulse 3;
      check (unreaped_alive pid) "gated helper was not an actual live/unreaped child";
      if phase <> "normal" then begin
        check (!(Fault.failures) >= 1) "designated observer fault did not fire";
        check (!(Fault.target) <> None) "designated exact returned promise was not captured"
      end;
      A.retire owner;
      let a = A.usage admission and i = I.usage io in
      check (outcome validation = `Sleeping && a.transactions = 1 && a.payload_bytes = 4096 &&
             a.descriptors = 3 && H.usage cpu = (1, 1) && i.active_jobs = 1)
        "DESIGNATED validation result/workspace retired with an actual live helper";
      let next_entered = ref false and device_entered = ref false in
      let next = A.with_lease admission next_cancel ~role:A.Consumer ~cost
        (fun () -> next_entered := true; return ()) in
      let same_device = I.with_devices io device_cancel ~devices:device
        (fun () -> device_entered := true; return ()) in
      pulse 3;
      check (not !next_entered && not !device_entered &&
             (A.usage admission).pending = 1 && (I.usage io).pending = 1)
        "waiting workspace/device callback entered before helper settlement";
      if cancel then H.cancel cancellation;
      pulse 3;
      check (unreaped_alive pid && outcome validation = `Sleeping &&
             (A.usage admission).transactions = 1 && H.usage cpu = (1, 1) &&
             (I.usage io).active_jobs = 1 && not !next_entered && not !device_entered)
        "cancellation released validation before actual helper stop/reap";
      write gate "release\n";
      let result = Lwt_unix.run validation in
      check (reaped pid) "validation returned before actual owned child was reaped";
      if cancel then check (match result with V.Rejected _ -> true | _ -> false)
        "cancelled validation did not reject"
      else if action = "candidate-mutation" || action = "tool-mutation" then begin
        check (match result with V.Rejected _ -> true | _ -> false)
          "late candidate/tool mutation passed after unrecorded helper receipt";
        check (has (result_message result) (if action = "candidate-mutation" then "candidate changed" else "driver changed"))
          "late mutation lost the actual post-helper identity fence"
      end else if phase <> "normal" then begin
        check (match policy, result with V.Warn, V.Warning (_, None) | V.Require, V.Rejected (_, None) -> true
          | _ -> false) "returned-promise setup fault changed policy/uncaptured-receipt semantics";
        check (has (result_message result) "Primary_waiter" && not (has (result_message result) "Secondary_waiter"))
          "retry error replaced first observer setup error";
        check (!(Fault.failures) = 2) "both finite observer setup faults were not exercised"
      end else if action = "malformed" then
        check (match policy, result with V.Warn, V.Warning (_, Some _) | V.Require, V.Rejected (_, Some _) -> true
          | _ -> false) "ordinary malformed receipt policy changed"
      else check (match result with V.Passed _ -> true | _ -> false) "ordinary qualified receipt failed";
      check (Lwt_unix.run next = Some () && Lwt_unix.run same_device = Some () &&
             !next_entered && !device_entered) "settled validation stranded queued workspace/device reuse";
      pulse 1;
      let a = A.usage admission and i = I.usage io in
      check (a.transactions = 0 && a.pending = 0 && a.payload_bytes = 0 && a.descriptors = 0 &&
             H.usage cpu = (0, 0) && i.active_jobs = 0 && i.pending = 0 && i.devices = [])
        "settled helper leaked CPU/IO/workspace accounting";
      if action <> "candidate-mutation" then check (read candidate = original) "helper changed candidate bytes unexpectedly";
      (* Reuse the actual supervisor and both gates for another real child,
         with a new cancellation identity and freshly captured file snapshot. *)
      write candidate original;
      if read helper <> helper_original then write helper helper_original;
      let reuse_cancel = H.cancellation () in
      let reuse_execute work = BorrowedWork.try_bind
        (fun () -> I.with_devices io reuse_cancel ~devices:device work)
        (function Some child -> return child | None -> fail (Failure "reuse device cancelled")) fail in
      let reuse_expected = Lwt_unix.run (inspect candidate) in
      let reused = A.with_lease admission reuse_cancel ~role:A.Consumer ~cost (fun () ->
        V.validate_with_execution ~execute:reuse_execute cpu reuse_cancel ~policy:V.Require
          ~tool:(Some {tool with V.arguments=[|gate;"pass"|]}) ~inspect
          ~candidate ~expected:reuse_expected) in
      check (match Lwt_unix.run reused with Some (V.Passed _) -> true | _ -> false)
        "actual supervised validation child could not reuse settled CPU/IO/workspace";
      check (List.length (Fault.pids ())=2 && List.for_all reaped (Fault.pids ()) &&
             H.usage cpu=(0,0) && (I.usage io).active_jobs=0 && (A.usage admission).transactions=0)
        "actual follow-up child failed exact reap/accounting reuse";
      check (not negative) "negative participant unexpectedly passed validation settlement";
      check (!(Fault.timer_failures) = timer_errors) "finite drain timer errors were not exercised";
      Printf.printf "PASS validation phase=%s action=%s policy=%s cancel=%b pids=%d faults=%d assertions=%d\n%!"
        phase action (match policy with V.Warn -> "warn" | V.Require -> "require" | V.Off -> "off")
        cancel (List.length pids) !(Fault.failures) !assertions
    end)
