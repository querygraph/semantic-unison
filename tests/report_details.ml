(* One-shot current-file observations must not become stale cached UI labels. *)
module U = UicommonForTest
let require value message = if not value then failwith message
let write path contents = let channel=open_out_bin path in
  output_string channel contents; close_out channel
let () =
  let root=Sys.getenv "UNISON_DETAIL_TEST_ROOT" in
  let left=Filename.concat root "left" and right=Filename.concat root "right" in
  Globals.setRawRoots [left;right];
  Lwt_unix.run (Globals.installRoots None); Globals.installRoots2 ();
  let file=Filename.concat left "observed" in write file "original";
  let path=Fspath.canonize (Some file) in
  let item={Common.path1=Path.fromString "observed";path2=Path.fromString "observed";
            replicas=Common.Problem "test row"} in
  let remember ?(target=path) () =
    U.semantic_detail:=Some {U.item;roots=Globals.roots ();snapshots=[target,Fs.stat target];text="semantic observation"} in
  remember ();
  require (U.take_semantic_detail item=Some "semantic observation") "fresh local observation discarded";
  require (U.take_semantic_detail item=None) "one-shot annotation reused by later formatting";
  remember ();
  write file "changed length after inspection";
  require (U.take_semantic_detail item=None) "changed file displayed stale classification";
  remember ();
  let replacement=Filename.concat left "replacement" in write replacement "changed length after inspection";
  Unix.rename replacement file;
  require (U.take_semantic_detail item=None) "replaced inode displayed stale classification";
  remember ();
  let other={item with Common.path1=Path.fromString "another"} in
  require (U.take_semantic_detail other=None) "annotation attached to another reconciliation row";
  let link=Filename.concat left "followed" in Unix.symlink file link;
  let link=Fspath.canonize (Some link) in remember ~target:link ();
  require (U.take_semantic_detail item=Some "semantic observation") "intentional followed symlink rejected";
  remember ();
  Remote.clientCloseRootConnection (Common.Local,Fspath.canonize (Some left));
  require (U.take_semantic_detail item=None) "connection close retained old observation";
  print_endline "Details observations: one-shot, changed/replaced files, row binding, followed symlinks and disconnect invalidation passed."
