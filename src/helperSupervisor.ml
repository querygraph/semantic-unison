open Lwt

external monotonic_now : unit -> float = "unsn_helper_monotonic_now"
external available_cpus : unit -> int = "unsn_helper_available_cpus"
external available_physical_cpus : unit -> int = "unsn_helper_available_physical_cpus"
external spawn_group :
  string -> string array -> string array -> Unix.file_descr -> Unix.file_descr -> int
  = "unsn_helper_spawn_group"
external exited_unreaped : int -> bool = "unsn_helper_exited_unreaped"

type cleanup = { mutable active : bool; dispose : unit -> unit }
type listener = { mutable listening : bool; notify : unit -> unit }
type cancellation_state = {
  mutable cancelled : bool; mutable cleanups : cleanup list;
  mutable listeners : listener list;
}
(* Remote's resource registry uses polymorphic hashing/equality. Object
   identity stays distinct and stable when this private state changes. *)
type cancellation = < state : cancellation_state >
let cancellation () =
  let state = { cancelled = false; cleanups = []; listeners = [] } in
  object method state = state end
let cancel c =
  if not c#state.cancelled then begin
    c#state.cancelled <- true;
    let listeners = c#state.listeners in
    c#state.listeners <- [];
    List.iter (fun listener ->
      if listener.listening then begin
        listener.listening <- false;
        try listener.notify () with _ -> ()
      end) listeners
  end
let is_cancelled c = c#state.cancelled
let on_cancel c notify =
  if is_cancelled c then (notify (); fun () -> ())
  else
    let listener = { listening = true; notify } in
    c#state.listeners <- listener :: c#state.listeners;
    fun () ->
      listener.listening <- false;
      c#state.listeners <- List.filter (fun x -> x != listener) c#state.listeners

let active_cleanups = ref []
let register_cleanup c dispose =
  let cleanup = { active = true; dispose = (fun () -> cancel c; dispose ()) } in
  let unregister () =
    cleanup.active <- false;
    c#state.cleanups <- List.filter (fun x -> x != cleanup) c#state.cleanups;
    active_cleanups := List.filter (fun x -> x != cleanup) !active_cleanups in
  (* Complete registration allocations before either registry is mutated.
     A failed constructor cannot strand an active, unreachable registration. *)
  let cancellation_cleanups = cleanup :: c#state.cleanups in
  let process_cleanups = cleanup :: !active_cleanups in
  c#state.cleanups <- cancellation_cleanups;
  active_cleanups := process_cleanups;
  unregister
let dispose_noerr cleanup =
  if cleanup.active then try cleanup.dispose () with _ -> ()
let cancel_and_cleanup c =
  cancel c;
  List.iter dispose_noerr c#state.cleanups
let () = at_exit (fun () -> List.iter dispose_noerr !active_cleanups)

type ticket = { number : int; weight : int; child : bool }
type t = {
  cpu_permits : int;
  max_children : int;
  max_pending : int;
  mutable used_cpu : int;
  mutable children : int;
  mutable next_ticket : int;
  mutable queue : ticket list;
}

let create ~cpu_permits ~max_children ~max_pending =
  if cpu_permits <= 0 || max_children <= 0 || max_pending <= 0 then
    invalid_arg "HelperSupervisor.create: limits must be positive";
  { cpu_permits; max_children; max_pending; used_cpu = 0; children = 0;
    next_ticket = 0; queue = [] }

let usage t = t.used_cpu, t.children
let tick = 0.01

