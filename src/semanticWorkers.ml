open Lwt
module H = HelperSupervisor
type fingerprint = { digest : string; stats : Unix.LargeFile.stats }
type inspection = { proof : (SemanticDelta.proof, string) result;
                    stats : Unix.LargeFile.stats }
type observation = { inspection : inspection;
  meaning : (FormatExtension.observation, string) result option }
type identification = { formats : string list; fingerprint : fingerprint option;
                        stats : Unix.LargeFile.stats }
type usage = { workers : int; pending : int; running : int; peak_running : int }
exception Failed of string
exception Cancelled_job
type response = Hashed of fingerprint | Inspected of inspection
  | Observed of observation
  | Identified of identification
  | Applied of SemanticDelta.application | Cancelled | Error of string
type operation = Digest | Inspect of FormatExtension.handle
  | Observe of FormatExtension.handle
  | Identify of (FormatRecognition.handle * bool) list
  | Apply of FormatExtension.handle * SemanticDelta.t * Unix.file_descr
type job = { id : int; fd : Unix.file_descr; cancelled : bool Atomic.t;
             operation : operation }
type shared = {
  mutex : Mutex.t; ready : Condition.t;
  jobs : job Queue.t; completions : (int * response) Queue.t;
  notify : Unix.file_descr;
  mutable stopping : bool; mutable running : int; mutable peak : int;
}
type t = {
  shared : shared; domains : unit Domain.t list; budget : H.t;
  io : IoAdmission.t option;
  max_pending : int; reader : Lwt_unix.file_descr;
  replies : (int, response Lwt.t) Hashtbl.t;
  mutable next_id : int; mutable pending : int; mutable slots : int;
  mutable admission : int list; mutable closing : bool;
  mutable joined : bool;
  mutable shutdown_result : unit Lwt.t option;
  pump_done : unit Lwt.t;
}
let close_noerr fd = try Unix.close fd with Unix.Unix_error _ -> ()
let close_operation = function Apply (_, _, fd) -> close_noerr fd | _ -> ()
let duplicate_operation = function
  | Apply (extension, plan, fd) ->
      let owned = Unix.dup ~cloexec:true fd in
      (try Apply (extension, plan, owned)
       with error -> close_noerr owned; raise error)
  | operation -> operation
let locked shared f =
  Mutex.lock shared.mutex;
  match f () with
  | x -> Mutex.unlock shared.mutex; x
  | exception e -> Mutex.unlock shared.mutex; raise e
let notify shared =
  let b = Bytes.make 1 '\001' in
  let rec write () = try ignore (Unix.write shared.notify b 0 1) with
    | Unix.Unix_error (Unix.EINTR, _, _) -> write ()
    | Unix.Unix_error ((Unix.EAGAIN | Unix.EWOULDBLOCK), _, _) -> ()
  in write ()
let unchanged a b =
  a.Unix.LargeFile.st_dev = b.Unix.LargeFile.st_dev &&
  a.Unix.LargeFile.st_ino = b.Unix.LargeFile.st_ino &&
  a.Unix.LargeFile.st_kind = b.Unix.LargeFile.st_kind &&
  a.Unix.LargeFile.st_size = b.Unix.LargeFile.st_size &&
  a.Unix.LargeFile.st_mtime = b.Unix.LargeFile.st_mtime &&
  a.Unix.LargeFile.st_ctime = b.Unix.LargeFile.st_ctime

(* The worker side below sees only [shared] and [job], never the owner record.
   Domain.spawn is the stock-compatible, manually audited boundary: shared
   queues/counters use the mutex, cancellation uses Atomic, hashing/channel
   state is private. This does not claim compiler-proved portability. *)
