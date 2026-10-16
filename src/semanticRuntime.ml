open Lwt
type t = {supervisor:HelperSupervisor.t;pool:SemanticWorkers.t;cpu_budget:int;
          admission:SemanticAdmission.t;io:IoAdmission.t}
let workers = Prefs.createInt "semanticworkers" 0 ~local:true
  ~category:(`Advanced `General)
  "CPU budget for semantic work (0 means physical cores where detected)"
  "Shared CPU permit budget for semantic work and external validation. \
   Auto uses physical cores on macOS and the available logical CPU count \
   when topology is unavailable. Set a positive count to override, including \
   all logical CPUs. A multithreaded SDK helper reserves its complete thread count."
let max_inflight = Prefs.createInt "semanticmaxinflight" 0 ~local:true
  ~category:(`Advanced `General)
  "maximum admitted semantic transactions (0 means domains plus source headroom)"
  "Shared transaction limit for semantic transfers and Adobe validation. \
   CPU permits remain independent; payload and descriptor credits may lower concurrency."
let payload_budget = Prefs.createInt "semanticpayloadbudget" 512 ~local:true
  ~category:(`Advanced `General)
  "estimated retained semantic/backend memory budget in MiB"
  "Admission credits for proof/encoding buffers and registered backend memory \
   declarations. This is not a process RSS cap; undeclared SDK heaps and directory \
   manifests remain outside this estimate."
let descriptor_budget = Prefs.createInt "semanticdescriptorbudget" 512 ~local:true
  ~category:(`Advanced `General)
  "reserved descriptor credits for semantic transactions"
  "Admission credits for semantic descriptors and worker duplicates, separate \
   from unrelated legacy transfers and external helper descriptor use."
let io_budget = Prefs.makeEndpointLocal (Prefs.createInt "semanticvolumejobs" 0 ~local:true
  ~category:(`Advanced `General)
  "maximum executing semantic jobs per filesystem (0 means CPU budget)"
  "Limit concurrent hash, metadata and validator execution on each endpoint-local \
   filesystem device. Source and output reservations are atomic. Waiting jobs \
   consume no CPU permits. Device groups do not identify physical disks, and \
   this setting does not limit unrelated ordinary transfers or external programs.")
let runtime = ref None
let resource_runtime = ref None
let supervisor_runtime = ref None
let debug = Trace.debug "semantic"
let configured_cpus () = match Prefs.read workers with
    | 0 -> HelperSupervisor.available_physical_cpus ()
    | n when n > 0 -> n
    | _ -> raise (Util.Fatal "semanticworkers must be zero or positive")
let helper_supervisor () =
  let n = configured_cpus () in
  let supervisor = match !supervisor_runtime with
    | Some (supervisor,existing) when existing = n -> supervisor
    | Some _ -> raise (Util.Fatal "Restart Unison to change its shared CPU budget")
    | None ->
        let supervisor = HelperSupervisor.create ~cpu_permits:n ~max_children:n ~max_pending:4096 in
        supervisor_runtime := Some (supervisor,n); supervisor in
  supervisor,n
let settings () =
  let n = configured_cpus () in
  let count = min n (SemanticWorkers.recommended_workers ()) in
  let io_jobs = match Prefs.read io_budget with
    | 0 -> n
    | value when value > 0 -> value
    | _ -> raise (Util.Fatal "semanticvolumejobs must be zero or positive") in
  let max_payload = List.fold_left (fun n handle -> max n (FormatExtension.payload_limit handle))
    0 (SemanticFormats.local_enabled ()) in
  let source_headroom = if max_payload = 0 then None else
    Some {SemanticAdmission.payload_bytes=8 * max_payload + 262144;descriptors=8} in
  let inflight = match Prefs.read max_inflight with
    | 0 -> count + (if source_headroom = None then 0 else 1)
    | value when value > 0 -> value
    | _ -> raise (Util.Fatal "semanticmaxinflight must be zero or positive") in
  let mib = Prefs.read payload_budget and descriptors = Prefs.read descriptor_budget in
  if mib <= 0 || mib > max_int / 1048576 then
    raise (Util.Fatal "semanticpayloadbudget must be a positive representable MiB budget");
  if descriptors <= 0 then raise (Util.Fatal "semanticdescriptorbudget must be positive");
  begin match source_headroom with
  | Some cost when inflight < 2 || cost.SemanticAdmission.payload_bytes > (mib * 1048576) / 2 ||
                   descriptors < 32 ->
      raise (Util.Fatal "Semantic resource budgets must fit one consumer and one reserved source transaction")
  | _ -> () end;
  if descriptors < 24 then
    raise (Util.Fatal "semanticdescriptorbudget must fit a 24-credit publication reservation");
  let consumer_payload = max 1048576 (8 * max_payload + 262144) in
  let source_payload = match source_headroom with None -> 0 | Some cost -> cost.SemanticAdmission.payload_bytes in
  if consumer_payload > mib * 1048576 - source_payload then
    raise (Util.Fatal "Semantic payload budget must fit a publication workspace and reserved source");
  (n,count,inflight,mib,descriptors,max_payload,io_jobs,source_headroom)
