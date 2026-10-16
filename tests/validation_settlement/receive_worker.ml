(* Prepended only to the private complete SemanticWorkers source. The gate
   pauses an actual Identify callback while both production-owned FD copies
   and CPU/I/O ownership remain live. No worker is fabricated or dispatched. *)
module ValidationSettlementWorker = struct
  let next = Atomic.make 0
  let env key = match Sys.getenv_opt key with Some value -> value | None -> ""
  let write path text =
    let pending=path ^ ".pending" in
    let channel=open_out_bin pending in
    Fun.protect ~finally:(fun () -> close_out channel) (fun () -> output_string channel text)
    ; Unix.rename pending path
  let pause fd =
    match env "UNISON_VALIDATION_TEST_PHASE" with
    | "files-validation" | "directory-join" | "directory-launch" ->
        let directory=env "UNISON_VALIDATION_TEST_OWNED" in
        let number=Atomic.fetch_and_add next 1 in
        let marker=Filename.concat directory (string_of_int number ^ ".worker") in
        let stats=Unix.LargeFile.fstat fd in
        write marker (Printf.sprintf "%d:%d:%Ld\n"
          stats.Unix.LargeFile.st_dev stats.st_ino stats.st_size);
        let release=Filename.concat directory "release.workers" in
        let deadline=Unix.gettimeofday () +. 20. in
        while not (Sys.file_exists release) do
          if Unix.gettimeofday () >= deadline then failwith "private worker gate expired";
          ignore (Unix.select [] [] [] 0.002)
        done;
        let after=Unix.LargeFile.fstat fd in
        if stats.Unix.LargeFile.st_dev<>after.st_dev || stats.st_ino<>after.st_ino then
          failwith "private worker descriptor identity changed while borrowed";
        write (marker ^ ".done") (Printf.sprintf "%d:%d:%Ld\n"
          after.Unix.LargeFile.st_dev after.st_ino after.st_size)
    | _ -> ()
end
