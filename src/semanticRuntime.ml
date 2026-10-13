open Lwt
type t = {supervisor:HelperSupervisor.t;pool:SemanticWorkers.t;cpu_budget:int;
          admission:SemanticAdmission.t}
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
  "estimated retained semantic payload budget in MiB"
  "Admission credits for proof and encoding buffers. This estimate is not \
   a process RSS cap and excludes external SDK memory and directory manifests."
let descriptor_budget = Prefs.createInt "semanticdescriptorbudget" 512 ~local:true
  ~category:(`Advanced `General)
  "reserved descriptor credits for semantic transactions"
  "Admission credits for semantic descriptors and worker duplicates, separate \
   from unrelated legacy transfers and external helper descriptor use."
let runtime = ref None
let debug = Trace.debug "semantic"
let get () =
  let n = match Prefs.read workers with
    | 0 -> HelperSupervisor.available_physical_cpus ()
    | n when n > 0 -> n
    | _ -> raise (Util.Fatal "semanticworkers must be zero or positive") in
  let count = min n (SemanticWorkers.recommended_workers ()) in
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
                   descriptors < 16 ->
      raise (Util.Fatal "Semantic resource budgets must fit one consumer and one reserved source transaction")
  | _ -> () end;
  let config = n,inflight,mib,descriptors,max_payload in
  match !runtime with
  | Some (t,existing) when existing = config -> t
  | Some _ -> raise (Util.Fatal "Restart Unison to change its semantic resource budgets")
  | None ->
    let supervisor = HelperSupervisor.create ~cpu_permits:n ~max_children:n ~max_pending:4096 in
    let pool = SemanticWorkers.create ~workers:count ~max_pending:4096 ~budget:supervisor in
    let admission = SemanticAdmission.create ~source_headroom ~max_transactions:inflight
      ~max_payload_bytes:(mib * 1048576) ~max_descriptors:descriptors ~max_pending:4096 in
    debug (fun () -> Util.msg
      "Semantic runtime: %d physical/fallback CPUs, %d logical CPUs, %d CPU permits, %d domains, %d transaction slots, %d MiB estimated payload, %d descriptor credits\n"
      (HelperSupervisor.available_physical_cpus ()) (HelperSupervisor.available_cpus ())
      n count inflight mib descriptors);
    let t = {supervisor;pool;cpu_budget=n;admission} in runtime := Some (t,config); t
let cancellations = Remote.resourceWithConnCleanup
  HelperSupervisor.cancel HelperSupervisor.cancel_and_cleanup
let with_cancellation f =
  let cancellation = cancellations.register (HelperSupervisor.cancellation ()) in
  let finished = ref false in
  let rec watch_abort () =
    if !finished then return () else if Abort.isAll () then
      (HelperSupervisor.cancel cancellation; return ())
    else Lwt_unix.sleep 0.05 >>= watch_abort in
  Lwt.ignore_result (watch_abort ());
  Lwt.try_bind (fun () -> f cancellation)
    (fun result -> finished := true; cancellations.release cancellation; return result)
    (fun e -> finished := true; cancellations.release_noerr cancellation; fail e)
let with_admission ?(role=SemanticAdmission.Consumer) cancellation ~payload_bytes ~descriptors f =
  Lwt.catch (fun () ->
    SemanticAdmission.with_lease (get ()).admission cancellation ~role
      ~cost:{SemanticAdmission.payload_bytes;descriptors} f >>= function
    | Some result -> return result
    | None -> fail (Util.Transient "Semantic resource admission cancelled"))
    (function
      | SemanticAdmission.Failed reason -> fail (Util.Transient reason)
      | e -> fail e)
let with_transaction ?(role=SemanticAdmission.Consumer) ~max_payload f =
  if max_payload <= 0 || max_payload > FormatExtension.max_payload then
    invalid_arg "SemanticRuntime.with_transaction: invalid declared payload limit";
  with_cancellation (fun cancellation ->
    with_admission ~role cancellation ~payload_bytes:(8 * max_payload + 262144)
      ~descriptors:8 (fun () -> f cancellation))
