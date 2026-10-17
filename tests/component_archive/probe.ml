(* Production-linked, empty private roots only. No transport/native Adobe work. *)
let require yes why=if not yes then failwith why
let () =
 if Array.length Sys.argv<>4 then (prerr_endline "usage: archive-probe PRIVATE_CASE PHASE NONCE";exit 2);
 let folder=Sys.argv.(1) and phase=Sys.argv.(2) and nonce=Sys.argv.(3) in
 require(not(Filename.is_relative folder) && List.mem phase ["write";"read";"off";"missing";"bad"])
   "fixed private archive phase required";
 let state=Filename.concat folder "state" in
 require(Sys.getenv "UNISON"=state && Util.unisonDir=state) "private UNISON confinement required";
 let s=Unix.lstat state in
 require(s.Unix.st_kind=Unix.S_DIR && s.st_uid=Unix.getuid () && s.st_perm land 0o7777=0o700)
   "private owner state required";
 Prefs.loadStrings ["componentownercache = "^(if phase="off" then "false" else "true");
   "adobevalidate = off";"semanticdng = false";"semanticworkers = 2";"log = false"];
 Case.init true Osx.isMacOSX;Props.init false;Osx.init Osx.isMacOSX;Fileinfo.init false;
 Globals.setRawRoots [Filename.concat folder "left";Filename.concat folder "right"];
 Lwt_unix.run(Globals.installRoots None);Update.storeRootsName ();
 Lwt_unix.run(Globals.propagatePrefs ());
 let root1,root2=Globals.roots () in
 let left=snd root1 and right=snd root2 in
 require(fst root1=Common.Local && fst root2=Common.Local) "local roots only";
 let binding=SemanticHash.string("original archive probe owner "^nonce) in
 let ledger=DngComponents.empty_owner_index ~max_entries:1 ~max_bytes:4096 in
 let expected=binding,SemanticHash.string(DngComponents.owner_index_bytes ~binding ledger) in
 ignore(Update.findUpdates ~wantWatcher:false None);
 if phase="write" then begin
   require(Update.component_owner_reference left=None) "write must start without adopted hint";
   let storage=Filename.concat state ("manifest-"^nonce) in
   Unix.mkdir storage 0o700;
   let directory=Unix.openfile storage [Unix.O_RDONLY;Unix.O_CLOEXEC] 0 in
   let publication=Fun.protect ~finally:(fun () -> Unix.close directory) (fun () ->
     let stage=Unix.openfile(Filename.concat storage "stage")
       [Unix.O_CREAT;Unix.O_EXCL;Unix.O_RDWR;Unix.O_CLOEXEC] 0o600 in
     Fun.protect ~finally:(fun () -> Unix.close stage) (fun () ->
       ignore(DngComponents.write_owner_index ~binding ledger stage);
       let publication=SemanticFile.with_borrowed_fd stage(fun file ->
         DngComponents.prepare_owner_index_publication ~binding ledger ~directory ~stage ~temporary:"stage" file) in
       DngComponents.publish_owner_index publication directory stage;publication)) in
   (* Both borrowed descriptors are actually closed before owner-state adoption. *)
   Update.set_component_owner_reference left publication;
   require(Update.component_owner_reference left=Some expected) "owner reference not adopted";
   require(Update.component_owner_reference right=None) "endpoint-local reference leaked to other root";
   Update.commitUpdates ()
 end else if phase="read" then begin
   require(Update.component_owner_reference left=Some expected) "archive did not restore exact hint";
   require(Update.component_owner_reference right=None) "other root acquired private hint";
   require(!Update.foundArchives) "archive was reset instead of restored";
   let before=Array.length(Sys.readdir "/dev/fd") in
   let directory=Unix.openfile(Filename.concat state ("manifest-"^nonce)) [Unix.O_RDONLY;Unix.O_CLOEXEC] 0 in
   let loaded=Fun.protect ~finally:(fun () -> Unix.close directory) (fun () ->
     Update.load_component_owner_index left ~directory ~max_entries:1 ~max_bytes:4096 ()) in
   require((match loaded with Some value -> DngComponents.owner_index_usage value=(0,0)
     | None -> false)) "archive-owned managed index did not load";
   require(Array.length(Sys.readdir "/dev/fd")=before) "archive-owned loader leaked FD";
   require(Update.load_component_owner_index right ~directory:Unix.stdin ~max_entries:1
     ~max_bytes:4096 ()=None) "missing endpoint hint touched arbitrary namespace";
   Update.commitUpdates ()
 end else begin
   require(Update.component_owner_reference left=None && Update.component_owner_reference right=None)
     "disabled/absent/malformed hint became authority";
   require(!Update.foundArchives) "optional hint failure reset archives";
   require(Update.load_component_owner_index left ~directory:Unix.stdin ~max_entries:1
     ~max_bytes:4096 ()=None) "disabled/missing/corrupt hint touched namespace";
   if phase="off" then Update.commitUpdates ()
 end;
 Lwt_unix.run(Update.unlockArchives ());Globals.uninstallRoots ();
 Printf.printf "PASS private archive phase %s; references endpoint-local; no file data/SDK/transport\n%!" phase
