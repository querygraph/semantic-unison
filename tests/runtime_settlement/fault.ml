(* Private metadata only. Promise identity is observed, never decoded/mutated.
   The actual worker touches only these Atomic callback barriers. *)
exception Primary_waiter
exception Secondary_waiter
let primary=Primary_waiter and secondary=Secondary_waiter
let phase=ref "normal"
let target=ref (Obj.repr ()) and captured=ref false
let attempts=ref 0 and failures=ref 0 and requested_failures=ref 2
let timer_requested=ref 0 and timer_failures=ref 0
let output_sleeping=ref (fun () -> false)
let output_captured=ref false
let entered=Array.init 2 (fun _ -> Atomic.make false)
let released=Array.init 2 (fun _ -> Atomic.make false)
let left=Array.init 2 (fun _ -> Atomic.make false)
external fd_count : unit -> int = "resource_fixture_fd_count"
let configure selected count =
  phase:=selected;captured:=false;attempts:=0;failures:=0;requested_failures:=count;
  timer_failures:=0;output_captured:=false;output_sleeping:=(fun()->false);
  timer_requested := (match Sys.getenv_opt "UNISON_SETTLEMENT_TIMER_FAULTS" with
    | None -> 0 | Some value -> int_of_string value);
  Array.iter (fun value -> Atomic.set value false) entered;
  Array.iter (fun value -> Atomic.set value false) released;
  Array.iter (fun value -> Atomic.set value false) left
let capture label promise =
  if label= !phase && not !captured then begin target:=promise;captured:=true end
let watch label work () = let promise=work () in capture label (Obj.repr promise);promise
let watch_output pending work () =
  let promise=work () in
  if not !output_captured then begin output_captured:=true;output_sleeping:=pending promise end;
  capture "rpc-output-action" (Obj.repr promise);promise
let before_sleep () =
  if !failures >= !requested_failures && !requested_failures > 0 &&
     !timer_failures < !timer_requested then begin
    incr timer_failures;raise secondary
  end
let before_add_waiter promise =
  if !captured && promise == !target then begin
    incr attempts;
    if !attempts<= !requested_failures then begin
      incr failures;if !attempts=1 then raise primary else raise secondary
    end
  end
let pause index =
  Atomic.set entered.(index) true;
  while not (Atomic.get released.(index)) do Domain.cpu_relax () done;
  Atomic.set left.(index) true
let release_all () = Array.iter (fun value -> Atomic.set value true) released
