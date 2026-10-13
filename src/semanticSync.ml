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
              match SemanticDelta.inspect ~max_payload extension base_file with
              | Error reason -> Error reason
              | Ok base -> with_file source (fun source_file ->
                match SemanticDelta.inspect ~max_payload extension source_file with
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

(* Resource admission is global and independent of CPU permits. Each local
   transaction may inspect source and basis concurrently. *)
type transaction = { path : Fspath.t; mutable fds : Unix.file_descr list;
  mutable busy : bool; mutable abandoned : bool; mutable owned : bool }
let close_transaction transaction =
  let fds = transaction.fds in
  transaction.fds <- [];
  let first = ref None in
  List.iter (fun fd -> try Unix.close fd with Unix.Unix_error _ as e ->
    if !first = None then first := Some e) fds;
  match !first with None -> () | Some e -> raise e
let cleanup_transaction transaction =
  transaction.abandoned <- true;
  if not transaction.busy then
    (try close_transaction transaction with Unix.Unix_error _ -> ());
  if transaction.owned then begin
    transaction.owned <- false;
    try Fs.unlink transaction.path with Unix.Unix_error (Unix.ENOENT,_,_) -> ()
  end
let cleanup_transaction_noerr transaction =
  try cleanup_transaction transaction with Unix.Unix_error _ -> ()
let transaction_resources = Remote.resourceWithConnCleanup
  cleanup_transaction cleanup_transaction_noerr
let register_transaction path basis_fd output_fd =
  let transaction =
    try {path;fds=[basis_fd;output_fd];busy=false;abandoned=false;owned=true}
    with error -> discard_unregistered_stage path basis_fd output_fd; raise error in
  try transaction_resources.register transaction with error ->
    (* Registration may have installed the record before raising. Empty its
       ownership first so a retained cleanup entry cannot close recycled fds. *)
    let fds = transaction.fds in
    transaction.fds <- [];
    transaction.abandoned <- true;
    List.iter close_fd_noerr fds;
    if transaction.owned then begin
      transaction.owned <- false; unlink_stage_noerr path
    end;
    (try transaction_resources.release_noerr transaction with _ -> ());
    raise error
let retain_source_fd transaction fd =
  let previous = transaction.fds in
  try transaction.fds <- fd :: previous with error ->
    if transaction.fds == previous then close_fd_noerr fd;
    raise error
let with_borrowed transaction f =
  if transaction.abandoned then Lwt.fail (Util.Transient "Local semantic transfer interrupted")
  else begin
    transaction.busy <- true;
    let finish () =
      transaction.busy <- false;
      if transaction.abandoned then
        (try close_transaction transaction with Unix.Unix_error _ -> ()) in
    Lwt.try_bind f
      (fun result -> finish ();
        if transaction.abandoned then Lwt.fail (Util.Transient "Local semantic transfer interrupted")
        else Lwt.return result)
      (fun e -> finish (); Lwt.fail e)
  end

(* Bound producers retain a separate descriptor-relative name owner. The
   legacy transaction's pathname cleanup is disabled for these stages. A
   connection close must await borrowed workers before removing their stage. *)
type publication = { context : StagePublication.t;
  mutable transaction : transaction option; mutable closing : bool;
  mutable closed : bool }
let close_publication publication =
  publication.closing <- true;
  (match publication.transaction with
   | Some transaction -> transaction.abandoned <- true
   | None -> ());
  let busy = match publication.transaction with
    | Some transaction -> transaction.busy | None -> false in
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
let release_transaction_noerr transaction =
  try transaction_resources.release_noerr transaction with _ ->
    (try cleanup_transaction_noerr transaction with _ -> ())
let register_publication context =
  let publication =
    try {context;transaction=None;closing=false;closed=false}
    with error -> StagePublication.close_noerr context; raise error in
  try publications.register publication with error ->
    release_publication_noerr publication; raise error
let register_bound_transaction path basis_fd output_fd =
  let transaction =
    try {path;fds=[basis_fd;output_fd];busy=false;abandoned=false;owned=false}
    with error -> close_fd_noerr basis_fd; close_fd_noerr output_fd; raise error in
  try transaction_resources.register transaction with error ->
    let fds = transaction.fds in
    transaction.fds <- [];
    transaction.abandoned <- true;
    List.iter close_fd_noerr fds;
    release_transaction_noerr transaction;
    raise error
let create_bound_transaction ~basis ~directory ~staging candidate path =
  if not (StagePublication.available ()) then None else
  let context =
    try
      let context = StagePublication.prepare ~working_dir:(Fspath.toString directory)
        ~stage:(Path.toString candidate) ~temporary:(Path.toString staging) in
      (try Some context with error -> StagePublication.close_noerr context; raise error)
    with error when StagePublication.preparation_unavailable error -> None in
  match context with
  | None -> None
  | Some context ->
      let publication = register_publication context in
      try
        if publication.closing then
          raise (Util.Transient "Local semantic publication interrupted");
        match Fs.clone_stage_handles basis path with
        | Fs.Declined_stage_handles Fs.Non_regular_source ->
            raise (Util.Transient "Semantic clone basis is no longer a regular file")
        | Fs.Declined_stage_handles _ ->
            publications.release publication; None
        | Fs.Shared_stage_handles (basis_fd, output_fd, parent) ->
            (* The native owner consumes the actual creation parent and keeps
               its own output witness before any transaction handoff can fail. *)
            (try StagePublication.adopt context ~parent ~stage:output_fd
             with error -> close_fd_noerr basis_fd; close_fd_noerr output_fd; raise error);
            let transaction = register_bound_transaction path basis_fd output_fd in
            (try
               publication.transaction <- Some transaction;
               Some (transaction, publication, basis_fd, output_fd)
             with error -> release_transaction_noerr transaction; raise error)
      with error -> release_publication_noerr publication; raise error
let with_publication_borrowed publication transaction f =
  Lwt.try_bind (fun () -> with_borrowed transaction f)
    (fun result ->
      (match publication with Some owner when owner.closing -> close_publication_noerr owner | _ -> ());
      Lwt.return result)
    (fun error ->
      (match publication with Some owner when owner.closing -> close_publication_noerr owner | _ -> ());
      Lwt.fail error)

let try_local_async_internal ?reservation ?producer ~source ~basis ~directory ~staging () =
  let open Lwt in
  let extensions = SemanticFormats.local_enabled () in
  if extensions = [] then return false else
  let max_payload = List.fold_left (fun n handle -> max n (FormatExtension.payload_limit handle))
    0 extensions in
  let callback_started = ref false in
  SemanticRuntime.with_transaction ?reservation ~max_payload (fun cancellation ->
    Util.convertUnixErrorsToTransient "creating local semantic staging" (fun () ->
      let candidate = Os.tempPath ~fresh:true directory
        (Path.addSuffixToFinalName staging "-semantic-clone") in
      let path = Fspath.concat directory candidate in
      let created = match producer with
        | Some _ ->
            (match create_bound_transaction ~basis ~directory ~staging candidate path with
             | None -> None
             | Some (transaction, publication, basis_fd, output_fd) ->
                 (try Some (transaction, Some publication, basis_fd, output_fd)
                  with error -> release_publication_noerr publication;
                    release_transaction_noerr transaction; raise error))
        | None ->
            match Fs.clone_stage_status basis path with
            | Fs.Declined_stage Fs.Non_regular_source ->
                raise (Util.Transient "Semantic clone basis is no longer a regular file")
            | Fs.Declined_stage _ -> None
            | Fs.Shared_stage (basis_fd, output_fd) ->
                let transaction = register_transaction path basis_fd output_fd in
                (try Some (transaction, None, basis_fd, output_fd)
                 with error -> release_transaction_noerr transaction; raise error) in
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
        catch (fun () ->
          let source_fd = Fs.openfile source [Unix.O_RDONLY;Unix.O_CLOEXEC;Unix.O_NONBLOCK] 0 in
          retain_source_fd transaction source_fd;
          let pool = (SemanticRuntime.get ()).pool in
          let rec select = function
            | [] -> return None
            | extension :: rest ->
          with_publication_borrowed publication transaction (fun () ->
            (* Settle both jobs, including failures, before releasing borrowed
               descriptors. An early failure never closes a sibling's fd. *)
            let settle f = Lwt.try_bind f
              (fun x -> return (Ok x)) (fun e -> return (Error e)) in
            let base = settle (fun () -> SemanticWorkers.inspect pool cancellation ~extension basis_fd)
            and target = settle (fun () -> SemanticWorkers.inspect pool cancellation ~extension source_fd) in
            base >>= fun base -> target >>= fun target ->
            match base,target with
            | Ok (Some base),Ok (Some target) -> return (base.proof,target.proof)
            | Error e,_ | _,Error e -> fail e
            | _ -> fail (Util.Transient "Local semantic inspection cancelled")) >>= fun (base,target) ->
          let plan = match base,target with
            | Ok base,Ok target -> SemanticDelta.plan ~nonce:(String.make 32 '\000') ~base ~target
            | Error reason,_ | _,Error reason -> Error reason in
          match plan with Error _ -> select rest | Ok plan -> return (Some (extension,plan)) in
          select extensions >>= function
          | None ->
            debug (fun () -> Util.msg "Local semantic fallback: no enabled profile proves eligibility\n");
            release (); return false
          | Some (extension,plan) ->
            with_publication_borrowed publication transaction (fun () -> SemanticWorkers.apply_report pool cancellation ~extension plan
              ~basis:basis_fd ~output:output_fd) >>= fun applied ->
            let report = match applied with Some report -> report | None ->
              raise (Util.Transient "Local semantic materialization cancelled") in
            (match publication,producer with
             | Some owner,Some producer ->
                 StagePublication.publish owner.context;
                 callback_started := true;
                 producer output_fd;
                 if transaction.abandoned || owner.closing then
                   raise (Util.Transient "Local semantic publication interrupted");
                 StagePublication.disarm owner.context
             | None,None ->
                 close_transaction transaction;
                 Fs.rename path (Fspath.concat directory staging);
                 transaction.owned <- false
             | _ -> assert false);
            release ();
            debug (fun () -> Util.msg
              "Local semantic workers wrote %d metadata bytes in %d writes from %d payload bytes (%s)\n"
              report.SemanticDelta.logical_bytes_written report.SemanticDelta.write_calls
              (SemanticDelta.payload_size plan) (SemanticDelta.profile plan));
            return true)
          (fun e -> release_noerr ();
            if !callback_started then fail e else match e with
            | SemanticWorkers.Failed reason -> fail (Util.Transient ("Local semantic worker: " ^ reason))
            | Unix.Unix_error _ ->
              Util.convertUnixErrorsToTransient "local semantic transfer" (fun () -> raise e)
            | _ -> fail e)
        with error ->
          (match publication with Some owner -> release_publication_noerr owner | None -> ());
          release_transaction_noerr transaction;
          raise error))

let try_local_async ~source ~basis ~directory ~staging =
  try_local_async_internal ~source ~basis ~directory ~staging ()
let try_local_async_with_producer ~producer ~source ~basis ~directory ~staging =
  try_local_async_internal ~producer ~source ~basis ~directory ~staging ()

let try_local_async_reserved ~reservation ~producer ~source ~basis ~directory ~staging =
  try_local_async_internal ~reservation ?producer ~source ~basis ~directory ~staging ()
