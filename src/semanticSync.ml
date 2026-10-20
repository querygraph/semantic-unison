let is_enabled () = SemanticFormats.local_enabled () <> []
let debug = Trace.debug "semantic"
let close_fd_noerr fd = try Unix.close fd with _ -> ()
let unlink_stage_noerr path = try Fs.unlink path with _ -> ()
let discard_unregistered_stage path basis output =
  close_fd_noerr basis; close_fd_noerr output; unlink_stage_noerr path
let with_file path f =
  let fd = Fs.openfile path [Unix.O_RDONLY;Unix.O_CLOEXEC;Unix.O_NONBLOCK] 0 in
  match SemanticFile.with_fd fd f with
  | result -> Unix.close fd; result
  | exception e -> Unix.close fd; raise e

let try_local ~source ~basis ~directory ~staging =
  let extensions = SemanticFormats.local_enabled () in
  if extensions = [] then false else
  let candidate = Os.tempPath ~fresh:true directory
    (Path.addSuffixToFinalName staging "-semantic-clone") in
  let candidate_path = Fspath.concat directory candidate in
  Util.convertUnixErrorsToTransient "semantic DNG transfer" (fun () ->
    match Fs.clone_stage_status basis candidate_path with
    | Fs.Declined_stage Fs.Non_regular_source ->
        raise (Util.Transient "Semantic clone basis is no longer a regular file")
    | Fs.Declined_stage _ -> false
    | Fs.Shared_stage (basis_fd, output_fd) ->
      (* Guard the allocations that establish the normal ownership closures.
         Their failure occurs before either descriptor has been borrowed. *)
      let close, cleanup, committed =
        try
          let closed = ref false and committed = ref false in
          let close () = if not !closed then begin
            closed := true;
            (try Unix.close basis_fd with Unix.Unix_error _ -> ());
            (try Unix.close output_fd with Unix.Unix_error _ -> ())
          end in
          let cleanup () = close ();
            if not !committed then
              (try Fs.unlink candidate_path with Unix.Unix_error (Unix.ENOENT,_,_) -> ()) in
          (close, cleanup, committed)
        with error ->
          discard_unregistered_stage candidate_path basis_fd output_fd;
          raise error in
      try
        let rec select = function
          | [] -> Error "no enabled profile proves eligibility"
          | handle :: rest ->
            let extension = FormatExtension.implementation handle in
            let max_payload = FormatExtension.payload_limit handle in
            let planned = SemanticFile.with_fd basis_fd (fun base_file ->
              match SemanticDelta.inspect ~max_payload ~span_semantics:(FormatExtension.span_semantics handle) extension base_file with
              | Error reason -> Error reason
              | Ok base -> with_file source (fun source_file ->
                match SemanticDelta.inspect ~max_payload ~span_semantics:(FormatExtension.span_semantics handle) extension source_file with
                | Error reason -> Error reason
                | Ok target -> SemanticDelta.plan ~nonce:(String.make 32 '\000') ~base ~target)) in
            match planned with Error _ -> select rest | Ok _ -> planned in
        let planned = select extensions in
        match planned with
        | Error reason ->
          debug (fun () -> Util.msg "DNG semantic fallback: %s\n" reason);
          cleanup (); false
        | Ok plan ->
          let report = SemanticFile.with_fd basis_fd
            (fun basis -> SemanticDelta.apply_report plan ~basis ~output:output_fd) in
          close ();
          Fs.rename candidate_path (Fspath.concat directory staging);
          committed := true;
          debug (fun () -> Util.msg
            "DNG semantic clone wrote %d metadata bytes in %d writes from %d payload bytes\n"
            report.SemanticDelta.logical_bytes_written report.SemanticDelta.write_calls
            (SemanticDelta.payload_size plan));
          true
      with e -> cleanup ();
        match e with
        | SemanticFile.Invalid reason -> raise (Util.Transient ("DNG semantic verification: " ^ reason))
        | _ -> raise e)

(* Resource admission is global and independent of CPU permits. Prepare every
   descriptor slot before clone/source acquisition; no post-open list handoff. *)
type transaction = {
  path:Fspath.t; pair:NotificationPipe.t; source_owner:NotificationPipe.t;
  on_uncertain:exn -> unit; interrupted_error:exn;
  mutable busy:bool; mutable abandoned:bool; mutable owned:bool;
  mutable publication_pending:bool; mutable retained:bool; mutable closed:bool;
  mutable retention_error:exn; mutable original_error:exn; mutable original_failed:bool;
}
let prepare_transaction path on_uncertain =
  let pair=NotificationPipe.prepare () and source_owner=NotificationPipe.prepare () in
  let transaction={path;pair;source_owner;on_uncertain;
    interrupted_error=Util.Transient "Local semantic transaction interrupted";
    busy=false;abandoned=false;owned=false;publication_pending=false;
    retained=false;closed=false;retention_error=Out_of_memory;original_error=Exit;original_failed=false} in
  NotificationPipe.keep_owner pair (fun () -> ignore(Sys.opaque_identity transaction));
  NotificationPipe.keep_owner source_owner (fun () -> ignore(Sys.opaque_identity transaction));
  transaction
