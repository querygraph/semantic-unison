(* Private fault infrastructure only. Obj identity watches Lwt's actual promise;
   it never decodes or alters a production value. Worker-side state is Atomic. *)
exception Primary_waiter
exception Secondary_waiter
let primary = Primary_waiter
let secondary = Secondary_waiter
let phase = ref "normal"
let target = ref (Obj.repr ())
let captured = ref false
let attempts = ref 0
let failures = ref 0
let timer_remaining = ref 0
let timer_failures = ref 0
let entered = Atomic.make false
let released = Atomic.make false
let left = Atomic.make false
let slots : (unit -> int) ref = ref (fun () -> -1)
external fd_count : unit -> int = "resource_fixture_fd_count"
let configure selected timers =
  phase := selected; captured := false; attempts := 0; failures := 0;
  timer_remaining := timers; timer_failures := 0;
  Atomic.set entered false; Atomic.set released false; Atomic.set left false
let capture label promise =
  if label = !phase && not !captured then begin
    target := promise; captured := true
  end
let watch label work () =
  let promise = work () in
  capture label (Obj.repr promise); promise
let before_add_waiter promise =
  if !captured && promise == !target then begin
      incr attempts;
      if !attempts = 1 then (incr failures; raise primary)
      else if !attempts = 2 then (incr failures; raise secondary)
  end
let before_sleep () =
  if !failures=2 && !timer_remaining>0 then begin
    decr timer_remaining; incr timer_failures; raise secondary
  end
let watch_slots read = slots := read
let pause () =
  Atomic.set entered true;
  while not (Atomic.get released) do Domain.cpu_relax () done;
  Atomic.set left true
