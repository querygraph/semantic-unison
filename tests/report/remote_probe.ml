(* Production-linked probe, never an IO admission. The external owner supplies
   private generated roots, pinned binaries/launcher and all process proofs. *)
let require yes why = if not yes then failwith why
let summary value = match value.SemanticRemote.component_observation with
  | Ok value -> value | Error why -> failwith why
exception Cleanup_failed of exn option * exn list
let () =
  if Array.length Sys.argv<>6 then begin
    prerr_endline "usage: component-probe LEFT RIGHT SERVER LAUNCHER supported|unsupported|no-capability|disabled|preflight";
    exit 2
  end;
  let left=Sys.argv.(1) and right=Sys.argv.(2) and server=Sys.argv.(3)
  and launcher=Sys.argv.(4) and mode=Sys.argv.(5) in
  List.iter (fun path -> require (not (Filename.is_relative path)) "absolute probe paths required")
    [left;right;server;launcher];
  require (List.mem mode ["supported";"unsupported";"no-capability";"disabled";"preflight"]) "unknown probe mode";
  Prefs.loadStrings ["semanticworkers = 2";"maxthreads = 2";"adobevalidate = off";
    "semanticdng = " ^ (if mode="disabled" then "false" else "true");
    "sshcmd = " ^ launcher;"servercmd = " ^ server];
  if mode="preflight" then begin
    print_endline "PROBE_PREFLIGHT_ONLY (preferences parsed; no roots installed or connection attempted)";
    exit 0
  end;
  Globals.setRawRoots [left;"ssh://localhost/" ^ right];
  let connected=ref [] and runtime=ref None in
  let cleanup () =
    let errors=ref [] in
    let attempt f=try f () with error -> errors:=error::!errors in
    List.iter (fun root -> attempt (fun () -> Remote.clientCloseRootConnection root)) !connected;
    (match !runtime with None -> () | Some state ->
      attempt (fun () -> Lwt_unix.run (SemanticWorkers.shutdown state.SemanticRuntime.pool));
      attempt (fun () -> require (HelperSupervisor.usage state.supervisor=(0,0)) "probe permits not settled"));
    List.rev !errors in
  let finish original = match original,cleanup () with
    | None,[] -> () | Some error,[] -> raise error
    | original,errors -> raise (Cleanup_failed (original,errors)) in
  let run () =
      Lwt_unix.run (Globals.installRoots None);
      let root1,root2=Globals.roots () in connected := [root1;root2];
      Lwt_unix.run (Globals.propagatePrefs ());
      let state=SemanticRuntime.get () in runtime:=Some state;
      require (state.cpu_budget=2) "probe CPU configuration differs";
      let inspect root=SemanticRemote.observe_components ~root
        ~path:(Fspath.concat (snd root) (Path.fromString "components.dng")) in
      let a=summary (Lwt_unix.run (inspect root1)) in
      let b=Lwt_unix.run (inspect root2) in
      require (b.SemanticRemote.component_snapshot=None) "peer acquired a local snapshot capability";
      (match mode,b.component_observation with
       | "supported",Ok b ->
           require (a.schema=b.schema && a.full_sha256<>b.full_sha256) "full identity/schema differs from fixture contract";
           let lane role value=List.assoc role value.SemanticReport.projections in
           require (lane ComponentHash.Encoded_pixels a<>None &&
             lane ComponentHash.Encoded_pixels a=lane ComponentHash.Encoded_pixels b) "pixel view differs";
           require (lane ComponentHash.Opaque a<>lane ComponentHash.Opaque b) "opaque mutation lost";
           Printf.printf "LOCAL_SHA256 %s\nREMOTE_SHA256 %s\n%!"
             (SemanticHash.hex a.full_sha256) (SemanticHash.hex b.full_sha256);
           (match SemanticReport.render_components ~left:a ~right:b with
            | Ok text -> print_string text | Error why -> failwith why)
       | "unsupported",Error why ->
           require (why="not TIFF") "unsupported fixture did not return its exact parser refusal";
           Printf.printf "REMOTE_UNSUPPORTED %s\n%!" (SemanticReport.display_reason why)
       | "no-capability",Error "Remote component inspection is not negotiated" -> ()
       | "disabled",Error "Component DNG profile is not enabled or negotiated" -> ()
       | _ -> failwith "unexpected component probe outcome");
      Printf.printf "PROBE_FUNCTIONAL %s\n%!" mode in
  (match run () with () -> finish None | exception error -> finish (Some error));
  print_endline "PROBE_LOCAL_RESOURCES_CLOSED (external client/server wait proofs still required)"
