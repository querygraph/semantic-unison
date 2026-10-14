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

let execute ~executable ~argv0 ~arguments =
  let supervisor, cpu_budget = SemanticRuntime.helper_supervisor () in
  let weight = Prefs.read threads and seconds = Prefs.read timeout and mib = Prefs.read output in
  if weight <= 0 || weight > cpu_budget then
    raise (Util.Fatal "externalhelperthreads must fit the shared CPU budget");
  if seconds <= 0 then raise (Util.Fatal "externalhelpertimeout must be positive");
  if mib <= 0 || mib > max_int / 1048576 then
    raise (Util.Fatal "externalhelperoutput must be a positive representable MiB limit");
  let limits = {HelperSupervisor.timeout=float_of_int seconds;terminate_grace=2.;
    stdout_bytes=mib*1048576;stderr_bytes=mib*1048576} in
  let environment = Unix.environment () in
  SemanticRuntime.with_cancellation (fun cancellation ->
    BorrowedWork.bind (fun () -> Lwt_unix.yield ()) (fun () ->
    Abort.checkAll ();
    BorrowedWork.bind (fun () -> HelperSupervisor.run ~argv0 supervisor
      ~weight cancellation ~limits ~executable ~arguments ~environment) (fun result ->
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
  if Sys.win32 then External.runExternalProgram command
  else execute ~executable:"/bin/sh" ~argv0:"/bin/sh" ~arguments:[|"-c";command|]

let runExternalProgramArgs command argv =
  if Sys.win32 then External.runExternalProgramArgs command argv
  else if Array.length argv = 0 then invalid_arg "SupervisedExternal: empty argv"
  else
    let executable = try External.resolve_program command with Not_found ->
      raise (Util.Transient ("External helper not found in PATH: " ^ command)) in
    execute ~executable ~argv0:argv.(0) ~arguments:(Array.sub argv 1 (Array.length argv - 1))