let resource_gate () =
  let n,_,inflight,mib,descriptors,max_payload,io_jobs,source_headroom = settings () in
  let config = n,inflight,mib,descriptors,max_payload,io_jobs in
  match !resource_runtime with
  | Some (gate,existing) when existing = config -> gate
  | Some _ -> raise (Util.Fatal "Restart Unison to change its semantic resource budgets")
  | None ->
      let gate = SemanticAdmission.create ~source_headroom ~max_transactions:inflight
        ~max_payload_bytes:(mib * 1048576) ~max_descriptors:descriptors ~max_pending:4096 in
      resource_runtime := Some (gate,config); gate
let get () =
  let n,count,inflight,mib,descriptors,max_payload,io_jobs,_ = settings () in
  let config = n,inflight,mib,descriptors,max_payload,io_jobs in
  let admission = resource_gate () in
  match !runtime with
  | Some (t,existing) when existing = config -> t
  | Some _ -> raise (Util.Fatal "Restart Unison to change its semantic resource budgets")
  | None ->
    let supervisor,_ = helper_supervisor () in
    let io = IoAdmission.create ~per_device:io_jobs ~max_pending:4096 in
    let read_observer = if Trace.enabled "semantic-reads" then Some (fun id reads ->
      Trace.debug "semantic-reads" (fun () ->
        Util.msg "Completed semantic worker job %d primary reader delivered %Ld logical bytes in %Ld chunks (saturated=%b).\n"
          id reads.SemanticFile.logical_bytes reads.chunks reads.saturated))
      else None in
    let pool = SemanticWorkers.create_with_io ~io ~workers:count ~max_pending:4096 ~budget:supervisor in
    SemanticWorkers.set_read_observer pool read_observer;
    debug (fun () -> Util.msg
      "Semantic runtime: %d physical/fallback CPUs, %d logical CPUs, %d CPU permits, %d domains, %d transaction slots, %d MiB estimated payload, %d descriptor credits, %d jobs per filesystem\n"
      (HelperSupervisor.available_physical_cpus ()) (HelperSupervisor.available_cpus ())
      n count inflight mib descriptors io_jobs);
    let t = {supervisor;pool;cpu_budget=n;admission;io} in runtime := Some (t,config); t
let cancellations = Remote.resourceWithConnCleanup
  HelperSupervisor.cancel HelperSupervisor.cancel_and_cleanup
let with_cancellation f =
  let finished = ref false in
  let cancellation = cancellations.register (HelperSupervisor.cancellation ()) in
  try
  let rec watch_abort () =
    if !finished then return () else if Abort.isAll () then
      (HelperSupervisor.cancel cancellation; return ())
    else Lwt_unix.sleep 0.05 >>= watch_abort in
  let success result = finished := true; cancellations.release cancellation; return result in
  let failure e = finished := true; cancellations.release_noerr cancellation; fail e in
  let invoke () = Lwt.ignore_result (watch_abort ()); f cancellation in
  BorrowedWork.try_bind invoke success failure
  with error ->
    finished := true;
    cancellations.release_noerr cancellation;
    raise error
