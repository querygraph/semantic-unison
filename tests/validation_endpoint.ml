open Lwt
let mode=ref "off" and calls=ref 0 and switch_link=ref (fun () -> ())
let release=Lwt.wait () and entered=ref false
module Recognition = struct
  let format="test/endpoint-private-validator"
  let identify file=if SemanticFile.size file>=4L && SemanticFile.read file 0L 4="TOY0"
    then FormatRecognition.Recognized else FormatRecognition.Not_matched
end
module Validator = struct
  let recognition=FormatRecognition.trusted ~suffixes:[".toy"] (module Recognition)
  let select ()=if !mode="off" then None else
    let captured= !mode in Some (fun (context:CandidateValidator.context) ->
    incr calls;
    if not (Util.startswith (Filename.basename (Filename.dirname context.candidate)) "validation-scan-") then
      failwith "validator received nonprivate path";
    context.inspect context.candidate >>= fun actual ->
    if actual<>context.expected then failwith "private endpoint snapshot differs";
    match captured with
    | "reject" -> fail (Util.Transient "original fake rejection")
    | "mutate" ->
        let ch=open_out_bin context.candidate in output_string ch "MUTATED";close_out ch;return ()
    | "residue" ->
        let ch=open_out_bin (Filename.concat (Filename.dirname context.candidate) "unexpected-fixture") in
        output_string ch "PRESERVE ORIGINAL DISPOSABLE RESIDUE";close_out ch;
        fail (Util.Transient "original rejection with residue")
    | "disable" -> mode:="off";return ()
    | "retarget" -> !switch_link ();return ()
    | "sleep" -> entered:=true;release
    | _ -> return ())