let acquire t ~weight ~child ~on_admitted ~abort_pending c =
  if weight <= 0 || weight > t.cpu_permits then
    invalid_arg "HelperSupervisor: weight outside CPU budget";
  if List.length t.queue >= t.max_pending then
    invalid_arg "HelperSupervisor: pending queue is full";
  let granted = return true and rejected = return false in
  let number = t.next_ticket in
  t.next_ticket <- t.next_ticket + 1;
  let ticket = { number; weight; child } in
  let queued = ref false and revoked = ref false in
  let remove () =
    if !queued then begin
      let remaining = List.filter (fun x -> x.number <> ticket.number) t.queue in
      t.queue <- remaining;
      queued := false
    end in
  let unregister = ref (fun () -> ()) in
  let retire_pending () =
    revoked := true;
    remove ();
    !unregister () in
  let cleanup_error error =
    (try retire_pending () with _ -> ());
    (try retire_pending () with _ -> ());
    raise error in
  let rec wait () =
    try
    if !revoked || is_cancelled c then (retire_pending (); rejected)
    else if (match t.queue with x :: _ -> x.number = ticket.number | [] -> false)
         && weight <= t.cpu_permits - t.used_cpu
         && (not child || t.children < t.max_children) then begin
      remove ();
      !unregister ();
      (* The caller preallocated this nonallocating ownership assignment.
         Neither the debit nor publishing the preallocated reply allocates. *)
      on_admitted ();
      t.used_cpu <- t.used_cpu + weight;
      if child then t.children <- t.children + 1;
      granted
    end else Lwt_unix.sleep tick >>= wait
    with error -> cleanup_error error
  in
  abort_pending := retire_pending;
  try
    unregister := register_cleanup c retire_pending;
    let rec publish () =
      let previous = t.queue in
      if List.length previous >= t.max_pending then
        invalid_arg "HelperSupervisor: pending queue is full";
      let next = previous @ [ticket] in
      (* Cancellation/reentrant cleanup during constructor allocation must
         not publish a revoked ticket or restore an earlier queue snapshot. *)
      if is_cancelled c then (!unregister (); rejected)
      else if t.queue != previous then publish ()
      else begin
        t.queue <- next;
        queued := true;
        wait ()
      end in
    publish ()
  with error -> cleanup_error error

let release t ~weight ~child =
  t.used_cpu <- t.used_cpu - weight;
  if child then t.children <- t.children - 1

let with_cpu_permits t ~weight c f =
  let owns_reservation = ref false in
  let abort_pending = ref (fun () -> ()) in
  let borrowed = ref false and awaited = ref (wait ()) in
  let unregister = ref (fun () -> ()) in
  let retired = return () and cancelled = return None in
  let release_once () =
    if !owns_reservation then begin
      owns_reservation := false;
      release t ~weight ~child:false;
      (try !unregister () with _ -> ())
    end in
  let recover_settled _ = release_once (); retired in
  let recover () =
    if !owns_reservation then begin
      if not !borrowed then release_once () else
      (* A repeated allocation failure must retain this registry owner until
         another cleanup/recovery observes actual borrower settlement. *)
      try ignore (try_bind (fun () -> !awaited) recover_settled recover_settled)
      with _ -> ()
    end in
  let success value = release_once (); return (Some value) in
  let failure error = release_once (); fail error in
  let start () =
    let promise = f () in
    awaited := promise;
    borrowed := true;
    promise in
  let activate admitted =
    if not admitted then ((try !unregister () with _ -> ()); cancelled)
    else BorrowedWork.try_bind start success failure in
  let on_admitted () = owns_reservation := true in
  let acquire_owned () = acquire t ~weight ~child:false ~on_admitted ~abort_pending c in
  let acquisition_failed error =
    (try !abort_pending () with _ -> ());
    recover ();
    if not !owns_reservation then (try !unregister () with _ -> ());
    fail error in
  unregister := register_cleanup c recover;
  try try_bind acquire_owned activate acquisition_failed
  with error ->
    (try !abort_pending () with _ -> ());
    recover ();
    if not !owns_reservation then (try !unregister () with _ -> ());
    raise error

type limits = {
  timeout : float;
  terminate_grace : float;
  stdout_bytes : int;
  stderr_bytes : int;
}

type outcome = Completed | Cancelled | Timed_out | Output_limit | Failed of string
type result = {
  outcome : outcome;
  status : Unix.process_status option;
  stdout : string;
  stderr : string;
  output_truncated : bool;
  elapsed : float;
}

