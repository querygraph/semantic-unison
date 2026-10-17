open Lwt

let transport = Features.register "semantic-delta-v0" ~arcFormatChange:false None
let debug = Trace.debug "semantic"
let close_fd_noerr fd = try Unix.close fd with _ -> ()
let unlink_stage_noerr path = try Fs.unlink path with _ -> ()
let discard_unregistered_stage path basis output =
  close_fd_noerr basis; close_fd_noerr output; unlink_stage_noerr path
let supported connection =
  SemanticFormats.peer_enabled () <> [] && Remote.connectionVersion connection >= 1 &&
  Features.enabled transport

(* Global resource leases are separate from CPU permits. Source reservations
   last through marshaling and queued RPC output; consumers preserve source
   headroom so bidirectional requests can make progress. *)
let max_path = 16384
let request_limit = max_path + SemanticDelta.max_request_size + 1024
let response_limit = SemanticDelta.max_envelope_size + 1024
let args = Umarshal.(prod2 (bounded_string max_path)
  (bounded_string SemanticDelta.max_request_size) id id)
let result = Umarshal.option (Umarshal.bounded_string SemanticDelta.max_envelope_size)

type retained_component_owner = {
  mutable retained_error : exn;
  mutable retained_next : retained_component_owner option;
}
let retained_component_owners = ref None
let component_retained_ownership () =
  let rec collect result = function
    | None -> List.rev result
    | Some node ->
      let result=match node.retained_error with
        | DngComponents.Cache_ownership_uncertain state -> state::result | _ -> result in
      collect result node.retained_next in
  collect [] !retained_component_owners
let hold_component_uncertainty work =
  let pending=Lwt.wait () in
  let node={retained_error=Out_of_memory;retained_next=None} in
  let link=Some node in
  BorrowedWork.catch work (function
    | DngComponents.Cache_ownership_uncertain _ as error ->
      node.retained_error<-error;node.retained_next<- !retained_component_owners;
      retained_component_owners:=link;
      (try Trace.log "Semantic report ownership uncertain; report admission remains held.\n" with _ -> ());
      pending
    | error -> Lwt.fail error)
