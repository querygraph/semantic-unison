let transport = Features.register "target-binding-v0" ~arcFormatChange:false None
let producer_transport = Features.register "target-binding-producer-v0" ~arcFormatChange:false None
let supported () = Features.enabled transport
let producer_supported () = supported () && Features.enabled producer_transport

type phase = Preparing | Ready | Producing | Finalized | Committing | Closed
type completion = Guarded_producer | Legacy_backend

type t = {
  slot : int;
  connection : Remote.connection option;
  session : bool Atomic.t;
  logical_root : Fspath.t;
  local_path : Path.local;
  working_dir : Fspath.t;
  candidate : Path.local;
  target : Path.local;
  normalize : bool;
  follow : bool;
  case_mode : Case.mode;
  check_apple_double : bool;
  require_producer : bool;
  mutable token : string;
  mutable context : FinalPublication.t option;
  mutable phase : phase;
  mutable closing_requested : bool;
  mutable handed_off : bool;
  mutable recover_settlement : (unit -> unit) option;
  mutable callback_pending : bool;
  mutable actual_fingerprint : Os.fullfingerprint option;
  reservation : SemanticAdmission.reservation option;
}

(* The endpoint's cooperative Lwt controller owns this registry. A fixed array
   makes revocation/removal allocation-free, including close-error paths. A
   borrowed slot stays occupied until its callback and helpers have settled. *)
let slots : t option array = Array.make 128 None
let current_session = ref (Atomic.make true)

let fail message = raise (Util.Transient ("Target publication binding: " ^ message))

let same_connection left right = match left, right with
  | None, None -> true
  | Some left, Some right -> left == right
  | _ -> false

let same_path left right = Path.toString left = Path.toString right
let same_root left right = Fspath.compare left right = 0

let remove t =
  match slots.(t.slot) with
  | Some present when present == t -> slots.(t.slot) <- None
  | _ -> ()

let retire_reservation t = match t.reservation with
  | None -> () | Some reservation -> SemanticAdmission.retire reservation

let close t =
  if t.phase <> Closed then begin
    t.phase <- Closed;
    t.closing_requested <- true;
    t.recover_settlement <- None;
    t.callback_pending <- false;
    (* Unregister first. Even a native cleanup exception cannot strand a slot;
       FinalPublication closes all its own descriptors before reporting it. *)
    remove t;
    try
      (match t.context with
       | None -> ()
       | Some context ->
           if t.handed_off then FinalPublication.release context
           else FinalPublication.abort_and_close context);
      retire_reservation t
    with error -> (try retire_reservation t with _ -> ()); raise error
  end

let close_noerr t = try close t with _ -> ()

let busy t = t.phase = Producing || t.phase = Committing

let recover_settlement t = match t.recover_settlement with
  | None -> ()
  | Some recover -> (try recover () with _ -> ())

let handoff_failure t =
  if t.callback_pending && busy t then begin
    t.closing_requested <- true;
    recover_settlement t
  end else close_noerr t

let invalidate_session () =
  Atomic.set !current_session false;
  Array.iter (function
    | None -> ()
    | Some t ->
        t.closing_requested <- true;
        recover_settlement t;
        match t.phase with
        | Producing | Committing | Preparing -> ()
        | Ready | Finalized | Closed -> close_noerr t) slots

let () = Remote.at_conn_close invalidate_session

let session () =
  if not (Atomic.get !current_session) then
    current_session := Atomic.make true;
  !current_session

let closing t =
  t.closing_requested || t.handed_off || t.phase = Closed ||
  not (Atomic.get t.session)

let check_open t =
  if closing t || not (busy t) then fail "ticket is closing or no longer borrowed"

let context t = match t.context with
  | Some context -> context
  | None -> fail "native preparation did not complete"

let native t = check_open t; context t
let published t = match t.context with
  | None -> false
  | Some context -> FinalPublication.published context

let requires_producer t = t.require_producer
let finalized t = match t.context with
  | None -> false
  | Some context -> FinalPublication.producer_finalized context
let fingerprint t = t.actual_fingerprint
let reservation t = t.reservation

let record_fingerprint t fingerprint =
  check_open t;
  if not t.require_producer || t.phase <> Producing then
    fail "fingerprint receipt requires a strict producer borrow";
  if not (finalized t) then fail "producer witness has not been frozen";
  if Os.isPseudoFingerprint fingerprint then fail "actual fingerprint receipt cannot be pseudo";
  (match t.actual_fingerprint with
   | Some _ -> fail "actual fingerprint receipt was already recorded"
   | None -> ());
  FinalPublication.check_candidate (context t);
  check_open t;
  (* Allocate the receipt before the second fence, then publish it only when
     the same frozen object remains current. A failed fence stores no receipt. *)
  let receipt = Some fingerprint in
  FinalPublication.check_candidate (context t);
  check_open t;
  t.actual_fingerprint <- receipt

