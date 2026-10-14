open Lwt
let reserve_entry budget ~prefix_bytes ~name_bytes =
  try ValidationTreeBudget.reserve budget ~prefix_bytes ~name_bytes
  with ValidationTreeBudget.Exceeded reason -> raise (Util.Transient reason)
let enabled () = match CandidateValidators.selected () with [] -> false | _ -> true
let with_descriptor path operation =
  let owned = ref true in
  let close fd = if !owned then begin owned := false;
    try Unix.close fd with Unix.Unix_error _ -> () end in
  let fd = Unix.openfile path [Unix.O_RDONLY;Unix.O_CLOEXEC;Unix.O_NONBLOCK] 0 in
  try BorrowedWork.try_bind (fun () -> operation fd)
    (fun result -> close fd;
      return result)
    (fun e -> close fd; fail e)
  with e -> close fd; raise e
let snapshot_of_fingerprint (result:SemanticWorkers.fingerprint) =
  let sha256 = SemanticHash.hex result.SemanticWorkers.digest in
  let st = result.SemanticWorkers.stats in
  { CandidateValidator.sha256; size = st.Unix.LargeFile.st_size;
    identity = Printf.sprintf "%d:%d:%Ld:%.17g:%.17g:%d:%d"
      st.Unix.LargeFile.st_dev st.Unix.LargeFile.st_ino st.Unix.LargeFile.st_size
      st.Unix.LargeFile.st_mtime st.Unix.LargeFile.st_ctime
      st.Unix.LargeFile.st_perm st.Unix.LargeFile.st_nlink }
let snapshot pool cancellation path =
  BorrowedWork.bind (fun () -> with_descriptor path (SemanticWorkers.digest pool cancellation)) (function
  | None -> fail (Util.Transient "Validation hashing cancelled")
  | Some result -> return (snapshot_of_fingerprint result))
type tree_entry = {
  path : Path.local;
  stats : Unix.LargeFile.stats;
  link : string option;
  properties : Props.t option;
  resource : Osx.ressStamp option;
}
let stable_stats stats = {stats with Unix.LargeFile.st_atime = 0.}
let all_children budget ~prefix_bytes path =
  let directory = Fs.opendir path in
  let rec read acc =
    Abort.checkAll ();
    match directory.Fs.readdir () with
    | "." | ".." -> read acc
    | name ->
        reserve_entry budget ~prefix_bytes ~name_bytes:(String.length name);
        read (name :: acc)
    | exception End_of_file -> List.sort String.compare acc in
  match read [] with
  | names -> directory.Fs.closedir (); names
  | exception e -> (try directory.Fs.closedir () with _ -> ()); raise e
let tree_snapshot directory candidate =
  let budget = ValidationTreePolicy.budget () in
  reserve_entry budget ~prefix_bytes:0 ~name_bytes:(String.length (Path.toString candidate));
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
      if ValidationTreeBudget.memory_enabled budget then begin
        let charge bytes = try ValidationTreeBudget.charge_metadata budget bytes
          with ValidationTreeBudget.Exceeded reason -> raise (Util.Transient reason) in
        Option.iter (fun target -> charge (String.length target)) link;
        Option.iter (fun properties -> charge (String.length (Umarshal.to_string Props.m properties))) properties
      end;
      let pending = if stats.Unix.LargeFile.st_kind = Unix.S_DIR then
        let prefix_bytes = String.length (Path.toString path) + 1 in
        List.fold_left (fun rest name -> Path.child path (Name.fromString name) :: rest)
          rest (all_children budget ~prefix_bytes absolute)
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
let validate_file ?partition ~reservation ~validators ~destination path =
  Abort.checkAll ();
  let runtime = SemanticRuntime.get () in
  let supervisor = runtime.SemanticRuntime.supervisor
  and budget = runtime.SemanticRuntime.cpu_budget
  and pool = runtime.SemanticRuntime.pool in
  let requirements = CandidateValidators.maximum_resources validators in
  if BackendResources.cpu_lanes requirements > budget then
    raise (Util.Fatal "Backend CPU declaration exceeds the shared budget");
  let payload_bytes,descriptors = BackendResources.add_cost requirements
    ~bytes:1048576 ~descriptors:9 in
  let candidate = Fspath.toString path in
  let recognizers = List.map (fun (validator:CandidateValidator.selected) ->
    validator.recognition,
    FormatRecognition.matches_filename validator.recognition destination) validators in
  SemanticRuntime.with_cancellation (fun cancellation ->
    let admitted f = match partition with
      | None -> SemanticRuntime.with_admission ?reservation cancellation ~payload_bytes ~descriptors f
      | Some gate -> BorrowedWork.bind
          (fun () -> SemanticAdmission.with_lease gate cancellation ~role:SemanticAdmission.Consumer
            ~cost:{SemanticAdmission.payload_bytes;descriptors} f)
          (function Some result -> return result
           | None -> fail (Util.Transient "Validation partition admission cancelled")) in
    admitted (fun () ->
      (* Recognition and the initial full digest use the same held input. Close
         that owner before helper execution; every phase retains this one loan. *)
      BorrowedWork.bind
        (fun () -> with_descriptor candidate (SemanticWorkers.identify pool cancellation ~recognizers)) (function
      | None -> fail (Util.Transient "Validation recognition cancelled")
      | Some {SemanticWorkers.formats=[];fingerprint=None;_} -> return ()
      | Some {SemanticWorkers.formats;fingerprint=Some fingerprint;_} when formats <> [] ->
          let selected = List.filter (fun (validator:CandidateValidator.selected) ->
            List.mem (FormatRecognition.format validator.recognition) formats) validators in
          if List.length selected <> List.length formats then
            fail (Util.Transient "Unexpected validation recognition selection")
          else
          let context = {
            CandidateValidator.supervisor;cancellation;cpu_budget=budget;candidate;
            expected=snapshot_of_fingerprint fingerprint;resources=requirements;
            inspect=snapshot pool cancellation;
            execute=SemanticRuntime.with_io_file cancellation candidate;
          } in
          let rec invoke = function
            | [] -> Abort.checkAll (); return ()
            | (validator:CandidateValidator.selected)::rest ->
                Abort.checkAll ();
                BorrowedWork.bind (fun () -> validator.validate {context with resources=validator.resources}) (fun () -> invoke rest) in
          invoke selected
      | Some _ -> fail (Util.Transient "Inconsistent validation recognition fingerprint"))))