let finite_positive x = x > 0. && x < infinity
let contains_nul s = String.contains s '\000'
let validate ~limits ~executable ~arguments ~environment =
  if Filename.is_relative executable || contains_nul executable then
    invalid_arg "HelperSupervisor: executable must be an absolute NUL-free path";
  if Array.exists contains_nul arguments || Array.exists contains_nul environment then
    invalid_arg "HelperSupervisor: NUL in argv/environment";
  if not (finite_positive limits.timeout)
     || not (finite_positive limits.terminate_grace)
     || limits.stdout_bytes < 0 || limits.stderr_bytes < 0 then
    invalid_arg "HelperSupervisor: invalid execution limits"

let close_noerr fd = try Unix.close fd with Unix.Unix_error _ -> ()
let signal_group pid signal =
  try Unix.kill (-pid) signal with Unix.Unix_error (Unix.ESRCH, _, _) -> ()

type capture = {
  mutable fd : Unix.file_descr;
  buffer : Buffer.t;
  cap : int;
  mutable eof : bool;
  mutable truncated : bool;
}

let capture fd cap =
  { fd; cap; buffer = Buffer.create (min cap 4096); eof = false; truncated = false }

(* Never register a pending read with legacy Lwt: its Unix.close cannot remove
   read waiters. Bounded nonblocking reads plus a cooperative timer make timeout
   and cancellation cleanup independent of that limitation. *)
let drain scratch stream =
  let rec loop remaining =
    if stream.eof || remaining = 0 then ()
    else
      try
        let n = Unix.read stream.fd scratch 0 (min remaining (Bytes.length scratch)) in
        if n = 0 then stream.eof <- true
        else begin
          let keep = min n (stream.cap - Buffer.length stream.buffer) in
          Buffer.add_subbytes stream.buffer scratch 0 keep;
          if keep < n then stream.truncated <- true;
          loop (remaining - n)
        end
      with
      | Unix.Unix_error ((Unix.EAGAIN | Unix.EWOULDBLOCK), _, _) -> ()
      | Unix.Unix_error (Unix.EINTR, _, _) -> ()
  in
  loop 65536

