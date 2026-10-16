(* Prepended to the private complete Files source. Qualified observation only:
   waitid(WNOWAIT) never reaps or signals a production-owned synthetic child. *)
module ValidationSettlementFiles = struct
  external exited_unreaped : int -> bool = "unsn_helper_exited_unreaped"
  type location = { root:Fspath.t; path:Path.local; directory:Fspath.t;
                    candidate:Path.local; destination:Path.local }
  let current : location option ref = ref None
  let selected root = Fspath.toString root = Lwt.validation_test_env "UNISON_VALIDATION_TEST_ROOT"
  let enter root path directory candidate destination =
    if selected root then current:=Some {root;path;directory;candidate;destination}
  let native_alive pid =
    try Unix.kill pid 0; not (exited_unreaped pid)
    with Unix.Unix_error ((Unix.ECHILD|Unix.ESRCH),_,_) -> false
  let data path =
    try let input=open_in_bin path in
      Fun.protect ~finally:(fun () -> close_in input)
        (fun () -> SemanticHash.hex (SemanticHash.string
          (really_input_string input (in_channel_length input))))
    with Unix.Unix_error _ | Sys_error _ -> "absent"
  let record phase = match !current with
    | None -> ()
    | Some location ->
        let candidate=Fspath.toString (Fspath.concat location.directory location.candidate)
        and destination=Fspath.toString (Fspath.concat location.directory location.destination) in
        let pids=Lwt.validation_test_ready () |> List.filter_map (fun (pid,_) ->
          if native_alive pid then Some (string_of_int pid) else None) in
        let archive=Update.updateArchive location.root location.path Common.NoUpdates in
        let archive=SemanticHash.hex (SemanticHash.string (Umarshal.to_string Update.marchive archive)) in
        let runtime=SemanticRuntime.get () in
        let cpu,children=HelperSupervisor.usage runtime.SemanticRuntime.supervisor in
        let admission=SemanticAdmission.usage runtime.SemanticRuntime.admission
        and io=IoAdmission.usage runtime.SemanticRuntime.io in
        Lwt.validation_test_log ["files";phase;candidate;destination;
          string_of_bool (Sys.file_exists candidate);data destination;archive;
          String.concat "," pids;string_of_int cpu;string_of_int children;
          string_of_int admission.transactions;string_of_int admission.payload_bytes;
          string_of_int admission.descriptors;string_of_int io.active_jobs;
          string_of_int (List.length (Lwt.validation_test_workers ()));
          string_of_int (SemanticWorkers.usage runtime.SemanticRuntime.pool).running]
  let ready wanted =
    let deadline=Unix.gettimeofday () +. 6. in
    let count () = if Lwt.validation_test_phase ()="execute"
      then List.length (Lwt.validation_test_ready ())
      else List.length (Lwt.validation_test_workers ()) in
    while count () < wanted do
      if Unix.gettimeofday () >= deadline then failwith "private external readiness barrier expired";
      ignore (Unix.select [] [] [] 0.002)
    done
  let () = Lwt.validation_test_set_barrier (fun count ->
    (* No event-loop pumping or reentrancy. Independent real worker domains or
       the already-spawned external child reach owned readiness files while
       this bounded private observation waits via Unix.select only. *)
    ready count;
    record "fault-before")
end
module CandidateValidation = struct
  include CandidateValidation
  let before_commit_with_reservation ~reservation ~directory ~candidate ~destination =
    Lwt.validation_test_watch "files-validation"
      (Fspath.toString (Fspath.concat directory candidate))
      (CandidateValidation.before_commit_with_reservation ~reservation ~directory ~candidate ~destination)
end