let remember_transaction transaction error =
  if not transaction.original_failed then begin
    transaction.original_error<-error;transaction.original_failed<-true
  end;
  NotificationPipe.remember_failure transaction.pair error;
  NotificationPipe.remember_failure transaction.source_owner error
let retain_transaction transaction error =
  if not transaction.retained then transaction.retention_error<-error;
  transaction.retained<-true;transaction.abandoned<-true;
  (try transaction.on_uncertain (if transaction.original_failed then transaction.original_error else error) with _ -> ());
  try NotificationPipe.retain_unsettled transaction.pair error
  with NotificationPipe.Uncertain _ -> ()
let adopt_transaction transaction basis output ~name_owned =
  NotificationPipe.adopt transaction.pair basis output;
  transaction.owned<-name_owned
let check_transaction transaction =
  if transaction.abandoned || transaction.closed then begin
    retain_transaction transaction transaction.interrupted_error;
    raise transaction.interrupted_error
  end
let transaction_descriptors transaction =
  let basis,output=NotificationPipe.descriptors transaction.pair in
  let source,_=NotificationPipe.descriptors transaction.source_owner in
  (if NotificationPipe.read_held transaction.pair then [basis] else []) @
  (if NotificationPipe.write_held transaction.pair then [output] else []) @
  (if NotificationPipe.read_held transaction.source_owner then [source] else [])
let close_transaction transaction =
  if transaction.retained then
    NotificationPipe.retain_unsettled transaction.pair transaction.retention_error;
  if not transaction.busy && not transaction.closed && not transaction.publication_pending then begin
    (* Attempt every independently owned slot even if one close is uncertain. *)
    (try NotificationPipe.close_all transaction.pair
     with NotificationPipe.Uncertain _ as error -> retain_transaction transaction error);
    (try NotificationPipe.close_all transaction.source_owner
     with NotificationPipe.Uncertain _ as error -> retain_transaction transaction error);
    if transaction.retained then raise transaction.retention_error;
    transaction.closed<-true
  end
let cleanup_transaction transaction =
  transaction.abandoned<-true;
  if not transaction.busy then close_transaction transaction;
  if transaction.owned && transaction.closed &&
     not(transaction.retained || transaction.publication_pending) then begin
    transaction.owned<-false;
    try Fs.unlink transaction.path with Unix.Unix_error (Unix.ENOENT,_,_) -> ()
  end
let cleanup_transaction_noerr transaction =
  try cleanup_transaction transaction with _ -> ()
let transaction_resources = Remote.resourceWithConnCleanup
  cleanup_transaction cleanup_transaction_noerr
let register_transaction transaction =
  try transaction_resources.register transaction with error ->
    remember_transaction transaction error;
    cleanup_transaction transaction;
    (try transaction_resources.release_noerr transaction with _ -> ());
    raise error
let open_source transaction source =
  let fd=Fs.openfile source [Unix.O_RDONLY;Unix.O_CLOEXEC;Unix.O_NONBLOCK] 0 in
  NotificationPipe.adopt_read transaction.source_owner fd;
  check_transaction transaction;fd
let with_borrowed transaction f =
  if transaction.abandoned then Lwt.fail transaction.interrupted_error else begin
    let uncertain = function
      | NotificationPipe.Uncertain _ | SemanticFile.Close_uncertain _
      | DngComponents.Cache_ownership_uncertain _ | DirectoryOwner.Uncertain _
      | StagePublication.Ownership_uncertain _ -> true
      | _ -> false in
    let retain entry=retain_transaction transaction (RetainedOwnership.cause entry) in
    let guard work=RetainedOwnership.guard ~is_uncertain:uncertain ~on_retained:retain work in
    let finish ()=transaction.busy<-false;
      if transaction.abandoned then close_transaction transaction in
    guard (fun () ->
      BorrowedWork.try_bind (fun () -> transaction.busy<-true;guard f)
        (fun result -> finish ();
          if transaction.abandoned then Lwt.fail transaction.interrupted_error else Lwt.return result)
        (fun error -> remember_transaction transaction error;finish ();Lwt.fail error))
  end

