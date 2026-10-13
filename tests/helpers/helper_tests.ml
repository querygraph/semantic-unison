open Lwt
module H = HelperSupervisor
module V = DngValidation
let check yes message = if not yes then failwith message
let helper = Sys.argv.(1)
let limits = { H.timeout = 2.; terminate_grace = 0.05;
               stdout_bytes = 4096; stderr_bytes = 4096 }
let supervisor () = H.create ~cpu_permits:2 ~max_children:2 ~max_pending:8
let run ?(limits=limits) ?(weight=1) t c args =
  H.run t ~weight c ~limits ~executable:helper ~arguments:args ~environment:[||]
let completed r = r.H.outcome = H.Completed && r.status = Some (Unix.WEXITED 0)
let describe r = Printf.sprintf "outcome=%s status=%s stdout=%S stderr=%S"
  (match r.H.outcome with H.Completed -> "completed" | H.Cancelled -> "cancelled"
   | H.Timed_out -> "timeout" | H.Output_limit -> "output-limit" | H.Failed s -> s)
  (match r.status with None -> "none" | Some (Unix.WEXITED n) -> "exit " ^ string_of_int n
   | Some (Unix.WSIGNALED n) -> "signal " ^ string_of_int n
   | Some (Unix.WSTOPPED n) -> "stopped " ^ string_of_int n) r.stdout r.stderr
let finish t = check (H.usage t = (0, 0)) "leaked admission permits"
let test name f = f (); Printf.printf "PASS %s\n%!" name

let hash = String.make 64 'a'
let tool_hash = String.make 64 'c'
let expected = { V.sha256 = hash; size = 23L; identity = "candidate-v1" }
let tool_snapshot = { V.sha256 = tool_hash; size = 100L; identity = "tool-v1" }
let inspect path = return (if path = helper then tool_snapshot else expected)
let tool mode = { V.executable = helper; executable_sha256 = tool_hash;
  build_id = "synthetic-1"; arguments = [|mode|]; environment = [||];
  cpu_weight = 1; limits }
let validate ?(policy=V.Require) ?(inspect=inspect) ?configured mode =
  let configured = match configured with None -> Some (tool mode) | Some t -> t in
  let t = supervisor () in
  let result = Lwt_unix.run (V.validate t (H.cancellation ()) ~policy
    ~tool:configured ~inspect ~candidate:"/synthetic/candidate.dng" ~expected) in
  finish t; result
let rejected = function V.Rejected _ -> true | _ -> false