let execute job =
  let check_cancel () = if Atomic.get job.cancelled then raise Cancelled_job in
  try
    check_cancel ();
    let stats = Unix.LargeFile.fstat job.fd in
    let result = SemanticFile.with_fd ~check_cancel job.fd (fun file ->
      match job.operation with
      | Digest -> Hashed {digest = SemanticFile.digest file; stats}
      | Identify recognizers ->
        let formats = List.filter_map (fun (recognizer,claimed) ->
          check_cancel ();
          let selected = claimed || match FormatRecognition.identify recognizer file with
            | FormatRecognition.Not_matched -> false
            | FormatRecognition.Recognized | FormatRecognition.Indeterminate _ -> true in
          if selected then Some (FormatRecognition.format recognizer) else None)
          recognizers in
        check_cancel ();
        SemanticFile.check file;
        let fingerprint = match formats with
          | [] -> None
          | _ -> Some {digest=SemanticFile.digest file;stats} in
        check_cancel ();
        SemanticFile.check file;
        Identified {formats;fingerprint;stats}
      | Inspect extension ->
        Inspected {proof = SemanticDelta.inspect ~max_payload:(FormatExtension.payload_limit extension)
          (FormatExtension.implementation extension) file; stats}
      | Observe extension ->
        let proof = SemanticDelta.inspect ~max_payload:(FormatExtension.payload_limit extension)
          (FormatExtension.implementation extension) file in
        check_cancel ();
        let meaning = match proof with
          | Error _ -> None
          | Ok proof -> SemanticDelta.observe ~extension proof in
        check_cancel ();
        SemanticFile.check file;
        Observed {inspection={proof;stats};meaning}
      | Apply (extension, plan, output) ->
        let report = SemanticDelta.apply_report_with_extension ~check_cancel
          ~max_payload:(FormatExtension.payload_limit extension) (FormatExtension.implementation extension)
          plan ~basis:file ~output in
        Applied report) in
    if not (unchanged stats (Unix.LargeFile.fstat job.fd)) then
      Error "file changed while hashing"
    else result
  with
  | Cancelled_job -> Cancelled
  | SemanticFile.Invalid reason | Invalid_argument reason -> Error reason
  | Unix.Unix_error (err, operation, _) -> Error (operation ^ ": " ^ Unix.error_message err)
  | _ -> Error "unexpected digest worker failure"
let rec worker shared () =
  let next = locked shared (fun () ->
    while Queue.is_empty shared.jobs && not shared.stopping do
      Condition.wait shared.ready shared.mutex
    done;
    if Queue.is_empty shared.jobs then None else begin
      let job = Queue.take shared.jobs in
      shared.running <- shared.running + 1;
      shared.peak <- max shared.peak shared.running;
      Some job
    end) in
  match next with
  | None -> ()
  | Some job ->
    let result = execute job in
    close_noerr job.fd;
    close_operation job.operation;
    locked shared (fun () ->
      shared.running <- shared.running - 1;
      Queue.add (job.id, result) shared.completions);
    notify shared;
    worker shared ()

let recommended_workers () = max 1 (Domain.recommended_domain_count ())
let take_completions shared = locked shared (fun () ->
  let rec drain acc =
    if Queue.is_empty shared.completions then List.rev acc
    else drain (Queue.take shared.completions :: acc)
  in drain [])
let dispatch t =
  let first_error = ref None in
  List.iter (fun (id, result) ->
    match Hashtbl.find_opt t.replies id with
    | None -> ()
    | Some reply ->
      Hashtbl.remove t.replies id;
      (try Lwt.wakeup reply result with error ->
         if !first_error = None then first_error := Some error)) (take_completions t.shared);
  !first_error
let rec pump t scratch =
  Lwt_unix.read t.reader scratch 0 (Bytes.length scratch) >>= fun _ ->
  let observer_error = dispatch t in
  let next = if t.joined then begin
    Lwt_unix.close t.reader;
    Lwt.wakeup t.pump_done ();
    return ()
  end else pump t scratch in
  (* An owner's unhandled observer exception must remain visible, but cannot
     discard sibling completions or leave this persistent pool unarmed. *)
  (match observer_error with
   | None -> ()
   | Some error -> Lwt.ignore_result
       (Lwt_unix.yield () >>= fun () -> Lwt.fail error));
  next
let create_internal ~io ~workers ~max_pending ~budget =
  if workers <= 0 || max_pending <= 0 then invalid_arg "SemanticWorkers.create: positive limits required";
  let owned_read = ref Unix.stdin and owned_write = ref Unix.stdout
  and has_read = ref false and has_write = ref false
  and reader_owner = ref None and shared_owner = ref None
  and domains = ref [] in
  let stop shared =
    locked shared (fun () -> shared.stopping <- true; Condition.broadcast shared.ready) in
  let cleanup () =
    (match !shared_owner with Some shared -> (try stop shared with _ -> ()) | None -> ());
    List.iter (fun domain -> try Domain.join domain with _ -> ()) !domains;
    domains := [];
    if !has_read then begin
      has_read := false;
      (try match !reader_owner with
       | Some reader -> Lwt_unix.close reader
       | None -> Unix.close !owned_read
       with _ -> ())
    end;
    if !has_write then begin
      has_write := false; (try Unix.close !owned_write with _ -> ())
    end in
  let read_fd, write_fd = Unix.pipe ~cloexec:true () in
  owned_read := read_fd; has_read := true;
  owned_write := write_fd; has_write := true;
  try
    Unix.set_nonblock read_fd;
    Unix.set_nonblock write_fd;
    let shared = { mutex = Mutex.create (); ready = Condition.create ();
      jobs = Queue.create (); completions = Queue.create (); notify = write_fd;
      stopping = false; running = 0; peak = 0 } in
    shared_owner := Some shared;
    for _ = 1 to workers do
      let domain = Domain.spawn (worker shared) in
      (* Linking the returned domain can allocate too. Stop and join this
         still-local handle before the outer guard joins earlier domains. *)
      (try domains := domain :: !domains
       with error -> (try stop shared with _ -> ());
         (try Domain.join domain with _ -> ()); raise error)
    done;
    let reader = Lwt_unix.of_unix_file_descr read_fd in
    reader_owner := Some reader;
    let t = { shared; domains = !domains; budget; io; max_pending; reader;
      replies = Hashtbl.create workers; next_id = 0; pending = 0; slots = 0;
      admission = []; closing = false; joined = false;
      shutdown_result = None; pump_done = Lwt.wait () } in
    Lwt.ignore_result (pump t (Bytes.create 4096));
    has_read := false; has_write := false;
    t
  with error -> cleanup (); raise error
