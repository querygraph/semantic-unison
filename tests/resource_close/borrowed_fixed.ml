exception Operation_failed
exception Cancelled
exception Close_failed
let close_attempts=ref 0 and close_fails=ref false
module Ownership=OwnedClose.Make(struct
  type descriptor=int
  let empty=0
  let close _ = incr close_attempts; if !close_fails then raise Close_failed
end)
module Completion=BorrowedClose.Make(Ownership)
let case ~uncertain outcome =
  close_attempts:=0;close_fails:=uncertain;
  let slot=Ownership.prepare ~label:"borrowed input" in
  let group=Ownership.group [|slot|] in
  let completion=Completion.prepare group in
  let gate=AdmissionFixture.{releases=0} in
  let reservation=AdmissionFixture.{gate;cost={payload_bytes=1;descriptors=1};state=Held;borrowing=false} in
  let result=AdmissionFixture.with_borrow reservation ~cost:reservation.cost
    (fun () -> Completion.promise completion) in
  Ownership.adopt slot 101;
  AdmissionFixture.retire_requested reservation;
  assert(gate.releases=0);
  Completion.finish completion outcome;
  assert(!close_attempts=1);
  if uncertain then begin
    assert(Lwt.poll result=None && gate.releases=0 && reservation.borrowing);
    assert(Completion.retained completion);
    assert(Completion.operation_outcome completion=outcome);
    assert(Completion.close_failure completion<>None);
    (* A caller retry cannot close again or release the borrowed reservation. *)
    (try Completion.finish completion outcome;assert false with Invalid_argument _ -> ());
    assert(!close_attempts=1 && gate.releases=0)
  end else begin
    assert(not(Completion.retained completion) && gate.releases=1 && not reservation.borrowing);
    match outcome with
    | Ok value -> assert(Lwt.poll result=Some value)
    | Error error -> (try ignore(Lwt.poll result);assert false with actual -> assert(actual==error))
  end
let () =
  List.iter (fun uncertain ->
    case ~uncertain (Ok 17);
    case ~uncertain (Error Operation_failed);
    case ~uncertain (Error Cancelled)) [false;true];
  print_endline "PASS exact production with_borrow: success/failure/cancellation settle only known close; uncertain retains"
