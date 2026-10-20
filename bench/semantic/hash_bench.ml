open Lwt
module H = HelperSupervisor
module W = SemanticWorkers
external wall : unit -> float = "benchmark_wall"
external cpu : unit -> float = "benchmark_cpu"
external peak_rss : unit -> float = "benchmark_peak_rss"
external fd_count : unit -> int = "benchmark_fd_count"

let rec await = function
  | [] -> return []
  | job :: jobs -> job >>= fun result -> await jobs >>= fun rest -> return (result :: rest)

let () =
  if Array.length Sys.argv <> 6 then failwith "file expected-sha256 bytes workers jobs";
  let path = Sys.argv.(1) and expected = Sys.argv.(2) in
  let size = Int64.of_string Sys.argv.(3) in
  let workers = int_of_string Sys.argv.(4) and count = int_of_string Sys.argv.(5) in
  let baseline_fds=fd_count () in
  let observed_peak_fds=ref baseline_fds in
  let budget = H.create ~cpu_permits:workers ~max_children:workers ~max_pending:count in
  let pool = W.create ~workers ~max_pending:count ~budget in
  let logical_bytes=ref 0L and read_chunks=ref 0L and observations=ref 0
  and saturated=ref false in
  let add total n =
    if n<0L || n>Int64.sub Int64.max_int !total then saturated:=true
    else total:=Int64.add !total n in
  W.set_read_observer pool (Some (fun _ reads ->
    incr observations;
    saturated:= !saturated || reads.SemanticFile.saturated;
    add logical_bytes reads.logical_bytes;add read_chunks reads.chunks));
  let completion_latencies = Array.make count nan in
  let hash index =
    let submitted = wall () in
    (* Each open creates a separate file offset; dup alone would not suffice. *)
    let fd = Unix.openfile path [Unix.O_RDONLY; Unix.O_CLOEXEC] 0 in
    observed_peak_fds:=max !observed_peak_fds (fd_count ());
    try_bind (fun () -> W.digest pool (H.cancellation ()) fd)
      (fun result ->
        Unix.close fd;
        completion_latencies.(index) <- wall () -. submitted;
        return result)
      (fun exn -> Unix.close fd; fail exn) in
  let start_cpu = cpu () and start_wall = wall () in
  let jobs = List.init count hash in
  let results = Lwt_unix.run (await jobs) in
  let elapsed_wall = wall () -. start_wall and elapsed_cpu = cpu () -. start_cpu in
  let correct = List.fold_left (fun n -> function
    | Some result when SemanticHash.hex result.W.digest = expected &&
        result.stats.Unix.LargeFile.st_size = size -> n + 1
    | _ -> n) 0 results in
  if not (Array.for_all (fun seconds ->
      Float.is_finite seconds && seconds >= 0. && seconds <= elapsed_wall)
      completion_latencies) then failwith "benchmark completion latency failed";
  let usage = W.usage pool in
  Lwt_unix.run (W.shutdown pool);
  let permits, children = H.usage budget in
  let final_fds=fd_count () in
  if correct <> count || permits <> 0 || children <> 0 || usage.pending <> 0 ||
     usage.running <> 0 || usage.peak_running > workers || final_fds<>baseline_fds then failwith "benchmark invariant failed";
  if !saturated || !observations<>count ||
     size>Int64.div Int64.max_int (Int64.of_int count) ||
     !logical_bytes<>Int64.mul size (Int64.of_int count) then
    failwith "benchmark primary-reader accounting failed";
  let latency_json = String.concat ","
      (Array.to_list (Array.map (Printf.sprintf "%.9f") completion_latencies)) in
  Printf.printf
    "{\"wall_seconds\":%.9f,\"process_cpu_seconds\":%.9f,\"correct_digests\":%d,\"peak_active_workers\":%d,\"final_cpu_permits\":%d,\"process_lifetime_peak_rss_bytes\":%.0f,\"observed_fd_count_peak\":%d,\"baseline_fd_count\":%d,\"final_fd_count\":%d,\"primary_logical_read_bytes\":%Ld,\"primary_read_chunks\":%Ld,\"primary_read_observations\":%d,\"job_completion_seconds\":[%s]}\n%!"
    elapsed_wall elapsed_cpu correct usage.peak_running permits (peak_rss ()) !observed_peak_fds baseline_fds final_fds !logical_bytes !read_chunks !observations latency_json
