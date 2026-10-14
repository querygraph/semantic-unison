module H = HelperSupervisor
let contains hay needle =
  let rec loop i = i + String.length needle <= String.length hay &&
    (String.sub hay i (String.length needle) = needle || loop (i+1)) in loop 0
let require condition label = if not condition then failwith label
let () =
 let launcher = Sys.argv.(1) and probe = Sys.argv.(2) in
 let supervisor = H.create ~cpu_permits:2 ~max_children:2 ~max_pending:8 in
 let policy = {H.launcher;descriptors=12;address_space_bytes=0L} in
 let limits = {H.timeout=2.;terminate_grace=0.02;stdout_bytes=8192;stderr_bytes=8192} in
 let run ?argv0 ?(policy=policy) ?(limits=limits) cancellation args =
  Lwt_unix.run (H.run ?argv0 ~process_limits:policy supervisor ~weight:1 cancellation
    ~limits ~executable:probe ~arguments:args ~environment:[|"LIMIT_ENV=literal $ ` ; spaces"|]) in
 let check result = require (result.H.outcome=H.Completed && result.status=Some (Unix.WEXITED 0)) result.stderr;
  require (contains result.stdout "LIMIT 12 12\n") "hard descriptor readback";
  require (contains result.stdout "GROUP 1\n") "exec changed PID/process group";
  require (H.usage supervisor=(0,0)) "unsettled supervisor" in
 let result=run (H.cancellation ()) [|"opens"|] in check result;
 require (contains result.stdout "OPEN 9 ERR 24\n") "descriptor cap was not enforced";
 let result=run (H.cancellation ()) [|"raise"|] in check result;
 require (contains result.stdout "RAISE -1 ERR 1\n") "hard cap could be raised";
 let result=run ~argv0:"literal argv zero" (H.cancellation ()) [|"args";"a b";"$x;`q`";""|] in check result;
 require (contains result.stdout "ARG 0 17 6c69746572616c2061726776207a65726f\n") "argv0 changed";
 require (contains result.stdout "ARG 2 3 612062\n" && contains result.stdout "ARG 4 0 \n") "literal argv changed";
 require (contains result.stdout "ENV literal $ ` ; spaces\n") "environment changed";
 let result=run ~argv0:"" (H.cancellation ()) [|"args"|] in check result;
 require (contains result.stdout "ARG 0 0 \n") "empty argv0 changed";
 let result=run (H.cancellation ()) [|"descendant"|] in check result;
 require (contains result.stdout "CHILD 12 12\n") "descendant did not inherit hard limit";
 let result=run ~limits:{limits with timeout=0.05} (H.cancellation ()) [|"busy"|] in
 require (result.outcome=H.Timed_out && H.usage supervisor=(0,0)) "limited child timeout/reap";
 let cancellation=H.cancellation () in
 let pending=H.run ~process_limits:policy supervisor ~weight:1 cancellation ~limits
   ~executable:probe ~arguments:[|"busy"|] ~environment:[||] in
 let cancelled = Lwt.bind (Lwt_unix.sleep 0.05) (fun () -> H.cancel cancellation;pending) in
 let result=Lwt_unix.run cancelled in require (result.outcome=H.Cancelled && H.usage supervisor=(0,0)) "limited child cancel/reap";
 let result=run ~limits:{limits with stdout_bytes=16} (H.cancellation ()) [|"flood"|] in
 require (result.outcome=H.Output_limit && H.usage supervisor=(0,0)) "limited child output/reap";
 List.iter (fun policy ->
   let rejected=try ignore (run ~policy (H.cancellation ()) [|"opens"|]);false with Invalid_argument _ -> true in
   require (rejected && H.usage supervisor=(0,0)) "invalid policy acquired resources")
   [{policy with descriptors=2};{policy with descriptors=(-1)};
    {policy with descriptors=0};{policy with launcher="relative"};{policy with address_space_bytes=(-1L)}];
 print_endline "PASS13 native limited-helper supervisor controls"