(* Descriptor and native name owners remain distinct. Close the raw slots before
   aborting a name; native uncertainty never authorizes local parent cleanup. *)
type publication = { context:StagePublication.owned; scope:retained_publication;
  staging_transaction:transaction;
  parent_handoff:StagePublication.parent_handoff; parent_owner:NotificationPipe.t;
  mutable closing:bool; mutable closed:bool;
  mutable close_failed:bool; mutable close_error:exn }
and retained_publication = {
  mutable held:transaction option;
  mutable publication:publication option;
  mutable native:StagePublication.owned option;
  mutable cause:exn; mutable cause_recorded:bool;
  mutable uncertain:bool; mutable linked:bool;
  pending:bool Lwt.t;
  link:retained_publication option;
  mutable next:retained_publication option;
}
let retained_publication_owners=ref None
let retained_publications () =
  let rec collect acc=function None->List.rev acc | Some scope->collect(scope::acc)scope.next in
  collect [] !retained_publication_owners
let retained_publication_cause scope=scope.cause
let retained_publication_native scope=scope.native
let retained_publication_pair_ownership scope =
  match scope.held with None->None | Some transaction->Some transaction.pair
let retained_publication_source_ownership scope =
  match scope.held with None->None | Some transaction->Some transaction.source_owner
let retained_publication_parent_ownership scope =
  match scope.publication with None->None | Some publication->Some publication.parent_owner
let retained_publication_descriptors scope =
  let known=match scope.held with None->[] | Some transaction->transaction_descriptors transaction in
  match scope.publication with
  | Some publication when NotificationPipe.read_held publication.parent_owner ->
      let parent,_=NotificationPipe.descriptors publication.parent_owner in parent::known
  | _ -> known
let create_publication_scope () =
  let pending=Lwt.wait () in
  let rec scope={held=None;publication=None;native=None;cause=Out_of_memory;cause_recorded=false;
    uncertain=false;linked=false;pending;link=Some scope;next=None} in scope
let record_publication_cause scope error =
  if not scope.cause_recorded then begin scope.cause<-error;scope.cause_recorded<-true end
let mark_scope_uncertain scope error =
  record_publication_cause scope error;scope.uncertain<-true;
  if not scope.linked then begin
    scope.next<- !retained_publication_owners;retained_publication_owners:=scope.link;scope.linked<-true
  end
let owned_call scope work =
  try work () with StagePublication.Ownership_uncertain native as error ->
    scope.native<-native;mark_scope_uncertain scope error;
    (match scope.held with Some transaction->retain_transaction transaction error | None->());
    raise error
let protect_publication_scope scope work =
  BorrowedWork.try_bind work
    (fun value -> if scope.uncertain then scope.pending else Lwt.return value)
    (fun error -> record_publication_cause scope error;
      if scope.uncertain then scope.pending else Lwt.fail error)
let close_publication publication =
  publication.closing<-true;
  let transaction=publication.staging_transaction in
  transaction.abandoned<-true;
  if not transaction.busy && not publication.closed && not publication.scope.uncertain then begin
    publication.closed<-true;transaction.publication_pending<-false;
    (try close_transaction transaction with error ->
      publication.close_failed<-true;publication.close_error<-error;
      record_publication_cause publication.scope error);
    (try
       if publication.scope.cause_recorded then
         NotificationPipe.remember_failure publication.parent_owner publication.scope.cause;
       NotificationPipe.close_all publication.parent_owner
     with NotificationPipe.Uncertain _ as error ->
       retain_transaction transaction error;
       publication.close_failed<-true;publication.close_error<-error);
    if not publication.scope.uncertain then
      (try owned_call publication.scope (fun () -> StagePublication.abort_owned publication.context)
       with error -> publication.close_failed<-true;publication.close_error<-error;
         record_publication_cause publication.scope error);
    if publication.close_failed then raise publication.close_error
  end
let close_publication_noerr publication =
  try close_publication publication with _ -> ()
let publications = Remote.resourceWithConnCleanup close_publication close_publication_noerr
let release_publication_noerr publication =
  try publications.release_noerr publication with _ -> close_publication_noerr publication
let release_transaction_noerr transaction =
  try transaction_resources.release_noerr transaction with _ -> cleanup_transaction_noerr transaction
