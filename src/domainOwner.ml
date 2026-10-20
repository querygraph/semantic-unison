type state = Empty | Held | Uncertain | Joined
type slot = {
  mutable state:state;
  mutable handle:Obj.t;
  mutable failure:exn;
  carrier:exn;
}
exception Join_uncertain of slot
let prepare () =
  let rec slot={state=Empty;handle=Obj.repr ();failure=Exit;
    carrier=Join_uncertain slot} in slot
let adopt slot (domain:unit Domain.t) =
  if slot.state<>Empty then invalid_arg "domain slot already adopted";
  (* A private, monomorphic optional slot avoids allocating Some after spawn.
     Only this typed entry point stores a handle; only the Held branch below
     reads it. Obj.repr preserves the GC root and does not allocate. The initial
     unit value is never cast or passed to Domain.join. *)
  slot.handle <- Obj.repr domain;
  slot.state <- Held
let join slot =
  if slot.state=Held then begin
    slot.state <- Uncertain;
    try
      Domain.join (Obj.obj slot.handle : unit Domain.t);
      slot.state <- Joined
    with error -> slot.failure <- error
  end;
  if slot.state=Uncertain then raise slot.carrier
let join_all slots =
  for index=0 to Array.length slots-1 do
    try join slots.(index) with Join_uncertain _ -> ()
  done;
  for index=0 to Array.length slots-1 do
    if slots.(index).state=Uncertain then raise slots.(index).carrier
  done
let state slot = slot.state
let cause slot = if slot.state=Uncertain then Some slot.failure else None
