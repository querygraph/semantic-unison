[@@@alert "-unsafe_multidomain"]
external fdcount : unit -> int = "fd_ownership_count"
let checks = ref 0 and cases = ref 0
let check yes reason = incr checks; if not yes then failwith reason
let selected = if Array.length Sys.argv > 2 then Sys.argv.(2) else "all"
let negative = Array.length Sys.argv > 3 && Sys.argv.(3) = "negative"
let root = Sys.argv.(1)
let write name bytes = let c = open_out_bin name in output_string c bytes; close_out c
let read name = let c = open_in_bin name in
  Fun.protect ~finally:(fun () -> close_in c) (fun () -> really_input_string c (in_channel_length c))
let run name f = if selected = "all" || selected = name then begin
  incr cases; let count = fdcount () in
  Printf.printf "case %s\n%!" name;
  f ();
  check (fdcount () = count) (name ^ ": owned descriptors escaped");
  check (Atomic.get Fault.domains = 0) (name ^ ": spawned domain escaped");
  Printf.printf "ok %d %s assertions=%d\n%!" !cases name !checks
end
let primary f = try f (); false with Fault.Primary -> true
let source = Filename.concat root "source" and target = Filename.concat root "target"
let initial = String.make 8192 'A'
let with_source f =
  let fd = Unix.openfile source [Unix.O_RDONLY] 0 in
  Fun.protect ~finally:(fun () -> Unix.close fd) (fun () -> f fd)