let normalize_target normalize path =
  if not normalize then path else
  match Path.deconstructRev path with
  | None -> fail "cannot normalize an empty target"
  | Some (name, parent) -> Path.child parent (Name.normalize name)

let check_policy t =
  if Path.followLink t.local_path <> t.follow then
    fail "follow-link policy changed after target setup";
  if (Case.ops ())#mode <> t.case_mode then
    fail "filename normalization policy changed after target setup";
  if Prefs.read Osx.rsrc <> t.check_apple_double then
    fail "resource-fork policy changed after target setup"

let recheck_resolution t =
  check_open t;
  check_policy t;
  let working_dir, target = Fspath.findWorkingDir t.logical_root t.local_path in
  let target = normalize_target t.normalize target in
  FinalPublication.recheck_resolution (context t)
    ~working_dir:(Fspath.toString working_dir) ~target:(Path.toString target);
  check_open t

let close_fd_noerr fd = try Unix.close fd with _ -> ()

let nonce () =
  (* Allocate both buffers and all read/close closures before owning the fd. *)
  let bytes = Bytes.create 32 in
  let hex = Bytes.create 64 in
  let owns_fd = ref true in
  let rec read fd position =
    if position < Bytes.length bytes then begin
      let count =
        try Unix.read fd bytes position (Bytes.length bytes - position)
        with Unix.Unix_error (Unix.EINTR, _, _) -> -1 in
      if count = 0 then fail "cannot obtain a random ticket";
      read fd (if count < 0 then position else position + count)
    end in
  let fd = Unix.openfile "/dev/urandom" [Unix.O_RDONLY; Unix.O_CLOEXEC] 0 in
  (try read fd 0; owns_fd := false; Unix.close fd
   with error -> if !owns_fd then close_fd_noerr fd; raise error);
  let digits = "0123456789abcdef" in
  for index = 0 to 31 do
    let byte = Char.code (Bytes.get bytes index) in
    Bytes.set hex (index * 2) digits.[byte lsr 4];
    Bytes.set hex (index * 2 + 1) digits.[byte land 15]
  done;
  Bytes.unsafe_to_string hex

let valid_token token =
  let rec loop index =
    index = 64 ||
    (let c = token.[index] in
     ((c >= '0' && c <= '9') || (c >= 'a' && c <= 'f')) && loop (index + 1)) in
  String.length token = 64 && loop 0

let find token =
  let rec loop index =
    if index = Array.length slots then None else
    match slots.(index) with
    | Some t when t.token = token -> Some t
    | _ -> loop (index + 1) in
  loop 0

let reserve_slot () =
  let rec loop index =
    if index = Array.length slots then fail "128 prepared or borrowed targets are already active";
    (match slots.(index) with Some t -> recover_settlement t | None -> ());
    match slots.(index) with None -> index | Some _ -> loop (index + 1) in
  loop 0

let rec unique_nonce () =
  let token = nonce () in
  match find token with None -> token | Some _ -> unique_nonce ()

exception Preparation_unavailable

let prepare_internal ~on_ready ?reservation ?connection ?(require_producer=false) ~logical_root ~local_path ~working_dir ~candidate
    ~target ~normalize ~check_apple_double () =
  (match reservation with
   | Some reservation when not (SemanticAdmission.is_held reservation) ->
       fail "preparation requires an admitted resource owner"
   | Some reservation when SemanticAdmission.reservation_role reservation <> SemanticAdmission.Consumer ||
       (SemanticAdmission.reservation_cost reservation).SemanticAdmission.descriptors < 24 ||
       (SemanticAdmission.reservation_cost reservation).SemanticAdmission.payload_bytes < 1048576 ->
       fail "preparation requires a complete consumer publication envelope"
   | _ -> ());
  if not (FinalPublication.available ()) then None else
  match Fileinfo.getType true logical_root Path.empty with
  | `FILE -> None  (* Supported ordinary file-root synchronization stays legacy. *)
  | `DIRECTORY ->
      let slot = reserve_slot () in
      let t = { slot; connection; session = session (); logical_root; local_path;
                working_dir; candidate; target; normalize;
                follow = Path.followLink local_path; case_mode = (Case.ops ())#mode;
                check_apple_double; require_producer; token = ""; context = None;
                phase = Preparing; closing_requested = false; handed_off = false;
                recover_settlement = None; callback_pending = false;
                actual_fingerprint = None; reservation } in
      slots.(slot) <- Some t;
      begin try
        t.token <- unique_nonce ();
        check_policy t;
        if closing t then fail "session closed during preparation";
        let native_context =
          try FinalPublication.prepare
            ~logical_root:(Fspath.toString logical_root)
            ~working_dir:(Fspath.toString working_dir)
            ~candidate:(Path.toString candidate) ~target:(Path.toString target)
            ~check_apple_double
          with error ->
            if FinalPublication.preparation_unavailable error then
              raise Preparation_unavailable
            else raise error in
        (* Guard the first ML allocation handing the native owner to the
           registry. Its custom finalizer is close-only as a last resort. *)
        (try t.context <- Some native_context
         with error -> FinalPublication.close_noerr native_context; raise error);
        if closing t then fail "session closed during native preparation";
        check_policy t;
        (* Check that setup's selected workdir/name really agree with the saved
           selection and Copy-only normalization before exposing a token. *)
        let fresh_working, fresh_target = Fspath.findWorkingDir logical_root local_path in
        FinalPublication.recheck_resolution native_context
          ~working_dir:(Fspath.toString fresh_working)
          ~target:(Path.toString (normalize_target normalize fresh_target));
        if closing t then fail "session closed during resolution verification";
        t.phase <- Ready;
        on_ready t;
        Some t.token
      with error ->
        close_noerr t;
        match error with Preparation_unavailable -> None | _ -> raise error
      end
  | `ABSENT | `SYMLINK -> fail "logical root is missing or is not a resolved directory"

