open Lwt
module H = HelperSupervisor
module Mailbox = SemanticMailbox
type fingerprint = { digest : string; stats : Unix.LargeFile.stats }
type inspection = { proof : (SemanticDelta.proof, string) result;
                    stats : Unix.LargeFile.stats }
type observation = { inspection : inspection;
  meaning : (FormatExtension.observation, string) result option }
type reconciliation = { merge_plan : (SemanticDelta.t, string) result;
                        stats : Unix.LargeFile.stats }
type identification = { formats : string list; fingerprint : fingerprint option;
                        stats : Unix.LargeFile.stats }
type recognition = { formats : string list; stats : Unix.LargeFile.stats }
type component_summary = { full_sha256 : string; layout_sha256 : string;
  projections : (ComponentHash.role * ComponentHash.projection option) list;
  refinements : DngComponents.outcome list; hash_bytes_requested : int64;
  checkpoint : ComponentHash.checkpoint option;
  reused_components : string list; invalidated_components : string list }
type component_inspection = { components : (component_summary, string) result;
                              stats : Unix.LargeFile.stats }
type usage = { workers : int; pending : int; running : int; peak_running : int }
exception Failed of string
exception Cancelled_job
type response = Hashed of fingerprint | Inspected of inspection
  | Observed of observation
  | Identified of identification
  | Recognized of recognition
  | Component_inspected of component_inspection
  | Reconciled of reconciliation
  | Applied of SemanticDelta.application
  | Snapshotted of ValidationSnapshot.report | Cancelled | Error of string
type operation = Digest | Inspect of FormatExtension.handle
  | Reconcile of FormatExtension.handle * string * SemanticDelta.proof * SemanticDelta.proof * SemanticDelta.proof
  | Observe of FormatExtension.handle
  | Components of DngComponents.decoders * int64 * bool
  | Restore_components of string * string * int64
  | Refresh_components of DngComponents.outcome list * DngComponents.decoders * string * string * int64 * bool
  | Identify of (FormatRecognition.handle * bool) list
  | Recognize of (FormatRecognition.handle * bool) list
  | Apply of FormatExtension.handle * SemanticDelta.t * Unix.file_descr
  | Snapshot of int64 * Unix.file_descr
type job = { id : int; fd : Unix.file_descr; cancelled : bool Atomic.t;
             operation : operation; measure_reads : bool }
type shared = {
  mutex : Mutex.t; ready : Condition.t;
  jobs : job Mailbox.t; completions : (int * response * SemanticFile.read_stats option) Mailbox.t;
  notify : Unix.file_descr;
  stopping : bool Atomic.t; running : int Atomic.t; peak : int Atomic.t;
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
  mutable read_observer : (int -> SemanticFile.read_stats -> unit) option;
}
let close_noerr fd = try Unix.close fd with Unix.Unix_error _ -> ()
let close_operation = function Apply (_, _, fd) | Snapshot (_,fd) -> close_noerr fd | _ -> ()
let duplicate_operation = function
  | Apply (extension, plan, fd) ->
      let owned = Unix.dup ~cloexec:true fd in
      (try Apply (extension, plan, owned)
       with error -> close_noerr owned; raise error)
  | Snapshot (limit,fd) ->
      let owned=Unix.dup ~cloexec:true fd in
      (try Snapshot (limit,owned) with error -> close_noerr owned;raise error)
  | operation -> operation
let locked shared f =
  Mutex.lock shared.mutex;
  match f () with
  | x -> Mutex.unlock shared.mutex; x
  | exception e -> Mutex.unlock shared.mutex; raise e
let notify shared =
  (* Completion is already published when a worker gets here. Do not allocate
     a scratch buffer between publication and the owner's wake-up. The literal
     is immutable and may safely be read by concurrent notifying domains. *)
  let rec write () = try ignore (Unix.write_substring shared.notify "\001" 0 1) with
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
   Queues use immutable atomic mailbox state; condition/counter transitions
   use the mutex. Cancellation uses Atomic; hashing/channel state is private. OxCaml selects Safe.spawn and checked extension contracts;
   stock retains Domain.spawn. Native contracts/FD ownership stay manual. *)
