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

type held_files = { descriptors : Unix.file_descr list; mutable busy : bool;
                    mutable closing : bool; mutable closed : bool }
let close_files files =
  files.closing <- true;
  if not files.busy && not files.closed then begin
    files.closed <- true;
    let first = ref None in
    List.iter (fun fd -> try Unix.close fd with Unix.Unix_error _ as e ->
      if !first = None then first := Some e) files.descriptors;
    match !first with None -> () | Some e -> raise e
  end
let close_files_noerr files = try close_files files with Unix.Unix_error _ -> ()
let held_files = Remote.resourceWithConnCleanup close_files close_files_noerr
let hold descriptors = {descriptors;busy=false;closing=false;closed=false}
let close_unborrowed_files files =
  files.closing <- true;
  if not files.closed then begin
    files.closed <- true;
    List.iter close_fd_noerr files.descriptors
  end
let register_held_fd fd =
  let files = try hold [fd] with error -> close_fd_noerr fd; raise error in
  try held_files.register files with error ->
    close_unborrowed_files files;
    (try held_files.release_noerr files with _ -> ());
    raise error
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
      let fd = Fs.openfile (Fspath.canonize (Some source))
        [Unix.O_RDONLY; Unix.O_CLOEXEC; Unix.O_NONBLOCK] 0 in
      let files = register_held_fd fd in
      BorrowedWork.try_bind
        (fun () -> SemanticRuntime.with_cancellation (fun cancellation ->
          borrowed files (fun () -> SemanticWorkers.inspect
            (SemanticRuntime.get ()).pool cancellation ~extension fd)))
        (fun result ->
          held_files.release files;
          match inspected result with
          | Error _ -> return None
          | Ok target ->
            match SemanticDelta.plan ~nonce ~base ~target with
            | Error _ -> return None
            | Ok plan -> return (Some (SemanticDelta.encode plan)))
        (fun e -> held_files.release_noerr files;
          match e with
          | SemanticWorkers.Failed reason -> fail (Util.Transient ("Semantic source: " ^ reason))
          | _ -> fail e))

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
  if candidate.owned then begin
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
    if candidate.owned then begin
      candidate.owned <- false; unlink_stage_noerr path
    end;
    (try candidates.release_noerr candidate with _ -> ());
    raise error

(* The name owner is independent of the worker descriptor lease. Connection
   cleanup defers its identity-bound unlink until borrowed work has settled. *)
type publication = { context : StagePublication.t;
  mutable candidate : candidate option; mutable closing : bool;
  mutable closed : bool }
let close_publication publication =
  publication.closing <- true;
  (match publication.candidate with
   | Some candidate -> candidate.files.closing <- true
   | None -> ());
  let busy = match publication.candidate with
    | Some candidate -> candidate.files.busy | None -> false in
  if not busy && not publication.closed then begin
    publication.closed <- true;
    StagePublication.abort_and_close publication.context
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
let register_publication context =
  let publication =
    try {context;candidate=None;closing=false;closed=false}
    with error -> StagePublication.close_noerr context; raise error in
  try publications.register publication with error ->
    release_publication_noerr publication; raise error
let register_bound_candidate path basis output =
  let candidate =
    try {basis;output;files=hold [basis;output];path;owned=false}
    with error -> close_fd_noerr basis; close_fd_noerr output; raise error in
  try candidates.register candidate with error ->
    close_unborrowed_files candidate.files;
    release_candidate_noerr candidate;
    raise error