let prepare ?reservation ?connection ?require_producer ~logical_root ~local_path
    ~working_dir ~candidate ~target ~normalize ~check_apple_double () =
  prepare_internal ~on_ready:(fun _ -> ()) ?reservation ?connection ?require_producer
    ~logical_root ~local_path ~working_dir ~candidate ~target ~normalize ~check_apple_double ()

let prepare_admitted ?connection ?(require_producer=false) ~logical_root ~local_path
    ~working_dir ~candidate ~target ~normalize ~check_apple_double () =
  if not (FinalPublication.available ()) then Lwt.return None else begin
  (* Recovery must happen before waiting for credits. A settled orphan can own
     the last consumer envelope; waiting first would prevent its slot recovery. *)
  Array.iter (function None -> () | Some t -> recover_settlement t) slots;
  let reservation = SemanticRuntime.make_publication_reservation () in
  let prepared = ref None in
  let remember t = prepared := Some t in
  let retire_error error =
    (* A cancellation wrapper's success-continuation allocation can fail after
       native preparation succeeded, synchronously or after a queued grant.
       Retire that recorded native owner before freeing its resource envelope. *)
    (match !prepared with
     | Some t -> prepared := None; close_noerr t
     | None -> (try SemanticAdmission.retire reservation with _ -> ()));
    Lwt.fail error in
  let prepare_now () =
    let token = prepare_internal ~on_ready:remember ~reservation ?connection ~require_producer ~logical_root
      ~local_path ~working_dir ~candidate ~target ~normalize ~check_apple_double () in
    match token with
    | None -> SemanticAdmission.retire reservation; Lwt.return None
    | Some token ->
        (* The registry owns the envelope now, including the producer-return
           gap. A failed result allocation closes the native owner first. *)
        try Lwt.return (Some token) with error -> retire_error error in
  let acquire_and_prepare () = SemanticRuntime.with_cancellation (fun cancellation ->
    try Lwt.try_bind (fun () -> SemanticAdmission.acquire reservation cancellation)
      (fun admitted ->
        if not admitted || HelperSupervisor.is_cancelled cancellation then
          (SemanticAdmission.retire reservation;
           Lwt.fail (Util.Transient "Target resource admission cancelled"))
        else prepare_now ()) retire_error
    with error -> retire_error error) in
  try Lwt.try_bind acquire_and_prepare Lwt.return retire_error
  with error -> retire_error error
  end

let verify_owner t connection logical_root =
  if not (same_connection t.connection connection) ||
     not (same_root t.logical_root logical_root) then
    fail "ticket belongs to another connection or logical root"

let release_ticket ?connection ~logical_root ~token () =
  if not (valid_token token) then fail "invalid ticket syntax";
  match find token with
  | None -> ()
  | Some t ->
      verify_owner t connection logical_root;
      t.closing_requested <- true;
      recover_settlement t;
      match t.phase with
      | Producing | Committing | Preparing -> ()
      | Ready | Finalized | Closed -> close t

let legacy_handoff t =
  if not t.handed_off then begin
    recheck_resolution t;
    (* A planned family/backend choice cannot hide a changed root or producer.
       Native phase dispatch allows planned auxiliaries while mutable, checks
       a frozen witness after finalization, and guards legacy named attachment. *)
    FinalPublication.check_handoff (context t);
    check_open t;
    (* Set ownership policy before releasing handles, so a pending exception
       or later scope cleanup cannot turn a legacy handoff into an unlink. *)
    t.handed_off <- true;
    FinalPublication.release (context t)
  end

