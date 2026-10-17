(* Original tiny source fixture; production archive transaction and managed store. *)
let require yes why=if not yes then failwith why
let ()=
 let folder=Sys.argv.(1) and phase=Sys.argv.(2) in
 let state=Filename.concat folder "state" in
 require(Util.unisonDir=state) "private state required";
 Prefs.loadStrings ["componentownercache = true";"adobevalidate = off";
  "semanticdng = false";"semanticworkers = 2";"log = false"];
 Case.init true Osx.isMacOSX;Props.init false;Osx.init Osx.isMacOSX;Fileinfo.init false;
 Globals.setRawRoots [Filename.concat folder "left";Filename.concat folder "right"];
 Lwt_unix.run(Globals.installRoots None);Update.storeRootsName ();
 Lwt_unix.run(Globals.propagatePrefs ());
 let left=snd(fst(Globals.roots ())) in
 ignore(Update.findUpdates ~wantWatcher:false None);
 let binding=SemanticHash.string "managed-archive-binding" in
 let generation=SemanticHash.string "managed-archive-generation" in
 let root="managed-archive-root" in
 let storage=Filename.concat state "managed" in
 if phase="write" then Unix.mkdir storage 0o700;
 let parent=Unix.openfile storage [Unix.O_RDONLY;Unix.O_CLOEXEC] 0 in
 if phase="write" then begin
  let source=Filename.concat state "original-tiny.bin" in
  let out=open_out_bin source in output_string out (String.make 128 'a');close_out out;
  let fd=Unix.openfile source [Unix.O_RDONLY;Unix.O_CLOEXEC] 0 in
  let checkpoint=SemanticFile.with_borrowed_fd fd(fun file ->
   ComponentHash.with_snapshot ~max_read_bytes:128L file
    {ComponentHash.id="dng";schema="dng-physical-partition/0";role=Structural;
     offset=0L;length=128L;children=[]}
    (fun session snapshot -> ComponentHash.checkpoint session snapshot)) in Unix.close fd;
  let entry=DngComponents.make_owner_entry ~root_identity:root ~path:"one"
   ~generation_sha256:generation ~checkpoint ~outcomes:[] in
  let store=DngComponents.prepare_managed_cache_store ~entry ~checkpoint
   ~index:(DngComponents.empty_owner_index ~max_entries:4 ~max_bytes:524288)
   ~expected_entry_sha256:None ~binding ~max_bytes:4194304L ~max_entries:2 in
  let rejected=try Update.adopt_component_cache_store left ~expected_reference:None store;false
   with ComponentHash.Invalid _ -> true in
  require rejected "unsettled store adopted";
  require(Update.component_owner_reference left=None) "unsettled store changed head";
  let namespace=DngComponents.prepare_cache_namespace ~parent () in
  DngComponents.provision_cache_namespace namespace ~parent;
  require(DngComponents.execute_managed_cache_store store ~namespace ~parent) "store exhausted";
  let refused=try Update.adopt_component_cache_store left
   ~expected_reference:(Some(binding,SemanticHash.string "wrong-head")) store;false
   with Util.Transient _ -> true in
  require refused "changed archive head accepted";
  require(Update.component_owner_reference left=None) "CAS refusal changed archive head";
  Update.adopt_component_cache_store left ~expected_reference:None store;
  require(Update.component_owner_reference left=Some(DngComponents.managed_cache_store_reference store))
   "settled store not adopted";
  require(Update.component_owner_namespace left=Some(DngComponents.cache_namespace_identity namespace))
   "store namespace identity not adopted";
  Update.commitUpdates ()
 end else if phase="missing" then begin
  require(Update.component_owner_reference left=None && Update.component_owner_namespace left=None)
   "legacy rewrite retained optional owner authority";
  require !Update.foundArchives "legacy rewrite reset ordinary archive"
 end else begin
  require !Update.foundArchives "archive not restored";
  let expected=match Update.component_owner_namespace left with
   | Some identity -> identity | None -> failwith "archive namespace identity not restored" in
  let namespace=DngComponents.prepare_cache_namespace ~expected ~parent () in
  DngComponents.provision_cache_namespace namespace ~parent;
  DngComponents.with_cache_namespace namespace ~parent(fun directory ->
   let index=match Update.load_component_owner_index left ~directory ~max_entries:4 ~max_bytes:524288 () with
    | Some index -> index | None -> failwith "committed manifest missing" in
   let entry=match DngComponents.select_owner_entry index ~root_identity:root ~path:"one"
    ~generation_sha256:generation with Some entry -> entry | None -> failwith "committed entry absent" in
   require(DngComponents.load_owner_record ~directory ~entry ()<>None) "committed record absent")
 end;
 Unix.close parent;Lwt_unix.run(Update.unlockArchives ());Globals.uninstallRoots ();
 Printf.printf "PASS managed archive %s; settled store/CAS/normal commit/cold load\n%!" phase
