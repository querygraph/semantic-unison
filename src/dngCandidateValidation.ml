open Lwt
let category = `Advanced `General
let policy_pref = Prefs.createString "adobevalidate" "off" ~local:true ~category
  "validate received DNG files (off, warn, require)"
  "Run a qualified Adobe SDK validation driver on each received DNG before \
   committing it, selected by filename claim or bounded TIFF content recognition. \
   Require blocks failed or unavailable validation; warn explicitly permits it \
   with a warning. Independent of semantic transfer eligibility and selection."
let validator = Prefs.makeEndpointLocal (Prefs.createString "adobevalidator" "" ~local:true ~category
  "absolute Adobe SDK validation driver path"
  "Absolute path to the qualified structured Adobe SDK validation driver. \
   The stock dng_validate command alone does not implement this protocol.")
let tool_hash = Prefs.makeEndpointLocal (Prefs.createString "adobevalidatorhash" "" ~local:true ~category
  "SHA-256 pin for the Adobe validation driver"
  "Lowercase full executable SHA-256 for the qualified validation driver.")
let build_id = Prefs.makeEndpointLocal (Prefs.createString "adobevalidatorbuild" "" ~local:true ~category
  "qualified Adobe validation driver build identifier"
  "Expected exact build identifier in the driver's structured receipt.")
let tool_threads = Prefs.makeEndpointLocal (Prefs.createInt "adobevalidatorthreads" 1 ~local:true ~category
  "CPU threads reserved for each Adobe SDK driver"
  "Thread count passed to the qualified SDK driver and reserved from the \
   shared CPU budget. It must describe actual driver parallelism.")
let workspace = Prefs.makeEndpointLocal (Prefs.createInt "adobevalidatorworkspace" 0 ~local:true ~category
  "estimated native workspace MiB per Adobe validation"
  "Optional conservative per-invocation native workspace estimate, admitted \
   before receiving staging/validation. Zero preserves legacy accounting. \
   This reserves credits, not SDK allocations or process RSS. Changes to a \
   resource-bearing backend declaration require restarting Unison.")
let timeout = Prefs.makeEndpointLocal (Prefs.createInt "adobevalidatetimeout" 300 ~local:true ~category
  "maximum seconds for each Adobe SDK validation"
  "Execution timeout after CPU admission. A timed-out driver is terminated \
   and reaped before require rejects the candidate.")
let policy () = match Prefs.read policy_pref with
  | "off" -> DngValidation.Off | "warn" -> DngValidation.Warn
  | "require" -> DngValidation.Require
  | _ -> raise (Util.Fatal "adobevalidate must be off, warn, or require")
let resources () =
  if policy () = DngValidation.Off then BackendResources.none else
  let lanes = Prefs.read tool_threads and mib = Prefs.read workspace in
  if lanes < 1 || lanes > 128 then
    raise (Util.Fatal "adobevalidatorthreads must be between one and 128");
  if mib < 0 || mib > max_int / 1048576 then
    raise (Util.Fatal "adobevalidatorworkspace must be nonnegative and fit accounting");
  if lanes = 1 && mib = 0 then BackendResources.none else
  BackendResources.make ~backend:"org.firstpair.adobe-validator/1" ~cpu_lanes:lanes
    ~covered_bytes:0 ~uncovered_estimate:(mib * 1048576) ~descriptor_credits:0
    ~coverage:BackendResources.Accounting_only
let feature = Features.register "dng-validation-v1" ~arcFormatChange:false
  (Some (fun _ enabled ->
    if policy () <> DngValidation.Off && not enabled then
      Some "Requested Adobe validation requires dng-validation-v1 support on both replicas"
    else None))
let recognition = FormatRecognition.trusted ~suffixes:[".dng"] (module DngRecognition)
let convert (snapshot:CandidateValidator.snapshot) : DngValidation.snapshot =
  {sha256=snapshot.sha256;size=snapshot.size;identity=snapshot.identity}