let execute c ~release ~owner_cleanup ~owner_settled limits executable argv0 arguments environment =
  let started = if Sys.win32 then 0. else monotonic_now () in
  let empty outcome =
    { outcome; status = None; stdout = ""; stderr = "";
      output_truncated = false;
      elapsed = if Sys.win32 then 0. else monotonic_now () -. started } in
  if Sys.win32 then return (empty (Failed "POSIX helper backend unavailable"))
  else
    (* Prepare the entire owner before creating pipes or a child. Descriptor
       slots and the child PID are installed by nonallocating assignments;
       later record/closure/registry allocation can always find that owner. *)
    let descriptors = Array.make 4 Unix.stdin in
    let owns_descriptor = Array.make 4 false in
    let out = capture Unix.stdin limits.stdout_bytes
    and err = capture Unix.stdin limits.stderr_bytes in
    let argv = Array.append [|argv0|] arguments in
    let owned_pid = ref (-1) in
    let scratch = Bytes.create 16384 in
    let outcome = ref Completed in
    let terminate_at = ref None in
    let reaped = ref None in
    let reaped_at = ref 0. in
    let killed = ref false in
    let disposed = ref false in
    let unregister = ref (fun () -> ()) in
    let close index =
      if owns_descriptor.(index) then begin
        owns_descriptor.(index) <- false;
        close_noerr descriptors.(index)
      end in
    let cleanup () =
      (* A failed close or pending action must not skip the other slots. *)
      for index = 0 to 3 do try close index with _ -> () done in
    let pipe first second =
      let r, w = Unix.pipe ~cloexec:true () in
      descriptors.(first) <- r; owns_descriptor.(first) <- true;
      descriptors.(second) <- w; owns_descriptor.(second) <- true in
    let rec reap_now () =
      if !owned_pid >= 0 then
        try
          let _, status = Unix.waitpid [] !owned_pid in
          (* waitpid has released this PID. Clear ownership before the
             option allocation so failure cannot signal a recycled group. *)
          owned_pid := -1;
          reaped := Some status
        with
        | Unix.Unix_error (Unix.EINTR, _, _) -> reap_now ()
        | Unix.Unix_error (Unix.ECHILD, _, _) -> owned_pid := -1 in
    let rec owns_child () =
      if !owned_pid < 0 then false else
      try ignore (exited_unreaped !owned_pid); true with
      | Unix.Unix_error (Unix.EINTR, _, _) -> owns_child ()
      | Unix.Unix_error (Unix.ECHILD, _, _) -> owned_pid := -1; false in
    let retire () =
      disposed := true;
      outcome := Cancelled;
      out.eof <- true; err.eof <- true;
      cleanup ();
      (try !unregister () with _ -> ());
      release () in
    let teardown () =
      (* A disconnected owner loop may never tick again. This exceptional
         synchronous path must kill/reap now; it does not run Lwt or wait
         through the ordinary graceful TERM timeout. *)
      if not !disposed then begin
        (* Keep the CPU/child reservation while the owned child settles.
           A status-allocation failure after reaping still retires pipes. *)
        match
          (if owns_child () then
             (try signal_group !owned_pid Sys.sigkill with Unix.Unix_error _ -> ());
           reap_now ())
        with
        | () -> retire ()
        | exception error ->
            if !owned_pid < 0 then retire ();
            raise error
      end in
    let request_stop reason now =
      if !outcome = Completed then begin
        outcome := reason;
        terminate_at := Some (now +. limits.terminate_grace);
        if !owned_pid >= 0 then signal_group !owned_pid Sys.sigterm
      end in
    let rec monitor () =
      if !disposed then return { outcome = Cancelled; status = !reaped;
        stdout = Buffer.contents out.buffer; stderr = Buffer.contents err.buffer;
        output_truncated = out.truncated || err.truncated;
        elapsed = monotonic_now () -. started }
      else
      let now = monotonic_now () in
      (* Drain both streams each turn, even when one floods output. *)
      (try drain scratch out; drain scratch err
       with exn -> request_stop (Failed (Printexc.to_string exn)) now);
      if out.truncated || err.truncated then request_stop Output_limit now;
      if is_cancelled c then request_stop Cancelled now;
      if now -. started >= limits.timeout then request_stop Timed_out now;
      (match !terminate_at with
       | Some deadline when now >= deadline && not !killed ->
           if !owned_pid >= 0 then signal_group !owned_pid Sys.sigkill;
           killed := true
       | _ -> ());
      if !owned_pid >= 0 && exited_unreaped !owned_pid then begin
        (* Kill leftover descendants before waitpid releases the leader's
           PID, so a recycled PID cannot name an unrelated process group. *)
        (* Darwin reports EPERM, rather than ESRCH, for a group whose only
           remaining member is the exited, unreaped leader. The leader is
           already proven exited here. A trusted helper must not create
           descendants that change credentials or escape its group. *)
        (try signal_group !owned_pid Sys.sigkill with
         | Unix.Unix_error (Unix.EPERM, _, _) -> ());
        let _, status = Unix.waitpid [] !owned_pid in
        owned_pid := -1;
        reaped := Some status;
        reaped_at := now
      end;
      if !reaped <> None && (out.eof && err.eof || now -. !reaped_at >= tick *. 2.) then begin
        if not (out.eof && err.eof) then begin
          (* Escaped descendants or unread data cannot produce a successful
             complete receipt. Never wait indefinitely for their pipe EOF. *)
          out.truncated <- not out.eof || out.truncated;
          err.truncated <- not err.eof || err.truncated;
          if !outcome = Completed then outcome := Output_limit
        end;
        let result = { outcome = !outcome; status = !reaped;
          stdout = Buffer.contents out.buffer; stderr = Buffer.contents err.buffer;
          output_truncated = out.truncated || err.truncated;
          elapsed = monotonic_now () -. started } in
        cleanup ();
        !unregister ();
        disposed := true;
        return result
      end else Lwt_unix.sleep tick >>= monitor
    in
    let failed exn =
      (* Unexpected OS failures must not leave an admitted child running.
         ECHILD means some external reaper already took ownership: never
         signal that PID's group after it may have been recycled. *)
      let lost_child = match exn with
        | Unix.Unix_error (Unix.ECHILD, _, _) -> true | _ -> false in
      if lost_child then owned_pid := -1;
      (try teardown () with _ ->
         (* A later status/cleanup allocation must not hide the first error.
            Unexpected OS refusal to reap remains outside a hard deadline. *)
         if !owned_pid >= 0 then raise exn);
      (try
         return { outcome = Failed (Printexc.to_string exn); status = !reaped;
           stdout = Buffer.contents out.buffer; stderr = Buffer.contents err.buffer;
           output_truncated = out.truncated || err.truncated;
           elapsed = monotonic_now () -. started }
       with _ -> raise exn) in
    let start () =
      unregister := register_cleanup c teardown;
      pipe 0 1;
      pipe 2 3;
      out.fd <- descriptors.(0); err.fd <- descriptors.(2);
      Unix.set_nonblock out.fd; Unix.set_nonblock err.fd;
      owned_pid := spawn_group executable argv environment descriptors.(1) descriptors.(3);
      close 1; close 3;
      monitor () in
    let is_settled () =
      !owned_pid < 0 && not owns_descriptor.(0) && not owns_descriptor.(1)
      && not owns_descriptor.(2) && not owns_descriptor.(3) in
    owner_cleanup := teardown;
    owner_settled := is_settled;
    (* Legacy Lwt can also raise while installing a waiter after [start]
       has returned a running monitor. Synchronous failure must settle its
       durable owner too, before [run] returns its permits. *)
    try catch start failed with exn ->
      (try teardown () with _ ->
         if !owned_pid >= 0 then raise exn);
      raise exn

type process_limits = { launcher : string; descriptors : int; address_space_bytes : int64 }
let run ?argv0 ?process_limits t ~weight c ~limits ~executable ~arguments ~environment =
  let argv0 = match argv0 with None -> executable | Some name -> name in
  if contains_nul argv0 then invalid_arg "HelperSupervisor: NUL in argv[0]";
  validate ~limits ~executable ~arguments ~environment;
  let executable,argv0,arguments = match process_limits with
    | None -> executable,argv0,arguments
    | Some policy ->
      if Filename.is_relative policy.launcher || contains_nul policy.launcher ||
         policy.descriptors < 0 || (policy.descriptors > 0 && policy.descriptors < 3) ||
         policy.address_space_bytes < 0L ||
         (policy.descriptors = 0 && policy.address_space_bytes = 0L) then
        invalid_arg "HelperSupervisor: invalid child process limits";
      let wrapped = Array.concat [[|"--unison-helper-limits-v1";
        string_of_int policy.descriptors;Int64.to_string policy.address_space_bytes;
        "--";executable;argv0|];arguments] in
      policy.launcher,policy.launcher,wrapped in
  let owns_reservation = ref false in
  let abort_pending = ref (fun () -> ()) in
  let owner_cleanup = ref (fun () -> ()) and owner_settled = ref (fun () -> true) in
  let cancelled = return { outcome = Cancelled; status = None; stdout = "";
    stderr = ""; output_truncated = false; elapsed = 0. } in
  let release_once () =
    if !owns_reservation && !owner_settled () then begin
      owns_reservation := false;
      release t ~weight ~child:true
    end in
  let execute_owned () =
    execute c ~release:release_once ~owner_cleanup ~owner_settled limits executable argv0 arguments environment in
  let failed exn =
    (try !owner_cleanup () with _ -> ());
    release_once (); fail exn in
  let succeeded result = release_once (); return result in
  let activate admitted =
    if not admitted then cancelled else
    (* Installing the outer waiter can fail after [execute_owned] returned an
       active monitor. Its run-local owner settles only this child before the
       surrounding caller is allowed to retire CPU/resource reservations. *)
    try try_bind execute_owned succeeded failed
    with exn ->
      (try !owner_cleanup () with _ -> ());
      release_once (); raise exn in
  let on_admitted () = owns_reservation := true in
  let acquire_owned () = acquire t ~weight ~child:true ~on_admitted ~abort_pending c in
  let acquisition_failed exn =
    (try !abort_pending () with _ -> ());
    failed exn in
  try try_bind acquire_owned activate acquisition_failed
  with exn ->
    (try !abort_pending () with _ -> ());
    (try !owner_cleanup () with _ -> ());
    release_once (); raise exn
