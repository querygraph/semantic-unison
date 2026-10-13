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

let try_local_async ~source ~basis ~directory ~staging =
  let open Lwt in
  let extensions = SemanticFormats.local_enabled () in
  if extensions = [] then return false else
  let max_payload = List.fold_left (fun n handle -> max n (FormatExtension.payload_limit handle))
    0 extensions in
  SemanticRuntime.with_transaction ~max_payload (fun cancellation ->
    Util.convertUnixErrorsToTransient "creating local semantic staging" (fun () ->
      let path = Fspath.concat directory
        (Os.tempPath ~fresh:true directory (Path.addSuffixToFinalName staging "-semantic-clone")) in
      match Fs.clone_stage_status basis path with
      | Fs.Declined_stage Fs.Non_regular_source ->
          raise (Util.Transient "Semantic clone basis is no longer a regular file")
      | Fs.Declined_stage _ -> return false
      | Fs.Shared_stage (basis_fd, output_fd) ->
        let transaction = register_transaction path basis_fd output_fd in
        catch (fun () ->
          let source_fd = Fs.openfile source [Unix.O_RDONLY;Unix.O_CLOEXEC;Unix.O_NONBLOCK] 0 in
          retain_source_fd transaction source_fd;
          let pool = (SemanticRuntime.get ()).pool in
          let rec select = function
            | [] -> return None
            | extension :: rest ->
          with_borrowed transaction (fun () ->
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
            transaction_resources.release transaction; return false
          | Some (extension,plan) ->
            with_borrowed transaction (fun () -> SemanticWorkers.apply_report pool cancellation ~extension plan
              ~basis:basis_fd ~output:output_fd) >>= fun applied ->
            let report = match applied with Some report -> report | None ->
              raise (Util.Transient "Local semantic materialization cancelled") in
            close_transaction transaction;
            Fs.rename path (Fspath.concat directory staging);
            transaction.owned <- false;
            transaction_resources.release transaction;
            debug (fun () -> Util.msg
              "Local semantic workers wrote %d metadata bytes in %d writes from %d payload bytes (%s)\n"
              report.SemanticDelta.logical_bytes_written report.SemanticDelta.write_calls
              (SemanticDelta.payload_size plan) (SemanticDelta.profile plan));
            return true)
          (fun e -> transaction_resources.release_noerr transaction;
            match e with
            | SemanticWorkers.Failed reason -> fail (Util.Transient ("Local semantic worker: " ^ reason))
            | Unix.Unix_error _ ->
              Util.convertUnixErrorsToTransient "local semantic transfer" (fun () -> raise e)
            | _ -> fail e)))