let select () =
  let selected = policy () in
  if selected = DngValidation.Off then None else begin
    (* Receiver preference installation does not repeat feature validation.
       Recheck at selection as well as during ordinary client negotiation. *)
    if not (Features.enabled feature) then
      raise (Util.Fatal "Requested Adobe validation requires dng-validation-v1 support on both replicas");
    let process_limits = HelperLimiter.selected () in
    let weight = Prefs.read tool_threads and seconds = Prefs.read timeout in
    let executable = Prefs.read validator and executable_sha256 = Prefs.read tool_hash
    and build_id = Prefs.read build_id in
    let tool = if executable = "" then None else Some {
      DngValidation.executable;executable_sha256;build_id;
      arguments=[||];environment=[|"LANG=C";"LC_ALL=C";"PATH=/usr/bin:/bin"|];
      cpu_weight=weight;
      limits={HelperSupervisor.timeout=float_of_int seconds;terminate_grace=2.;
              stdout_bytes=16384;stderr_bytes=262144} } in
    Some (fun (context:CandidateValidator.context) ->
      Abort.checkAll ();
      if weight < 1 || weight > context.cpu_budget then
        raise (Util.Fatal "adobevalidatorthreads must be between one and the CPU budget");
      if seconds <= 0 then raise (Util.Fatal "adobevalidatetimeout must be positive");
      let inspect path = BorrowedWork.bind (fun () -> context.inspect path)
        (fun snapshot -> return (convert snapshot)) in
      let inspect_limiter path = BorrowedWork.bind (fun () -> context.inspect path)
        (fun snapshot -> return (snapshot.CandidateValidator.sha256,snapshot.size,snapshot.identity)) in
      let check_cancel () =
        Abort.checkAll ();
        if HelperSupervisor.is_cancelled context.cancellation then
          raise (Util.Transient "Helper limiter validation cancelled") in
      (* Capture only while the child is retained; print after the supervisor
         has settled, when owner logging may safely run the event loop. *)
      let group_observation = ref None in
      let observe_group = if Trace.enabled "validation-group" then
        Some (fun count -> group_observation := Some count) else None in
      let execute run = BorrowedWork.bind (fun () -> context.execute run) (fun child ->
        Trace.debug "validation-group" (fun () ->
          let count = match !group_observation with
            | None -> "unobserved" | Some None -> "unknown"
            | Some (Some count) -> string_of_int count in
          let pid = match child.HelperSupervisor.child_pid with
            | None -> "none" | Some pid -> string_of_int pid in
          Util.msg "Retained group v0 pid=%s candidate-sha256=%s other-members=%s\n"
            pid context.expected.sha256 count);
        return child) in
      BorrowedWork.bind (fun () -> HelperLimiter.with_verified process_limits
        ~inspect:inspect_limiter ~check_cancel (fun process_limits ->
          DngValidation.validate_with_execution ?process_limits ?observe_group ~execute
            context.supervisor context.cancellation ~policy:selected ~tool ~inspect
            ~candidate:context.candidate ~expected:(convert context.expected))) (fun result ->
      Abort.checkAll ();
      match result with
      | DngValidation.Skipped | DngValidation.Passed _ -> return ()
      | DngValidation.Warning (reason,_) ->
          (* A worker completion can reach this callback synchronously. Let
             its notification pump rearm before the warning printer, which
             may run the owner loop to forward a remote warning or await UI
             acknowledgement. Logging alone is invisible in some UIs. *)
          BorrowedWork.bind (fun () -> Lwt_unix.yield ()) (fun () ->
            let check_cancel () =
              Abort.checkAll ();
              if HelperSupervisor.is_cancelled context.cancellation then
                raise (Util.Transient "DNG validation cancelled") in
            check_cancel ();
            Util.warn (Printf.sprintf "Adobe DNG validation warning for %s: %s"
              context.candidate reason);
            check_cancel ();
            return ())
      | DngValidation.Rejected (reason,_) ->
          fail (Util.Transient (Printf.sprintf "Adobe DNG validation rejected %s: %s"
            context.candidate reason))))
  end
