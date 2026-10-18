module type Operations = sig
  type descriptor
  val empty : descriptor
  val close : descriptor -> unit
end
module Make (Operations : Operations) = struct
  type state = Empty | Held | Uncertain | Settled
  type slot = {label:string; mutable state:state; mutable fd:Operations.descriptor;
               mutable cause:exn; mutable grouped:bool}
  type group = {slots:slot array; unresolved:exn}
  (* The exception is allocated while the group is empty. The owner retains the
     group itself, so failure delivery requires no new evidence allocation. *)
  exception Unresolved of unit ref
  let prepare ~label =
    {label;state=Empty;fd=Operations.empty;cause=Exit;grouped=false}
  let group slots =
    if Array.exists (fun slot -> slot.grouped || slot.state <> Empty) slots then
      invalid_arg "close group requires ungrouped empty slots";
    Array.iteri (fun i slot ->
      for j=0 to i-1 do
        if slot == slots.(j) then invalid_arg "duplicate close slot"
      done) slots;
    let result={slots=Array.copy slots;unresolved=Unresolved (ref ())} in
    Array.iter (fun slot -> slot.grouped <- true) result.slots;
    result
  let adopt slot fd =
    if not slot.grouped || slot.state <> Empty then
      invalid_arg "descriptor slot is not prepared for adoption";
    slot.fd <- fd;
    slot.state <- Held
  let close_all group =
    Array.iter (fun slot ->
      if slot.state = Held then begin
        (* Consume authority BEFORE entering the OS. The descriptor number is
           historical after this point, even if the close callback raises. *)
        slot.state <- Uncertain;
        try Operations.close slot.fd; slot.state <- Settled
        with error -> slot.cause <- error
      end) group.slots;
    if Array.exists (fun slot -> slot.state = Uncertain) group.slots then
      raise group.unresolved
  let state slot = slot.state
  let label slot = slot.label
  let cause slot = if slot.state = Uncertain then Some slot.cause else None
  let settled group =
    Array.for_all (fun slot -> slot.state = Empty || slot.state = Settled) group.slots
  let owns_exception group error = group.unresolved == error
end