(* Shared read-source lifetime for reports and remote transfer planning. The
   caller's transaction remains charged if native close ownership is uncertain. *)
let with_owned_source path work =
  hold_component_uncertainty (fun () ->
    let settled=ref false in
    let source=DngComponents.open_component_source(fun () ->
      Fs.openfile path [Unix.O_RDONLY;Unix.O_CLOEXEC;Unix.O_NONBLOCK] 0) in
    let fd=DngComponents.component_source_descriptor source in
    let finish cause =
      settled:=true;
      try DngComponents.settle_component_source source cause;None with error -> Some error in
    BorrowedWork.try_bind (fun () -> work fd)
      (fun result -> match finish None with None -> return result | Some error -> fail error)
      (fun error -> if !settled then fail error else
        match finish (Some error) with Some error -> fail error | None -> assert false))

type held_files = { descriptors : Unix.file_descr list; mutable busy : bool;
                    mutable closing : bool; mutable closed : bool;
                    mutable publication_pending : bool; mutable retained : bool }
let close_files files =
  files.closing <- true;
  if not files.busy && not files.closed && not(files.retained || files.publication_pending) then begin
    files.closed <- true;
    let first = ref None in
    List.iter (fun fd -> try Unix.close fd with Unix.Unix_error _ as e ->
      if !first = None then first := Some e) files.descriptors;
    match !first with None -> () | Some e -> raise e
  end
let close_files_noerr files = try close_files files with Unix.Unix_error _ -> ()
let hold descriptors = {descriptors;busy=false;closing=false;closed=false;publication_pending=false;retained=false}
let close_unborrowed_files files =
  files.closing <- true;
  if not files.closed && not(files.retained || files.publication_pending) then begin
    files.closed <- true;
    List.iter close_fd_noerr files.descriptors
  end
let borrowed files f =
  if files.closing then fail (Util.Transient "Semantic transfer interrupted") else begin
    let finish () = files.busy <- false; if files.closing then close_files_noerr files in
    BorrowedWork.try_bind (fun () -> files.busy <- true; f ())
      (fun result -> finish ();
        if files.closing then fail (Util.Transient "Semantic transfer interrupted")
        else return result)
      (fun e -> finish (); fail e)
  end
let inspected = function
  | Some result -> result.SemanticWorkers.proof
  | None -> raise (Util.Transient "Semantic inspection cancelled")

let make_plan connection (source, request) =
  if not (supported connection) then return None else
    Util.convertUnixErrorsToTransient "planning semantic transfer" (fun () ->
      if Filename.is_relative source || String.contains source '\000' then
        raise (Util.Transient "Invalid semantic source path");
      let nonce,base = match SemanticDelta.decode_request request with
        | Ok x -> x
        | Error reason -> raise (Util.Transient ("Invalid semantic request: " ^ reason)) in
      match SemanticFormats.resolve_peer (SemanticDelta.proof_profile base) with
      | None -> return None
      | Some extension ->
      BorrowedWork.try_bind
        (fun () -> with_owned_source (Fspath.canonize (Some source)) (fun fd ->
          SemanticRuntime.with_cancellation (fun cancellation ->
            SemanticWorkers.inspect (SemanticRuntime.get ()).pool cancellation ~extension fd)))
        (fun result ->
          match inspected result with
          | Error _ -> return None
          | Ok target ->
            match SemanticDelta.plan ~nonce ~base ~target with
            | Error _ -> return None
            | Ok plan -> return (Some (SemanticDelta.encode plan)))
        (function
          | SemanticWorkers.Failed reason -> fail (Util.Transient ("Semantic source: " ^ reason))
          | error -> fail error))

let source_scope connection (_,request) f =
  if not (supported connection) then f () else
  let _,base = match SemanticDelta.decode_request request with
    | Ok result -> result
    | Error reason -> raise (Util.Transient ("Invalid semantic request: " ^ reason)) in
  match SemanticFormats.resolve_peer (SemanticDelta.proof_profile base) with
  | None -> f ()
  | Some extension ->
      SemanticRuntime.with_transaction ~role:SemanticAdmission.Source
        ~max_payload:(FormatExtension.payload_limit extension) (fun _ -> f ())

let response_limit_for_args (_,request) =
  match SemanticDelta.decode_request request with
  | Ok (_,base) ->
      begin match SemanticFormats.resolve_peer (SemanticDelta.proof_profile base) with
      | Some extension -> FormatExtension.payload_limit extension + 65536 + 1024
      | None -> response_limit end
  | Error _ -> response_limit

let request_plan = Remote.registerBoundedServerCmd "semanticPlanV0"
  ~withScope:source_scope ~maxResultForArgs:response_limit_for_args
  ~maxArgs:request_limit ~maxResult:response_limit args result make_plan

type candidate = { basis : Unix.file_descr; output : Unix.file_descr;
  files : held_files; path : Fspath.t; mutable owned : bool }
let close candidate = close_files candidate.files
let cleanup candidate =
  (try close candidate with Unix.Unix_error _ -> ());
  if candidate.owned && not(candidate.files.retained || candidate.files.publication_pending) then begin
    candidate.owned <- false;
    try Fs.unlink candidate.path with Unix.Unix_error (Unix.ENOENT,_,_) -> ()
  end
let cleanup_noerr candidate = try cleanup candidate with Unix.Unix_error _ -> ()
let candidates = Remote.resourceWithConnCleanup cleanup cleanup_noerr
let register_candidate path basis output =
  let candidate =
    try {basis;output;files=hold [basis;output];path;owned=true}
    with error -> discard_unregistered_stage path basis output; raise error in
  try candidates.register candidate with error ->
    (* The registry may retain this object after a failed handoff. Mark and
       close its unborrowed descriptors before trying to unregister it. *)
    close_unborrowed_files candidate.files;
    if candidate.owned && not(candidate.files.retained || candidate.files.publication_pending) then begin
      candidate.owned <- false; unlink_stage_noerr path
    end;
    (try candidates.release_noerr candidate with _ -> ());
    raise error

(* The name owner is independent of the worker descriptor lease. Connection
   cleanup defers its identity-bound unlink until borrowed work has settled. *)
type publication = { context : StagePublication.owned; scope : retained_publication;
  mutable candidate : candidate option; mutable closing : bool;
  mutable closed : bool; mutable close_failed : bool; mutable close_error : exn;
  mutable loose_basis : Unix.file_descr; mutable loose_output : Unix.file_descr;
  mutable loose_parent : Unix.file_descr; mutable loose_fds : bool; mutable loose_parent_held : bool }
and retained_publication = {
  mutable publication : publication option;
  mutable native : StagePublication.owned option;
  mutable cause : exn; mutable cause_recorded : bool;
  mutable uncertain : bool; mutable linked : bool;
  pending : bool Lwt.t;
  link : retained_publication option;
  mutable next : retained_publication option;
}
let retained_publication_owners = ref None
let retained_publications () =
  let rec collect acc = function None -> List.rev acc
    | Some scope -> collect (scope::acc) scope.next in
  collect [] !retained_publication_owners
let retained_publication_cause scope = scope.cause
let retained_publication_native scope = scope.native
let retained_publication_descriptors scope = match scope.publication with
  | Some {candidate=Some candidate;_} -> candidate.files.descriptors
  | Some publication ->
    (if publication.loose_parent_held then [publication.loose_parent] else []) @
    (if publication.loose_fds then [publication.loose_basis;publication.loose_output] else [])
  | None -> []
let create_publication_scope () =
  let pending=Lwt.wait () in
  let rec scope={publication=None;native=None;cause=Out_of_memory;cause_recorded=false;
    uncertain=false;linked=false;pending;link=Some scope;next=None} in scope
let record_publication_cause scope error =
  if not scope.cause_recorded then begin scope.cause<-error;scope.cause_recorded<-true end
let owned_call scope work =
  try work () with StagePublication.Ownership_uncertain native as error ->
    record_publication_cause scope error;
    scope.native<-native;scope.uncertain<-true;
    (match scope.publication with Some {candidate=Some candidate;_}->candidate.files.retained<-true | _->());
    if not scope.linked then begin
      scope.next<- !retained_publication_owners;retained_publication_owners:=scope.link;scope.linked<-true
    end;
    raise error
let protect_publication_scope scope work =
  BorrowedWork.try_bind work
    (fun value -> if scope.uncertain then scope.pending else Lwt.return value)
    (fun error -> record_publication_cause scope error;
      if scope.uncertain then scope.pending else Lwt.fail error)
let close_publication publication =
  publication.closing <- true;
  (match publication.candidate with
   | Some candidate -> candidate.files.closing <- true
   | None -> ());
  let busy = match publication.candidate with
    | Some candidate -> candidate.files.busy | None -> false in
  if not busy && not publication.closed then begin
    publication.closed <- true;
    (try owned_call publication.scope (fun () -> StagePublication.abort_owned publication.context)
     with error -> publication.close_failed<-true;publication.close_error<-error;
       record_publication_cause publication.scope error);
    if not publication.scope.uncertain then begin
      if publication.loose_fds then begin
        publication.loose_fds<-false;
        close_fd_noerr publication.loose_basis;close_fd_noerr publication.loose_output
      end;
      if publication.loose_parent_held then begin
        publication.loose_parent_held<-false;close_fd_noerr publication.loose_parent
      end;
      (match publication.candidate with Some candidate ->
        candidate.files.publication_pending<-false;
        if candidate.files.closing then cleanup candidate
       | None -> ())
    end;
    if publication.close_failed then raise publication.close_error
  end
let close_publication_noerr publication =
  try close_publication publication with _ -> ()
let publications = Remote.resourceWithConnCleanup
  close_publication close_publication_noerr
let release_publication_noerr publication =
  try publications.release_noerr publication with _ -> close_publication_noerr publication
let release_candidate_noerr candidate =
  try candidates.release_noerr candidate with _ ->
    (try cleanup_noerr candidate with _ -> ())
let register_publication scope context =
  let publication =
    try {context;scope;candidate=None;closing=false;closed=false;close_failed=false;close_error=Out_of_memory;
      loose_basis=Unix.stdin;loose_output=Unix.stdin;loose_parent=Unix.stdin;
      loose_fds=false;loose_parent_held=false}
    with error -> record_publication_cause scope error;
      owned_call scope (fun () -> StagePublication.abort_owned context);raise error in
  (try scope.publication<-Some publication with error ->
    record_publication_cause scope error;
    owned_call scope (fun () -> StagePublication.abort_owned context);raise error);
  try publications.register publication with error ->
    record_publication_cause scope error;release_publication_noerr publication;raise error
let register_bound_candidate path basis output =
  let candidate =
    try {basis;output;files=hold [basis;output];path;owned=false}
    with error -> close_fd_noerr basis; close_fd_noerr output; raise error in
  try candidates.register candidate with error ->
    close_unborrowed_files candidate.files;
    release_candidate_noerr candidate;
    raise error
let create_bound_candidate scope ~basis ~directory ~staging stage path =
  if not (StagePublication.available ()) then None else
  let context =
    try
      let context = owned_call scope (fun () -> StagePublication.prepare_owned ~working_dir:(Fspath.toString directory)
        ~stage:(Path.toString stage) ~temporary:(Path.toString staging)) in
      (try Some context with error -> record_publication_cause scope error;
        owned_call scope (fun () -> StagePublication.abort_owned context);raise error)
    with error when StagePublication.preparation_unavailable error -> None in
  match context with
  | None -> None
  | Some context ->
      let publication = register_publication scope context in
      try
        if publication.closing then
          raise (Util.Transient "Remote semantic publication interrupted");
        match Fs.clone_stage_handles basis path with
        | Fs.Declined_stage_handles Fs.Non_regular_source ->
            raise (Util.Transient "Semantic clone basis is no longer a regular file")
        | Fs.Declined_stage_handles _ ->
            publications.release publication; None
        | Fs.Shared_stage_handles (basis_fd, output_fd, parent) ->
            publication.loose_basis<-basis_fd;publication.loose_output<-output_fd;
            publication.loose_parent<-parent;publication.loose_fds<-true;publication.loose_parent_held<-true;
            let adopt ()=StagePublication.adopt_owned context ~parent ~stage:output_fd in
            publication.loose_parent_held<-false;
            owned_call scope adopt;
            (* Adoption owns the name before fallible record/registry allocation.
               The existing constructor settles the raw pair on its own failure. *)
            publication.loose_fds<-false;
            let candidate = register_bound_candidate path basis_fd output_fd in
            (try
               publication.candidate <- Some candidate;
               candidate.files.publication_pending<-true;
               Some (candidate, publication)
             with error ->
               record_publication_cause scope error;
               release_publication_noerr publication;
               if scope.uncertain then begin
                 candidate.files.retained<-true;
                 publication.loose_fds<-true
               end;
               release_candidate_noerr candidate;raise error)
      with error -> record_publication_cause scope error;release_publication_noerr publication;raise error
let borrowed_with_publication publication candidate f =
  BorrowedWork.try_bind (fun () -> borrowed candidate.files f)
    (fun result ->
      (match publication with Some owner when owner.closing -> close_publication_noerr owner | _ -> ());
      Lwt.return result)
    (fun error ->
      (match publication with Some owner when owner.closing -> close_publication_noerr owner | _ -> ());
      Lwt.fail error)

let nonce () =
  (* The only current clone-stage backend is macOS. Use OS randomness for
     transaction correlation; this nonce is not peer authentication. *)
  let b = Bytes.create 32 in
  let owned = ref true in
  let close fd = if !owned then begin owned := false; Unix.close fd end in
  let rec read fd off = if off < 32 then
    let n = try Unix.read fd b off (32-off) with
      Unix.Unix_error (Unix.EINTR,_,_) -> -1 in
    if n = 0 then raise (Util.Transient "Cannot obtain semantic transaction nonce")
    else read fd (if n < 0 then off else off+n) in
  (* Buffers, ownership state and callbacks precede the native open. Clear the
     slot before close, so a failed close cannot close a reused number later. *)
  let fd = Unix.openfile "/dev/urandom" [Unix.O_RDONLY; Unix.O_CLOEXEC] 0 in
  try read fd 0; close fd; Bytes.to_string b
  with error -> (try close fd with _ -> ()); raise error

let try_transfer_internal ?reservation ?producer ~connection ~source ~basis ~directory ~staging ~expected_size () =
  if not (supported connection) then return false else
  let extensions = SemanticFormats.peer_enabled () in
  let max_payload = List.fold_left (fun n handle -> max n (FormatExtension.payload_limit handle))
    0 extensions in
  let callback_started = ref false in
  SemanticRuntime.with_transaction ?reservation ~max_payload (fun cancellation ->
    let scope=create_publication_scope () in
    protect_publication_scope scope (fun () ->
    Util.convertUnixErrorsToTransient "creating semantic staging" (fun () ->
      let stage = Os.tempPath ~fresh:true directory (Path.addSuffixToFinalName staging "-sde") in
      let candidate_path = Fspath.concat directory stage in
      let created = match producer with
        | Some _ ->
            (match create_bound_candidate scope ~basis ~directory ~staging stage candidate_path with
             | None -> None
             | Some (candidate,publication) ->
                 (try Some (candidate,Some publication)
                  with error -> record_publication_cause scope error;release_publication_noerr publication;
                    release_candidate_noerr candidate;raise error))
        | None ->
            match Fs.clone_stage_status basis candidate_path with
            | Fs.Declined_stage Fs.Non_regular_source ->
                raise (Util.Transient "Semantic clone basis is no longer a regular file")
            | Fs.Declined_stage _ -> None
            | Fs.Shared_stage (basis,output) ->
                let candidate = register_candidate candidate_path basis output in
                (try Some (candidate,None)
                 with error -> release_candidate_noerr candidate; raise error) in
      match created with
      | None -> return false
      | Some (candidate,publication) ->
        try
        let basis = candidate.basis and output = candidate.output in
        let release () =
          (match publication with Some owner -> publications.release owner | None -> ());
          candidates.release candidate in
        let release_noerr () =
          (match publication with Some owner -> release_publication_noerr owner | None -> ());
          release_candidate_noerr candidate in
        BorrowedWork.catch (fun () ->
          let rec select = function
            | [] -> return None
            | extension :: rest ->
          BorrowedWork.bind
            (fun () -> borrowed_with_publication publication candidate (fun () -> SemanticWorkers.inspect
              (SemanticRuntime.get ()).pool cancellation ~extension basis)) (fun result ->
          let base = match result with
            | Some result when result.SemanticWorkers.stats.Unix.LargeFile.st_size <> expected_size ->
                Error "target length changed"
            | _ -> inspected result in
          match base with Error _ -> select rest | Ok base -> return (Some (extension,base))) in
          BorrowedWork.bind (fun () -> select extensions) (function
          | None ->
            debug (fun () -> Util.msg "Remote semantic fallback: no negotiated profile proves eligibility\n");
            release (); return false
          | Some (extension,base) ->
            let nonce = nonce () in
            let request = SemanticDelta.encode_request ~nonce base in
            BorrowedWork.bind
              (fun () -> request_plan connection (Fspath.toString source,request)) (function
            | None ->
              debug (fun () -> Util.msg "Remote semantic fallback: source proof differs\n");
              release (); return false
            | Some response ->
              let plan = match SemanticDelta.decode ~max_payload:(FormatExtension.payload_limit extension) response with
                | Ok plan when SemanticDelta.binds_request ~nonce ~base plan -> plan
                | Ok _ -> raise (Util.Transient "Semantic response does not match receiver request")
                | Error reason -> raise (Util.Transient ("Invalid semantic response: " ^ reason)) in
              BorrowedWork.bind
                (fun () -> borrowed_with_publication publication candidate (fun () -> SemanticWorkers.apply_report
                  (SemanticRuntime.get ()).pool cancellation ~extension plan ~basis ~output)) (fun applied ->
              let applied = match applied with Some report -> report | None ->
                raise (Util.Transient "Semantic materialization cancelled") in
              (match publication,producer with
               | Some owner,Some producer ->
                   owned_call scope (fun () -> StagePublication.publish_owned owner.context);
                   callback_started := true;
                   producer output;
                   if candidate.files.closing || owner.closing then
                     raise (Util.Transient "Semantic publication interrupted");
                   owned_call scope (fun () -> StagePublication.disarm_owned owner.context)
               | None,None ->
                   close candidate;
                   Fs.rename candidate.path (Fspath.concat directory staging);
                   candidate.owned <- false
               | _ -> assert false);
              release ();
              debug (fun () -> Util.msg "Remote semantic clone wrote %d logical metadata bytes in %d write calls (%d payload bytes; %d-byte comparison windows; %s)\n"
                applied.SemanticDelta.logical_bytes_written applied.write_calls
                (SemanticDelta.payload_size plan) applied.comparison_window (SemanticDelta.profile plan));
              return true))))
          (fun e -> record_publication_cause scope e;release_noerr ();
            if !callback_started then fail e else match e with
            | SemanticWorkers.Failed reason -> fail (Util.Transient ("Semantic worker: " ^ reason))
            | SemanticFile.Invalid reason -> fail (Util.Transient ("Semantic verification: " ^ reason))
            | Unix.Unix_error _ ->
              Util.convertUnixErrorsToTransient "semantic transfer" (fun () -> raise e)
            | _ -> fail e)
        with error ->
          record_publication_cause scope error;
          (match publication with Some owner -> release_publication_noerr owner | None -> ());
          release_candidate_noerr candidate;
          raise error)))

let try_transfer ~connection ~source ~basis ~directory ~staging ~expected_size =
  try_transfer_internal ~connection ~source ~basis ~directory ~staging ~expected_size ()
let try_transfer_with_producer ~producer ~connection ~source ~basis ~directory ~staging ~expected_size =
  try_transfer_internal ~producer ~connection ~source ~basis ~directory ~staging ~expected_size ()

(* Advisory current-file observations use their own negotiated command. They
   carry no transfer/commit authority, and never download the complete file. *)
let inspection_transport = Features.register "semantic-inspect-v0" ~arcFormatChange:false None
let meaning_transport = Features.register "semantic-inspect-v1" ~arcFormatChange:false None
let component_transport = Features.register "semantic-components-v0" ~arcFormatChange:false None
let component_details = Prefs.createBool "semanticcomponents" false ~local:true
  ~send_value:(fun _ -> false) ~category:(`Advanced `General)
  "show experimental local DNG component hashes in details"
  "On explicit semantic details requests, additionally hash DNG components. \
   This reads each complete file and changes no transfer or conflict decision. \
   Remote inspection requires its separate capability and an enabled DNG profile."
let component_details_enabled () = Prefs.read component_details
type inspection = {
  observation : SemanticReport.observation;
  local_snapshot : (Fspath.t * Unix.LargeFile.stats) option;
}
let inspection_supported connection =
  Remote.connectionVersion connection >= 1 && Features.enabled inspection_transport
let meaning_supported connection = inspection_supported connection && Features.enabled meaning_transport
let report_failure profile reason =
  {observation=SemanticReport.Unavailable (profile,SemanticReport.reason reason);local_snapshot=None}
let same_report_stats a b =
  a.Unix.LargeFile.st_dev=b.Unix.LargeFile.st_dev && a.st_ino=b.st_ino &&
  a.st_kind=b.st_kind && a.st_size=b.st_size && a.st_mtime=b.st_mtime && a.st_ctime=b.st_ctime
let capture_report profile f = BorrowedWork.catch f (function
  | SemanticWorkers.Failed why | Util.Transient why -> return (report_failure profile why)
  | Unix.Unix_error (error,operation,_) ->
      return (report_failure profile (operation ^ ": " ^ Unix.error_message error))
  | error -> fail error)
type component_inspection = {
  component_observation : (SemanticReport.component_observation, string) result;
  component_snapshot : (Fspath.t * Unix.LargeFile.stats) option;
}
let component_schema="dng-physical-partition/0;component-projection/0;no-decoders"
(* Reserve the existing 8*payload+256KiB estimate for the bounded component
   model as well as its small wire summary; this is not an RSS ceiling. *)
let component_envelope_payload=FormatExtension.max_region
let component_failure why = {component_observation=Error (SemanticReport.reason why);
                            component_snapshot=None}
let capture_component f = BorrowedWork.catch f (function
  | SemanticWorkers.Failed why | Util.Transient why -> return (component_failure why)
  | Unix.Unix_error (error,operation,_) ->
      return (component_failure (operation ^ ": " ^ Unix.error_message error))
  | error -> fail error)
let inspect_components ?worker cancellation path =
  capture_component (fun () ->
    let settled=ref false in
    let source=DngComponents.open_component_source(fun () ->
      Fs.openfile path [Unix.O_RDONLY;Unix.O_CLOEXEC;Unix.O_NONBLOCK] 0) in
    let fd=DngComponents.component_source_descriptor source in
    let finish cause =
      settled:=true;
      try DngComponents.settle_component_source source cause;None with error -> Some error in
    BorrowedWork.try_bind (fun () ->
      let stats=Unix.LargeFile.fstat fd in
      let decoders=match DngComponents.freeze_decoders [] with
        | Ok value -> value | Error why -> raise(Util.Transient why) in
      let pool=(SemanticRuntime.get()).pool in
      match worker with
      | None -> SemanticWorkers.components pool cancellation ~decoders ~max_read_bytes:stats.st_size fd
      | Some inspect -> inspect ~pool ~cancellation ~decoders ~max_read_bytes:stats.st_size fd)
      (fun result ->
        let observed=match result with
          | None -> component_failure "Component inspection cancelled"
          | Some value when not(same_report_stats value.SemanticWorkers.stats (Fs.stat path)) ->
            component_failure "File changed or was replaced during component inspection"
          | Some value ->
            let component_observation=match value.SemanticWorkers.components with
              | Error why -> Error(SemanticReport.reason why)
              | Ok summary -> Ok {SemanticReport.schema=component_schema;
                full_sha256=summary.full_sha256;layout_sha256=summary.layout_sha256;
                projections=summary.projections} in
            {component_observation;component_snapshot=Some(path,value.stats)} in
        match finish None with None -> return observed | Some error -> fail error)
      (fun error -> if !settled then fail error else
        match finish (Some error) with Some error -> fail error | None -> assert false))
let inspect_file ?(meaning=false) cancellation extension path =
  let profile = FormatExtension.profile extension in
  capture_report profile (fun () -> with_owned_source path (fun fd ->
    let pool = (SemanticRuntime.get ()).pool in
    let inspect () =
      if meaning then SemanticWorkers.observe pool cancellation ~extension fd else
      BorrowedWork.bind (fun () -> SemanticWorkers.inspect pool cancellation ~extension fd)
        (fun result -> return (Option.map (fun inspection -> {SemanticWorkers.inspection;meaning=None}) result)) in
    BorrowedWork.bind inspect (fun result ->
      let observed = match result with
      | None -> report_failure profile "Semantic inspection cancelled"
      | Some result when not (same_report_stats result.SemanticWorkers.inspection.stats (Fs.stat path)) ->
          report_failure profile "File changed or was replaced during semantic inspection"
      | Some result ->
        let observation = match result.SemanticWorkers.inspection.proof with
          | Ok proof -> SemanticReport.from_proof ?meaning:result.SemanticWorkers.meaning proof
          | Error why -> SemanticReport.Unsupported (profile,SemanticReport.reason why) in
        {observation;local_snapshot=Some (path,result.SemanticWorkers.inspection.stats)} in
      return observed)))
let inspection_args = Umarshal.(prod3 (bounded_string max_path)
  (bounded_string 128) (bounded_string 32) id id)
let inspection_result = Umarshal.bounded_string SemanticReport.max_size
let component_profile_enabled () = List.exists (fun handle ->
  List.mem (FormatExtension.profile handle) [DngSemantic.profile;DngExtended.profile;DngLayout.profile])
  (SemanticFormats.peer_enabled ())
let components_supported connection = Remote.connectionVersion connection >= 1 &&
  Features.enabled component_transport
let valid_component_request (path,schema,nonce) =
  schema=component_schema && String.length nonce=32 &&
  not (Filename.is_relative path) && not (String.contains path '\000')
(* Retain inside the resource lease: propagating an exception out of it would
   retire credits despite unresolved native descriptor ownership. Allocate the
   held promise/node/link before inspection can acquire a cache descriptor. *)
let component_scope connection request f =
  if valid_component_request request && components_supported connection && component_profile_enabled () then
    (* Fixed bounded model/summary, not editable payloads; keep the source envelope
       through encoding and queued RPC output without nested admission. *)
    SemanticRuntime.with_transaction ~role:SemanticAdmission.Source
      ~max_payload:component_envelope_payload (fun _ -> hold_component_uncertainty f)
  else f ()
let inspect_components_source connection ((path,schema,nonce) as request) =
  if not (valid_component_request request) then fail (Util.Transient "Invalid component inspection request")
  else
    let finish observation=return (SemanticReport.encode_components ~nonce ~schema observation) in
    if not (components_supported connection && component_profile_enabled ()) then
      finish (Error "Component inspection is not enabled or negotiated")
    else BorrowedWork.bind (fun () -> SemanticRuntime.with_cancellation (fun cancellation ->
      inspect_components cancellation (Fspath.canonize (Some path))))
      (fun result -> finish result.component_observation)
let inspect_components_peer = Remote.registerBoundedServerCmd "semanticComponentsV0"
  ~withScope:component_scope ~maxArgs:(max_path+128+32+1024)
  ~maxResult:(SemanticReport.max_component_size+1024) inspection_args
  (Umarshal.bounded_string SemanticReport.max_component_size) inspect_components_source
let observe_components_using local_worker ~root ~path =
  match fst root with
  | Common.Local -> capture_component (fun () ->
      SemanticRuntime.with_transaction ~role:SemanticAdmission.Source ~max_payload:component_envelope_payload
        (fun cancellation -> hold_component_uncertainty (fun () ->
          inspect_components ?worker:local_worker cancellation path)))
  | Common.Remote _ ->
      if not (component_profile_enabled ()) then
        return (component_failure "Component DNG profile is not enabled or negotiated")
      else
        let connection=Remote.connectionOfRoot root in
        if not (components_supported connection) then
          return (component_failure "Remote component inspection is not negotiated")
        else capture_component (fun () ->
          let nonce=nonce () in
          BorrowedWork.bind (fun () -> inspect_components_peer connection
            (Fspath.toString path,component_schema,nonce)) (fun encoded ->
            match SemanticReport.decode_components ~nonce ~schema:component_schema encoded with
            | Error why -> fail (Util.Transient ("Invalid component inspection reply: " ^ why))
            | Ok component_observation -> return {component_observation;component_snapshot=None}))
let observe_components ~root ~path = observe_components_using None ~root ~path
let observe_components_with_worker ~local_worker ~root ~path =
  observe_components_using (Some local_worker) ~root ~path
let inspect_source ~meaning connection (path,profile,nonce) =
  if String.length nonce<>32 || profile="" || String.contains profile '\000' ||
     Filename.is_relative path || String.contains path '\000' then
    fail (Util.Transient "Invalid semantic inspection request")
  else
    let finish observation = return ((if meaning then SemanticReport.encode_observation else SemanticReport.encode) ~nonce observation) in
    if not ((if meaning then meaning_supported else inspection_supported) connection) then
      finish (SemanticReport.Unavailable (profile,"Semantic inspection was not negotiated"))
    else match SemanticFormats.resolve_peer profile with
    | None -> finish (SemanticReport.Unsupported (profile,"Profile is not enabled or negotiated"))
    | Some extension ->
        BorrowedWork.bind (fun () -> SemanticRuntime.with_cancellation (fun cancellation ->
          inspect_file ~meaning cancellation extension (Fspath.canonize (Some path))))
          (fun result -> finish result.observation)
let inspection_scope connection (_,profile,_) f =
  if not (inspection_supported connection) then f () else
  match SemanticFormats.resolve_peer profile with
  | None -> f ()
  | Some extension -> SemanticRuntime.with_transaction ~role:SemanticAdmission.Source
      ~max_payload:(FormatExtension.payload_limit extension) (fun _ -> f ())
let inspect_peer = Remote.registerBoundedServerCmd "semanticInspectV0"
  ~withScope:inspection_scope ~maxArgs:(max_path + 128 + 32 + 1024)
  ~maxResult:(SemanticReport.max_size + 1024) inspection_args inspection_result (inspect_source ~meaning:false)
let inspect_meaning_peer = Remote.registerBoundedServerCmd "semanticInspectV1"
  ~withScope:inspection_scope ~maxArgs:(max_path + 128 + 32 + 1024)
  ~maxResult:(SemanticReport.max_observation_size + 1024) inspection_args
  (Umarshal.bounded_string SemanticReport.max_observation_size) (inspect_source ~meaning:true)
let observe ~root ~path ~extension =
  let profile=FormatExtension.profile extension in
  match fst root with
  | Common.Local ->
      SemanticRuntime.with_transaction ~role:SemanticAdmission.Source
        ~max_payload:(FormatExtension.payload_limit extension)
        (fun cancellation -> inspect_file ~meaning:true cancellation extension path)
  | Common.Remote _ ->
      let connection=Remote.connectionOfRoot root in
      if not (inspection_supported connection) then
        return (report_failure profile "Peer does not support negotiated semantic inspection")
      else capture_report profile (fun () ->
        let nonce=nonce () in
        let request,decode = if meaning_supported connection then inspect_meaning_peer,SemanticReport.decode_observation
          else inspect_peer,SemanticReport.decode in
        BorrowedWork.bind (fun () -> request connection (Fspath.toString path,profile,nonce)) (fun encoded ->
        match decode ~nonce ~profile ~max_payload:(FormatExtension.payload_limit extension) encoded with
        | Error why -> fail (Util.Transient ("Invalid semantic inspection reply: " ^ why))
        | Ok observation -> return {observation;local_snapshot=None}))

let try_transfer_reserved ~reservation ~producer ~connection ~source ~basis ~directory ~staging ~expected_size =
  try_transfer_internal ~reservation ?producer ~connection ~source ~basis ~directory ~staging ~expected_size ()