let create ~workers ~max_pending ~budget =
  create_internal ~io:None ~workers ~max_pending ~budget
let create_with_io ~io ~workers ~max_pending ~budget =
  create_internal ~io:(Some io) ~workers ~max_pending ~budget
let usage t =
  let running, peak_running = locked t.shared (fun () -> t.shared.running, t.shared.peak) in
  {workers = List.length t.domains; pending = t.pending; running; peak_running}

let submit t cancellation fd requested_operation =
  if t.closing then fail (Failed "digest pool is closed")
  else if t.pending >= t.max_pending then fail (Failed "digest queue is full")
  else
    (* Allocate the guard and controller bookkeeping before acquiring either
       duplicate. Continuation/listener setup is part of this ownership phase. *)
    let owned = ref fd and operation = ref requested_operation
    and owns_input = ref false and owns_operation = ref false
    and pending_registered = ref false in
    let id = t.next_id in
    t.next_id <- t.next_id + 1;
    let cancelled = Atomic.make false and admission_cancel = H.cancellation () in
    let stop () = Atomic.set cancelled true; H.cancel admission_cancel in
    let unregister_cancel = ref (fun () -> ()) in
    let finished = ref false and transferred = ref false and has_slot = ref false in
    let cleanup_error = ref None in
    let cleanup_owned () =
      if not !transferred then begin
        if !owns_input then begin
          owns_input := false; (try close_noerr !owned with _ -> ())
        end;
        if !owns_operation then begin
          owns_operation := false; (try close_operation !operation with _ -> ())
        end
      end in
    let rec monitor () =
      if !finished then return ()
      else if t.closing || H.is_cancelled cancellation then begin
        stop (); return ()
      end else Lwt_unix.sleep 0.01 >>= monitor in
    let remove_admission () = t.admission <- List.filter ((<>) id) t.admission in
    let rec wait_slot () =
      if Atomic.get cancelled || t.closing then return false
      else if t.slots < List.length t.domains &&
        (match t.admission with x :: _ -> x = id | [] -> false) then begin
        remove_admission (); t.slots <- t.slots + 1; has_slot := true; return true
      end else Lwt_unix.sleep 0.01 >>= wait_slot in
    let finish () =
      if not !finished then begin
        finished := true;
        let attempt f = try f () with error ->
          if !cleanup_error = None then cleanup_error := Some error in
        attempt (fun () -> !unregister_cancel ());
        attempt remove_admission;
        if !has_slot then begin has_slot := false; t.slots <- t.slots - 1 end;
        if not !transferred then Hashtbl.remove t.replies id;
        attempt cleanup_owned;
        if !pending_registered then begin
          pending_registered := false; t.pending <- t.pending - 1
        end;
        if t.closing && t.pending = 0 then attempt (fun () -> notify t.shared);
        match !cleanup_error with None -> () | Some error -> raise error
      end in
    let execute () =
        (* A blocked filesystem must not occupy a domain slot or the slot FIFO.
           Register here, only after the atomic I/O reservation is admitted. *)
        t.admission <- t.admission @ [id];
        wait_slot () >>= fun admitted ->
        if not admitted then return None
        else BorrowedWork.try_bind (fun () ->
          H.with_cpu_permits t.budget ~weight:1 admission_cancel (fun () ->
          if t.closing || Atomic.get cancelled then return Cancelled
          else begin
            let reply = Lwt.wait () in
            Hashtbl.add t.replies id reply;
            locked t.shared (fun () ->
              Queue.add {id; fd = !owned; cancelled; operation = !operation} t.shared.jobs;
              transferred := true;
              Condition.signal t.shared.ready);
            reply
          end)) (function
        | None | Some Cancelled -> return None
        | Some (Error reason) -> fail (Failed reason)
        | Some ((Hashed _ | Inspected _ | Observed _ | Identified _ | Applied _) as result) ->
          if t.closing || H.is_cancelled cancellation then return None
          else return (Some result)) fail in
    let admitted_execution () = match t.io with
      | None -> execute ()
      | Some io ->
          let descriptors = match !operation with
            | Apply (_, _, output) -> [!owned;output]
            | Digest | Inspect _ | Observe _ | Identify _ -> [!owned] in
          let devices = IoAdmission.devices_of_fds descriptors in
          BorrowedWork.try_bind
            (fun () -> IoAdmission.with_devices io admission_cancel ~devices execute)
            (function
          | None -> return None
          | Some result -> return result) fail in
    try
      owned := Unix.dup ~cloexec:true fd; owns_input := true;
      operation := duplicate_operation requested_operation; owns_operation := true;
      t.pending <- t.pending + 1; pending_registered := true;
      unregister_cancel := H.on_cancel cancellation stop;
      Lwt.ignore_result (monitor ());
      BorrowedWork.try_bind admitted_execution
        (fun result -> finish (); return result)
        (fun exn ->
          (try finish () with _ -> ());
          match exn with
          | IoAdmission.Failed reason -> fail (Failed reason)
          | _ -> fail exn)
    with error ->
      (* Before queue transfer the controller owns both descriptors. Afterwards
         only the worker closes them. Returned sleeping work is guarded at each
         mapping/ownership layer; persistent allocation failures and callbacks
         which dispatch independently before throwing remain outside that
         finite observer-installation guarantee. *)
      (try finish () with _ -> ());
      match error with
      | Unix.Unix_error (err, operation, _) ->
          fail (Failed (operation ^ ": " ^ Unix.error_message err))
      | _ -> raise error

