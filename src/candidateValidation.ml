open Lwt
let category = `Advanced `General
let policy_pref = Prefs.createString "adobevalidate" "off" ~local:true ~category
  "validate received DNG files (off, warn, require)"
  "Run a qualified Adobe SDK validation driver on each received DNG before \
   committing it. Require blocks failed or unavailable validation; warn \
   explicitly permits it with a warning. Independent of semanticdng."
let validator = Prefs.makeEndpointLocal (Prefs.createString "adobevalidator" "" ~local:true ~category
  "absolute Adobe SDK validation driver path"
  "Absolute path to the qualified structured Adobe SDK validation driver. \
   The stock dng_validate command alone does not implement this protocol.")
let tool_hash = Prefs.makeEndpointLocal (Prefs.createString "adobevalidatorhash" "" ~local:true ~category
  "SHA-256 pin for the Adobe validation driver"
  "Lowercase full executable SHA-256 for the qualified validation driver.")
let build_id = Prefs.makeEndpointLocal (Prefs.createString "adobevalidatorbuild" "" ~local:true ~category
  "qualified Adobe validation driver build identifier"
  "Expected exact build identifier in the driver's structured receipt.")
let tool_threads = Prefs.makeEndpointLocal (Prefs.createInt "adobevalidatorthreads" 1 ~local:true ~category
  "CPU threads reserved for each Adobe SDK driver"
  "Thread count passed to the qualified SDK driver and reserved from the \
   shared CPU budget. It must describe actual driver parallelism.")
let timeout = Prefs.makeEndpointLocal (Prefs.createInt "adobevalidatetimeout" 300 ~local:true ~category
  "maximum seconds for each Adobe SDK validation"
  "Execution timeout after CPU admission. A timed-out driver is terminated \
   and reaped before require rejects the candidate.")
let policy () = match Prefs.read policy_pref with
  | "off" -> DngValidation.Off | "warn" -> DngValidation.Warn
  | "require" -> DngValidation.Require
  | _ -> raise (Util.Fatal "adobevalidate must be off, warn, or require")
let enabled () = policy () <> DngValidation.Off
let _feature = Features.register "dng-validation-v0" (Some (fun _ enabled ->
  if policy () <> DngValidation.Off && not enabled then
    Some "Requested Adobe validation requires dng-validation-v0 support on both replicas"
  else None))
let snapshot pool cancellation path =
  let fd = Unix.openfile path [Unix.O_RDONLY;Unix.O_CLOEXEC;Unix.O_NONBLOCK] 0 in
  let close () = try Unix.close fd with Unix.Unix_error _ -> () in
  Lwt.try_bind (fun () -> SemanticWorkers.digest pool cancellation fd)
    (fun result -> close ();
      let result = match result with None -> raise (Util.Transient "Validation hashing cancelled")
        | Some result -> result in
      let sha256 = SemanticHash.hex result.SemanticWorkers.digest in
      let st = result.SemanticWorkers.stats in
      return { DngValidation.sha256; size = st.Unix.LargeFile.st_size;
        identity = Printf.sprintf "%d:%d:%Ld:%.17g:%.17g:%d:%d"
          st.Unix.LargeFile.st_dev st.Unix.LargeFile.st_ino st.Unix.LargeFile.st_size
          st.Unix.LargeFile.st_mtime st.Unix.LargeFile.st_ctime
          st.Unix.LargeFile.st_perm st.Unix.LargeFile.st_nlink })
    (fun e -> close (); fail e)
let is_dng path =
  Filename.check_suffix (String.lowercase_ascii (Path.toString path)) ".dng"
type tree_entry = {
  path : Path.local;
  stats : Unix.LargeFile.stats;
  link : string option;
  properties : Props.t option;
  resource : Osx.ressStamp option;
}
let stable_stats stats = {stats with Unix.LargeFile.st_atime = 0.}
let all_children path =
  let directory = Fs.opendir path in
  let rec read acc = match directory.Fs.readdir () with
    | "." | ".." -> read acc
    | name -> read (name :: acc)
    | exception End_of_file -> List.sort String.compare acc in
  match read [] with
  | names -> directory.Fs.closedir (); names
  | exception e -> (try directory.Fs.closedir () with _ -> ()); raise e
let tree_snapshot directory candidate =
  (* Inspect every entry, including hidden, AppleDouble and Unison temporary
     names. Never follow a symlink or apply Os.childrenOf's filtering/deletion.
     This O(entries) metadata manifest is retained until all helpers settle. *)
  let rec scan pending entries = match pending with
    | [] -> List.rev entries
    | path :: rest ->
      Abort.checkAll ();
      let absolute = Fspath.concat directory path in
      let stats = stable_stats (Fs.lstat absolute) in
      let link = if stats.Unix.LargeFile.st_kind = Unix.S_LNK
        then Some (Fs.readlink absolute) else None in
      let properties,resource = match stats.Unix.LargeFile.st_kind with
        | Unix.S_REG | Unix.S_DIR ->
          let info = Fileinfo.get false directory path in
          Some info.Fileinfo.desc, Some (Fileinfo.ressStamp info)
        | _ -> None,None in
      let pending = if stats.Unix.LargeFile.st_kind = Unix.S_DIR then
        List.fold_left (fun rest name -> Path.child path (Name.fromString name) :: rest)
          rest (all_children absolute)
        else rest in
      if stable_stats (Fs.lstat absolute) <> stats then
        raise (Util.Transient "Validation candidate changed while recording its tree");
      scan pending ({path;stats;link;properties;resource} :: entries)
  in scan [candidate] []
