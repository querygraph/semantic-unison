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
let timeout = Prefs.makeEndpointLocal (Prefs.createInt "adobevalidatetimeout" 300 ~local:true ~category
  "maximum seconds for each Adobe SDK validation"
  "Execution timeout after CPU admission. A timed-out driver is terminated \
   and reaped before require rejects the candidate.")
let policy () = match Prefs.read policy_pref with
  | "off" -> DngValidation.Off | "warn" -> DngValidation.Warn
  | "require" -> DngValidation.Require
  | _ -> raise (Util.Fatal "adobevalidate must be off, warn, or require")
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
      let inspect path = context.inspect path >>= fun snapshot -> return (convert snapshot) in
      DngValidation.validate_with_execution ~execute:context.execute
        context.supervisor context.cancellation ~policy:selected ~tool ~inspect
        ~candidate:context.candidate ~expected:(convert context.expected)
      >>= fun result ->
      Abort.checkAll ();
      match result with
      | DngValidation.Skipped | DngValidation.Passed _ -> return ()
      | DngValidation.Warning (reason,_) ->
          Trace.log (Printf.sprintf "Adobe DNG validation warning for %s: %s\n"
            context.candidate reason);
          return ()
      | DngValidation.Rejected (reason,_) ->
          fail (Util.Transient (Printf.sprintf "Adobe DNG validation rejected %s: %s"
            context.candidate reason)))
  end