let execute job =
  let check_cancel () = if Atomic.get job.cancelled then raise Cancelled_job in
  try
    check_cancel ();
    let stats = Unix.LargeFile.fstat job.fd in
    let operation file =
      match job.operation with
      | Digest -> Hashed {digest = SemanticFile.digest file; stats}
      | Identify recognizers | Recognize recognizers ->
        let formats = List.filter_map (fun (recognizer,claimed) ->
          check_cancel ();
          let selected = claimed || match FormatRecognition.identify recognizer file with
            | FormatRecognition.Not_matched -> false
            | FormatRecognition.Recognized | FormatRecognition.Indeterminate _ -> true in
          if selected then Some (FormatRecognition.format recognizer) else None)
          recognizers in
        check_cancel ();
        SemanticFile.check file;
        let fingerprint = match formats,job.operation with
          | _,Recognize _ -> None
          | [],_ -> None
          | _ -> Some {digest=SemanticFile.digest file;stats} in
        check_cancel ();
        SemanticFile.check file;
        (match job.operation with Recognize _ -> Recognized {formats;stats}
         | _ -> Identified {formats;fingerprint;stats})
      | Inspect extension ->
        Inspected {proof = SemanticDelta.inspect ~span_semantics:(FormatExtension.span_semantics extension)
          ~max_payload:(FormatExtension.payload_limit extension)
          (FormatExtension.implementation extension) file; stats}
      | (Components _ | Restore_components _ | Refresh_components _) as operation ->
        let summarize session refined outcomes capture reused invalidated =
            check_cancel ();
            let projections=List.map (fun role -> role,ComponentHash.projection refined role)
              [ComponentHash.Encoded_pixels;ComponentHash.Standard_metadata;
               ComponentHash.Private_metadata;ComponentHash.Structural;ComponentHash.Opaque] in
            {full_sha256=ComponentHash.full_sha256 refined;
             layout_sha256=ComponentHash.layout_sha256 refined;projections;
             refinements=outcomes;hash_bytes_requested=ComponentHash.bytes_requested session;
             checkpoint=(if capture then Some(ComponentHash.checkpoint session refined) else None);
             reused_components=reused;invalidated_components=invalidated} in
        let components=match operation with
          | Components (decoders,max_read_bytes,capture) ->
            DngComponents.with_snapshot ~decoders ~max_read_bytes file
              (fun session ~initial:_ ~refined outcomes -> summarize session refined outcomes capture [] [])
          | Restore_components (expected_checkpoint_sha256,encoded,max_read_bytes) ->
            DngComponents.with_checkpoint ~expected_checkpoint_sha256 ~max_read_bytes file encoded
              (fun session snapshot -> summarize session snapshot [] false [] [])
          | Refresh_components (previous,decoders,expected_checkpoint_sha256,encoded,max_read_bytes,capture) ->
            DngComponents.with_refreshed_checkpoint ~previous ~decoders ~expected_checkpoint_sha256
              ~max_read_bytes file encoded (fun session result ->
                summarize session result.snapshot result.outcomes capture result.reused result.invalidated)
          | _ -> assert false in
        check_cancel ();SemanticFile.check file;
        Component_inspected {components;stats}
      | Observe extension ->
        let proof = SemanticDelta.inspect ~span_semantics:(FormatExtension.span_semantics extension)
          ~max_payload:(FormatExtension.payload_limit extension)
          (FormatExtension.implementation extension) file in
        check_cancel ();
        let meaning = match proof with
          | Error _ -> None
          | Ok proof -> SemanticDelta.observe ~extension proof in
        check_cancel ();
        SemanticFile.check file;
        Observed {inspection={proof;stats};meaning}
      | Reconcile(extension,nonce,base,left,right) ->
        Reconciled {merge_plan=SemanticDelta.reconcile_xmp
          ~max_payload:(FormatExtension.payload_limit extension)
          (FormatExtension.implementation extension) ~nonce ~base ~left ~right file;stats}
      | Apply (extension, plan, output) ->
        let report = SemanticDelta.apply_report_with_extension ~check_cancel
          ~max_payload:(FormatExtension.payload_limit extension) (FormatExtension.implementation extension)
          plan ~basis:file ~output in
        Applied report
      | Snapshot (max_bytes,output) ->
        Snapshotted (ValidationSnapshot.materialize ~check_cancel ~max_bytes
          ~clone:ValidationSnapshot.existing_clone ~source:job.fd ~output) in
    (* Snapshot owns independent source/output readers. The outer reader's
       zero counter would not measure that job; do not emit a false sample. *)
    let measured = job.measure_reads && (match job.operation with Snapshot _ -> false | _ -> true) in
    let result,reads = if measured then
        let result,reads = SemanticFile.with_read_stats ~check_cancel job.fd operation in
        result,Some reads
      else SemanticFile.with_fd ~check_cancel job.fd operation,None in
    if not (unchanged stats (Unix.LargeFile.fstat job.fd)) then
      Error "file changed while hashing",None
    else result,reads
  with
  | Cancelled_job -> Cancelled,None
  | SemanticFile.Invalid reason | ComponentHash.Invalid reason | Invalid_argument reason -> Error reason,None
  | Unix.Unix_error (err, operation, _) -> Error (operation ^ ": " ^ Unix.error_message err),None
  | _ -> Error "unexpected digest worker failure",None
