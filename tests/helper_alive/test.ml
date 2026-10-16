open Lwt
module H=HelperSupervisor
let check b s = if not b then failwith s
let () =
 let budget=H.create ~cpu_permits:2 ~max_children:2 ~max_pending:4 in
 let limits:H.limits={timeout=3.;terminate_grace=0.1;stdout_bytes=1024;stderr_bytes=1024} in
 let groups=ref [] and samples=ref [] in
 let alive pid tick =
   check(pid>0 && Float.is_finite tick && tick>=0.) "invalid live observation";
   samples:=(pid,tick)::!samples in
 let invoke ?observe_alive () = H.run ?observe_alive ~observe_group:(fun n -> groups:=n::!groups)
   budget ~weight:1 (H.cancellation ()) ~limits ~executable:"/bin/sleep"
   ~arguments:[|"0.2"|] ~environment:[||] in
 let a=invoke ~observe_alive:alive () and b=invoke ~observe_alive:alive () in
 let a,b=Lwt_unix.run(a >>= fun a -> b >>= fun b -> return (a,b)) in
 let verify result = check(result.H.outcome=H.Completed && result.status=Some(Unix.WEXITED 0)) "sleep helper failed";
   match result.child_pid with Some pid -> pid | None -> failwith "helper PID missing" in
 let pa=verify a and pb=verify b in
 check(pa<>pb) "helper identities reused";
 let span pid =
   let times=List.filter_map(fun (p,t) -> if p=pid then Some t else None)(List.rev !samples) in
   check(List.length times>=2) "insufficient nonterminal samples";
   let rec ordered = function x::(y::_ as rest) -> check(x<=y) "clock reversed";ordered rest | _ -> () in
   ordered times; List.hd times,List.hd(List.rev times) in
 let af,al=span pa and bf,bl=span pb in
 check(min al bl > max af bf) "no observed live-helper overlap";
 let count=List.length !samples in
 ignore(verify(Lwt_unix.run(invoke ())));
 check(List.length !samples=count) "default run emitted live samples";
 check(!groups=[Some 0;Some 0;Some 0]) "helper group census incomplete";
 check(H.usage budget=(0,0)) "helper permits or child slots leaked";
 Printf.printf "PASS3 reaped helpers; common-clock live overlap %.6f seconds; %d samples; default observer absent\n%!"
   (min al bl -. max af bf) count