let same_tree_entry a b =
  a.path = b.path && a.stats = b.stats && a.link = b.link && a.resource = b.resource &&
  match a.properties,b.properties with
  | None,None -> true
  | Some a,Some b -> Props.similar a b
  | _ -> false
let verify_tree before after =
  let rec same before after = match before,after with
    | [],[] -> true
    | a::before,b::after -> same_tree_entry a b && same before after
    | _ -> false in
  if not (same before after) then
    raise (Util.Transient "Validation candidate tree changed during validation")
let validate_file ~selected path =
  Abort.checkAll ();
  let runtime = SemanticRuntime.get () in
  let supervisor = runtime.SemanticRuntime.supervisor
  and budget = runtime.SemanticRuntime.cpu_budget
  and pool = runtime.SemanticRuntime.pool in
  let weight = Prefs.read tool_threads in
  if weight < 1 || weight > budget then
    raise (Util.Fatal "adobevalidatorthreads must be between one and the CPU budget");
  if Prefs.read timeout <= 0 then raise (Util.Fatal "adobevalidatetimeout must be positive");
  let tool = if Prefs.read validator = "" then None else Some {
    DngValidation.executable = Prefs.read validator;
    executable_sha256 = Prefs.read tool_hash; build_id = Prefs.read build_id;
    arguments = [||]; environment = [|"LANG=C";"LC_ALL=C";"PATH=/usr/bin:/bin"|];
    cpu_weight = weight;
    limits = {HelperSupervisor.timeout = float_of_int (Prefs.read timeout);
      terminate_grace = 2.; stdout_bytes = 16384; stderr_bytes = 262144} } in
  let candidate = Fspath.toString path in
  SemanticRuntime.with_cancellation (fun cancellation ->
    SemanticRuntime.with_admission cancellation ~payload_bytes:1048576 ~descriptors:9 (fun () ->
    let inspect path = snapshot pool cancellation path in
    inspect candidate >>= fun expected ->
    DngValidation.validate_with_execution
      ~execute:(SemanticRuntime.with_io_file cancellation candidate)
      supervisor cancellation ~policy:selected ~tool
      ~inspect ~candidate ~expected))
  >>= fun result ->
  Abort.checkAll ();
  match result with
  | DngValidation.Skipped | DngValidation.Passed _ -> return ()
  | DngValidation.Warning (reason,_) ->
      Trace.log (Printf.sprintf "Adobe DNG validation warning for %s: %s\n" candidate reason);
      return ()
  | DngValidation.Rejected (reason,_) ->
      fail (Util.Transient (Printf.sprintf "Adobe DNG validation rejected %s: %s" candidate reason))
let before_commit ~directory ~candidate ~destination =
  let selected = policy () in
  if selected = DngValidation.Off then return () else
  let before = Util.convertUnixErrorsToTransient "recording validation candidate tree"
    (fun () -> tree_snapshot directory candidate) in
  (* A staged directory is committed as a unit. A fixed number of owner-loop
     consumers pull files lazily; helpers still share the global weighted CPU
     budget. Await every active consumer on failure before allowing cleanup. *)
  let remaining = ref (List.filter_map (fun entry ->
    let destination = if entry.path = candidate then destination else entry.path in
    if entry.stats.Unix.LargeFile.st_kind = Unix.S_REG && is_dng destination then
      Some (Fspath.concat directory entry.path)
    else None) before) and failure = ref None in
  let next () = match !remaining with
    | [] -> None
    | path :: rest -> remaining := rest; Some path in
  let rec consume () =
    if !failure <> None then return () else
    Lwt.catch (fun () -> match next () with
      | None -> return ()
      | Some path -> validate_file ~selected path >>= consume)
      (fun error -> if !failure = None then failure := Some error; return ()) in
  let count = min 256 (SemanticRuntime.get ()).SemanticRuntime.cpu_budget in
  Lwt.catch (fun () ->
    Lwt_util.iter (fun _ -> consume ()) (List.init count (fun i -> i)) >>= fun () ->
    match !failure with
    | None -> verify_tree before (tree_snapshot directory candidate); return ()
    | Some error -> fail error)
    (fun e -> match e with
      | Unix.Unix_error _ | SemanticFile.Invalid _ | SemanticWorkers.Failed _ ->
        fail (Util.Transient ("Inspecting validation candidate: " ^ Printexc.to_string e))
      | _ -> fail e)