let rec worker shared () =
  let next = locked shared (fun () ->
    let rec take () = match Mailbox.pop shared.jobs with
      | Mailbox.Item job ->
          let running = Atomic.get shared.running + 1 in
          Atomic.set shared.running running;
          Atomic.set shared.peak (max (Atomic.get shared.peak) running);
          Some job
      | Mailbox.Empty when not (Atomic.get shared.stopping) ->
          (* Producers hold this same mutex while publishing/signalling, so
             waiting after an empty snapshot cannot lose their wakeup. *)
          Condition.wait shared.ready shared.mutex; take ()
      | Mailbox.Empty | Mailbox.Drained -> None in
    take ()) in
  match next with
  | None -> ()
  | Some job ->
    let result,reads = execute job in
    close_noerr job.fd;
    close_operation job.operation;
    locked shared (fun () ->
      Atomic.set shared.running (Atomic.get shared.running - 1);
      match Mailbox.push shared.completions (job.id, result, reads) with
      | Mailbox.Added -> ()
      | Mailbox.Full | Mailbox.Closed -> failwith "worker completion mailbox invariant");
    notify shared;
    worker shared ()

let recommended_workers () = max 1 (Domain.recommended_domain_count ())
let take_completions shared = locked shared (fun () ->
  let rec drain acc =
    match Mailbox.pop shared.completions with
    | Mailbox.Item result -> drain (result :: acc)
    | Mailbox.Empty | Mailbox.Drained -> List.rev acc
  in drain [])
let dispatch t =
  let first_error = ref None in
  List.iter (fun (id, result, reads) ->
    match Hashtbl.find_opt t.replies id with
    | None -> ()
    | Some reply ->
      let read_observer = t.read_observer in
      Hashtbl.remove t.replies id;
      (try
         Lwt.wakeup reply result;
         (* Owner-only diagnostics follow reply settlement. A logging exception
            cannot strand this reply or prevent sibling completion delivery. *)
         (match read_observer,reads with
          | Some observer,Some reads -> observer id reads
          | _ -> ())
       with error ->
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
  if workers <= 0 || max_pending <= 0 || max_pending > 65536 then
    invalid_arg "SemanticWorkers.create: positive workers and1..65536 pending jobs required";
  let owned_read = ref Unix.stdin and owned_write = ref Unix.stdout
  and has_read = ref false and has_write = ref false
  and reader_owner = ref None and shared_owner = ref None
  and domains = ref [] in
  let stop shared =
    locked shared (fun () -> Atomic.set shared.stopping true; Mailbox.close shared.jobs; Condition.broadcast shared.ready) in
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
      jobs = Mailbox.create ~capacity:max_pending;
      completions = Mailbox.create ~capacity:max_pending; notify = write_fd;
      stopping = Atomic.make false; running = Atomic.make 0; peak = Atomic.make 0 } in
    shared_owner := Some shared;
    for _ = 1 to workers do
      let domain = Domain.spawn (* ox-safe-worker-spawn *) (fun () -> worker shared ()) in
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
      shutdown_result = None; pump_done = Lwt.wait (); read_observer = None } in
    Lwt.ignore_result (pump t (Bytes.create 4096));
    has_read := false; has_write := false;
    t
  with error -> cleanup (); raise error
let create ~workers ~max_pending ~budget =
  create_internal ~io:None ~workers ~max_pending ~budget
let create_with_io ~io ~workers ~max_pending ~budget =
  create_internal ~io:(Some io) ~workers ~max_pending ~budget
let set_read_observer t observer =
  if t.closing || t.pending <> 0 then
    invalid_arg "SemanticWorkers.set_read_observer requires an idle open pool";
  t.read_observer <- observer
let usage t =
  let running, peak_running = locked t.shared (fun () -> Atomic.get t.shared.running, Atomic.get t.shared.peak) in
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
              (match Mailbox.push t.shared.jobs {id; fd = !owned; cancelled; operation = !operation;
                 measure_reads = Option.is_some t.read_observer} with
               | Mailbox.Added -> transferred := true
               | Mailbox.Full | Mailbox.Closed -> raise (Failed "worker job mailbox invariant"));
              Condition.signal t.shared.ready);
            reply
          end)) (function
        | None | Some Cancelled -> return None
        | Some (Error reason) -> fail (Failed reason)
        | Some ((Hashed _ | Inspected _ | Observed _ | Identified _ | Recognized _ | Component_inspected _ | Reconciled _ | Applied _ | Snapshotted _) as result) ->
          if t.closing || H.is_cancelled cancellation then return None
          else return (Some result)) fail in
    let admitted_execution () = match t.io with
      | None -> execute ()
      | Some io ->
          let descriptors = match !operation with
            | Apply (_, _, output) | Snapshot (_,output) -> [!owned;output]
            | Digest | Inspect _ | Observe _ | Identify _ | Recognize _ | Components _ | Restore_components _ | Refresh_components _ | Reconcile _ -> [!owned] in
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

