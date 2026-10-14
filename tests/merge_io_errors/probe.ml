let check value message = if not value then failwith message
let fd_count () =
  let directory = Unix.opendir "/dev/fd" in
  Fun.protect ~finally:(fun () -> Unix.closedir directory) (fun () ->
    let rec loop n = match Unix.readdir directory with
      | "." | ".." -> loop n | _ -> loop (n+1)
      | exception End_of_file -> n in loop 0)
let () =
  Prefs.loadStrings ["semanticworkers = 1"; "semanticvolumejobs = 1"];
  let runtime = SemanticRuntime.get () in
  let root = Fspath.canonize (Some (Sys.getcwd ())) in
  let file name = Fspath.concat root (Path.fromString name) in
  let fingerprint = Os.data_only_fingerprint (Fingerprint.file root (Path.fromString "base")) in
  let baseline = fd_count () in
  let failures = ref 0 in
  List.iter (fun (name,base,left,right,output) ->
    let result = try
      ignore (Lwt_unix.run (SemanticSync.merge_local_async ~base_fingerprint:fingerprint
        ~base:(file base) ~left:(file left) ~right:(file right) ~output:(file output)));
      "unexpected success"
    with Util.Transient message -> "transient: " ^ message
       | error -> Printexc.to_string error in
    let a = SemanticAdmission.usage runtime.admission in
    let w = SemanticWorkers.usage runtime.pool in
    let io = IoAdmission.usage runtime.io in
    check (fd_count () = baseline) (name ^ ": descriptor not settled");
    check (a.transactions=0 && a.pending=0 && a.payload_bytes=0 && a.descriptors=0)
      (name ^ ": transaction credits not settled");
    check (w.pending=0 && w.running=0 && io.active_jobs=0 && io.pending=0)
      (name ^ ": worker/I/O not settled");
    check (HelperSupervisor.usage runtime.supervisor = (0,0)) (name ^ ": CPU not settled");
    if not (String.starts_with ~prefix:"transient: " result) then incr failures;
    Printf.printf "%s %s: %s\n%!" (if String.starts_with ~prefix:"transient: " result then "PASS" else "FAIL") name result)
    ["missing-base","absent","left","right","output";
     "missing-left","base","absent","right","output";
     "missing-right","base","left","absent","output";
     "missing-output","base","left","right","absent";
     "base-parent-not-directory","base/child","left","right","output";
     "output-is-directory","base","left","right","directory"];
  Lwt_unix.run (SemanticWorkers.shutdown runtime.pool);
  if !failures <> 0 then exit 2
