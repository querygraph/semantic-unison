(* Private test controls. Promise identity is observed, never decoded. *)
exception Primary_waiter
exception Secondary_waiter
let target : Obj.t option ref = ref None
let attempts = ref 0
let failures = ref 0
let selected = ref "normal"
let timers = ref 0
let timer_failures = ref 0
let native_pids : (unit -> int list) ref = ref (fun () -> [])
let configure ?(timer_errors=0) phase =
  selected := phase; target := None; attempts := 0; failures := 0;
  timers := timer_errors; timer_failures := 0
let watch phase promise =
  if !selected = phase && !target = None then begin
    if !native_pids () = [] then failwith "waiter watch installed before actual child spawn";
    target := Some (Obj.repr promise)
  end;
  promise
let before_add_waiter promise = match !target with
  | Some watched when watched == promise ->
      incr attempts;
      if !attempts = 1 then (incr failures; raise Primary_waiter)
      else if !attempts = 2 then (incr failures; raise Secondary_waiter)
  | _ -> ()
let before_sleep () =
  if !failures >= 2 && !timers > 0 then begin
    decr timers; incr timer_failures; raise Secondary_waiter
  end

external pid_count : unit -> int = "validation_fixture_pid_count"
external pid_at : int -> int = "validation_fixture_pid_at"
external reset_native : unit -> unit = "validation_fixture_reset"
let pids () = List.init (pid_count ()) pid_at
let () = native_pids := pids
