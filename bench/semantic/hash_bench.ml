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
  let hash () =
    (* Each open creates a separate file offset; dup alone would not suffice. *)
    let fd = Unix.openfile path [Unix.O_RDONLY; Unix.O_CLOEXEC] 0 in
    observed_peak_fds:=max !observed_peak_fds (fd_count ());
    try_bind (fun () -> W.digest pool (H.cancellation ()) fd)
      (fun result -> Unix.close fd; return result)
      (fun exn -> Unix.close fd; fail exn) in
  let start_cpu = cpu () and start_wall = wall () in
  let jobs = List.init count (fun _ -> hash ()) in
  let results = Lwt_unix.run (await jobs) in
  let elapsed_wall = wall () -. start_wall and elapsed_cpu = cpu () -. start_cpu in
  let correct = List.fold_left (fun n -> function
    | Some result when SemanticHash.hex result.W.digest = expected &&
        result.stats.Unix.LargeFile.st_size = size -> n + 1
    | _ -> n) 0 results in
  let usage = W.usage pool in
  Lwt_unix.run (W.shutdown pool);
  let permits, children = H.usage budget in
  let final_fds=fd_count () in
  if correct <> count || permits <> 0 || children <> 0 || usage.pending <> 0 ||
     usage.running <> 0 || usage.peak_running > workers || final_fds<>baseline_fds then failwith "benchmark invariant failed";
  Printf.printf
    "{\"wall_seconds\":%.9f,\"process_cpu_seconds\":%.9f,\"correct_digests\":%d,\"peak_active_workers\":%d,\"final_cpu_permits\":%d,\"process_lifetime_peak_rss_bytes\":%.0f,\"observed_fd_count_peak\":%d,\"baseline_fd_count\":%d,\"final_fd_count\":%d}\n%!"
    elapsed_wall elapsed_cpu correct usage.peak_running permits (peak_rss ()) !observed_peak_fds baseline_fds final_fds
