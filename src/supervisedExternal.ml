open Lwt
let category = `Advanced `General
let threads = Prefs.makeEndpointLocal (Prefs.createInt "externalhelperthreads" 1
  ~local:true ~category "CPU threads reserved per copy/merge/diff helper"
  "Reserve the complete thread/process CPU weight of a configured external \
   command from the shared semantic/SDK budget. This declaration does not \
   constrain arbitrary programs' own thread creation. Applies on POSIX.")
let timeout = Prefs.makeEndpointLocal (Prefs.createInt "externalhelpertimeout" 3600
  ~local:true ~category "maximum seconds for external copy/merge/diff helpers"
  "Execution deadline after CPU admission. Increase for intentionally long \
   foreground commands. Timed-out groups are terminated and reaped before \
   staging or merge cleanup. Applies on POSIX; not a queue-wait deadline.")
let output = Prefs.makeEndpointLocal (Prefs.createInt "externalhelperoutput" 4
  ~local:true ~category "maximum captured MiB per helper output stream"
  "Bound stdout and stderr separately. Exceeding either limit terminates \
   and reaps the helper group and rejects the operation. This is not a \
   whole-process or child RSS/descriptor limit. Applies on POSIX.")

let format_result status stdout stderr =
  let stdout = Util.trimWhitespace stdout and stderr = Util.trimWhitespace stderr in
  (if stdout = "" || stderr = "" then stdout ^ stderr
   else stdout ^ "\n\nError Output:" ^ stderr) ^
  (if status = Unix.WEXITED 0 then "" else "\n\n" ^ Util.process_status_to_string status)

let inspect_limiter cancellation path =
  let owned = ref true in
  let close fd = if !owned then begin owned := false; Unix.close fd end in
  let close_noerr fd = try close fd with Unix.Unix_error _ -> () in
  let fd = Unix.openfile path [Unix.O_RDONLY;Unix.O_NONBLOCK;Unix.O_CLOEXEC] 0 in
  try BorrowedWork.try_bind (fun () -> SemanticWorkers.digest
    (SemanticRuntime.get ()).pool cancellation fd)
    (fun result -> close fd; match result with
     | None -> fail (Util.Transient "Helper limiter hashing cancelled")
     | Some result ->
       let st = result.SemanticWorkers.stats in
       return (SemanticHash.hex result.digest,st.Unix.LargeFile.st_size,
         Printf.sprintf "%d:%d:%Ld:%.17g:%.17g:%d:%d" st.st_dev st.st_ino
           st.st_size st.st_mtime st.st_ctime st.st_perm st.st_nlink))
    (fun error -> close_noerr fd; fail error)
  with error -> close_noerr fd; raise error

(* Owner diagnostics only, emitted after helper settlement. No command arguments
   or captured output are logged, and a historical PID is never an owned handle. *)
let trace_process ~weight ~group (process:HelperSupervisor.result) =
  Trace.debug "external-process" (fun () ->
    let pid=match process.child_pid with None->"none" | Some n->string_of_int n in
    let status=match process.status with None->"none"
      | Some(Unix.WEXITED n)->"exit:"^string_of_int n
      | Some(Unix.WSIGNALED n)->"signal:"^string_of_int n
      | Some(Unix.WSTOPPED n)->"stopped:"^string_of_int n in
    let outcome=match process.outcome with
      | HelperSupervisor.Completed->"completed" | HelperSupervisor.Cancelled->"cancelled"
      | HelperSupervisor.Timed_out->"timed-out" | HelperSupervisor.Output_limit->"output-limit"
      | HelperSupervisor.Failed _->"failed" in
    let members=match group with None->"unobserved" | Some None->"unknown"
      | Some(Some n)->string_of_int n in
    Util.msg "External result v0 pid=%s status=%s outcome=%s cpu-weight=%d other-members=%s capture-truncated=%b\n"
      pid status outcome weight members process.output_truncated)

let execute ~executable ~argv0 ~arguments =
  let process_limits = HelperLimiter.selected () in
  let supervisor, cpu_budget = SemanticRuntime.helper_supervisor () in
  let weight = Prefs.read threads and seconds = Prefs.read timeout and mib = Prefs.read output in
  if weight <= 0 || weight > cpu_budget then
    raise (Util.Fatal "externalhelperthreads must fit the shared CPU budget");
  if seconds <= 0 then raise (Util.Fatal "externalhelpertimeout must be positive");
  if mib <= 0 || mib > max_int / 1048576 then
    raise (Util.Fatal "externalhelperoutput must be a positive representable MiB limit");
  let limits = {HelperSupervisor.timeout=float_of_int seconds;terminate_grace=2.;
    stdout_bytes=mib*1048576;stderr_bytes=mib*1048576} in
  let observation=ref None in
  let observe_group=if Trace.enabled "external-process" then
    Some(fun count -> observation:=Some count) else None in
  let environment = Unix.environment () in
  (* Registered cleanup at process exit reports through observe_teardown and
     may also resume this continuation on cancellation: trace exactly once. *)
  let traced = ref false in
  let trace result =
    if not !traced then begin traced := true; trace_process ~weight ~group:!observation result end in
  SemanticRuntime.with_cancellation (fun cancellation ->
    BorrowedWork.bind (fun () -> Lwt_unix.yield ()) (fun () ->
    Abort.checkAll ();
    let check_cancel () =
      Abort.checkAll ();
      if HelperSupervisor.is_cancelled cancellation then
        raise (Util.Transient "External helper limiter cancelled") in
    BorrowedWork.bind (fun () -> HelperLimiter.with_verified process_limits
      ~inspect:(inspect_limiter cancellation) ~check_cancel (fun process_limits ->
        HelperSupervisor.run ~argv0 ?process_limits ?observe_group ~observe_teardown:trace supervisor
          ~weight cancellation ~limits ~executable ~arguments ~environment)) (fun result ->
    trace result;
    Abort.checkAll ();
    if HelperSupervisor.is_cancelled cancellation then
      fail (Util.Transient "External helper cancelled")
    else match result.HelperSupervisor.outcome, result.status with
    | HelperSupervisor.Completed, Some (Unix.WSIGNALED _ as status) ->
        fail (Util.Transient ("External helper " ^ Util.process_status_to_string status ^ ": " ^ executable))
    | HelperSupervisor.Completed, Some status when not result.output_truncated ->
        return (status, format_result status result.stdout result.stderr)
    | outcome, _ ->
        let reason = match outcome with
          | HelperSupervisor.Cancelled -> "cancelled"
          | HelperSupervisor.Timed_out -> "timed out"
          | HelperSupervisor.Output_limit -> "exceeded captured output limit"
          | HelperSupervisor.Failed reason -> "failed: " ^ reason
          | HelperSupervisor.Completed -> "returned no complete process status" in
        fail (Util.Transient ("External helper " ^ reason ^ ": " ^ executable)))))

let runExternalProgram command =
  if Sys.win32 then (ignore (HelperLimiter.selected ()); External.runExternalProgram command)
  else execute ~executable:"/bin/sh" ~argv0:"/bin/sh" ~arguments:[|"-c";command|]

let runExternalProgramArgs command argv =
  if Sys.win32 then (ignore (HelperLimiter.selected ()); External.runExternalProgramArgs command argv)
  else if Array.length argv = 0 then invalid_arg "SupervisedExternal: empty argv"
  else
    let executable = try External.resolve_program command with Not_found ->
      raise (Util.Transient ("External helper not found in PATH: " ^ command)) in
    execute ~executable ~argv0:argv.(0) ~arguments:(Array.sub argv 1 (Array.length argv - 1))
