open Lwt
type cost = { payload_bytes : int; descriptors : int }
type role = Source | Consumer
type usage = {
  transactions : int; pending : int; payload_bytes : int; descriptors : int;
  peak_transactions : int; peak_payload_bytes : int; peak_descriptors : int;
}
type state = Fresh | Pending | Held | Retiring | Retired
type t = {
  max_transactions : int; max_payload_bytes : int;
  max_descriptors : int; max_pending : int;
  source_headroom : cost option;
  mutable transactions : int; mutable payload_bytes : int;
  mutable descriptors : int; mutable peak_transactions : int;
  mutable peak_payload_bytes : int; mutable peak_descriptors : int;
  mutable pending : int;
  mutable sources : reservation list; mutable consumers : reservation list;
  mutable pumping : bool; mutable scheduled : bool;
}
and reservation = {
  gate : t; role : role; cost : cost;
  reply : bool Lwt.t; granted : bool Lwt.t; declined : bool Lwt.t;
  mutable state : state; mutable unregister : unit -> unit;
  mutable borrowing : bool;
}
exception Failed of string
let create ~(source_headroom:cost option) ~max_transactions ~max_payload_bytes ~max_descriptors ~max_pending =
  if max_transactions <= 0 || max_payload_bytes <= 0 || max_descriptors <= 0 || max_pending <= 0 then
    invalid_arg "SemanticAdmission.create: positive limits required";
  begin match source_headroom with
  | Some cost when cost.payload_bytes < 0 || cost.descriptors < 0 ||
      max_transactions < 2 || cost.payload_bytes > max_payload_bytes / 2 ||
      cost.descriptors > max_descriptors / 2 ->
      invalid_arg "SemanticAdmission.create: budgets must fit a consumer and reserved source"
  | _ -> () end;
  {max_transactions;max_payload_bytes;max_descriptors;max_pending;source_headroom;
   transactions=0;payload_bytes=0;descriptors=0;peak_transactions=0;
   peak_payload_bytes=0;peak_descriptors=0;pending=0;sources=[];consumers=[];pumping=false;scheduled=false}
let usage t =
  {transactions=t.transactions;pending=t.pending;
   payload_bytes=t.payload_bytes;descriptors=t.descriptors;
   peak_transactions=t.peak_transactions;peak_payload_bytes=t.peak_payload_bytes;
   peak_descriptors=t.peak_descriptors}
let headroom t = function Source -> None | Consumer -> t.source_headroom
let fits t role (cost:cost) =
  let transactions,payload,descriptors = match headroom t role with
    | None -> 0,0,0 | Some cost -> 1,cost.payload_bytes,cost.descriptors in
  t.transactions < t.max_transactions - transactions &&
  cost.payload_bytes <= t.max_payload_bytes - payload - t.payload_bytes &&
  cost.descriptors <= t.max_descriptors - descriptors - t.descriptors
let reserve t (cost:cost) =
  t.transactions <- t.transactions + 1;
  t.payload_bytes <- t.payload_bytes + cost.payload_bytes;
  t.descriptors <- t.descriptors + cost.descriptors;
  t.peak_transactions <- max t.peak_transactions t.transactions;
  t.peak_payload_bytes <- max t.peak_payload_bytes t.payload_bytes;
  t.peak_descriptors <- max t.peak_descriptors t.descriptors
let noop () = ()
let unregister r =
  let cleanup = r.unregister in
  r.unregister <- noop;
  (* HelperSupervisor marks its observer inactive before allocating list
     removal. Failure here cannot authorize another grant or debit. *)
  try cleanup () with _ -> ()
let rec trim = function
  | r :: rest when r.state <> Pending -> trim rest
  | queue -> queue
let dispatch t =
  (* Allocate the pump closures before publishing its reentrancy latch. No
     option constructor separates removing a queued owner from its debit. *)
  let rec drain () =
    t.sources <- trim t.sources;
    t.consumers <- trim t.consumers;
    match t.sources with
    | ticket :: rest when fits t Source ticket.cost ->
        t.sources <- rest; grant ticket
    | _ -> match t.consumers with
        | ticket :: rest when fits t Consumer ticket.cost ->
            t.consumers <- rest; grant ticket
        | _ -> ()
  and grant ticket =
    ticket.state <- Held;
    t.pending <- t.pending - 1;
    reserve t ticket.cost;
    unregister ticket;
    (* A reply observer can throw after the grant is already published. Keep
       draining ready owners before propagating that first exception; otherwise
       an unrelated waiter can remain asleep with free capacity and no pump. *)
    (try Lwt.wakeup_from ticket.reply ticket.granted; drain ()
     with error -> (try drain () with _ -> ()); raise error) in
  (* wakeup_from may execute owner continuations synchronously. Reentrant
     retirement/cancellation updates the queues observed by the next drain. *)
  if not t.pumping then begin
    t.pumping <- true;
    match drain () with
    | () -> t.pumping <- false
    | exception error -> t.pumping <- false; raise error
  end
let request_dispatch t =
  (* Connection cleanup cancels a group of tokens synchronously. Starting a
     waiter from an earlier token's callback could create resources after their
     connection-close registry was already swept. Defer starts until the owner
     yields; queued tickets still disappear synchronously on cancellation. *)
  if not t.scheduled then begin
    let schedule () =
      t.scheduled <- true;
      try Lwt.ignore_result (Lwt_unix.yield () >>= fun () ->
        t.scheduled <- false; dispatch t; return ())
      with error -> t.scheduled <- false; raise error in
    try schedule () with error ->
      (* One finite allocation failure must not strand already queued owners.
         A partly installed first pump and this retry may both run; dispatch
         is reentrant-safe. Persistent allocation failure remains unqualified. *)
      (try schedule () with _ -> ());
      raise error
  end
