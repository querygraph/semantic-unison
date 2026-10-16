type 'a state = { front : 'a list; back : 'a list; count : int; closed : bool }
type 'a t = { capacity : int; state : 'a state Atomic.t }
type push = Added | Full | Closed
type 'a pop = Item of 'a | Empty | Drained
type usage = { capacity : int; pending : int; closed : bool }
let create ~capacity =
  if capacity <= 0 || capacity > 65536 then invalid_arg "SemanticMailbox: capacity outside1..65536";
  {capacity;state=Atomic.make {front=[];back=[];count=0;closed=false}}
let rec push t item =
  let before=Atomic.get t.state in
  if before.closed then Closed
  else if before.count >= t.capacity then Full
  else
    let after={before with back=item::before.back;count=before.count+1} in
    if Atomic.compare_and_set t.state before after then Added
    else push t item
let rec pop t =
  let before=Atomic.get t.state in
  if before.count=0 then (if before.closed then Drained else Empty)
  else
    let front,back=match before.front with
      | [] -> List.rev before.back,[]
      | front -> front,before.back in
    match front with
    | [] -> assert false
    | item::rest ->
        let after={front=rest;back;count=before.count-1;closed=before.closed} in
        (* Publish no ownership loss if allocating the reply fails: allocate
           both the new queue state and item envelope before winning CAS. *)
        let result=Item item in
        if Atomic.compare_and_set t.state before after then result else pop t
let rec close t =
  let before=Atomic.get t.state in
  if not before.closed &&
     not (Atomic.compare_and_set t.state before {before with closed=true}) then close t
let usage t =
  let state=Atomic.get t.state in
  {capacity=t.capacity;pending=state.count;closed=state.closed}