end
let ()=CandidateValidators.register (module Validator)
let check yes reason=if not yes then failwith reason
let write p value=let ch=open_out_bin p in output_string ch value;close_out ch
let sorted paths=List.sort String.compare (List.map Path.toString paths)
let () =
  let cwd=Sys.getcwd () in
  let left=Filename.concat cwd "left" and right=Filename.concat cwd "right" in
  Unix.mkdir left 0o700;Unix.mkdir right 0o700;
  List.iter (fun name -> Unix.mkdir (Filename.concat left name) 0o700) ["nested";"frozen"];
  List.iter (fun (name,body) -> write (Filename.concat left name) body)
    ["plain","TOY0 generated";"nested/stable","TOY0 nested fixture";"frozen/old","TOY0 immutable fixture";
     "ignored","TOY0 ignored fixture"];
  write (Filename.concat cwd "external") "TOY0 follow target";
  Unix.symlink (Filename.concat cwd "external") (Filename.concat left "link");
  let profile=Filename.concat (Sys.getenv "UNISON") "scan.prf" in
  write profile ("root = "^left^"\nroot = "^right^
    "\nbatch = true\nlog = false\nfastcheck = true\nsemanticworkers = 2\nsemanticmaxinflight = 1\nsemanticpayloadbudget = 8\nsemanticdescriptorbudget = 64\nignore = Path ignored\nimmutable = Path frozen\n");
  Uicommon.initPrefs ~profileName:"scan" ~promptForRoots:(fun () -> None) ();
  Uicommon.connectRoots ~displayWaitMessage:(fun () -> ()) ();
  let initial=Update.findUpdates None in
  let root=Fspath.canonize (Some left) in
  let pair=List.hd initial in
  let _,ui,_=if Fspath.compare (snd (List.hd (Globals.rootsList ()))) root=0
    then fst pair else snd pair in
  Update.replaceArchiveLocal root Path.empty (Update.makeArchive ui);
  let collect ?(files=20) ?(bytes=4096) ?(paths=[Path.empty]) ?(subpaths=None) () =
    Update.findLocalWithValidation ~max_files:files ~max_path_bytes:bytes true root paths subpaths in
  let expected=["frozen/old";"nested/stable";"plain"] in
  let updates,paths=collect () in
  check (sorted paths=expected) "actual unchanged nested scan selection";
  check (List.for_all (fun (_,ui,_) -> ui=Common.NoUpdates) updates) "unchanged update result differs";
  let base=Fspath.resolve_existing (Sys.getenv "UNISON") in
  let run ?(staging_base=base) paths =
    ValidationScanWork.run ~staging_base ~roots:[root] ~root ~paths ~max_bytes:1024L in
  let quiet () =
    check (Sys.getcwd ()=cwd) "endpoint changed process CWD";
    check (not (Array.exists (fun name -> Util.startswith name "validation-scan-")
      (Sys.readdir (Fspath.toString base)))) "private endpoint directory residue";
    let runtime=SemanticRuntime.get () in
    check ((SemanticRuntime.admission_usage ()).transactions=0 &&
      (SemanticWorkers.usage runtime.pool).pending=0 &&
      (IoAdmission.usage runtime.io).active_jobs=0 && HelperSupervisor.usage runtime.supervisor=(0,0))
      "endpoint resource admission did not settle" in
  let missing=Fspath.child base (Name.fromString "absent-staging-base") in
  Lwt_unix.run (run ~staging_base:missing paths);
  check (!calls=0 && not (Sys.file_exists (Fspath.toString missing))) "disabled endpoint opened inputs";
  mode:="pass";
  let refused=try Lwt_unix.run (run ~staging_base:root paths);false with Util.Transient _ -> true in
  check refused "staging inside replica permitted";
  let originals=List.map (fun path ->
    let full=Fspath.toString (Fspath.concat root path) in
    let info=Unix.LargeFile.stat full in full,{info with Unix.LargeFile.st_atime=0.}) paths in
  Lwt_unix.run (run paths);check (!calls=3) "actual selected endpoint coverage differs";quiet ();
  mode:="disable";let before= !calls in Lwt_unix.run (run paths);
  check (!calls=before+3 && !mode="off") "endpoint reselected changed policy midway";quiet ();
  List.iter (fun selected ->
    mode:=selected;
    let failed=try Lwt_unix.run (run paths);false with Util.Transient _ -> true in
    check failed "endpoint accepted rejected/mutated private candidate";quiet ()) ["reject";"mutate"];
  mode:="residue";
  let prior= !calls in
  let preserved=try Lwt_unix.run (run paths);false with
    ValidationScanWork.Cleanup_failed (Some (Util.Transient reason),Unix.Unix_error (Unix.ENOTEMPTY,_,_)) ->
      reason="original rejection with residue" in
  check (preserved && !calls=prior+1) "directory failure lost original rejection or retried callback";
  let leftovers=Array.to_list (Sys.readdir (Fspath.toString base))
    |> List.filter (fun name -> Util.startswith name "validation-scan-") in
  check (List.length leftovers=1) "unexpected residue was recursively deleted";
  let leftover=Filename.concat (Fspath.toString base) (List.hd leftovers) in
  check (Sys.readdir leftover=[|"unexpected-fixture"|]) "directory cleanup removed unrelated entry";
  (* Explicit test-owned disposal after proving production preserved the entry. *)
  Unix.unlink (Filename.concat leftover "unexpected-fixture");Unix.rmdir leftover;quiet ();
  mode:="sleep";
  let pending=run paths in
  let until=Unix.gettimeofday ()+.5. in
  let rec await ()=if !entered then return () else
    if Unix.gettimeofday ()>until then failwith "sleeping validator not reached" else
    Lwt_unix.sleep 0.001 >>= await in
  Lwt_unix.run (await ());Abort.all ();
  Lwt_unix.run (Lwt_unix.sleep 0.02);
  check (Lwt.poll pending=None && (SemanticRuntime.admission_usage ()).transactions=1 && Array.exists (fun name -> Util.startswith name "validation-scan-")
    (Sys.readdir (Fspath.toString base))) "abort retired an active endpoint callback";
  Lwt.wakeup release ();
  let cancelled=try Lwt_unix.run pending;false with Util.Transient _ -> true in
  Abort.reset ();check cancelled "endpoint abort not observed after callback";quiet ();
  List.iter (fun (name,before) ->
    let after=Unix.LargeFile.stat name in
    check (before={after with Unix.LargeFile.st_atime=0.}) "original source metadata changed") originals;
  mode:="pass";
  write (Filename.concat left "frozen/old") "changed but deliberately immutable";
  let updates,paths=collect ~subpaths:(Some ([],[])) () in
  check (sorted paths=expected) "watcher hint dropped coverage";
  check (List.for_all (fun (_,ui,_) -> ui=Common.NoUpdates) updates) "validation changed immutable update semantics";
  let _,paths=collect ~paths:[Path.fromString "nested";Path.fromString "nested/stable"] () in
  check (sorted paths=["nested/stable"]) "selected overlap/namespace dedup";
  List.iter (fun (files,bytes) ->
    let failed=try ignore (collect ~files ~bytes ());false with ValidationPaths.Limit_exceeded _ -> true in
    check failed "coverage budget silently truncated";
    let _,paths=collect () in check (sorted paths=expected) "failed scan poisoned next scan") [1,4096;20,1];
  Prefs.loadStrings ["follow = Path link"];
  let _,paths=collect () in check (sorted paths=["frozen/old";"link";"nested/stable";"plain"]) "follow selection";
  write (Filename.concat cwd "other-target") "TOY0 other target";
  switch_link:=(fun () -> Unix.unlink (Filename.concat left "link");
    Unix.symlink (Filename.concat cwd "other-target") (Filename.concat left "link"));
  mode:="retarget";
  let retargeted=try Lwt_unix.run (run [Path.fromString "link"]);false with Util.Transient _ -> true in
  check retargeted "followed logical path retarget accepted";quiet ();
  Unix.unlink (Filename.concat left "link");
  Unix.symlink (Filename.concat cwd "external") (Filename.concat left "link");
  mode:="pass";Lwt_unix.run (run [Path.fromString "link"]);quiet ();
  let _,paths=collect ~paths:[Path.fromString "ignored"] () in
  check (paths=[]) "explicit ignored selection was traversed";
  write (Filename.concat left "plain") "changed generated source";
  write (Filename.concat left "new") "new generated source";
  let updates,paths=collect () in
  check (sorted paths=["frozen/old";"link";"nested/stable";"new";"plain"]) "new/changed coverage";
  check (List.exists (fun (_,ui,_) -> ui<>Common.NoUpdates) updates) "coverage suppressed real updates";
  let ledger=ValidationPaths.create ~max_files:1 ~max_path_bytes:20 in
  ValidationPaths.add ledger (Path.fromString "one");ValidationPaths.add ledger (Path.fromString "one");
  (try ValidationPaths.add ledger (Path.fromString "two");failwith "limit accepted" with ValidationPaths.Limit_exceeded _ -> ());
  (try ignore (ValidationPaths.paths ledger);failwith "partial prefix returned" with ValidationPaths.Limit_exceeded _ -> ());
  Lwt_unix.run (SemanticWorkers.shutdown (SemanticRuntime.get ()).pool);
  let artifact=Filename.concat cwd "descriptor-artifact" in write artifact "GENERATED ARTIFACT";
  let closes=ref 0 in
  let close fd=incr closes;Unix.close fd in
  let value=Lwt_unix.run (ValidationDescriptor.with_file ~close artifact (fun _ -> return 17)) in
  check (value=17 && !closes=1 && ValidationDescriptor.retained ()=[]) "known descriptor completion";
  let failed=try ignore (Lwt_unix.run (ValidationDescriptor.with_file ~close artifact (fun _ -> fail Exit)));false with Exit -> true in
  check (failed && !closes=2 && ValidationDescriptor.retained ()=[]) "known descriptor failure cleanup";
  let borrowed=Lwt.wait () in
  let pending=ValidationDescriptor.with_file ~close artifact (fun _ -> borrowed) in
  check (Lwt.poll pending=None && !closes=2) "descriptor closed before borrower settlement";
  Lwt.wakeup borrowed 29;check (Lwt_unix.run pending=29 && !closes=3) "descriptor borrower completion";
  let uncertain_calls=ref 0 in
  let gate=SemanticAdmission.create ~source_headroom:None ~max_transactions:2
    ~max_payload_bytes:2097152 ~max_descriptors:8 ~max_pending:4 in
  let charged work=SemanticAdmission.with_lease gate (HelperSupervisor.cancellation ())
    ~role:SemanticAdmission.Consumer ~cost:{SemanticAdmission.payload_bytes=1048576;descriptors=4} work in
  let uncertain=charged (fun () -> ValidationDescriptor.with_file ~close:(fun fd ->
    incr uncertain_calls;Unix.close fd;raise (Unix.Unix_error (Unix.EINTR,"injected-close",artifact)))
    artifact (fun _ -> fail (Failure "original borrowed operation"))) in
  check (Lwt.poll uncertain=None && !uncertain_calls=1 &&
    (SemanticAdmission.usage gate).transactions=1 && (SemanticAdmission.usage gate).descriptors=4)
    "uncertain close released owner/admission";
  let owners=ValidationDescriptor.retained () in
  check (List.length owners=1 && ValidationDescriptor.before_close (List.hd owners)<>None &&
    ValidationDescriptor.original_failure (List.hd owners)=Some (Failure "original borrowed operation")) "uncertain close facts lost";
  ignore (Lwt_unix.run (ValidationDescriptor.with_file artifact (fun _ -> return ())));
  check (!uncertain_calls=1 && List.length (ValidationDescriptor.retained ())=1) "later descriptor reused uncertain numeric handle";
  let still_open=charged (fun () -> ValidationDescriptor.with_file ~close:(fun _ ->
    raise (Unix.Unix_error (Unix.EINTR,"injected-unclosed",artifact))) artifact (fun _ -> return ())) in
  check (Lwt.poll still_open=None && List.length (ValidationDescriptor.retained ())=2 &&
    (SemanticAdmission.usage gate).transactions=2 && (SemanticAdmission.usage gate).descriptors=8)
    "multiple uncertain identities/admission lost";
  print_endline "EXPECTED two descriptor uncertainty carriers and two admitted loans retained until this disposable process exits; injected models, no numeric retry";
  print_endline "PASS endpoint private snapshots/off/inside-root/rejection/mutation/abort/follow-retarget and actual selected unchanged/nested/immutable/ignore/follow/overlap/budget scan controls; no helpers"