let snapshot t cancellation ~max_bytes ~source ~output =
  if max_bytes<0L then invalid_arg "SemanticWorkers.snapshot byte limit";
  BorrowedWork.try_bind (fun () -> submit t cancellation source (Snapshot (max_bytes,output))) (function
  | None -> return None
  | Some (Snapshotted report) -> return (Some report)
  | Some _ -> fail (Failed "unexpected snapshot response")) fail

let inspect t cancellation ~extension fd =
  BorrowedWork.try_bind (fun () -> submit t cancellation fd (Inspect extension)) (function
  | None -> return None
  | Some (Inspected result) -> return (Some result)
  | Some _ -> fail (Failed "unexpected inspection response")) fail

let components t cancellation ?(capture_checkpoint=false) ~decoders ~max_read_bytes fd =
  if max_read_bytes<0L then invalid_arg "SemanticWorkers.components read limit";
  BorrowedWork.try_bind (fun () -> submit t cancellation fd (Components(decoders,max_read_bytes,capture_checkpoint))) (function
  | None -> return None
  | Some (Component_inspected result) -> return (Some result)
  | Some _ -> fail (Failed "unexpected component inspection response")) fail

let restore_components t cancellation ~expected_checkpoint_sha256 ~encoded ~max_read_bytes fd =
  if max_read_bytes<0L || String.length expected_checkpoint_sha256<>32 ||
    String.length encoded>ComponentHash.max_checkpoint_size then
    invalid_arg "SemanticWorkers.restore_components bounds";
  BorrowedWork.try_bind
    (fun () -> submit t cancellation fd (Restore_components(expected_checkpoint_sha256,encoded,max_read_bytes)))
    (function
      | None -> return None
      | Some (Component_inspected result) -> return (Some result)
      | Some _ -> fail (Failed "unexpected restored component response")) fail

let refresh_components t cancellation ~previous ~decoders ?(capture_checkpoint=false)
    ~expected_checkpoint_sha256 ~encoded ~max_read_bytes fd =
  if max_read_bytes<0L || List.length previous>64 || String.length expected_checkpoint_sha256<>32 ||
    String.length encoded>ComponentHash.max_checkpoint_size then
    invalid_arg "SemanticWorkers.refresh_components bounds";
  BorrowedWork.try_bind
    (fun () -> submit t cancellation fd
      (Refresh_components(previous,decoders,expected_checkpoint_sha256,encoded,max_read_bytes,capture_checkpoint)))
    (function
      | None -> return None
      | Some (Component_inspected result) -> return (Some result)
      | Some _ -> fail (Failed "unexpected refreshed component response")) fail

let reconcile_xmp t cancellation ~extension ~nonce ~base ~left ~right fd =
  BorrowedWork.try_bind
    (fun () -> submit t cancellation fd (Reconcile(extension,nonce,base,left,right))) (function
    | None -> return None
    | Some(Reconciled result) -> return(Some result)
    | Some _ -> fail(Failed "unexpected reconciliation response")) fail

let check_recognizers recognizers =
  if List.length recognizers > FormatRecognition.max_recognizers then
    invalid_arg "candidate recognition limit";
  let ids = List.map (fun (handle,_) -> FormatRecognition.format handle) recognizers in
  if List.length (List.sort_uniq String.compare ids) <> List.length ids then
    invalid_arg "duplicate candidate recognition format"
let recognize t cancellation ~recognizers fd =
  check_recognizers recognizers;
  BorrowedWork.try_bind (fun () -> submit t cancellation fd (Recognize recognizers)) (function
  | None -> return None
  | Some (Recognized result) -> return (Some result)
  | Some _ -> fail (Failed "unexpected recognition response")) fail
let identify t cancellation ~recognizers fd =
  check_recognizers recognizers;
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
        locked t.shared (fun () -> Atomic.set t.shared.stopping true; Mailbox.close t.shared.jobs; Condition.broadcast t.shared.ready);
        List.iter Domain.join t.domains;
        t.joined <- true;
        Mailbox.close t.shared.completions;
        notify t.shared;
        t.pump_done >>= fun () -> close_noerr t.shared.notify; return ()
      end in
    Lwt.ignore_result (try_bind finish
      (fun () -> Lwt.wakeup result (); return ())
      (fun exn -> Lwt.wakeup_exn result exn; return ()));
    result
