open Lwt
module H = HelperSupervisor
module W = SemanticWorkers
module A = SemanticAdmission
module V = DngValidation
external wall : unit -> float = "adobe_benchmark_wall"
external parent_cpu : unit -> float = "adobe_benchmark_parent_cpu"
external children_cpu : unit -> float = "adobe_benchmark_children_cpu"

let quote value =
  let buffer = Buffer.create (String.length value + 2) in
  Buffer.add_char buffer '"';
  String.iter (function
    | '"' -> Buffer.add_string buffer "\\\""
    | '\\' -> Buffer.add_string buffer "\\\\"
    | '\n' -> Buffer.add_string buffer "\\n"
    | '\r' -> Buffer.add_string buffer "\\r"
    | '\t' -> Buffer.add_string buffer "\\t"
    | c when Char.code c < 32 -> Buffer.add_string buffer (Printf.sprintf "\\u%04x" (Char.code c))
    | c -> Buffer.add_char buffer c) value;
  Buffer.add_char buffer '"'; Buffer.contents buffer

let () =
  if Array.length Sys.argv <> 9 && Array.length Sys.argv <> 10 then
    failwith "candidate sha256 bytes driver driver-sha256 build-id CPU-budget jobs [deadline-seconds]";
  let candidate = Sys.argv.(1) and candidate_hash = Sys.argv.(2)
  and candidate_size = Int64.of_string Sys.argv.(3) and executable = Sys.argv.(4)
  and executable_hash = Sys.argv.(5) and build_id = Sys.argv.(6)
  and permits = int_of_string Sys.argv.(7) and count = int_of_string Sys.argv.(8) in
  let seconds = if Array.length Sys.argv = 10 then float_of_string Sys.argv.(9) else 300. in
  if permits < 1 || permits > 128 || count < 1 || count > 4096 then
    invalid_arg "benchmark CPU/job counts exceed bounds";
  if not (Float.is_finite seconds) || seconds <= 0. || seconds > 3600. then
    invalid_arg "benchmark deadline must be finite, positive and at most 3600 seconds";
  let domains = min permits (W.recommended_workers ()) in
  let budget = H.create ~cpu_permits:permits ~max_children:permits ~max_pending:4096 in
  let pool = W.create ~workers:domains ~max_pending:4096 ~budget in
  (* Match validation-only Runtime admission: no semantic source headroom,
     domains transaction slots and the same estimated per-file credits. *)
  let admission = A.create ~source_headroom:None ~max_transactions:domains
    ~max_payload_bytes:536870912 ~max_descriptors:512 ~max_pending:4096 in
  let cancellation = H.cancellation () in
  let inspect path =
    let fd = Unix.openfile path [Unix.O_RDONLY; Unix.O_CLOEXEC] 0 in
    BorrowedWork.try_bind (fun () -> W.digest pool cancellation fd)
      (fun result ->
        Unix.close fd;
        match result with
        | None -> failwith "benchmark digest cancelled"
        | Some result ->
            let stats = result.W.stats in
            return { V.sha256 = SemanticHash.hex result.W.digest;
              size = stats.Unix.LargeFile.st_size;
              identity = Printf.sprintf "%d:%d:%Ld:%.17g:%.17g:%d:%d"
                stats.Unix.LargeFile.st_dev stats.Unix.LargeFile.st_ino stats.Unix.LargeFile.st_size
                stats.Unix.LargeFile.st_mtime stats.Unix.LargeFile.st_ctime
                stats.Unix.LargeFile.st_perm stats.Unix.LargeFile.st_nlink })
      (fun exception_ -> Unix.close fd; fail exception_) in
  let tool = Some {V.executable; executable_sha256 = executable_hash; build_id;
    arguments = [||]; environment = [|"LANG=C"; "LC_ALL=C"; "PATH=/usr/bin:/bin"|];
    cpu_weight = 1;
    limits = {H.timeout = 300.; terminate_grace = 2.; stdout_bytes = 16384; stderr_bytes = 262144}} in
  let validate index =
    A.with_lease admission cancellation ~role:A.Consumer
      ~cost:{A.payload_bytes = 1048576; descriptors = 8}
      (fun () ->
        inspect candidate >>= fun expected ->
        if expected.V.sha256 <> candidate_hash || expected.V.size <> candidate_size then
          failwith "independent fixture identity mismatch";
        V.validate budget cancellation ~policy:V.Require ~tool ~inspect ~candidate ~expected
        >>= function
        | V.Passed receipt when receipt.V.report.raw_digest = V.Valid ->
            return (index, receipt)
        | V.Rejected (reason, _) | V.Warning (reason, _) -> failwith reason
        | _ -> failwith "benchmark requires a valid raw digest receipt")
    >>= function Some result -> return result | None -> failwith "benchmark admission cancelled" in
  let signal_cancelled = Atomic.make false in
  let handler = Sys.Signal_handle (fun _ -> Atomic.set signal_cancelled true) in
  let previous_term = Sys.signal Sys.sigterm handler
  and previous_int = Sys.signal Sys.sigint handler in
  let deadline = wall () +. seconds in
  let watching = ref true and peak_children = ref 0 and peak_cpu = ref 0 in
  let rec watch () =
    if Atomic.get signal_cancelled || wall () >= deadline then H.cancel cancellation;
    let cpu, children = H.usage budget in
    peak_children := max !peak_children children; peak_cpu := max !peak_cpu cpu;
    if !watching then Lwt_unix.sleep 0.001 >>= watch else return () in
  let start_parent = parent_cpu () and start_children = children_cpu () and start_wall = wall () in
  let watcher = watch () in
  let first_error = ref None in
  let remember error =
    (match !first_error with None -> first_error := Some error | Some _ -> ());
    H.cancel cancellation in
  let outcome = try Ok (Lwt_unix.run
    (BorrowedWork.all ~on_error:remember
       (List.init count (fun index () ->
         BorrowedWork.catch (fun () -> validate index)
           (fun error -> remember error; fail error))))) with error -> Error error in
  let elapsed_wall = wall () -. start_wall and elapsed_parent = parent_cpu () -. start_parent
  and elapsed_children = children_cpu () -. start_children in
  watching := false;
  Lwt_unix.run watcher;
  let workers = W.usage pool and resources = A.usage admission in
  Lwt_unix.run (W.shutdown pool);
  Sys.set_signal Sys.sigterm previous_term;
  Sys.set_signal Sys.sigint previous_int;
  let cpu, children = H.usage budget in
  if cpu <> 0 || children <> 0 ||
     workers.W.pending <> 0 || workers.W.running <> 0 ||
     resources.A.transactions <> 0 || resources.A.pending <> 0 ||
     resources.A.payload_bytes <> 0 || resources.A.descriptors <> 0 ||
     !peak_cpu > permits || !peak_children > permits then failwith "benchmark resources leaked";
  let results = match !first_error,outcome with
    | Some error,_ -> raise error | None,Error error -> raise error
    | None,Ok results -> results in
  if List.length results <> count then failwith "benchmark result count differs";
  let receipts = List.map (fun (index, receipt) ->
    let report = receipt.V.report and process = receipt.V.process in
    if report.V.candidate_sha256 <> candidate_hash || report.V.candidate_size <> candidate_size ||
       receipt.V.executable_sha256 <> executable_hash || receipt.V.build_id <> build_id ||
       report.V.errors <> 0 || process.H.outcome <> H.Completed ||
       process.H.status <> Some (Unix.WEXITED 0) || process.H.output_truncated then
      failwith "benchmark receipt incorrect";
    Printf.sprintf
      "{\"job\":%d,\"stdout\":%s,\"stderr\":%s,\"warnings\":%d,\"supervisor_elapsed_seconds\":%.9f}"
      index (quote process.H.stdout) (quote process.H.stderr) report.V.warnings process.H.elapsed) results in
  Printf.printf
    "{\"wall_seconds\":%.9f,\"parent_cpu_seconds\":%.9f,\"child_cpu_seconds\":%.9f,\"correct_receipts\":%d,\"pool_domains\":%d,\"peak_admitted_children\":%d,\"peak_cpu_permits\":%d,\"peak_hash_workers\":%d,\"peak_transactions\":%d,\"final_cpu_permits\":%d,\"final_children\":%d,\"receipts\":[%s]}\n%!"
    elapsed_wall elapsed_parent elapsed_children count domains !peak_children !peak_cpu
    workers.W.peak_running resources.A.peak_transactions cpu children (String.concat "," receipts)