let () =
  test "online CPU budget available" (fun () -> check (H.available_cpus () > 0) "no CPUs");
  test "physical CPU budget matches host topology or logical fallback" (fun () ->
    let logical = H.available_cpus () and physical = H.available_physical_cpus () in
    check (physical > 0 && physical <= logical) "physical budget outside logical capacity";
    if Sys.file_exists "/System/Library/CoreServices/SystemVersion.plist" then begin
      (* Compare against the OS utility independently of the production C stub.
         If topology is unavailable, the documented logical fallback applies. *)
      let input = Unix.open_process_args_in "/usr/sbin/sysctl"
        [|"sysctl"; "-n"; "hw.physicalcpu"|] in
      let expected = try Some (int_of_string (input_line input))
        with End_of_file | Failure _ -> None in
      let status = Unix.close_process_in input in
      let expected = match expected, status with
        | Some n, Unix.WEXITED 0 when n > 0 -> min logical n
        | _ -> logical in
      check (physical = expected) "physical budget differs from macOS topology"
    end else
      check (physical = logical) "portable logical fallback differs";
    Printf.printf "CPU topology: logical=%d automatic=%d\n%!" logical physical);
  test "cancellation identity remains stable in connection resource registry" (fun () ->
    let a = H.cancellation () and b = H.cancellation () in
    let resources = Hashtbl.create 2 in
    Hashtbl.add resources a 1; Hashtbl.add resources b 2;
    H.cancel a;
    check (Hashtbl.find resources a = 1 && Hashtbl.find resources b = 2)
      "cancel token hash/equality changed";
    Hashtbl.remove resources a;
    check (Hashtbl.length resources = 1) "resource did not unregister");
  test "worker cancellation callback synchronous, once, unregisterable" (fun () ->
    let c = H.cancellation () and hits = ref 0 in
    let unregister = H.on_cancel c (fun () -> incr hits) in
    let removed = H.on_cancel c (fun () -> hits := !hits + 100) in
    removed (); H.cancel c; H.cancel c;
    check (!hits = 1) "callback needs a tick or ran twice";
    unregister ();
    let unregister_late = H.on_cancel c (fun () -> incr hits) in
    check (!hits = 2) "late cancellation not immediate"; unregister_late ());
  test "literal argv, no shell" (fun () ->
    let t = supervisor () in
    let text = "$(touch /bad); `false` * ' \"\n" in
    let r = Lwt_unix.run (run t (H.cancellation ()) [|"echo"; text|]) in
    check (completed r && r.stdout = text ^ "\n") ("argv changed: " ^ describe r); finish t);
  test "bounded simultaneous stdout/stderr" (fun () ->
    let t = supervisor () in
    let r = Lwt_unix.run (run t (H.cancellation ()) [|"flood"|]) in
    check (r.outcome = H.Output_limit && r.output_truncated) "output did not fail closed";
    check (String.length r.stdout <= 4096 && String.length r.stderr <= 4096)
      "unbounded capture";
    check (r.status <> None) "child not reaped"; finish t);
  test "timeout escalates ignored TERM and releases permits" (fun () ->
    let t = supervisor () in
    let r = Lwt_unix.run (run ~limits:{limits with timeout = 0.15} t
      (H.cancellation ()) [|"ignore-term"|]) in
    check (r.outcome = H.Timed_out && r.status = Some (Unix.WSIGNALED Sys.sigkill))
      "timeout did not kill child";
    check (r.elapsed < 1.5) "timeout stuck"; finish t);
  test "owner loop remains responsive during cancellation" (fun () ->
    let t = supervisor () and c = H.cancellation () in
    let child = run t c [|"sleep"; "1"|] in
    let ticks = ref 0 in
    let rec ticker n = if n = 0 then (H.cancel c; return ())
      else Lwt_unix.sleep 0.01 >>= fun () -> incr ticks; ticker (n - 1) in
    let timer = ticker 5 in
    let r = Lwt_unix.run (timer >>= fun () -> child) in
    check (!ticks = 5 && r.outcome = H.Cancelled && r.status <> None)
      "owner blocked or cancellation failed"; finish t);
  test "disconnect cleanup kills and reaps with stopped owner loop" (fun () ->
    let t = supervisor () and c = H.cancellation () in
    let path = Filename.concat (Filename.dirname helper) "disconnect-pid" in
    let child = run t c [|"pid-sleep"; path|] in
    let rec ready attempts =
      if Sys.file_exists path then () else if attempts = 0 then failwith "child not ready"
      else (ignore (Unix.select [] [] [] 0.01); ready (attempts - 1)) in
    ready 100;
    let input = open_in path in
    let pid = int_of_string (input_line input) in close_in input;
    H.cancel_and_cleanup c;
    (* Assert cleanup before ANY further event-loop execution. *)
    finish t;
    let reaped = try ignore (Unix.waitpid [Unix.WNOHANG] pid); false
      with Unix.Unix_error (Unix.ECHILD, _, _) -> true in
    check reaped "disconnected helper left running or unreaped";
    H.cancel_and_cleanup c;
    let r = Lwt_unix.run child in
    check (r.outcome = H.Cancelled && r.status = Some (Unix.WSIGNALED Sys.sigkill))
      "resumed monitor lost cleanup result";
    finish t);
  test "disconnect removes pending admission without an owner-loop tick" (fun () ->
    let t = H.create ~cpu_permits:1 ~max_children:1 ~max_pending:1 in
    let a = H.cancellation () and b = H.cancellation () and c = H.cancellation () in
    let first = run t a [|"sleep"; "10"|] in
    let second = run t b [|"echo"; "never"|] in
    H.cancel_and_cleanup b;
    let third = run t c [|"echo"; "never"|] in
    H.cancel_and_cleanup c; H.cancel_and_cleanup a;
    finish t;
    ignore (Lwt_unix.run (first >>= fun _ -> second >>= fun _ -> third)); finish t);
  test "normal process exit cleans abandoned helpers" (fun () ->
    let executable = Filename.concat (Filename.dirname helper) "exit_guard" in
    let marker = Filename.concat (Filename.dirname helper) "exit-marker" in
    let pid = Unix.create_process executable [|executable; helper; marker|]
      Unix.stdin Unix.stdout Unix.stderr in
    let _, status = Unix.waitpid [] pid in
    check (status = Unix.WEXITED 0) "exit safeguard process failed";
    ignore (Unix.select [] [] [] 0.5);
    check (not (Sys.file_exists marker)) "abandoned helper survived parent exit");
  test "macOS helpers do not inherit unrelated non-cloexec descriptors" (fun () ->
    if Sys.file_exists "/System/Library/CoreServices/SystemVersion.plist" then begin
      let path = Filename.concat (Filename.dirname helper) "private-descriptor" in
      let fd = Unix.openfile path [Unix.O_RDWR; Unix.O_CREAT; Unix.O_TRUNC] 0o600 in
      Unix.clear_close_on_exec fd;
      let t = supervisor () in
      let r = Lwt_unix.run (run t (H.cancellation ()) [|"check-inherited"; path|]) in
      Unix.close fd;
      check (completed r && r.stdout = "closed\n") "unrelated descriptor inherited";
      finish t
    end);
  test "weighted admission and queued cancellation" (fun () ->
    let t = supervisor () and waiting = H.cancellation () in
    let first = run ~weight:2 t (H.cancellation ()) [|"sleep"; "0.12"|] in
    let second = run t waiting [|"echo"; "must not run"|] in
    check (H.usage t = (2, 1)) "weight did not reserve whole budget";
    H.cancel waiting;
    let a, b = Lwt_unix.run (second >>= fun b -> first >>= fun a -> return (a, b)) in
    check (completed a && b.outcome = H.Cancelled && b.status = None)
      "queued cancellation spawned a child"; finish t);
  test "CPU callbacks release permits on exception" (fun () ->
    let t = supervisor () in
    let failed = try ignore (Lwt_unix.run (H.with_cpu_permits t ~weight:2
      (H.cancellation ()) (fun () -> fail (Failure "synthetic")))); false
      with Failure _ -> true in
    check failed "lost callback exception"; finish t);
  test "two children can run concurrently" (fun () ->
    let t = supervisor () in
    let a = run t (H.cancellation ()) [|"sleep"; "0.12"|] in
    let b = run t (H.cancellation ()) [|"sleep"; "0.12"|] in
    check (H.usage t = (2, 2)) "children serialized unexpectedly";
    let a, b = Lwt_unix.run (a >>= fun a -> b >>= fun b -> return (a, b)) in
    check (completed a && completed b) "concurrent children failed"; finish t);
  test "remaining descendants terminated before leader reap" (fun () ->
    let t = supervisor () in
    let marker = Filename.concat (Filename.dirname helper) "descendant-marker" in
    let r = Lwt_unix.run (run t (H.cancellation ()) [|"descendant"; marker|]) in
    check (completed r) "leader failed";
    Lwt_unix.run (Lwt_unix.sleep 0.5);
    check (not (Sys.file_exists marker)) "descendant survived"; finish t);
  test "missing executable fails without leaking budget" (fun () ->
    let t = supervisor () in
    let r = Lwt_unix.run (H.run t ~weight:1 (H.cancellation ()) ~limits
      ~executable:"/unison-synthetic-does-not-exist" ~arguments:[||] ~environment:[||]) in
    check (match r.outcome with H.Failed _ -> true | _ -> false) "spawn failure lost";
    finish t);
  test "valid qualified structured receipt" (fun () ->
    check (match validate "valid" with V.Passed r ->
      r.report.raw_digest = V.Valid && r.candidate = expected | _ -> false) "valid rejected");
  test "missing optional raw digest remains distinct from corruption" (fun () ->
    check (match validate "missing" with V.Passed r -> r.report.raw_digest = V.Missing
      | _ -> false) "missing digest rejected");
  List.iter (fun mode -> test ("reject " ^ mode) (fun () ->
    check (rejected (validate mode)) (mode ^ " passed")))
    ["mismatch"; "error-zero"; "unsupported"; "wrong-hash"; "wrong-build";
     "malformed"; "exit-nonzero"];
  test "policy off does not inspect or execute" (fun () ->
    check (validate ~policy:V.Off ~inspect:(fun _ -> failwith "called")
      ~configured:None "valid" = V.Skipped) "off performed work");
  test "require tool unavailable rejected, warn explicit" (fun () ->
    check (rejected (validate ~configured:None "valid")) "missing tool passed";
    check (match validate ~policy:V.Warn "mismatch" with V.Warning _ -> true
      | _ -> false) "warning policy wrong");
  test "tool pin mismatch rejected before invocation" (fun () ->
    let configured = Some {(tool "valid") with executable_sha256 = hash} in
    check (match validate ~configured "valid" with V.Rejected (_, None) -> true
      | _ -> false) "wrong pin spawned");
  test "post-validation candidate mutation rejected" (fun () ->
    let reads = ref 0 in
    let inspect path = if path = helper then return tool_snapshot
      else (incr reads; return (if !reads = 1 then expected
        else {expected with identity = "candidate-v2"})) in
    check (rejected (validate ~inspect "valid")) "mutation passed");
  test "warn cannot permit mutation after malformed receipt" (fun () ->
    let reads = ref 0 in
    let inspect path = if path = helper then return tool_snapshot
      else (incr reads; return (if !reads = 1 then expected
        else {expected with identity = "candidate-v2"})) in
    check (rejected (validate ~policy:V.Warn ~inspect "malformed"))
      "warn permitted mutation");
  test "warn cannot permit candidate changed before validation" (fun () ->
    let inspect _ = return {expected with identity = "candidate-v2"} in
    check (rejected (validate ~policy:V.Warn ~inspect "valid"))
      "warn permitted pre-validation mutation");
  List.iter (fun (name,expected,inspect,cancel) ->
    test ("warn rejects pre-helper candidate inspection " ^ name) (fun () ->
      let t=supervisor() and cancellation=H.cancellation() in
      if cancel then H.cancel cancellation;
      let executions=ref 0 in
      let execute run=incr executions;run() in
      let result=Lwt_unix.run(V.validate_with_execution ~execute t cancellation
        ~policy:V.Warn ~tool:(Some(tool "valid")) ~inspect
        ~candidate:"/synthetic/candidate.dng" ~expected) in
      check (match result with V.Rejected(_,None) -> true | _ -> false)
        "warn inspection failure was relaxed or spawned a helper";
      check (!executions=0) "candidate inspection failure entered helper execution";
      finish t))
    ["EIO",expected,(fun _ -> fail(Unix.Unix_error(Unix.EIO,"private candidate inspection",""))),false;
     "malformed snapshot",expected,(fun _ -> return {expected with V.sha256="bad"}),false;
     "invalid expected",{expected with V.size=(-1L)},(fun _ -> failwith "invalid expected inspected"),false;
     "cancelled inspection",expected,(fun _ -> fail(Failure "private inspection cancelled")),true];
  test "strict parser rejects extra fields and oversized receipt" (fun () ->
    let r = match validate "valid" with V.Passed r -> r | _ -> failwith "valid failed" in
    let bad text = match V.parse_report text with Error _ -> true | _ -> false in
    check (bad (r.process.stdout ^ "END\n") && bad (String.make 4097 'x') &&
      bad (String.sub r.process.stdout 0 (String.length r.process.stdout - 1)))
      "parser accepted malformed receipt");
  print_endline "All helper/validation tests passed."
