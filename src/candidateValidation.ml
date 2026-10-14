open Lwt
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
let validate_file ~reservation ~validators ~destination path =
  Abort.checkAll ();
  let runtime = SemanticRuntime.get () in
  let supervisor = runtime.SemanticRuntime.supervisor
  and budget = runtime.SemanticRuntime.cpu_budget
  and pool = runtime.SemanticRuntime.pool in
  let candidate = Fspath.toString path in
  let recognizers = List.map (fun (validator:CandidateValidator.selected) ->
    validator.recognition,
    FormatRecognition.matches_filename validator.recognition destination) validators in
  SemanticRuntime.with_cancellation (fun cancellation ->
    SemanticRuntime.with_admission ?reservation cancellation ~payload_bytes:1048576 ~descriptors:9 (fun () ->
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
            expected=snapshot_of_fingerprint fingerprint;
            inspect=snapshot pool cancellation;
            execute=SemanticRuntime.with_io_file cancellation candidate;
          } in
          let rec invoke = function
            | [] -> Abort.checkAll (); return ()
            | (validator:CandidateValidator.selected)::rest ->
                Abort.checkAll ();
                BorrowedWork.bind (fun () -> validator.validate context) (fun () -> invoke rest) in
          invoke selected
      | Some _ -> fail (Util.Transient "Inconsistent validation recognition fingerprint"))))
let before_commit_with_reservation ~reservation ~directory ~candidate ~destination =
  let validators = CandidateValidators.selected () in
  if validators = [] then return () else
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
          (fun () -> validate_file ~reservation ~validators ~destination path) (fun () -> consume ()))
      (fun error -> remember error; return ()) in
  (* A retained publication envelope loans one workspace at a time. Legacy
     directory handoff uses the same serial loan rather than nested admission. *)
  let count = match reservation with Some _ -> 1
    | None -> min 256 (SemanticRuntime.get ()).SemanticRuntime.cpu_budget in
  BorrowedWork.catch (fun () ->
    BorrowedWork.bind
      (fun () -> BorrowedWork.all ~on_error:remember (List.init count (fun _ -> consume)))
      (fun _ -> if !failed then fail !failure
        else (verify_tree before (tree_snapshot directory candidate); return ())))
    (fun e -> match e with
      | Unix.Unix_error _ | SemanticFile.Invalid _ | SemanticWorkers.Failed _ ->
        fail (Util.Transient ("Inspecting validation candidate: " ^ Printexc.to_string e))
      | _ -> fail e)

let before_commit ~directory ~candidate ~destination =
  before_commit_with_reservation ~reservation:None ~directory ~candidate ~destination
