exception Uncertain
exception Ordinary
exception Observer
let () =
  let scenario=Sys.argv.(1) in
  let gate=AdmissionFixture.{releases=0} in
  let r=AdmissionFixture.{gate;cost={payload_bytes=1;descriptors=1};state=Held;borrowing=false} in
  let raw=Lwt.wait () in
  let predicate e=if scenario="classifier" then raise Observer else e=Uncertain in
  let guarded () = RetainedOwnership.guard ~is_uncertain:predicate
    ~on_retained:(fun _ -> if scenario="callback" then raise Observer)
    (fun () ->
      if scenario="sync" then raise Uncertain;
      if scenario="observer" then ScopeFault.armed:=true;
      raw) in
  let result=AdmissionFixture.with_borrow r ~cost:r.cost guarded in
  AdmissionFixture.retire_requested r;
  if scenario<>"sync" then
    if scenario="success" then Lwt.wakeup raw 17
    else Lwt.wakeup_exn raw (if scenario="ordinary" then Ordinary else Uncertain);
  let retained=scenario<>"success" && scenario<>"ordinary" in
  if retained then begin
    assert(Lwt.poll result=None && gate.releases=0 && r.borrowing);
    assert(RetainedOwnership.count ()=1);
    RetainedOwnership.iter (fun entry ->
      assert(RetainedOwnership.reply_sleeping entry);
      assert(RetainedOwnership.cause entry=Uncertain);
      if scenario="observer" then assert(RetainedOwnership.reported_error entry=ScopeFault.Observer);
      if scenario="classifier" then assert(RetainedOwnership.classification_error entry=Some Observer));
    Gc.full_major ();
    assert(RetainedOwnership.count ()=1 && gate.releases=0)
  end else begin
    assert(gate.releases=1 && not r.borrowing && RetainedOwnership.count ()=0);
    if scenario="success" then assert(Lwt.poll result=Some 17)
    else (try ignore(Lwt.poll result);assert false with Ordinary -> ())
  end;
  print_endline ("PASS "^scenario)