let create_bound_candidate ~basis ~directory ~staging stage path =
  if not (StagePublication.available ()) then None else
  let context =
    try
      let context = StagePublication.prepare ~working_dir:(Fspath.toString directory)
        ~stage:(Path.toString stage) ~temporary:(Path.toString staging) in
      (try Some context with error -> StagePublication.close_noerr context; raise error)
    with error when StagePublication.preparation_unavailable error -> None in
  match context with
  | None -> None
  | Some context ->
      let publication = register_publication context in
      try
        if publication.closing then
          raise (Util.Transient "Semantic publication interrupted");
        match Fs.clone_stage_handles basis path with
        | Fs.Declined_stage_handles Fs.Non_regular_source ->
            raise (Util.Transient "Semantic clone basis is no longer a regular file")
        | Fs.Declined_stage_handles _ ->
            publications.release publication; None
        | Fs.Shared_stage_handles (basis,output,parent) ->
            (try StagePublication.adopt context ~parent ~stage:output
             with error -> close_fd_noerr basis; close_fd_noerr output; raise error);
            let candidate = register_bound_candidate path basis output in
            (try
               publication.candidate <- Some candidate;
               Some (candidate,publication)
             with error -> release_candidate_noerr candidate; raise error)
      with error -> release_publication_noerr publication; raise error
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
    Util.convertUnixErrorsToTransient "creating semantic staging" (fun () ->
      let stage = Os.tempPath ~fresh:true directory (Path.addSuffixToFinalName staging "-sde") in
      let candidate_path = Fspath.concat directory stage in
      let created = match producer with
        | Some _ ->
            (match create_bound_candidate ~basis ~directory ~staging stage candidate_path with
             | None -> None
             | Some (candidate,publication) ->
                 (try Some (candidate,Some publication)
                  with error -> release_publication_noerr publication;
                    release_candidate_noerr candidate; raise error))
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
                   StagePublication.publish owner.context;
                   callback_started := true;
                   producer output;
                   if candidate.files.closing || owner.closing then
                     raise (Util.Transient "Semantic publication interrupted");
                   StagePublication.disarm owner.context
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
          (fun e -> release_noerr ();
            if !callback_started then fail e else match e with
            | SemanticWorkers.Failed reason -> fail (Util.Transient ("Semantic worker: " ^ reason))
            | SemanticFile.Invalid reason -> fail (Util.Transient ("Semantic verification: " ^ reason))
            | Unix.Unix_error _ ->
              Util.convertUnixErrorsToTransient "semantic transfer" (fun () -> raise e)
            | _ -> fail e)
        with error ->
          (match publication with Some owner -> release_publication_noerr owner | None -> ());
          release_candidate_noerr candidate;
          raise error))

let try_transfer ~connection ~source ~basis ~directory ~staging ~expected_size =
  try_transfer_internal ~connection ~source ~basis ~directory ~staging ~expected_size ()
let try_transfer_with_producer ~producer ~connection ~source ~basis ~directory ~staging ~expected_size =
  try_transfer_internal ~producer ~connection ~source ~basis ~directory ~staging ~expected_size ()

(* Advisory current-file observations use their own negotiated command. They
   carry no transfer/commit authority, and never download the complete file. *)
let inspection_transport = Features.register "semantic-inspect-v0" ~arcFormatChange:false None
let meaning_transport = Features.register "semantic-inspect-v1" ~arcFormatChange:false None
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
let inspect_file ?(meaning=false) cancellation extension path =
  let profile = FormatExtension.profile extension in
  capture_report profile (fun () ->
    let fd = Fs.openfile path [Unix.O_RDONLY;Unix.O_CLOEXEC;Unix.O_NONBLOCK] 0 in
    let files = register_held_fd fd in
    BorrowedWork.try_bind (fun () -> borrowed files (fun () ->
      let pool = (SemanticRuntime.get ()).pool in
      if meaning then SemanticWorkers.observe pool cancellation ~extension fd else begin
      BorrowedWork.bind (fun () -> SemanticWorkers.inspect pool cancellation ~extension fd)
        (fun result -> return (Option.map (fun inspection -> {SemanticWorkers.inspection;meaning=None}) result)) end))
      (fun result ->
        let observed = try match result with
        | None -> report_failure profile "Semantic inspection cancelled"
        | Some result when not (same_report_stats result.SemanticWorkers.inspection.stats (Fs.stat path)) ->
            report_failure profile "File changed or was replaced during semantic inspection"
        | Some result ->
          let observation = match result.SemanticWorkers.inspection.proof with
            | Ok proof -> SemanticReport.from_proof ?meaning:result.SemanticWorkers.meaning proof
            | Error why -> SemanticReport.Unsupported (profile,SemanticReport.reason why) in
          {observation;local_snapshot=Some (path,result.SemanticWorkers.inspection.stats)}
        with error -> held_files.release_noerr files; raise error in
        held_files.release files; return observed)
      (fun error -> held_files.release_noerr files; fail error))
let inspection_args = Umarshal.(prod3 (bounded_string max_path)
  (bounded_string 128) (bounded_string 32) id id)
let inspection_result = Umarshal.bounded_string SemanticReport.max_size
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