let register_publication scope context transaction =
  let publication =
    try
      let parent_handoff=StagePublication.prepare_parent_handoff () in
      let parent_owner=NotificationPipe.prepare_read_handoff parent_handoff in
      let publication={context;scope;staging_transaction=transaction;parent_handoff;parent_owner;
        closing=false;closed=false;close_failed=false;close_error=Out_of_memory} in
      NotificationPipe.keep_owner parent_owner (fun () -> ignore(Sys.opaque_identity publication));
      publication
    with error -> record_publication_cause scope error;
      owned_call scope (fun () -> StagePublication.abort_owned context);raise error in
  (try scope.publication<-Some publication with error ->
    record_publication_cause scope error;
    owned_call scope (fun () -> StagePublication.abort_owned context);raise error);
  transaction.publication_pending<-true;
  try publications.register publication with error ->
    record_publication_cause scope error;release_publication_noerr publication;raise error
let create_bound_transaction scope transaction ~basis ~directory ~staging candidate path =
  if not(StagePublication.available ()) then None else
  let context =
    try
      let context=owned_call scope (fun () -> StagePublication.prepare_owned
        ~working_dir:(Fspath.toString directory) ~stage:(Path.toString candidate) ~temporary:(Path.toString staging)) in
      (try Some context with error -> record_publication_cause scope error;
        owned_call scope (fun () -> StagePublication.abort_owned context);raise error)
    with error when StagePublication.preparation_unavailable error -> None in
  match context with
  | None -> None
  | Some context ->
    let publication=register_publication scope context transaction in
    try
      if publication.closing then raise transaction.interrupted_error;
      match Fs.clone_stage_handles basis path with
      | Fs.Declined_stage_handles Fs.Non_regular_source ->
          raise(Util.Transient "Semantic clone basis is no longer a regular file")
      | Fs.Declined_stage_handles _ -> publications.release publication;None
      | Fs.Shared_stage_handles(basis_fd,output_fd,parent) ->
          adopt_transaction transaction basis_fd output_fd ~name_owned:false;
          NotificationPipe.adopt_read publication.parent_owner parent;
          check_transaction transaction;
          let adopt ()=StagePublication.adopt_owned_tracked context publication.parent_handoff ~parent ~stage:output_fd in
          owned_call scope adopt;
          let transaction=register_transaction transaction in
          (try Some(transaction,publication,basis_fd,output_fd) with error ->
            remember_transaction transaction error;record_publication_cause scope error;
            release_publication_noerr publication;release_transaction_noerr transaction;raise error)
    with error -> remember_transaction transaction error;record_publication_cause scope error;
      release_publication_noerr publication;release_transaction_noerr transaction;raise error
let with_publication_borrowed publication transaction f =
  BorrowedWork.try_bind (fun () -> with_borrowed transaction f)
    (fun result ->
      (match publication with Some owner when owner.closing->close_publication_noerr owner | _->());
      Lwt.return result)
    (fun error ->
      (match publication with Some owner when owner.closing->close_publication_noerr owner | _->());
      Lwt.fail error)

