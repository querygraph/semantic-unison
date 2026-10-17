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
  require (not (SemanticRemote.component_details_enabled ())) "component pass enabled by default";
  Prefs.loadStrings ["semanticcomponents = true"];
  require (SemanticRemote.component_details_enabled ()) "explicit component preference ignored";
  Prefs.loadStrings ["semanticworkers = 2"];
  let root1,root2=Globals.roots () in
  let remote=Lwt_unix.run (SemanticRemote.observe_components
    ~root:(Common.Remote "no-component-connection",snd root1) ~path) in
  require (remote.component_observation=Error "Component DNG profile is not enabled or negotiated" &&
    remote.component_snapshot=None) "unnegotiated component request attempted a remote observation";
  let inspect root = SemanticRemote.observe_components ~root
    ~path:(Fspath.concat (snd root) (Path.fromString "components.dng")) in
  let a=Lwt_unix.run (inspect root1) and b=Lwt_unix.run (inspect root2) in
  let summary value=match value.SemanticRemote.component_observation with
    | Ok value -> value | Error why -> failwith why in
  let a_summary=summary a and b_summary=summary b in
  require (a_summary.full_sha256<>b_summary.full_sha256) "opaque change lost from full identity";
  require (List.assoc ComponentHash.Encoded_pixels a_summary.projections=
    List.assoc ComponentHash.Encoded_pixels b_summary.projections) "opaque change invalidated pixel view";
  require (a.component_snapshot<>None && b.component_snapshot<>None) "owner snapshot binding omitted";
  let text=match SemanticReport.render_components ~left:a_summary ~right:b_summary with
    | Ok text -> text | Error why -> failwith why in
  require (String.length text>0) "owner component report empty";
  let unsupported=Lwt_unix.run (SemanticRemote.observe_components ~root:root1 ~path) in
  require (match unsupported.component_observation with Error _ -> true | _ -> false)
    "non-DNG observation became supported";
  let missing=Fspath.concat (snd root1) (Path.fromString "absent-components.dng") in
  require (match (Lwt_unix.run (SemanticRemote.observe_components ~root:root1 ~path:missing)).component_observation
    with Error _ -> true | _ -> false) "missing-file operational refusal lost";
  let runtime=SemanticRuntime.get () in
  Lwt_unix.run (SemanticWorkers.shutdown runtime.pool);
  require (HelperSupervisor.usage runtime.supervisor=(0,0)) "component owner leaked permits";
  print_endline "Component owner: explicit preference/default off, local views, remote refusal, opaque/pixel separation, snapshots, unsupported/missing paths and settled permits passed.";
  print_endline "Details observations: one-shot, changed/replaced files, row binding, followed symlinks and disconnect invalidation passed."
