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
    let finish () =
      transaction.busy <- false;
      if transaction.abandoned then
        (try close_transaction transaction with Unix.Unix_error _ -> ()) in
    BorrowedWork.try_bind (fun () -> transaction.busy <- true; f ())
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
  BorrowedWork.try_bind (fun () -> with_borrowed transaction f)
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
        BorrowedWork.catch (fun () ->
          let source_fd = Fs.openfile source [Unix.O_RDONLY;Unix.O_CLOEXEC;Unix.O_NONBLOCK] 0 in
          retain_source_fd transaction source_fd;
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
            return true)))
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

(* Capture a compact base before an archive may refer to these exact bytes.
   A later lookup still requires the agreeing previous-common fingerprint. *)
let capture_common_base_async ~root ~path ~source =
  let open Lwt in
  if not (SemanticMergeCache.enabled ()) then return () else
  let usage = SemanticRuntime.admission_usage () in
  if usage.SemanticAdmission.transactions<>0 || usage.SemanticAdmission.pending<>0 then return () else
  SemanticRuntime.with_transaction ~role:SemanticAdmission.Source ~max_payload:FormatExtension.max_region (fun cancellation ->
    let owned = ref true in
    let fd = Fs.openfile source [Unix.O_RDONLY;Unix.O_CLOEXEC;Unix.O_NONBLOCK] 0 in
    try
    let close () = if !owned then (owned := false; close_fd_noerr fd) in
    BorrowedWork.try_bind (fun () ->
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
      (fun () -> close ();return ())
      (fun error -> close ();fail error)
    with error ->
      if !owned then (owned := false;close_fd_noerr fd);
      raise error)

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
    let owned = ref [] in
    let close () =
      let fds = !owned in owned := [];
      List.iter close_fd_noerr fds in
    let open_fd path flags =
      let fd = Fs.openfile path (Unix.O_CLOEXEC :: Unix.O_NONBLOCK :: flags) 0 in
      (try owned := fd :: !owned with error -> close_fd_noerr fd; raise error);
      fd in
    let same a b =
      a.Unix.LargeFile.st_kind = Unix.S_REG && b.Unix.LargeFile.st_kind = Unix.S_REG &&
      a.st_dev = b.st_dev && a.st_ino = b.st_ino && a.st_size = b.st_size &&
      a.st_mtime = b.st_mtime && a.st_ctime = b.st_ctime in
    BorrowedWork.try_bind (fun () ->
      let runtime = SemanticRuntime.get () in
      BorrowedWork.bind (fun () -> HelperSupervisor.with_cpu_permits
        runtime.supervisor ~weight:1 cancellation (fun () -> return (match cache with
          | None -> None
          | Some (root,path) -> SemanticMergeCache.load ~root ~path ~fingerprint:base_fingerprint)))
        (fun admitted ->
      let cached = match admitted with Some cached -> cached | None -> fail "cache lookup cancelled" in
      let base_fd = match cached with None -> Some (open_fd base [Unix.O_RDONLY]) | Some _ -> None in
      let left_fd = open_fd left [Unix.O_RDONLY] in
      let right_fd = open_fd right [Unix.O_RDONLY] in
      let output_fd = open_fd output [Unix.O_RDWR] in
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
      (fun report -> close (); return report)
      (fun error -> close (); match error with
       | SemanticWorkers.Failed reason -> Lwt.fail (Util.Transient ("DNG scalar merge: " ^ reason))
       | _ -> Lwt.fail error))

let merge_local_async ~base_fingerprint ~base ~left ~right ~output =
  merge_local_async_internal ~cache:None ~base_fingerprint ~base ~left ~right ~output
let merge_local_async_with_cache ~cache ~base_fingerprint ~base ~left ~right ~output =
  merge_local_async_internal ~cache:(Some cache) ~base_fingerprint ~base ~left ~right ~output
