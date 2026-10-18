module type Operations = sig (* ox-portable-operations *)
  type descriptor
  val empty : descriptor
  val close : descriptor -> unit
end
module Make (Operations : Operations) = struct
  type state = Empty | Held | Uncertain | Settled
  type slot = {label:string; state:state Atomic.t; fd:Operations.descriptor Atomic.t;
               cause:exn Atomic.t; grouped:bool Atomic.t}
  type group = {slots:slot list; unresolved:exn}
  (* The exception is allocated while the group is empty. The owner retains the
     group itself, so failure delivery requires no new evidence allocation. *)
  exception Unresolved of unit Atomic.t
  let prepare ~label =
    {label;state=Atomic.make Empty;fd=Atomic.make Operations.empty;cause=Atomic.make Exit;grouped=Atomic.make false}
  let group slots =
    if Array.exists (fun slot -> Atomic.get slot.grouped || Atomic.get slot.state <> Empty) slots then
      invalid_arg "close group requires ungrouped empty slots";
    Array.iteri (fun i slot ->
      for j=0 to i-1 do
        if slot == slots.(j) then invalid_arg "duplicate close slot"
      done) slots;
    let result={slots=Array.to_list slots;unresolved=Unresolved (Atomic.make ())} in
    List.iter (fun slot -> Atomic.set slot.grouped true) result.slots;
    result
  let adopt slot fd =
    if not (Atomic.get slot.grouped) || Atomic.get slot.state <> Empty then
      invalid_arg "descriptor slot is not prepared for adoption";
    Atomic.set slot.fd fd;
    Atomic.set slot.state Held
  let close_all group =
    List.iter (fun slot ->
      if Atomic.get slot.state = Held then begin
        (* Consume authority BEFORE entering the OS. The descriptor number is
           historical after this point, even if the close callback raises. *)
        Atomic.set slot.state Uncertain;
        try Operations.close (Atomic.get slot.fd); Atomic.set slot.state Settled
        with error -> Atomic.set slot.cause error
      end) group.slots;
    if List.exists (fun slot -> Atomic.get slot.state = Uncertain) group.slots then
      raise group.unresolved
  let state slot = Atomic.get slot.state
  let label slot = slot.label
  let cause slot = if Atomic.get slot.state = Uncertain then Some (Atomic.get slot.cause) else None
  let settled group =
    List.for_all (fun slot -> match Atomic.get slot.state with Empty | Settled -> true | Held | Uncertain -> false) group.slots
  let owns_exception group error = group.unresolved == error
end