let () =
  write source initial; write target initial;
  List.iter (fun mode -> run mode (fun () -> with_source (fun fd ->
    Fault.reset mode; let count = fdcount () in
    check (primary (fun () -> SemanticFile.with_fd fd (fun _ -> ()))) "semantic primary exception changed";
    check (fdcount () = count) "semantic owned duplicate escaped";
    check ((Unix.fstat fd).Unix.st_size = 8192 && read source = initial) "semantic borrower closed/changed source";
    check (!(Fault.hits) = 1) "semantic fault did not reach its designated allocation seam")))
    ["semantic-channel";"semantic-channel-register";"semantic-record"];
  run "semantic-callback" (fun () -> with_source (fun fd ->
    Fault.reset ""; let count = fdcount () in
    check (primary (fun () -> SemanticFile.with_fd fd (fun _ -> raise Fault.Primary))) "callback primary exception changed";
    check (fdcount () = count && !(Fault.close_calls) = 1) "callback failure did not close once"));
  run "semantic-close-recycle" (fun () -> with_source (fun fd ->
    Fault.reset "semantic-close-recycle";
    let failed = try SemanticFile.with_fd fd (fun _ -> ()); false
      with Unix.Unix_error(Unix.EIO,"fixture-close",_) -> true in
    check (failed && Fault.sentinel_alive () && !(Fault.close_calls) = 1) "close failure retried a recycled descriptor";
    Fault.dispose_sentinel ()));
  run "semantic-primary-close-recycle" (fun () -> with_source (fun fd ->
    Fault.reset "semantic-close-recycle";
    check (primary (fun () -> SemanticFile.with_fd fd (fun _ -> raise Fault.Primary))) "cleanup close error replaced primary";
    check (Fault.sentinel_alive () && !(Fault.close_calls) = 1) "primary cleanup retried recycled channel FD";
    Fault.dispose_sentinel ()));
  List.iter (fun mode -> run mode (fun () ->
    let budget = HelperSupervisor.create ~cpu_permits:2 ~max_children:2 ~max_pending:8 in
    Fault.reset mode; let count = fdcount () in
    check (primary (fun () -> ignore (SemanticWorkers.create ~workers:2 ~max_pending:8 ~budget))) "pool primary exception changed";
    check (fdcount () = count) "pool pipe descriptors escaped";
    check (Atomic.get Fault.domains = 0 && !(Fault.hits) = 1) "pool failure did not join its real domains"))
    ["pool-read-flags";"pool-write-flags";"pool-shared";"pool-domain-link";"pool-reader";"pool-record";"pool-pump"];
  run "pool-close-recycle" (fun () ->
    Fault.reset "pool-close-recycle";
    let budget = HelperSupervisor.create ~cpu_permits:1 ~max_children:1 ~max_pending:8 in
    check (primary (fun () -> ignore (SemanticWorkers.create ~workers:1 ~max_pending:8 ~budget))) "pool close replaced primary";
    check (Fault.sentinel_alive () && !(Fault.close_calls) = 2) "pool pipe cleanup retried recycled FD";
    Fault.dispose_sentinel ());
  List.iter (fun mode -> run mode (fun () ->
    Fault.reset "";
    let budget = HelperSupervisor.create ~cpu_permits:1 ~max_children:1 ~max_pending:8 in
    let pool = SemanticWorkers.create ~workers:1 ~max_pending:8 ~budget in
    Fun.protect ~finally:(fun () -> if not negative then begin
      Fault.reset ""; ignore (Lwt_unix.run (SemanticWorkers.shutdown pool))
    end)
      (fun () -> with_source (fun fd ->
        let output = Unix.openfile target [Unix.O_RDWR] 0 in
        Fun.protect ~finally:(fun () -> Unix.close output) (fun () ->
          let module E = struct
            let profile = "fd-ownership-test/0"
            let inspect _ = Ok {FormatExtension.regions=[{offset=4L;length=8}]}
          end in
          let inspect path = let input = Unix.openfile path [Unix.O_RDONLY] 0 in
            Fun.protect ~finally:(fun () -> Unix.close input) (fun () ->
              SemanticFile.with_fd input (fun f -> match SemanticDelta.inspect (module E) f with Ok p -> p | Error s -> failwith s)) in
          let proof = inspect source in
          let plan = match SemanticDelta.plan ~nonce:(String.make 32 'n') ~base:proof ~target:proof with Ok p -> p | Error s -> failwith s in
          let extension = FormatExtension.trusted ~max_payload:8 (module E) in
          Fault.reset mode; let count = fdcount () in
          let failed = primary (fun () -> ignore (Lwt_unix.run (SemanticWorkers.apply_report pool (HelperSupervisor.cancellation ()) ~extension plan ~basis:fd ~output))) in
          check failed "submit primary exception changed";
          if mode = "submit-close-recycle" then begin
            check (Fault.sentinel_alive () && !(Fault.close_calls) = 2) "submit cleanup retried recycled FD";
            Fault.dispose_sentinel ()
          end;
          check (fdcount () = count) "submit owned duplicate escaped";
          check ((SemanticWorkers.usage pool).pending = 0 && HelperSupervisor.usage budget = (0,0)) "submit controller ownership escaped";
          check ((Unix.fstat fd).Unix.st_size = 8192 && (Unix.fstat output).Unix.st_size = 8192) "submit closed borrowed caller FD";
          check (!(Fault.hits) = 1) "submit fault seam not invoked")))))
    ["submit-operation";"submit-listener";"submit-monitor";"submit-admission";"submit-close-recycle"];
  run "normal-pool-file-worker" (fun () ->
    Fault.reset "";
    let budget = HelperSupervisor.create ~cpu_permits:2 ~max_children:2 ~max_pending:8 in
    let pool = SemanticWorkers.create ~workers:2 ~max_pending:8 ~budget in
    Fun.protect ~finally:(fun () -> ignore (Lwt_unix.run (SemanticWorkers.shutdown pool)))
      (fun () -> with_source (fun fd ->
        let result = Lwt_unix.run (SemanticWorkers.digest pool (HelperSupervisor.cancellation ()) fd) in
        check (match result with Some result -> result.SemanticWorkers.digest = SemanticHash.string initial | None -> false) "normal hashing changed";
        check ((SemanticWorkers.usage pool).pending = 0 && HelperSupervisor.usage budget = (0,0)) "normal job did not settle";
        check ((Unix.fstat fd).Unix.st_size = 8192) "normal job closed borrower")));
  check (!cases > 0) "no controls selected";
  Printf.printf "All %d early-FD ownership cases passed; %d assertions\n%!" !cases !checks
