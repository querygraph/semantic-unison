(* Links actual retained pre-hint production modules, not a model of their reader. *)
let require yes why=if not yes then failwith why
let () =
 if Array.length Sys.argv<>3 then (prerr_endline "usage: old-archive-probe PRIVATE_CASE read|rewrite";exit 2);
 let folder=Sys.argv.(1) and phase=Sys.argv.(2) in
 require(not(Filename.is_relative folder) && List.mem phase ["read";"rewrite"]) "private legacy phase required";
 let state=Filename.concat folder "state" in
 require(Sys.getenv "UNISON"=state && Util.unisonDir=state) "private UNISON confinement required";
 let info=Unix.lstat state in
 require(info.Unix.st_kind=Unix.S_DIR && info.st_uid=Unix.getuid () && info.st_perm land 0o7777=0o700)
   "private owner state required";
 Prefs.loadStrings ["log = false"];
 Case.init true Osx.isMacOSX;Props.init false;Osx.init Osx.isMacOSX;Fileinfo.init false;
 Globals.setRawRoots [Filename.concat folder "left";Filename.concat folder "right"];
 Lwt_unix.run(Globals.installRoots None);Update.storeRootsName ();
 Lwt_unix.run(Globals.propagatePrefs ());
 let first,second=Globals.roots () in
 require(fst first=Common.Local && fst second=Common.Local) "local roots only";
 ignore(Update.findUpdates ~wantWatcher:false None);
 require(!Update.foundArchives) "old reader reset archives";
 if phase="rewrite" then Update.commitUpdates ();
 Lwt_unix.run(Update.unlockArchives ());Globals.uninstallRoots ();
 Printf.printf "PASS retained old-code archive %s; no component hint registration/file data/remote transport\n%!" phase
