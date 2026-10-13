(* Process-exit regression: deliberately abandon a live supervised thread. *)
let () =
  let supervisor = HelperSupervisor.create ~cpu_permits:1 ~max_children:1 ~max_pending:1 in
  ignore (HelperSupervisor.run supervisor ~weight:1 (HelperSupervisor.cancellation ())
    ~limits:{HelperSupervisor.timeout = 5.; terminate_grace = 0.05;
             stdout_bytes = 1024; stderr_bytes = 1024}
    ~executable:Sys.argv.(1) ~arguments:[|"marker"; Sys.argv.(2)|] ~environment:[||])
  (* No Lwt_unix.run. The supervisor's at_exit safeguard must kill/reap. *)