let with_admission ?reservation ?(role=SemanticAdmission.Consumer) cancellation ~payload_bytes ~descriptors f =
  BorrowedWork.catch (fun () ->
    let cost = {SemanticAdmission.payload_bytes;descriptors} in
    match reservation with
    | Some reservation ->
        if role <> SemanticAdmission.Consumer ||
           SemanticAdmission.reservation_role reservation <> SemanticAdmission.Consumer then
          invalid_arg "SemanticRuntime.with_admission: source cannot borrow a receiver reservation";
        if HelperSupervisor.is_cancelled cancellation then
          fail (Util.Transient "Semantic resource admission cancelled")
        else SemanticAdmission.with_borrow reservation ~cost f
    | None -> BorrowedWork.bind
      (fun () -> SemanticAdmission.with_lease (resource_gate ()) cancellation ~role ~cost f) (function
      | Some result -> return result
      | None -> fail (Util.Transient "Semantic resource admission cancelled")))
    (function
      | SemanticAdmission.Failed reason -> fail (Util.Transient reason)
      | e -> fail e)
let with_io_file cancellation path f =
  (* This descriptor groups cooperative endpoint-private candidates for
     scheduling. It does not pin the pathname subsequently opened by a helper
     or replace candidate-content/publication fences. *)
  let owned = ref true in
  let fd = Unix.openfile path [Unix.O_RDONLY;Unix.O_CLOEXEC;Unix.O_NONBLOCK] 0 in
  try
    let close () = if !owned then begin
      owned := false;
      try Unix.close fd with Unix.Unix_error _ -> () end in
    BorrowedWork.try_bind (fun () ->
      if (Unix.LargeFile.fstat fd).Unix.LargeFile.st_kind <> Unix.S_REG then
        raise (Unix.Unix_error (Unix.EINVAL,"filesystem I/O candidate",path));
      let devices = IoAdmission.devices_of_fds [fd] in
      BorrowedWork.bind
        (fun () -> IoAdmission.with_devices (get ()).io cancellation ~devices f) (function
      | Some result -> return result
      | None -> fail (Util.Transient "Filesystem I/O admission cancelled")))
      (fun result -> close (); return result)
      (fun e -> close (); match e with
        | IoAdmission.Failed reason -> fail (Util.Transient reason)
        | _ -> fail e)
  with e ->
    (* Guard the first closure/continuation allocations after opening too.
       Clear ownership before close so an outer failure cannot close a reused FD. *)
    if !owned then begin owned := false;
      try Unix.close fd with Unix.Unix_error _ -> () end;
    raise e
let publication_cost max_payload =
  let plan = CandidateValidators.maximum_resources (CandidateValidators.selected ()) in
  let _,budget = helper_supervisor () in
  if BackendResources.cpu_lanes plan > budget then
    raise (Util.Fatal "Backend CPU declaration exceeds the shared budget");
  let payload_bytes,descriptors = BackendResources.add_cost plan
    ~bytes:(max 1048576 (8 * max_payload + 262144)) ~descriptors:24 in
  let manifests = 2 * ValidationTreePolicy.memory_bytes () in
  if payload_bytes > max_int - manifests then
    raise (Util.Fatal "Validation publication memory accounting overflow");
  {SemanticAdmission.payload_bytes=payload_bytes+manifests;descriptors}
let make_publication_reservation () =
  let _,_,_,_,_,max_payload,_,_ = settings () in
  try SemanticAdmission.make_reservation (resource_gate ()) ~role:SemanticAdmission.Consumer
    ~cost:(publication_cost max_payload)
  with SemanticAdmission.Failed reason ->
    raise (Util.Transient ("Receiving resource admission: " ^ reason))
let admission_usage () = SemanticAdmission.usage (resource_gate ())
let with_transaction ?reservation ?(role=SemanticAdmission.Consumer) ~max_payload f =
  if max_payload <= 0 || max_payload > FormatExtension.max_payload then
    invalid_arg "SemanticRuntime.with_transaction: invalid declared payload limit";
  with_cancellation (fun cancellation ->
    let cost = match role with
      | SemanticAdmission.Source ->
          {SemanticAdmission.payload_bytes=8 * max_payload + 262144;descriptors=8}
      | SemanticAdmission.Consumer -> publication_cost max_payload in
    with_admission ?reservation ~role cancellation ~payload_bytes:cost.SemanticAdmission.payload_bytes
      ~descriptors:cost.SemanticAdmission.descriptors (fun () -> f cancellation))