let try_local_async_internal ?reservation ?producer ~source ~basis ~directory ~staging () =
  let open Lwt in
  let extensions = SemanticFormats.local_enabled () in
  if extensions = [] then return false else
  let max_payload = List.fold_left (fun n handle -> max n (FormatExtension.payload_limit handle))
    0 extensions in
  let callback_started = ref false in
  SemanticRuntime.with_transaction ?reservation ~max_payload (fun cancellation ->
    let scope=create_publication_scope () in
    protect_publication_scope scope (fun () ->
    Util.convertUnixErrorsToTransient "creating local semantic staging" (fun () ->
      let candidate = Os.tempPath ~fresh:true directory
        (Path.addSuffixToFinalName staging "-semantic-clone") in
      let path = Fspath.concat directory candidate in
      let transaction=prepare_transaction path (mark_scope_uncertain scope) in
      scope.held<-Some transaction;
      let created = match producer with
        | Some _ ->
            (match create_bound_transaction scope transaction ~basis ~directory ~staging candidate path with
             | None -> None
             | Some (transaction, publication, basis_fd, output_fd) ->
                 (try Some (transaction, Some publication, basis_fd, output_fd)
                  with error -> record_publication_cause scope error;release_publication_noerr publication;
                    release_transaction_noerr transaction;raise error))
        | None ->
            match Fs.clone_stage_status basis path with
            | Fs.Declined_stage Fs.Non_regular_source ->
                raise (Util.Transient "Semantic clone basis is no longer a regular file")
            | Fs.Declined_stage _ -> None
            | Fs.Shared_stage (basis_fd, output_fd) ->
                adopt_transaction transaction basis_fd output_fd ~name_owned:true;
                check_transaction transaction;
                let transaction=register_transaction transaction in
                (try Some (transaction, None, basis_fd, output_fd)
                 with error -> remember_transaction transaction error;
                   release_transaction_noerr transaction;raise error) in
      match created with
      | None -> return false
      | Some (transaction, publication, basis_fd, output_fd) ->
        try
        let release () =
          (match publication with Some owner -> publications.release owner | None -> ());
          transaction_resources.release transaction in
        let release_noerr () =
          (match publication with Some owner -> release_publication_noerr owner | None -> ());
          release_transaction_noerr transaction in
        BorrowedWork.catch (fun () ->
          let source_fd=open_source transaction source in
          let pool = (SemanticRuntime.get ()).pool in
          let rec select = function
            | [] -> return None
            | extension :: rest ->
          BorrowedWork.bind (fun () -> with_publication_borrowed publication transaction (fun () ->
            (* Settle both jobs, including failures, before releasing borrowed
               descriptors. An early failure never closes a sibling's fd. *)
            BorrowedWork.bind (fun () -> BorrowedWork.all
              [(fun () -> SemanticWorkers.inspect pool cancellation ~extension basis_fd);
               (fun () -> SemanticWorkers.inspect pool cancellation ~extension source_fd)]) (function
              | [Some base; Some target] -> return (base.proof,target.proof)
              | _ -> fail (Util.Transient "Local semantic inspection cancelled")))) (fun (base,target) ->
          let plan = match base,target with
            | Ok base,Ok target -> SemanticDelta.plan ~nonce:(String.make 32 '\000') ~base ~target
            | Error reason,_ | _,Error reason -> Error reason in
          match plan with Error _ -> select rest | Ok plan -> return (Some (extension,plan))) in
          BorrowedWork.bind (fun () -> select extensions) (function
          | None ->
            debug (fun () -> Util.msg "Local semantic fallback: no enabled profile proves eligibility\n");
            release (); return false
          | Some (extension,plan) ->
            BorrowedWork.bind
              (fun () -> with_publication_borrowed publication transaction (fun () -> SemanticWorkers.apply_report pool cancellation ~extension plan
                ~basis:basis_fd ~output:output_fd)) (fun applied ->
            let report = match applied with Some report -> report | None ->
              raise (Util.Transient "Local semantic materialization cancelled") in
            let publish () = match publication,producer with
             | Some owner,Some producer ->
                 with_publication_borrowed publication transaction (fun () ->
                   owned_call scope (fun () -> StagePublication.publish_owned owner.context);
                   callback_started := true;
                   producer output_fd;
                   if transaction.abandoned || owner.closing then raise transaction.interrupted_error;
                   owned_call scope (fun () -> StagePublication.disarm_owned owner.context);
                   return ())
             | None,None ->
                 close_transaction transaction;
                 Fs.rename path (Fspath.concat directory staging);
                 transaction.owned <- false;return ()
             | _ -> assert false in
            BorrowedWork.bind publish (fun () ->
              release ();
              debug (fun () -> Util.msg
                "Local semantic workers wrote %d metadata bytes in %d writes from %d payload bytes (%s)\n"
                report.SemanticDelta.logical_bytes_written report.SemanticDelta.write_calls
                (SemanticDelta.payload_size plan) (SemanticDelta.profile plan));
              return true))))
          (fun e -> remember_transaction transaction e;record_publication_cause scope e;release_noerr ();
            if !callback_started then fail e else match e with
            | SemanticWorkers.Failed reason -> fail (Util.Transient ("Local semantic worker: " ^ reason))
            | Unix.Unix_error _ ->
              Util.convertUnixErrorsToTransient "local semantic transfer" (fun () -> raise e)
            | _ -> fail e)
        with error ->
          remember_transaction transaction error;record_publication_cause scope error;
          (match publication with Some owner -> release_publication_noerr owner | None -> ());
          release_transaction_noerr transaction;
          raise error)))

let try_local_async ~source ~basis ~directory ~staging =
  try_local_async_internal ~source ~basis ~directory ~staging ()
let try_local_async_with_producer ~producer ~source ~basis ~directory ~staging =
  try_local_async_internal ~producer ~source ~basis ~directory ~staging ()

let try_local_async_reserved ~reservation ~producer ~source ~basis ~directory ~staging =
  try_local_async_internal ~reservation ?producer ~source ~basis ~directory ~staging ()

(* Separate capture/merge owners. Every slot/link/guard exists before open; an
   uncertain borrower keeps all inputs, not just the descriptor that reported. *)
type retained_inputs = {
  slots:NotificationPipe.t array; paths:string array; opened:bool array;
  interrupted_error:exn;
  mutable closed:bool; mutable retained:bool;
  mutable failure:exn; mutable failed:bool;
  mutable unresolved:exn; mutable linked:bool;
  link:retained_inputs option; mutable next:retained_inputs option;
}
let retained_input_owners=ref None
let retained_inputs () =
  let rec collect acc=function None->List.rev acc | Some owner->collect(owner::acc)owner.next in
  collect [] !retained_input_owners
let retained_input_count owner=Array.length owner.slots
let retained_input_slot owner index=owner.slots.(index)
let retained_input_path owner index=owner.paths.(index)
let retained_input_failure owner=if owner.failed then Some owner.failure else None
let retained_input_uncertainty owner=owner.unresolved
let remember_inputs owner error =
  if not owner.failed then begin owner.failure<-error;owner.failed<-true end;
  for index=0 to Array.length owner.slots-1 do
    NotificationPipe.remember_failure owner.slots.(index) error
  done
let retain_inputs owner error =
  if not owner.retained then owner.unresolved<-error;
  owner.retained<-true;
  if not owner.linked then begin
    owner.next<- !retained_input_owners;retained_input_owners:=owner.link;owner.linked<-true
  end;
  try NotificationPipe.retain_unsettled owner.slots.(0) error
  with NotificationPipe.Uncertain _->()
let prepare_inputs count =
  if count<1 || count>4 then invalid_arg "semantic input slot count";
  let slots=Array.init count(fun _->NotificationPipe.prepare ()) in
  let paths=Array.make count "" and opened=Array.make count false in
  let rec owner={slots;paths;opened;interrupted_error=Util.Transient "Semantic input acquisition interrupted";
    closed=false;retained=false;failure=Exit;failed=false;unresolved=Exit;
    linked=false;link=Some owner;next=None} in
  Array.iter(fun slot->NotificationPipe.keep_owner slot(fun()->ignore(Sys.opaque_identity owner)))slots;
  owner
let input_open owner index path flags =
  let slot=owner.slots.(index) in
  if owner.closed || owner.retained || owner.opened.(index) then invalid_arg "semantic input owner state";
  owner.paths.(index)<-Fspath.toString path;owner.opened.(index)<-true;
  let fd=Fs.openfile path (Unix.O_CLOEXEC::Unix.O_NONBLOCK::flags) 0 in
  NotificationPipe.adopt_read slot fd;
  if owner.closed || owner.retained then begin
    retain_inputs owner owner.interrupted_error;raise owner.interrupted_error
  end;
  fd
let close_inputs owner =
  if owner.retained then NotificationPipe.retain_unsettled owner.slots.(0) owner.unresolved;
  if not owner.closed then begin
    for index=0 to Array.length owner.slots-1 do
      try NotificationPipe.close_all owner.slots.(index)
      with NotificationPipe.Uncertain _ as error->retain_inputs owner error
    done;
    if owner.retained then raise owner.unresolved;
    owner.closed<-true
  end
let with_inputs count work =
  let owner=prepare_inputs count in
  let uncertain=function
    | NotificationPipe.Uncertain _ | SemanticFile.Close_uncertain _
    | DngComponents.Cache_ownership_uncertain _ | DirectoryOwner.Uncertain _
    | StagePublication.Ownership_uncertain _->true
    | _->false in
  let retain entry=retain_inputs owner (RetainedOwnership.cause entry) in
  let guard work=RetainedOwnership.guard ~is_uncertain:uncertain ~on_retained:retain work in
  guard(fun()->
    BorrowedWork.try_bind (fun()->guard(fun()->work owner))
      (fun result->close_inputs owner;Lwt.return result)
      (fun error->remember_inputs owner error;close_inputs owner;Lwt.fail error))

(* Capture a compact base before an archive may refer to these exact bytes.
   A later lookup still requires the agreeing previous-common fingerprint. *)
let capture_common_base_async ~root ~path ~source =
  let open Lwt in
  if not (SemanticMergeCache.enabled ()) then return () else
  let usage = SemanticRuntime.admission_usage () in
  if usage.SemanticAdmission.transactions<>0 || usage.SemanticAdmission.pending<>0 then return () else
  SemanticRuntime.with_transaction ~role:SemanticAdmission.Source ~max_payload:FormatExtension.max_region (fun cancellation ->
    with_inputs 1 (fun owner ->
    let fd=input_open owner 0 source [Unix.O_RDONLY] in
      let before = Unix.LargeFile.fstat fd in
      let stable () =
        let matches after = before.Unix.LargeFile.st_kind=Unix.S_REG &&
          after.Unix.LargeFile.st_kind=Unix.S_REG && before.st_dev=after.st_dev &&
          before.st_ino=after.st_ino && before.st_size=after.st_size &&
          before.st_mtime=after.st_mtime && before.st_ctime=after.st_ctime in
        matches (Unix.LargeFile.fstat fd) && matches (Fs.lstat source) in
      let info = Fileinfo.get false source Path.empty in
      if info.Fileinfo.typ<>`FILE || Osx.ressLength info.osX.Osx.ressInfo<>Uutil.Filesize.zero ||
         not (stable ()) then raise (Util.Transient "DNG cache capture requires a stable regular data file");
      let runtime = SemanticRuntime.get () in
      let fingerprint () =
        if HelperSupervisor.is_cancelled cancellation then raise (Util.Transient "DNG base capture cancelled");
        let fingerprint=Os.data_only_fingerprint (Fingerprint.file_descriptor fd) in
        if not (stable ()) then raise (Util.Transient "DNG base changed during fingerprinting");
        return fingerprint in
      BorrowedWork.bind (fun () -> IoAdmission.with_devices runtime.io cancellation
        ~devices:(IoAdmission.devices_of_fds [fd]) (fun () ->
          HelperSupervisor.with_cpu_permits runtime.supervisor ~weight:1 cancellation fingerprint))
        (function
         | Some (Some fingerprint) ->
           let rec inspect = function
             | [] -> return ()
             | name::rest -> match FormatExtension.resolve name with
               | None -> inspect rest
               | Some extension -> BorrowedWork.bind
                 (fun () -> SemanticWorkers.inspect runtime.pool cancellation ~extension fd)
                 (function
                  | Some {SemanticWorkers.proof=Ok proof;_} ->
                    if not (stable ()) then raise (Util.Transient "DNG base changed during capture");
                    let final_info=Fileinfo.get false source Path.empty in
                    if Osx.ressLength final_info.Fileinfo.osX.Osx.ressInfo<>Uutil.Filesize.zero then
                      raise (Util.Transient "DNG base resource fork changed");
                    BorrowedWork.bind (fun () -> HelperSupervisor.with_cpu_permits
                      runtime.supervisor ~weight:1 cancellation (fun () ->
                        SemanticMergeCache.store ~root ~path ~fingerprint proof;return ()))
                      (function Some () -> return () | None ->
                        raise (Util.Transient "DNG base persistence cancelled"))
                  | Some {SemanticWorkers.proof=Error _;_} -> inspect rest
                  | None -> raise (Util.Transient "DNG base capture cancelled")) in
           inspect [DngExtended.profile;DngSemantic.profile]
         | _ -> raise (Util.Transient "DNG base capture admission cancelled")))
)

(* This entry point is deliberately separate from transfer optimization. The
   merge owner provides a private saved base and the previous archive's exact
   fingerprint, not a peer's SDR claim or whichever replica was scanned first. *)
let merge_local_async_internal ~cache ~base_fingerprint ~base ~left ~right ~output =
  let open Lwt in
  let fail reason = raise (Util.Transient ("DNG scalar merge: " ^ reason)) in
  if Os.isPseudoFingerprint base_fingerprint then fail "the saved base has only a pseudo-fingerprint";
  let extensions = List.filter_map FormatExtension.resolve
    [DngExtended.profile; DngSemantic.profile] in
  SemanticRuntime.with_transaction ~max_payload:FormatExtension.max_region (fun cancellation ->
    BorrowedWork.catch (fun () -> with_inputs 4 (fun owner ->
    let open_fd index path flags=input_open owner index path flags in
    let same a b =
      a.Unix.LargeFile.st_kind = Unix.S_REG && b.Unix.LargeFile.st_kind = Unix.S_REG &&
      a.st_dev = b.st_dev && a.st_ino = b.st_ino && a.st_size = b.st_size &&
      a.st_mtime = b.st_mtime && a.st_ctime = b.st_ctime in
      let runtime = SemanticRuntime.get () in
      BorrowedWork.bind (fun () -> HelperSupervisor.with_cpu_permits
        runtime.supervisor ~weight:1 cancellation (fun () -> return (match cache with
          | None -> None
          | Some (root,path) -> SemanticMergeCache.load ~root ~path ~fingerprint:base_fingerprint)))
        (fun admitted ->
      let cached = match admitted with Some cached -> cached | None -> fail "cache lookup cancelled" in
      let base_fd = match cached with
        | None ->
            (try Some (open_fd 0 base [Unix.O_RDONLY]) with
             | Unix.Unix_error (Unix.ENOENT,_,_) ->
                 fail "no saved common base is available; synchronize a common version with compact capture or backupcurrent enabled before merging")
        | Some _ -> None in
      let left_fd = open_fd 1 left [Unix.O_RDONLY] in
      let right_fd = open_fd 2 right [Unix.O_RDONLY] in
      let output_fd = open_fd 3 output [Unix.O_RDWR] in
      let before = Option.map Unix.LargeFile.fstat base_fd in
      let base_stable () = match before,base_fd with
        | Some before,Some fd -> same before (Unix.LargeFile.fstat fd) && same before (Fs.stat base)
        | None,None -> true | _ -> false in
      if not (base_stable ()) then fail "saved base name changed";
      List.iter (fun path ->
        let info = Fileinfo.get true path Path.empty in
        if info.Fileinfo.typ <> `FILE ||
           Osx.ressLength info.Fileinfo.osX.Osx.ressInfo <> Uutil.Filesize.zero then
          fail "regular files without resource forks are required") ((if cached=None then [base] else []) @ [left;right;output]);
      let runtime = SemanticRuntime.get () in
      let verify_base () =
        if HelperSupervisor.is_cancelled cancellation then fail "archive verification cancelled";
        let _, fingerprint = Os.safeFingerprint base Path.empty
          (Fileinfo.get true base Path.empty) None in
        if not (Os.fullfingerprintEqual fingerprint base_fingerprint) then
          fail "saved base does not match the previous sync archive";
        if not (base_stable ()) then fail "saved base changed during archive verification";
        if HelperSupervisor.is_cancelled cancellation then fail "archive verification cancelled";
        return () in
      let pool = runtime.pool in
      let rec select reasons = function
        | [] -> fail ("no compatible fixed-region profile: " ^ String.concat "; " (List.rev reasons))
        | extension :: rest ->
          BorrowedWork.bind (fun () -> BorrowedWork.all
            [(fun () -> match cached,base_fd with
               | Some proof,_ when SemanticDelta.proof_profile proof=FormatExtension.profile extension ->
                   return (Some {SemanticWorkers.proof=Ok proof;stats=Unix.LargeFile.fstat left_fd})
               | Some _,_ -> return (Some {SemanticWorkers.proof=Error "cached profile differs";stats=Unix.LargeFile.fstat left_fd})
               | None,Some fd -> SemanticWorkers.inspect pool cancellation ~extension fd
               | _ -> fail "base unavailable");
             (fun () -> SemanticWorkers.inspect pool cancellation ~extension left_fd);
             (fun () -> SemanticWorkers.inspect pool cancellation ~extension right_fd)]) (function
          | [Some b;Some l;Some r] ->
            (match b.proof,l.proof,r.proof with
             | Ok b,Ok l,Ok r ->
               BorrowedWork.bind (fun () -> SemanticWorkers.reconcile_xmp pool cancellation
                 ~extension ~nonce:(String.make 32 '\000') ~base:b ~left:l ~right:r left_fd) (function
               | None -> fail "reconciliation cancelled"
               | Some merged -> match merged.merge_plan with
                 | Error reason -> select (reason :: reasons) rest
                 | Ok plan ->
                   if not (base_stable ()) then
                     fail "saved base changed before materialization";
                   BorrowedWork.bind (fun () -> SemanticWorkers.apply_report pool cancellation
                     ~extension plan ~basis:left_fd ~output:output_fd) (function
                   | None -> fail "materialization cancelled"
                   | Some report -> return report))
             | Error reason,_,_ | _,Error reason,_ | _,_,Error reason -> select (reason :: reasons) rest)
          | _ -> fail "inspection cancelled") in
      (* Release the base I/O/CPU lease before any worker acquires its own.
         Holding it through inspection would deadlock a one-job filesystem. *)
      BorrowedWork.bind (fun () -> match base_fd with
        | None -> return (Some (Some ()))
        | Some fd -> IoAdmission.with_devices runtime.io cancellation
          ~devices:(IoAdmission.devices_of_fds [fd]) (fun () ->
            HelperSupervisor.with_cpu_permits runtime.supervisor ~weight:1 cancellation verify_base))
        (function Some (Some ()) -> select [] extensions
         | _ -> fail "archive verification admission cancelled")))
      )
      (fun error -> match error with
       | SemanticWorkers.Failed reason -> Lwt.fail (Util.Transient ("DNG scalar merge: " ^ reason))
       | (Unix.Unix_error _ | Sys_error _ | Sys_blocked_io) ->
           (* The shared utility also converts Not_found/End_of_file. Invoke it
              only for OS failures, after descriptor/resource settlement. *)
           (try Util.convertUnixErrorsToTransient "DNG scalar merge" (fun () -> raise error)
            with error -> Lwt.fail error)
       | _ -> Lwt.fail error))

let merge_local_async ~base_fingerprint ~base ~left ~right ~output =
  merge_local_async_internal ~cache:None ~base_fingerprint ~base ~left ~right ~output
let merge_local_async_with_cache ~cache ~base_fingerprint ~base ~left ~right ~output =
  merge_local_async_internal ~cache:(Some cache) ~base_fingerprint ~base ~left ~right ~output
