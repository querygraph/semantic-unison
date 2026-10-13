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
  c#state.cleanups <- cleanup :: c#state.cleanups;
  active_cleanups := cleanup :: !active_cleanups;
  fun () ->
    cleanup.active <- false;
    c#state.cleanups <- List.filter (fun x -> x != cleanup) c#state.cleanups;
    active_cleanups := List.filter (fun x -> x != cleanup) !active_cleanups
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

let acquire t ~weight ~child c =
  if weight <= 0 || weight > t.cpu_permits then
    invalid_arg "HelperSupervisor: weight outside CPU budget";
  if List.length t.queue >= t.max_pending then
    invalid_arg "HelperSupervisor: pending queue is full";
  let ticket = { number = t.next_ticket; weight; child } in
  t.next_ticket <- t.next_ticket + 1;
  t.queue <- t.queue @ [ticket];
  let remove () =
    t.queue <- List.filter (fun x -> x.number <> ticket.number) t.queue in
  let unregister = ref (fun () -> ()) in
  unregister := register_cleanup c (fun () -> remove (); !unregister ());
  let rec wait () =
    if is_cancelled c then (remove (); !unregister (); return false)
    else if (match t.queue with x :: _ -> x.number = ticket.number | [] -> false)
         && weight <= t.cpu_permits - t.used_cpu
         && (not child || t.children < t.max_children) then begin
      remove ();
      !unregister ();
      t.used_cpu <- t.used_cpu + weight;
      if child then t.children <- t.children + 1;
      return true
    end else Lwt_unix.sleep tick >>= wait
  in
  wait ()

let release t ~weight ~child =
  t.used_cpu <- t.used_cpu - weight;
  if child then t.children <- t.children - 1

let with_cpu_permits t ~weight c f =
  acquire t ~weight ~child:false c >>= fun admitted ->
  if not admitted then return None
  else try_bind f
    (fun value -> release t ~weight ~child:false; return (Some value))
    (fun exn -> release t ~weight ~child:false; fail exn)

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
  fd : Unix.file_descr;
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

let execute c ~release limits executable arguments environment =
  let started = if Sys.win32 then 0. else monotonic_now () in
  let empty outcome =
    { outcome; status = None; stdout = ""; stderr = "";
      output_truncated = false;
      elapsed = if Sys.win32 then 0. else monotonic_now () -. started } in
  if Sys.win32 then return (empty (Failed "POSIX helper backend unavailable"))
  else
    let opened = ref [] in
    let pipe () =
      let r, w = Unix.pipe ~cloexec:true () in
      opened := r :: w :: !opened;
      r, w in
    let cleanup () = List.iter close_noerr !opened; opened := [] in
    let close fd = close_noerr fd; opened := List.filter ((<>) fd) !opened in
    let spawned =
      try
        let out_r, out_w = pipe () in
        let err_r, err_w = pipe () in
        Unix.set_nonblock out_r;
        Unix.set_nonblock err_r;
        let argv = Array.append [|executable|] arguments in
        let pid = spawn_group executable argv environment out_w err_w in
        close out_w; close err_w;
        Ok (pid, capture out_r limits.stdout_bytes, capture err_r limits.stderr_bytes)
      with exn -> cleanup (); Error exn
    in
    match spawned with
    | Error exn -> return (empty (Failed (Printexc.to_string exn)))
    | Ok (pid, out, err) ->
        let scratch = Bytes.create 16384 in
        let outcome = ref Completed in
        let terminate_at = ref None in
        let reaped = ref None in
        let reaped_at = ref 0. in
        let killed = ref false in
        let disposed = ref false in
        let unregister = ref (fun () -> ()) in
        let teardown () =
          (* A disconnected owner loop may never tick again. This exceptional
             synchronous path must kill/reap now; it does not run Lwt or wait
             through the ordinary graceful TERM timeout. *)
          if not !disposed then begin
            if !reaped = None then begin
              let owned = try ignore (exited_unreaped pid); true with
                | Unix.Unix_error (Unix.ECHILD, _, _) -> false in
              if owned then
                (try signal_group pid Sys.sigkill with Unix.Unix_error _ -> ());
              let rec reap () =
                try let _, status = Unix.waitpid [] pid in reaped := Some status
                with
                | Unix.Unix_error (Unix.EINTR, _, _) -> reap ()
                | Unix.Unix_error (Unix.ECHILD, _, _) -> () in
              reap ()
            end;
            disposed := true;
            outcome := Cancelled;
            out.eof <- true; err.eof <- true;
            cleanup ();
            !unregister ();
            release ()
          end in
        unregister := register_cleanup c teardown;
        let request_stop reason now =
          if !outcome = Completed then begin
            outcome := reason;
            terminate_at := Some (now +. limits.terminate_grace);
            signal_group pid Sys.sigterm
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
               signal_group pid Sys.sigkill; killed := true
           | _ -> ());
          if !reaped = None && exited_unreaped pid then begin
            (* Kill leftover descendants before waitpid releases the leader's
               PID, so a recycled PID cannot name an unrelated process group. *)
            (* Darwin reports EPERM, rather than ESRCH, for a group whose only
               remaining member is the exited, unreaped leader. The leader is
               already proven exited here. A trusted helper must not create
               descendants that change credentials or escape its group. *)
            (try signal_group pid Sys.sigkill with
             | Unix.Unix_error (Unix.EPERM, _, _) -> ());
            let _, status = Unix.waitpid [] pid in
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
            return result
          end else Lwt_unix.sleep tick >>= monitor
        in
        catch monitor (fun exn ->
          (* Unexpected OS failures must not leave an admitted child running.
             ECHILD means some external reaper already took ownership: never
             signal that PID's group after it may have been recycled. *)
          let lost_child = match exn with
            | Unix.Unix_error (Unix.ECHILD, _, _) -> true | _ -> false in
          if !reaped = None && not lost_child then
            (try signal_group pid Sys.sigkill with Unix.Unix_error _ -> ());
          let rec reap () =
            if !reaped <> None || lost_child then return ()
            else
              let status =
                try let p, s = Unix.waitpid [Unix.WNOHANG] pid in
                    if p = 0 then `Waiting else `Reaped s
                with
                | Unix.Unix_error (Unix.EINTR, _, _) -> `Waiting
                | Unix.Unix_error (Unix.ECHILD, _, _) -> `Lost in
              match status with
              | `Waiting -> Lwt_unix.sleep tick >>= reap
              | `Reaped s -> reaped := Some s; return ()
              | `Lost -> return () in
          reap () >>= fun () ->
          cleanup ();
          !unregister ();
          return { outcome = Failed (Printexc.to_string exn); status = !reaped;
            stdout = Buffer.contents out.buffer; stderr = Buffer.contents err.buffer;
            output_truncated = out.truncated || err.truncated;
            elapsed = monotonic_now () -. started })

let run t ~weight c ~limits ~executable ~arguments ~environment =
  validate ~limits ~executable ~arguments ~environment;
  acquire t ~weight ~child:true c >>= fun admitted ->
  if not admitted then return { outcome = Cancelled; status = None; stdout = "";
    stderr = ""; output_truncated = false; elapsed = 0. }
  else
    let released = ref false in
    let release_once () =
      if not !released then begin
        released := true; release t ~weight ~child:true
      end in
    try_bind
      (fun () -> execute c ~release:release_once limits executable arguments environment)
      (fun result -> release_once (); return result)
      (fun exn -> release_once (); fail exn)
