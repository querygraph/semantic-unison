open Lwt
module H=HelperSupervisor
module W=SemanticWorkers
module A=SemanticAdmission
let check condition reason=if not condition then failwith reason
let write path data=let output=open_out_bin path in output_string output data;close_out output
let bytes path=let input=open_in_bin path in
  Fun.protect ~finally:(fun () -> close_in input)
    (fun () -> really_input_string input (in_channel_length input))
let () =
  let directory=Filename.concat (Sys.getcwd ()) "private" in Unix.mkdir directory 0o700;
  let source=Filename.concat (Sys.getcwd ()) "original" in
  let data="ORIGINAL GENERATED INPUT" in write source data;
  let budget=H.create ~cpu_permits:2 ~max_children:2 ~max_pending:16 in
  let io=IoAdmission.create ~per_device:1 ~max_pending:16 in
  let pool=W.create_with_io ~io ~workers:2 ~max_pending:16 ~budget in
  let admission=A.create ~source_headroom:None ~max_transactions:1 ~max_payload_bytes:1048576
    ~max_descriptors:16 ~max_pending:8 in
  let stage=ref None and candidate=ref "" in
  let create ()=let owner=ValidationStage.create ~directory ~source ~max_bytes:1024L in
    stage:=Some owner;owner in
  let run cancellation validate on_retained =
    A.with_lease admission cancellation ~role:A.Consumer
      ~cost:{A.payload_bytes=1048576;descriptors=16} (fun () ->
        ValidationStageWork.run ~pool ~cancellation ~max_bytes:1024L ~create
          ~validate:(fun ~candidate:path ~snapshot ->
            candidate:=path;check (path<>source && bytes path=data) "helper received original/wrong snapshot";
            validate ~candidate:path ~snapshot)
          ~on_retained ()) in
  let quiet ()=check ((A.usage admission).transactions=0 && (A.usage admission).pending=0)
      "outer admission not settled";
    check ((W.usage pool).pending=0 && H.usage budget=(0,0) && (IoAdmission.usage io).active_jobs=0)
      "worker/CPU/IO not settled" in
  let no_retention _=failwith "unexpected retention" in
  ignore (Lwt_unix.run (run (H.cancellation ()) (fun ~candidate:_ ~snapshot:_ -> return ()) no_retention));
  check (not (Sys.file_exists !candidate) && bytes source=data) "success did not clean private stage";quiet ();
  let failed=try ignore (Lwt_unix.run (run (H.cancellation ())
      (fun ~candidate:_ ~snapshot:_ -> fail Exit) no_retention));false with Exit -> true in
  check (failed && not (Sys.file_exists !candidate) && bytes source=data) "callback failure cleanup";quiet ();
  let changed=try ignore (Lwt_unix.run (run (H.cancellation ())
      (fun ~candidate ~snapshot:_ -> write candidate "MUTATED PRIVATE STAGE";return ()) no_retention));false
    with ValidationStageWork.Snapshot_changed -> true in
  check (changed && bytes source=data && not (Sys.file_exists !candidate)) "private mutation accepted/original changed";quiet ();
  let cancellation=H.cancellation () and release=Lwt.wait () in
  let entered=ref false in
  let pending=run cancellation (fun ~candidate:_ ~snapshot:_ -> entered:=true;release) no_retention in
  let until=Unix.gettimeofday ()+.5. in
  let rec wait_for_validator ()=if !entered then return () else
    if Unix.gettimeofday ()>until then failwith "validator not reached" else
    match Lwt.poll pending with
    | Some _ -> failwith "validation completed before callback"
    | None -> Lwt_unix.sleep 0.001 >>= wait_for_validator in
  Lwt_unix.run (wait_for_validator ());H.cancel cancellation;
  Lwt_unix.run (Lwt_unix.sleep 0.002);
  check (Lwt.poll pending=None && Sys.file_exists !candidate && (A.usage admission).transactions=1)
    "cancel retired sleeping validation or released admission";
  Lwt.wakeup release ();
  let cancelled=try ignore (Lwt_unix.run pending);false with ValidationStageWork.Cancelled -> true in
  check (cancelled && not (Sys.file_exists !candidate) && bytes source=data) "cancelled callback settlement";quiet ();
  let retained=ref false in
  let unknown=run (H.cancellation ()) (fun ~candidate:_ ~snapshot:_ ->
    let owner=match !stage with Some owner -> owner | None -> failwith "missing owner" in
    let original,_=ValidationStage.descriptors owner in
    Unix.close original; (* Explicit borrowed-FD lifetime violation: deterministic EBADF model. *)
    fail (Failure "original validation error"))
    (fun _ -> retained:=true;raise Exit) in
  let until=Unix.gettimeofday ()+.5. in
  let rec wait_retained ()=if !retained then return () else
    if Unix.gettimeofday ()>until then failwith "retention not reached" else
    match Lwt.poll unknown with
    | Some _ -> failwith "uncertain work completed"
    | None -> Lwt_unix.sleep 0.001 >>= wait_retained in
  Lwt_unix.run (wait_retained ());
  check (Lwt.poll unknown=None && (A.usage admission).transactions=1)
    "uncertainty/log failure released outer admission";
  check (List.length (ValidationStageWork.retained_owners ())=1) "opaque owner not retained";
  Lwt_unix.run (W.shutdown pool);
  check (H.usage budget=(0,0) && (W.usage pool).pending=0 && (IoAdmission.usage io).active_jobs=0)
    "unknown cleanup left worker work live";
  check (bytes source=data) "original changed";
  print_endline "PASS async staging success/failure/private-mutation/sleeping-cancel/retained-uncertainty";
  print_endline "EXPECTED retained symbolic admission=1 until this control process exits; injected source FD was already closed, no numeric retry."
