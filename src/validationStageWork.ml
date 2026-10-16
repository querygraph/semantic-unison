open Lwt
exception Cancelled
exception Snapshot_changed
let retained = ref []
let retained_owners ()=List.rev !retained
let run ~pool ~cancellation ~max_bytes ~create ~validate
    ?(select=fun ~source:_ -> return true) ?(on_retained=fun _ -> ()) () =
  if max_bytes<0L then invalid_arg "ValidationStageWork.max_bytes";
  let hold owner =
    if not (List.exists (fun current -> current==owner) !retained) then
      retained:=owner:: !retained;
    let pending=Lwt.wait () in
    (try on_retained owner with _ -> ());
    pending in
  let cancelled ()=if HelperSupervisor.is_cancelled cancellation then raise Cancelled in
  let finish owner failure =
    try
      ValidationStage.retire ?failure owner;
      match failure with None -> return () | Some error -> fail error
    with
    | ValidationStage.Unresolved_ownership held -> hold held
    | cleanup ->
      match failure with
      | None -> fail cleanup
      | Some original -> fail (ValidationStage.Preparation_failed (original,cleanup)) in
  let execute owner =
    cancelled ();
    let source,output=ValidationStage.descriptors owner in
    BorrowedWork.bind
      (fun () -> select ~source)
      (fun selected ->
      ValidationStage.check owner;cancelled ();
      if not selected then return () else
      BorrowedWork.bind
      (fun () -> SemanticWorkers.snapshot pool cancellation ~max_bytes ~source ~output)
      (function
      | None -> fail Cancelled
      | Some snapshot ->
        ValidationStage.check owner;cancelled ();
        let candidate=ValidationStage.path owner in
        BorrowedWork.bind (fun () -> validate ~candidate ~snapshot) (fun () ->
          ValidationStage.check owner;cancelled ();
          BorrowedWork.bind (fun () -> SemanticWorkers.digest pool cancellation output) (function
          | None -> fail Cancelled
          | Some fingerprint ->
            ValidationStage.check owner;cancelled ();
            if SemanticHash.hex fingerprint.SemanticWorkers.digest<>snapshot.ValidationSnapshot.sha256 ||
               fingerprint.stats.Unix.LargeFile.st_size<>snapshot.bytes then fail Snapshot_changed
            else return ()))) ) in
  BorrowedWork.try_bind
    (fun () ->
      cancelled ();
      let owner=create () in
      (try BorrowedWork.try_bind (fun () -> execute owner)
        (fun () -> finish owner None) (fun error -> finish owner (Some error))
       with error -> finish owner (Some error)))
    (fun () -> return ())
    (function ValidationStage.Unresolved_ownership owner -> hold owner | error -> fail error)
