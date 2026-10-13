open Lwt
module Devices = Set.Make (Int)

type usage = {
  active_jobs : int; pending : int; peak_jobs : int; peak_per_device : int;
  devices : (int * int) list;
}
type ticket = {
  devices : int list;
  reply : bool Lwt.t;
  mutable waiting : bool;
  mutable unregister : unit -> unit;
}
type t = {
  per_device : int; max_pending : int;
  mutable active_jobs : int;
  mutable peak_jobs : int; mutable peak_per_device : int;
  mutable devices : (int * int) list;
  mutable queue : ticket list;
  mutable pumping : bool; mutable scheduled : bool;
}
exception Failed of string

let create ~per_device ~max_pending =
  if per_device <= 0 || max_pending <= 0 then
    invalid_arg "IoAdmission.create: positive limits required";
  {per_device;max_pending;active_jobs=0;peak_jobs=0;peak_per_device=0;
   devices=[];queue=[];pumping=false;scheduled=false}

let usage t =
  {active_jobs=t.active_jobs;pending=List.length t.queue;peak_jobs=t.peak_jobs;
   peak_per_device=t.peak_per_device;devices=t.devices}

let normalize devices =
  let devices = List.sort_uniq Int.compare devices in
  match devices with
  | [_] | [_;_] -> devices
  | _ -> invalid_arg "IoAdmission: one or two distinct device keys required"

let devices_of_fds fds =
  match fds with
  | [_] | [_;_] -> normalize (List.map (fun fd ->
      (Unix.LargeFile.fstat fd).Unix.LargeFile.st_dev) fds)
  | _ -> invalid_arg "IoAdmission.devices_of_fds: one or two descriptors required"

let count t device = match List.assoc_opt device t.devices with
  | None -> 0 | Some count -> count
let fits t devices = List.for_all (fun device -> count t device < t.per_device) devices
let conflicts blocked devices = List.exists (fun device -> Devices.mem device blocked) devices
let add_devices blocked devices = List.fold_left (fun set device -> Devices.add device set) blocked devices

(* Build the new ledger before changing any accounting state. Idle entries are
   removed on release; no device history outlives the active jobs using it. *)
let updated_ledger ledger devices delta =
  let ledger = List.fold_left (fun ledger device ->
    let previous = match List.assoc_opt device ledger with None -> 0 | Some n -> n in
    let next = previous + delta in
    assert (next >= 0);
    let rest = List.remove_assoc device ledger in
    if next = 0 then rest else (device,next) :: rest) ledger devices in
  List.sort (fun (a,_) (b,_) -> Int.compare a b) ledger

let reserve t devices =
  let ledger = updated_ledger t.devices devices 1 in
  t.devices <- ledger;
  t.active_jobs <- t.active_jobs + 1;
  t.peak_jobs <- max t.peak_jobs t.active_jobs;
  List.iter (fun (_,count) -> t.peak_per_device <- max t.peak_per_device count) ledger

(* A later ticket may pass only if disjoint from all earlier blocked tickets.
   This prevents a stream of A-only jobs from starving an older A+B request. *)
let select t =
  let rec scan blocked before = function
    | [] -> None
    | (ticket:ticket) :: rest ->
        if not (conflicts blocked ticket.devices) && fits t ticket.devices then
          Some (ticket, List.rev_append before rest)
        else scan (add_devices blocked ticket.devices) (ticket :: before) rest
  in scan Devices.empty [] t.queue

let dispatch t =
  if not t.pumping then begin
    t.pumping <- true;
    let first_error = ref None in
    let rec drain () = match select t with
      | None -> ()
      | Some (ticket,remaining) ->
          reserve t ticket.devices;
          t.queue <- remaining;
          ticket.waiting <- false;
          ticket.unregister ();
          (* A throwing result observer must not strand admissible siblings.
             Reentrant release/enqueue is observed by the next fresh scan. *)
          (try Lwt.wakeup ticket.reply true with error ->
             if !first_error = None then first_error := Some error);
          drain () in
    (match drain () with
     | () -> t.pumping <- false
     | exception error -> t.pumping <- false; raise error);
    match !first_error with
    | None -> ()
    | Some error -> Lwt.ignore_result (Lwt_unix.yield () >>= fun () -> fail error)
  end

let request_dispatch t =
  if not t.scheduled then begin
    t.scheduled <- true;
    Lwt.ignore_result (Lwt_unix.yield () >>= fun () ->
      t.scheduled <- false; dispatch t; return ())
  end

let release t devices =
  let ledger = updated_ledger t.devices devices (-1) in
  t.devices <- ledger;
  t.active_jobs <- t.active_jobs - 1;
  assert (t.active_jobs >= 0);
  request_dispatch t

let acquire t cancellation devices =
  if HelperSupervisor.is_cancelled cancellation then return false
  else
    let blocked = List.fold_left (fun blocked (ticket:ticket) ->
      add_devices blocked ticket.devices) Devices.empty t.queue in
    if not t.scheduled && not (conflicts blocked devices) && fits t devices then
      (reserve t devices; return true)
    else if List.length t.queue >= t.max_pending then
      fail (Failed "filesystem I/O admission queue is full")
    else begin
      let ticket = {devices;reply=Lwt.wait ();waiting=true;unregister=(fun () -> ())} in
      t.queue <- t.queue @ [ticket];
      ticket.unregister <- HelperSupervisor.on_cancel cancellation (fun () ->
        if ticket.waiting then begin
          ticket.waiting <- false;
          t.queue <- List.filter (fun other -> other != ticket) t.queue;
          ticket.unregister ();
          request_dispatch t;
          Lwt.wakeup ticket.reply false
        end);
      ticket.reply
    end

let with_devices t cancellation ~devices f =
  let devices = normalize devices in
  acquire t cancellation devices >>= fun admitted ->
  if not admitted then return None
  else if HelperSupervisor.is_cancelled cancellation then
    (release t devices; return None)
  else
    let released = ref false in
    let release_once () =
      if not !released then begin release t devices; released := true end in
    try_bind f
      (fun result -> release_once (); return (Some result))
      (fun error -> release_once (); fail error)