let validate_tree ?partition ~count ~reservation ~validators ~directory ~candidate ~destination () =
  let before = Util.convertUnixErrorsToTransient "recording validation candidate tree"
    (fun () -> tree_snapshot directory candidate) in
  (* A staged directory is committed as a unit. A fixed number of owner-loop
     consumers pull files lazily; helpers still share the global weighted CPU
     budget. Await every active consumer on failure before allowing cleanup. *)
  let remaining = ref (List.filter_map (fun entry ->
    let destination = if entry.path = candidate then destination else entry.path in
    if entry.stats.Unix.LargeFile.st_kind = Unix.S_REG then
      Some (Fspath.concat directory entry.path,Path.toString destination)
    else None) before) and failed = ref false and failure = ref Out_of_memory in
  let remember error = if not !failed then begin failed := true; failure := error end in
  let next () = match !remaining with
    | [] -> None
    | path :: rest -> remaining := rest; Some path in
  let rec consume () =
    if !failed then return () else
    BorrowedWork.catch (fun () -> match next () with
      | None -> return ()
      | Some (path,destination) -> BorrowedWork.bind
          (fun () -> validate_file ?partition ~reservation ~validators ~destination path) (fun () -> consume ()))
      (fun error -> remember error; return ()) in
  (* A retained publication envelope loans one workspace at a time. Legacy
     directory handoff uses the same serial loan rather than nested admission. *)
  BorrowedWork.catch (fun () ->
    BorrowedWork.bind
      (fun () -> BorrowedWork.all ~on_error:remember (List.init count (fun _ -> consume)))
      (fun _ -> if !failed then fail !failure
        else (verify_tree before (tree_snapshot directory candidate); return ())))
    (fun e -> match e with
      | Unix.Unix_error _ | SemanticFile.Invalid _ | SemanticWorkers.Failed _ ->
        fail (Util.Transient ("Inspecting validation candidate: " ^ Printexc.to_string e))
      | _ -> fail e)

let before_commit_with_reservation ~reservation ~directory ~candidate ~destination =
  let validators = CandidateValidators.selected () in
  if validators = [] then return () else
  let manifests = ValidationTreePolicy.memory_bytes () in
  let _,cpu_budget = SemanticRuntime.helper_supervisor () in
  let resources = CandidateValidators.maximum_resources validators in
  if BackendResources.cpu_lanes resources > cpu_budget then
    raise (Util.Fatal "Backend CPU declaration exceeds the shared budget");
  let count = match reservation with Some _ -> 1
    | None ->
        if manifests <> 0 && (Util.convertUnixErrorsToTransient "recording validation candidate kind"
          (fun () -> Fs.lstat (Fspath.concat directory candidate))).Unix.LargeFile.st_kind <> Unix.S_DIR
        then 1 else min 256 (if manifests=0 then cpu_budget else
          BackendResources.parallel_workspaces resources ~cpu_budget) in
  if manifests = 0 then
    validate_tree ~count ~reservation ~validators ~directory ~candidate ~destination ()
  else begin
    let per_bytes,per_descriptors = BackendResources.add_cost resources ~bytes:1048576 ~descriptors:9 in
    let scale value = if value > max_int / count then
        raise (Util.Fatal "Validation tree workspace accounting overflow") else value * count in
    let child_bytes = scale per_bytes and child_descriptors = scale per_descriptors in
    if child_bytes > max_int - 2 * manifests || child_descriptors > max_int - 15 then
      raise (Util.Fatal "Validation tree workspace accounting overflow");
    let payload_bytes = child_bytes + 2 * manifests and descriptors = child_descriptors + 15 in
    SemanticRuntime.with_cancellation (fun cancellation ->
      SemanticRuntime.with_admission ?reservation cancellation ~payload_bytes ~descriptors (fun () ->
        (* This gate partitions already-held credits. Its leases never wait on
           the global gate. The complete tree and all children settle before
           the parent envelope can retire, including rejection/cancellation. *)
        let partition = SemanticAdmission.create ~source_headroom:None ~max_transactions:count
          ~max_payload_bytes:child_bytes ~max_descriptors:child_descriptors ~max_pending:count in
        BorrowedWork.bind
          (fun () -> validate_tree ~partition ~count ~reservation:None ~validators ~directory ~candidate ~destination ())
          (fun () ->
            let usage = SemanticAdmission.usage partition in
            if usage.transactions <> 0 || usage.pending <> 0 then
              fail (Util.Transient "Validation partition did not settle") else return ()) ))
  end

let before_commit ~directory ~candidate ~destination =
  before_commit_with_reservation ~reservation:None ~directory ~candidate ~destination
