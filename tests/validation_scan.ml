let check yes reason=if not yes then failwith reason
let write p value=let ch=open_out_bin p in output_string ch value;close_out ch
let sorted paths=List.sort String.compare (List.map Path.toString paths)
let () =
  let cwd=Sys.getcwd () in
  let left=Filename.concat cwd "left" and right=Filename.concat cwd "right" in
  Unix.mkdir left 0o700;Unix.mkdir right 0o700;
  List.iter (fun name -> Unix.mkdir (Filename.concat left name) 0o700) ["nested";"frozen"];
  List.iter (fun (name,body) -> write (Filename.concat left name) body)
    ["plain","generated";"nested/stable","nested fixture";"frozen/old","immutable fixture";
     "ignored","ignored fixture"];
  write (Filename.concat cwd "external") "follow target";
  Unix.symlink (Filename.concat cwd "external") (Filename.concat left "link");
  let profile=Filename.concat (Sys.getenv "UNISON") "scan.prf" in
  write profile ("root = "^left^"\nroot = "^right^
    "\nbatch = true\nlog = false\nfastcheck = true\nignore = Path ignored\nimmutable = Path frozen\n");
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
  print_endline "PASS actual selected unchanged/nested/immutable/ignore/follow/overlap/budget scan controls; no helpers"