let digest t cancellation fd =
  BorrowedWork.try_bind (fun () -> submit t cancellation fd Digest) (function
  | None -> return None
  | Some (Hashed result) -> return (Some result)
  | Some _ -> fail (Failed "unexpected digest response")) fail

let inspect t cancellation ~extension fd =
  BorrowedWork.try_bind (fun () -> submit t cancellation fd (Inspect extension)) (function
  | None -> return None
  | Some (Inspected result) -> return (Some result)
  | Some _ -> fail (Failed "unexpected inspection response")) fail

let identify t cancellation ~recognizers fd =
  if List.length recognizers > FormatRecognition.max_recognizers then
    invalid_arg "candidate recognition limit";
  let ids = List.map (fun (handle,_) -> FormatRecognition.format handle) recognizers in
  if List.length (List.sort_uniq String.compare ids) <> List.length ids then
    invalid_arg "duplicate candidate recognition format";
  BorrowedWork.try_bind (fun () -> submit t cancellation fd (Identify recognizers)) (function
  | None -> return None
  | Some (Identified result) -> return (Some result)
  | Some _ -> fail (Failed "unexpected identification response")) fail

let observe t cancellation ~extension fd =
  BorrowedWork.try_bind (fun () -> submit t cancellation fd (Observe extension)) (function
  | None -> return None
  | Some (Observed result) -> return (Some result)
  | Some _ -> fail (Failed "unexpected observation response")) fail

let apply_report t cancellation ~extension plan ~basis ~output =
  BorrowedWork.try_bind
    (fun () -> submit t cancellation basis (Apply (extension, plan, output))) (function
  | None -> return None
  | Some (Applied report) -> return (Some report)
  | Some _ -> fail (Failed "unexpected materialization response")) fail

let apply t cancellation ~extension plan ~basis ~output =
  BorrowedWork.try_bind
    (fun () -> apply_report t cancellation ~extension plan ~basis ~output) (function
  | None -> return None
  | Some _ -> return (Some ())) fail

let inspect_dng t cancellation fd =
  inspect t cancellation ~extension:(FormatExtension.trusted ~max_payload:FormatExtension.max_region (module DngSemantic)) fd
let apply_dng t cancellation plan ~basis ~output =
  apply t cancellation ~extension:(FormatExtension.trusted ~max_payload:FormatExtension.max_region (module DngSemantic)) plan ~basis ~output

let shutdown t = match t.shutdown_result with
  | Some result -> result
  | None ->
    t.closing <- true;
    let result = Lwt.wait () in
    t.shutdown_result <- Some result;
    let rec finish () =
      if t.pending <> 0 then Lwt_unix.sleep 0.01 >>= finish
      else begin
        locked t.shared (fun () -> t.shared.stopping <- true; Condition.broadcast t.shared.ready);
        List.iter Domain.join t.domains;
        t.joined <- true;
        notify t.shared;
        t.pump_done >>= fun () -> close_noerr t.shared.notify; return ()
      end in
    Lwt.ignore_result (try_bind finish
      (fun () -> Lwt.wakeup result (); return ())
      (fun exn -> Lwt.wakeup_exn result exn; return ()));
    result
