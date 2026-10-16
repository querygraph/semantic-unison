let check b s=if not b then failwith s
let () =
 let t=LiveSamples.create () in
 check(LiveSamples.summary t None="samples=0 valid=false first=none last=none") "empty span trusted";
 LiveSamples.add t 41 1.; LiveSamples.add t 41 2.;
 check(LiveSamples.summary t (Some 41)="samples=2 valid=true first=1 last=2") "span fields differ";
 check(LiveSamples.summary t (Some 42)="samples=2 valid=false first=none last=none") "wrong child trusted";
 List.iter(fun (pid,time) -> let t=LiveSamples.create () in LiveSamples.add t 41 1.; LiveSamples.add t pid time;
   check(not t.valid) "bad live sample accepted") [42,2.;41,0.;0,2.;41,nan;41,infinity];
 let t=LiveSamples.create () in for i=1 to 65537 do LiveSamples.add t 41 (float i) done;
 check(t.count=65536 && not t.valid) "sample budget overflow trusted";
 print_endline "PASS bounded live collector, timestamp/PID validation and child binding"
