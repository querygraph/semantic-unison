open Lwt
type cost = { payload_bytes : int; descriptors : int }
type role = Source | Consumer
type usage = {
  transactions : int; pending : int; payload_bytes : int; descriptors : int;
  peak_transactions : int; peak_payload_bytes : int; peak_descriptors : int;
}
type ticket = {
  cost : cost; reply : bool Lwt.t;
  mutable waiting : bool; mutable unregister : unit -> unit;
}
type t = {
  max_transactions : int; max_payload_bytes : int;
  max_descriptors : int; max_pending : int;
  source_headroom : cost option;
  mutable transactions : int; mutable payload_bytes : int;
  mutable descriptors : int; mutable peak_transactions : int;
  mutable peak_payload_bytes : int; mutable peak_descriptors : int;
  mutable sources : ticket list; mutable consumers : ticket list;
  mutable pumping : bool; mutable scheduled : bool;
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
   peak_payload_bytes=0;peak_descriptors=0;sources=[];consumers=[];pumping=false;scheduled=false}
let usage t =
  {transactions=t.transactions;pending=List.length t.sources + List.length t.consumers;
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
let dispatch t =
  (* Lwt.wakeup may execute owner continuations synchronously. Reentrant
     release/cancellation updates the queue; this pump observes the new head. *)
  if not t.pumping then begin
    t.pumping <- true;
    let rec drain () =
      let next = match t.sources with
        | ticket :: rest when fits t Source ticket.cost ->
            t.sources <- rest; Some ticket
        | _ -> match t.consumers with
            | ticket :: rest when fits t Consumer ticket.cost ->
                t.consumers <- rest; Some ticket
            | _ -> None in
      match next with
      | Some ticket ->
          ticket.waiting <- false;
          ticket.unregister (); reserve t ticket.cost;
          Lwt.wakeup ticket.reply true; drain ()
      | _ -> () in
    match drain () with
    | () -> t.pumping <- false
    | exception e -> t.pumping <- false; raise e
  end
let request_dispatch t =
  (* Connection cleanup cancels a group of tokens synchronously. Starting a
     waiter from an earlier token's callback could create resources after their
     connection-close registry was already swept. Defer starts until the owner
     yields; queued tickets still disappear synchronously on cancellation. *)
  if not t.scheduled then begin
    t.scheduled <- true;
    Lwt.ignore_result (Lwt_unix.yield () >>= fun () ->
      t.scheduled <- false; dispatch t; return ())
  end
let release t (cost:cost) =
  t.transactions <- t.transactions - 1;
  t.payload_bytes <- t.payload_bytes - cost.payload_bytes;
  t.descriptors <- t.descriptors - cost.descriptors;
  request_dispatch t
let acquire t cancellation role (cost:cost) =
  let transactions,payload,descriptors = match headroom t role with
    | None -> 0,0,0 | Some cost -> 1,cost.payload_bytes,cost.descriptors in
  if cost.payload_bytes < 0 || cost.descriptors < 0 ||
     t.max_transactions <= transactions ||
     cost.payload_bytes > t.max_payload_bytes - payload ||
     cost.descriptors > t.max_descriptors - descriptors then
    fail (Failed "semantic reservation exceeds the configured resource budget")
  else if HelperSupervisor.is_cancelled cancellation then return false
  else if (match role with Source -> t.sources = [] | Consumer -> t.consumers = []) &&
          fits t role cost then (reserve t cost; return true)
  else if List.length t.sources + List.length t.consumers >= t.max_pending then
    fail (Failed "semantic admission queue is full")
  else begin
    let ticket = {cost;reply=Lwt.wait ();waiting=true;unregister=(fun () -> ())} in
    (match role with Source -> t.sources <- t.sources @ [ticket]
      | Consumer -> t.consumers <- t.consumers @ [ticket]);
    ticket.unregister <- HelperSupervisor.on_cancel cancellation (fun () ->
      if ticket.waiting then begin
        ticket.waiting <- false;
        (match role with
          | Source -> t.sources <- List.filter (fun x -> x != ticket) t.sources
          | Consumer -> t.consumers <- List.filter (fun x -> x != ticket) t.consumers);
        ticket.unregister ();
        request_dispatch t;
        Lwt.wakeup ticket.reply false
      end);
    ticket.reply
  end
let with_lease t cancellation ~role ~cost f =
  acquire t cancellation role cost >>= fun admitted ->
  if not admitted then return None
  else if HelperSupervisor.is_cancelled cancellation then
    (release t cost; return None)
  else try_bind f
    (fun result -> release t cost; return (Some result))
    (fun e -> release t cost; fail e)