let release t (cost:cost) =
  t.transactions <- t.transactions - 1;
  t.payload_bytes <- t.payload_bytes - cost.payload_bytes;
  t.descriptors <- t.descriptors - cost.descriptors;
  request_dispatch t
(* The caller owns this handle before any debit, queue publication or native
   open. In particular, acquisition failure can always retire the same handle. *)
let make_reservation t ~role ~(cost:cost) =
  let transactions,payload,descriptors = match headroom t role with
    | None -> 0,0,0 | Some cost -> 1,cost.payload_bytes,cost.descriptors in
  if cost.payload_bytes < 0 || cost.descriptors < 0 ||
     t.max_transactions <= transactions ||
     cost.payload_bytes > t.max_payload_bytes - payload ||
     cost.descriptors > t.max_descriptors - descriptors then
    raise (Failed "semantic reservation exceeds the configured resource budget");
  (match role,t.source_headroom with
   | Source,Some headroom when cost.payload_bytes > headroom.payload_bytes ||
       cost.descriptors > headroom.descriptors ->
       raise (Failed "source reservation exceeds its declared service headroom")
   | _ -> ());
  {gate=t;role;cost;reply=Lwt.wait ();granted=Lwt.return true;declined=Lwt.return false;
   state=Fresh;unregister=(fun () -> ());borrowing=false}
let reservation_cost r = r.cost
let reservation_role r = r.role
let is_held r = r.state = Held
let retire r =
  match r.state with
  | Retired | Retiring -> ()
  | Fresh -> r.state <- Retired
  | Pending ->
      (* Logical revocation is allocation-free. The pump drops leading
         tombstones; a later acquire compacts before publishing a new cell. *)
      r.state <- Retired;
      r.gate.pending <- r.gate.pending - 1;
      unregister r;
      (* Settle this owner's reply even if scheduling a sibling pump fails;
         a throwing reply observer must still schedule that deferred pump. *)
      (try Lwt.wakeup_from r.reply r.declined; request_dispatch r.gate
       with error -> (try request_dispatch r.gate with _ -> ()); raise error)
  | Held ->
      r.state <- Retiring;
      if not r.borrowing then begin
        r.state <- Retired;
        release r.gate r.cost
      end
let acquire r cancellation =
  if r.state <> Fresh then invalid_arg "SemanticAdmission.acquire: single-use reservation";
  let t = r.gate in
  (* Build both compacted lists before publishing either one. No descriptor
     or budget debit is owned by a fresh request at this allocation boundary. *)
  let sources = List.filter (fun r -> r.state = Pending) t.sources
  and consumers = List.filter (fun r -> r.state = Pending) t.consumers in
  t.sources <- sources; t.consumers <- consumers;
  if HelperSupervisor.is_cancelled cancellation then
    (retire r; r.declined)
  else if (match r.role with Source -> t.sources = [] | Consumer -> t.consumers = []) &&
          fits t r.role r.cost then begin
    (* [granted] and the caller's cleanup owner were allocated before debit. *)
    r.state <- Held; reserve t r.cost; r.granted
  end else if t.pending >= t.max_pending then
    fail (Failed "semantic admission queue is full")
  else begin
    (* Prepare the queue cell and cancellation observer before publishing it.
       on_cancel can call back immediately; do not then publish a retired entry. *)
    let queue = match r.role with
      | Source -> t.sources @ [r] | Consumer -> t.consumers @ [r] in
    r.state <- Pending;
    t.pending <- t.pending + 1;
    try
      r.unregister <- HelperSupervisor.on_cancel cancellation (fun () ->
        if r.state = Pending then retire r);
      if r.state = Pending then
        (match r.role with Source -> t.sources <- queue | Consumer -> t.consumers <- queue);
      r.reply
    with error -> retire r; raise error
  end
let finish_borrow r =
  if r.borrowing then begin
    r.borrowing <- false;
    if r.state = Retiring then begin
      r.state <- Retired;
      release r.gate r.cost
    end
  end
let with_borrow r ~(cost:cost) f =
  if r.state <> Held then fail (Failed "semantic reservation is not available for borrowing")
  else if r.borrowing then fail (Failed "semantic reservation already has an active workspace")
  else if cost.payload_bytes < 0 || cost.descriptors < 0 ||
          cost.payload_bytes > r.cost.payload_bytes || cost.descriptors > r.cost.descriptors then
    fail (Failed "semantic workspace exceeds its retained reservation")
  else begin
    let success value = finish_borrow r; return value in
    let failure error = (try finish_borrow r with _ -> ()); fail error in
    let invoke () =
      r.borrowing <- true; f () in
    BorrowedWork.try_bind invoke success failure
  end
let with_lease t cancellation ~role ~cost f =
  let r = make_reservation t ~role ~cost in
  let cleanup error = (try retire r with _ -> ()); fail error in
  try BorrowedWork.try_bind (fun () -> acquire r cancellation)
    (fun admitted ->
      if not admitted || HelperSupervisor.is_cancelled cancellation then
        (retire r; return None)
      else BorrowedWork.try_bind (fun () -> with_borrow r ~cost f)
        (fun result -> retire r; return (Some result)) cleanup)
    cleanup
  with error -> cleanup error