let quarantine t =
  check_open t;
  let name = ".unison.validation-rejected-" ^ t.token ^ ".unison.tmp" in
  (* All helpers must be settled before this explicit close. Keep the borrowed
     registry reservation until the containing callback itself settles. *)
  t.closing_requested <- true;
  FinalPublication.quarantine_and_close (context t) ~name

let borrow ~producing ~on_success ?connection ~token ~logical_root ~local_path
    ~working_dir ~candidate ~target f =
  BorrowedWork.try_bind
    (fun () ->
      if not (valid_token token) then fail "invalid ticket syntax";
      let t = match find token with
        | None -> fail "ticket has expired or was already consumed"
        | Some t -> t in
      verify_owner t connection logical_root;
      let eligible =
        if producing then t.require_producer && t.phase = Ready
        else if t.require_producer then t.phase = Finalized
        else t.phase = Ready in
      if not eligible then fail "ticket is not eligible for this producer or commit operation";
      (* Revoke this phase's authorization before remaining verification or
         callback allocation. Keep the record indexed for idempotent release
         and capacity accounting. State-ineligible replays above never close
         another active borrow or destroy its later commit authorization. *)
      t.phase <- if producing then Producing else Committing;
      (try
         let callback_returned = ref false in
         let awaited = ref (Lwt.wait ()) in
         let settle_success value =
           try
             if t.closing_requested || not (Atomic.get t.session) then
               fail "session closed while publication was borrowed";
             on_success t value
           with error -> close_noerr t; Lwt.fail error in
         let settle_failure error = close_noerr t; Lwt.fail error in
         (* Allocate the recovery closures before callback dispatch. Bundled
            Lwt installs its waiter after dispatch; if that allocation throws
            with an outstanding promise, retain descriptors until a later
            recovery installation observes settlement, rather than close under
            running helpers. This is not a universal OOM/async guarantee. *)
         let recovered _ = close_noerr t; Lwt.return () in
         let recovery () =
           if !callback_returned && busy t then begin
             ignore (BorrowedWork.try_bind (fun () -> !awaited) recovered recovered);
             t.recover_settlement <- None
           end in
         t.recover_settlement <- Some recovery;
         let computation () =
           check_open t;
           if not (same_path t.local_path local_path) ||
              not (same_root t.working_dir working_dir) ||
              not (same_path t.candidate candidate) ||
              not (same_path t.target target) then
             fail "publication paths differ from target setup";
           recheck_resolution t;
           if not producing && t.require_producer then begin
             if not (finalized t) then fail "strict commit has no finalized producer witness";
             (match t.actual_fingerprint with
              | None -> fail "strict commit has no actual fingerprint receipt"
              | Some _ -> ());
             FinalPublication.check_candidate (context t);
             check_open t
           end;
           let promise = f t in
           awaited := promise;
           callback_returned := true;
           t.callback_pending <- true;
           promise in
         try
           let result = BorrowedWork.try_bind computation settle_success settle_failure in
           t.recover_settlement <- None;
           result
         with error ->
           handoff_failure t;
           Lwt.fail error
       with error -> handoff_failure t; raise error))
    Lwt.return Lwt.fail

let with_binding ?connection ~token ~logical_root ~local_path ~working_dir
    ~candidate ~target f =
  borrow ~producing:false
    ~on_success:(fun t value -> close t; Lwt.return value)
    ?connection ~token ~logical_root ~local_path ~working_dir ~candidate ~target f

let complete_producer t value =
  if t.handed_off then begin
    close t;
    Lwt.return (value, Legacy_backend)
  end else begin
    recheck_resolution t;
    if not (finalized t) then fail "producer did not freeze its actual output witness";
    (match t.actual_fingerprint with
     | None -> fail "producer did not record its actual fingerprint"
     | Some _ -> ());
    FinalPublication.check_candidate (context t);
    check_open t;
    (* Allocate the entire result while still borrowed. Its allocation failure
       closes the now-settled producer rather than exposing an unreachable
       Finalized ticket. The normal idle owner is retained across source checks. *)
    let result = Lwt.return (value, Guarded_producer) in
    check_open t;
    t.phase <- Finalized;
    t.callback_pending <- false;
    t.recover_settlement <- None;
    result
  end

let with_producer ?connection ~token ~logical_root ~local_path ~working_dir
    ~candidate ~target f =
  borrow ~producing:true ~on_success:complete_producer
    ?connection ~token ~logical_root ~local_path ~working_dir ~candidate ~target f
