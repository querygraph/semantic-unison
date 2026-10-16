external pid : unit -> int = "helper_owner_pid"
external reset_native : unit -> unit = "helper_owner_reset"
external exited_unreaped : int -> bool = "unsn_helper_exited_unreaped"
exception Primary
exception Secondary
let selected = ref 0
let secondary = ref 0
let fired = ref false
let secondary_fired = ref false
let waited = ref 0
let prematurely_released = ref false
let check_budget = ref (fun () -> true)
let sentinel = ref None
let on_publish = ref (fun () -> ())
let on_registration = ref (fun () -> ())
let registration_callback () = !on_registration ()
let publish_callback () = !on_publish ()
let hit code =
  if !selected = code && not !fired then begin
    fired := true; raise Out_of_memory
  end else if !secondary = code && not !secondary_fired then begin
    secondary_fired := true; raise Secondary
  end
let before_wait target =
  if target = pid () && not (!check_budget ()) then prematurely_released := true
let after_wait target result =
  if target = pid () && fst result = target then incr waited
let after_close descriptor =
  if !selected = 17 && not !fired && pid () > 0 then begin
    let fresh = Unix.openfile "/dev/null" [Unix.O_RDONLY; Unix.O_CLOEXEC] 0 in
    if fresh <> descriptor then begin Unix.close fresh; failwith "close control did not recycle FD" end;
    sentinel := Some fresh;
    fired := true;
    raise Out_of_memory
  end
let reset code extra budget =
  reset_native (); selected := code; secondary := extra;
  fired := false; secondary_fired := false; waited := 0;
  prematurely_released := false; check_budget := budget; sentinel := None; on_publish := (fun () -> ()); on_registration := (fun () -> ())
