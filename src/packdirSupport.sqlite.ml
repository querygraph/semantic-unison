(* Built with the packdir library (tools/packdir, SQLite through the opam
   sqlite3 binding): packed roots are supported.

   Update detection on the packed root goes through PackdirHook. A
   container X.sqlar, with no plain X/ beside it, is the directory X; its
   members are X's files, with the plain files of X/ when the two sit side
   by side (a member wins for a name in both). A container is read once per
   run, and not at all while its file is as a state file in the Unison
   directory records it. *)

module N = Dng_archive.Native

let available = true
let debug = Trace.debug "packdir"

let root : Fspath.t option ref = ref None
let depth = ref 0

let owns fspath = match !root with Some r -> r = fspath | None -> false

let depth_of path =
  if Path.isEmpty path then 0 else List.length (String.split_on_char '/' (Path.toString path))

let abs fspath path = Fspath.toString (Fspath.concat fspath path)

let is_dir p = match N.stat ~follow:false p with s -> s.N.kind = `Dir | exception Unix.Unix_error _ -> false

let container_stat p = match N.stat ~follow:false (p ^ ".sqlar") with
  | s when s.N.kind = `Reg -> Some s
  | _ -> None
  | exception Unix.Unix_error _ -> None

(* Container rel path -> (file stamp, members), kept across runs. *)
type stamp = int64 * int64 * int64
let state : (string, stamp * Packdir.member list) Hashtbl.t = Hashtbl.create 1024
let state_path = ref ""
let dirty = ref false

let load_state () =
  try In_channel.with_open_bin !state_path (fun ic ->
    match (Marshal.from_channel ic : string * (string, stamp * Packdir.member list) Hashtbl.t) with
    | "unison-packdir-state/1", t -> Hashtbl.iter (Hashtbl.replace state) t
    | _ -> ())
  with Sys_error _ | End_of_file | Failure _ -> ()

let save_state () =
  if !dirty && !state_path <> "" then begin
    let temp = !state_path ^ ".tmp" in
    Out_channel.with_open_bin temp (fun oc -> Marshal.to_channel oc ("unison-packdir-state/1", state) []);
    Sys.rename temp !state_path;
    dirty := false
  end

(* Durability (docs/packdir-design.md, "Durability"). Containers written in a
   run are listed in a pending file before their first write; drive-cache
   barriers run every packbarrier GiB and before Unison's archives are
   committed; the list is cleared after the commit. A container listed as
   pending by an earlier run, or whose file no longer matches the state, may
   not have reached the platter whole: it is verified before use, and set
   aside when damaged, so the leaf reads as missing and is brought back. *)
let pending_path () = !state_path ^ ".pending"
let suspects : (string, unit) Hashtbl.t = Hashtbl.create 64
let pending_this_run : (string, unit) Hashtbl.t = Hashtbl.create 1024
let failed_this_run : (string, unit) Hashtbl.t = Hashtbl.create 64
let since_barrier = ref 0
let last_written = ref ""

let load_pending () =
  try List.iter (fun l -> if l <> "" then Hashtbl.replace suspects l ())
        (In_channel.with_open_bin (pending_path ()) In_channel.input_lines)
  with Sys_error _ -> ()

let mark_pending rel =
  if not (Hashtbl.mem pending_this_run rel) then begin
    Out_channel.with_open_gen [Open_wronly; Open_creat; Open_append; Open_binary] 0o600 (pending_path ()) (fun oc ->
      output_string oc (rel ^ "\n"); flush oc; Unix.fsync (Unix.descr_of_out_channel oc));
    Hashtbl.replace pending_this_run rel ()
  end

let barrier () =
  if !last_written <> "" then begin
    Packdir.barrier !last_written;
    debug (fun () -> Util.msg "packdir: barrier after %d bytes\n" !since_barrier);
    since_barrier := 0
  end

let wrote path bytes =
  last_written := path;
  since_barrier := !since_barrier + bytes;
  (* packbarrier = 0: a barrier after every container write. *)
  if !since_barrier >= Prefs.read PackdirConfig.barrier_gib * 1073741824 then barrier ()

let before_commit () =
  barrier ();
  save_state ();
  (* Tests: stop after the barrier, before Unison's archives are written. *)
  if Sys.getenv_opt "UNISON_PACKDIR_CRASH_BEFORE_COMMIT" <> None then Unix._exit 4

(* After the commit, only containers whose job failed stay pending: the next
   run verifies them before use. *)
let after_commit () =
  if Hashtbl.length pending_this_run > 0 || Hashtbl.length suspects > 0 then begin
    Out_channel.with_open_bin (pending_path () ^ ".tmp") (fun oc ->
      Hashtbl.iter (fun rel () -> output_string oc (rel ^ "\n")) failed_this_run;
      flush oc; Unix.fsync (Unix.descr_of_out_channel oc));
    Sys.rename (pending_path () ^ ".tmp") (pending_path ());
    Hashtbl.reset pending_this_run; Hashtbl.reset suspects;
    Hashtbl.iter (fun rel () -> Hashtbl.replace suspects rel ()) failed_this_run
  end

let set_aside rel p problems =
  let aside = Printf.sprintf "%s.sqlar.damaged-%.0f" p (Unix.time ()) in
  Sys.rename (p ^ ".sqlar") aside;
  Hashtbl.remove state rel; dirty := true;
  Util.warn (Printf.sprintf "packed root: %s.sqlar is damaged (%s); set aside as %s, and the leaf will be \
                             copied again\n" rel (String.concat "; " problems) aside)

(* Members of the container for [rel] (relative to the root): from the
   state when its file is unchanged, else read from the container, verified
   first when it may not have reached the platter whole. *)
let read_this_run : (string, Packdir.member list) Hashtbl.t = Hashtbl.create 1024
let members fspath rel =
  match Hashtbl.find_opt read_this_run rel with
  | Some m -> Some m
  | None ->
      let p = abs fspath (Path.fromString rel) in
      match container_stat p with
      | None -> None
      | Some s ->
          let st = (s.N.ino, s.N.size, s.N.mtime_ns) in
          let recorded = Hashtbl.find_opt state rel in
          let suspicious = Hashtbl.mem suspects rel ||
            (match recorded with Some (st', _) -> st' <> st | None -> false) in
          match recorded with
          | Some (st', m) when st' = st && not suspicious -> Hashtbl.replace read_this_run rel m; Some m
          | _ ->
              let c = Packdir.open_ (p ^ ".sqlar") in
              let problems, m = Fun.protect ~finally:(fun () -> Packdir.close c) (fun () ->
                (if suspicious then Packdir.verify c else []), Packdir.members c) in
              if problems <> [] then (set_aside rel p problems; None)
              else begin
                Hashtbl.replace state rel (st, m); dirty := true;
                Hashtbl.replace read_this_run rel m;
                Some m
              end

let stats ~kind ~perm ~size ~mtime =
  let t = Int64.to_float mtime /. 1e9 in
  { Unix.LargeFile.st_dev = 0; st_ino = 0; st_kind = kind; st_perm = perm; st_nlink = 1;
    st_uid = Unix.getuid (); st_gid = Unix.getgid (); st_rdev = 0; st_size = size;
    st_atime = t; st_mtime = t; st_ctime = t }

let member_named fspath path =
  let rel = Path.toString path in
  match members fspath (Filename.dirname rel) with
  | Some ms -> List.find_opt (fun (m : Packdir.member) -> m.name = Filename.basename rel && not m.retained) ms
  | None -> None

(* Members keep their mode in the sqlar table, but packed roots run with
   perms = 0 (checked in Uicommon), so a fixed mode is reported. *)
let member_perm = 0o644

let stat fspath path =
  if not (owns fspath) then None else
  let d = depth_of path in
  if d = !depth then begin
    let p = abs fspath path in
    if is_dir p then None
    else match container_stat p with
      | Some s -> Some (stats ~kind:Unix.S_DIR ~perm:0o755 ~size:0L ~mtime:s.N.mtime_ns)
      | None -> None
  end else if d = !depth + 1 then
    match member_named fspath path with
    | Some m -> Some (stats ~kind:Unix.S_REG ~perm:member_perm ~size:m.size ~mtime:m.mtime_ns)
    | None -> None
  else None

(* What Os.childrenOf would keep from a real listing. *)
let plain_names p =
  try List.filter (fun n ->
      n <> "." && n <> ".." && not (Os.isTempFile n) && not (String.length n > 2 && String.sub n 0 2 = "._"))
      (Array.to_list (Sys.readdir p))
  with Sys_error _ -> []

(* The container files and their companions, never shown as plain files. *)
let packdir_file n =
  Filename.check_suffix n ".sqlar" || Filename.check_suffix n ".sqlar-journal"
  || Filename.check_suffix n ".sqlar.repack" || Util.findsubstring ".sqlar.damaged-" n <> None

let children fspath path =
  if not (owns fspath) then None else
  let d = depth_of path in
  let p = abs fspath path in
  if d = 0 && !depth > 1 then
    (* The root: everything but the packed marker. *)
    Some (List.sort compare (List.filter (fun n -> n <> PackdirConfig.marker) (plain_names p)))
  else if d = !depth - 1 then begin
    let names = List.filter (fun n -> d > 0 || n <> PackdirConfig.marker) (plain_names p) in
    if not (List.exists packdir_file names) then None else
    let containers = List.filter_map (fun n ->
      if Filename.check_suffix n ".sqlar" then Some (Filename.chop_suffix n ".sqlar") else None) names in
    Some (List.sort_uniq compare (containers @ List.filter (fun n -> not (packdir_file n)) names))
  end else if d = !depth then
    match members fspath (Path.toString path) with
    | None -> None
    | Some ms ->
        (* Retained members are deletions kept on disk: not shown. *)
        let live = List.filter (fun (m : Packdir.member) -> not m.retained) ms in
        Some (List.sort_uniq compare (List.map (fun (m : Packdir.member) -> m.name) live @ plain_names p))
  else None

let fingerprint fspath path =
  if not (owns fspath) || depth_of path <> !depth + 1 then None else
  Option.map (fun (m : Packdir.member) -> m.fp) (member_named fspath path)

(* ------------------------------------------------------------------ *)
(* Propagation into the packed root: Transport sends every action whose
   target is on the packed root here instead of to Files. Writes happen in
   one transaction per container, synchronously, so one writer at a time
   reaches the disk. *)

let transient fmt = Printf.ksprintf (fun m -> raise (Util.Transient ("packed root: " ^ m))) fmt

(* One container's work: store [files] (name, source path, Unison's
   fingerprint from update detection) as members of the container for [rel].
   Reading and hashing happen outside [write_lock]; only the transaction runs
   inside it. Returns the bytes stored and the members after. *)
type locker = { lock : 'a. (unit -> 'a) -> 'a }

let pack_job ~(write_lock : locker) fspathTo (rel, files) =
  let p = abs fspathTo (Path.fromString rel) in
  N.mkdir_p (Filename.dirname p);
  let c = write_lock.lock (fun () -> Packdir.open_ (p ^ ".sqlar")) in
  Fun.protect ~finally:(fun () -> Packdir.close c) (fun () ->
    let puts = List.map (fun (name, source, _) -> { Packdir.member = name; source }) files in
    let bytes = Packdir.apply ~write_lock:(fun f -> write_lock.lock f) c ~puts ~retain:[] in
    bytes, Packdir.members c)

(* Record a finished job: barrier accounting, the state, this run's view, and
   the fingerprint check: a source whose stored bytes no longer match the
   fingerprint update detection took changed during synchronization. *)
let record fspathTo (rel, files) (bytes, ms) =
  let p = abs fspathTo (Path.fromString rel) in
  wrote (p ^ ".sqlar") bytes;
  (match container_stat p with
   | Some s -> Hashtbl.replace state rel ((s.N.ino, s.N.size, s.N.mtime_ns), ms); dirty := true
   | None -> ());
  Hashtbl.replace read_this_run rel ms;
  List.iter (fun (name, _, (fp : Os.fullfingerprint)) ->
    if not (List.exists (fun (m : Packdir.member) -> m.name = name) ms) then transient "%s/%s was not stored" rel name;
    (* The stored MD5, as update detection will read it, against the one it took. *)
    let stored = Os.data_only_fingerprint (Fingerprint.file fspathTo (Path.fromString (rel ^ "/" ^ name))) in
    if not (Os.fullfingerprintEqual stored fp) then
      transient "%s/%s changed during synchronization; stored as found, will be compared again" rel name) files

(* The writer lock, in the Unison directory: every worker's transaction takes
   it, so the packed disk sees one writer at a time. *)
let lock_fd = lazy (Unix.openfile (!state_path ^ ".writer") [Unix.O_RDWR; Unix.O_CREAT] 0o600)
let with_lock f =
  let fd = Lazy.force lock_fd in
  Unix.lockf fd Unix.F_LOCK 0;
  Fun.protect ~finally:(fun () -> Unix.lockf fd Unix.F_ULOCK 0) f

(* Run the jobs, each in its own forked process, at most packworkers at a
   time across every item Unison propagates at once (one shared region), so
   the workers stay busy from one item to the next; the parent waits on each
   job's pipe without blocking Unison's event loop. With packworkers = 1 the
   jobs run in this process, one after another. A job whose process dies
   fails its item; its container stays pending and is verified next run. *)
let region = lazy (Lwt_util.make_region (max 1 (Prefs.read PackdirConfig.workers)))

let run_in_child fspathTo job =
  let rd, wr = Unix.pipe ~cloexec:true () in
  flush_all ();
  match Unix.fork () with
  | 0 ->
      Unix.close rd;
      let r = try Ok (pack_job ~write_lock:{ lock = with_lock } fspathTo job)
        with Failure e | Sys_error e -> Error e
           | Unix.Unix_error (e, f, a) -> Error (Printf.sprintf "%s: %s %s" f (Unix.error_message e) a) in
      let oc = Unix.out_channel_of_descr wr in
      Marshal.to_channel oc r []; close_out oc; Unix._exit 0
  | pid ->
      Unix.close wr;
      let fd = Lwt_unix.of_unix_file_descr rd in
      let buf = Buffer.create 4096 and chunk = Bytes.create 65536 in
      let rec drain () =
        Lwt.bind (Lwt_unix.read fd chunk 0 65536) (fun n ->
          if n = 0 then Lwt.return () else (Buffer.add_subbytes buf chunk 0 n; drain ())) in
      Lwt.bind (drain ()) (fun () ->
        Lwt_unix.close fd;
        ignore (Unix.waitpid [] pid);
        Lwt.return (if Buffer.length buf = 0 then Error "its worker stopped"
                    else (Marshal.from_string (Buffer.contents buf) 0 : (int * Packdir.member list, string) result)))

let run_jobs fspathTo jobs =
  List.iter (fun (rel, _) -> mark_pending rel) jobs;
  let one ((rel, _) as job) =
    if Prefs.read PackdirConfig.workers <= 1 then
      Lwt.return (rel, try Ok (pack_job ~write_lock:{ lock = (fun f -> f ()) } fspathTo job)
                       with Failure e | Sys_error e -> Error e)
    else Lwt_util.run_in_region (Lazy.force region) 1 (fun () ->
      Lwt.bind (run_in_child fspathTo job) (fun r -> Lwt.return (rel, r))) in
  Lwt.bind (Lwt_util.map one jobs) (fun results ->
    (* Record in job order; the first problem fails the item, after everything
       that did arrive is recorded. *)
    let first = ref None in
    List.iter2 (fun job (rel, r) ->
      match r with
      | Ok r -> (try record fspathTo job r with Util.Transient m -> if !first = None then first := Some m)
      | Error e -> Hashtbl.replace failed_this_run rel (); if !first = None then first := Some (rel ^ ": " ^ e)) jobs results;
    match !first with Some m -> Lwt.fail (Util.Transient m) | None -> Lwt.return ())

(* What the target now holds, for Unison's archive: read back through the
   same hooks update detection uses, so the next run sees what was recorded. *)
let file_arch fspathTo pt desc fp =
  let info = Fileinfo.get false fspathTo pt in
  if info.Fileinfo.typ <> `FILE then transient "%s did not arrive" (Path.toString pt);
  Update.ArchiveFile (Props.override info.Fileinfo.desc desc, fp, Fileinfo.stamp info, Osx.stamp info.Fileinfo.osX)

(* A plain file above the packed depth: written beside, then renamed into
   place, with its modification time. *)
let plain_copy source target mtime_ns =
  let temp = Filename.concat (Filename.dirname target) (".unison-packdir." ^ Filename.basename target ^ ".tmp") in
  In_channel.with_open_bin source (fun ic -> Out_channel.with_open_bin temp (fun oc ->
    let buf = Bytes.create N.block in
    let rec loop () = let n = input ic buf 0 N.block in if n > 0 then (output oc buf 0 n; loop ()) in
    loop (); flush oc; Unix.fsync (Unix.descr_of_out_channel oc)));
  N.utimens temp mtime_ns mtime_ns;
  Sys.rename temp target

let name_of pt = Filename.basename (Path.toString pt)
let parent_of pt = Filename.dirname (Path.toString pt)

(* Prepare: create directories and copy plain files above the packed depth,
   and collect one job per container to write. *)
let rec prepare fspathFrom fspathTo pf pt arch jobs =
  let d = depth_of pt in
  let source = abs fspathFrom pf in
  match arch with
  | Update.ArchiveFile (_, fp, _, _) when d = !depth + 1 ->
      (parent_of pt, [(name_of pt, source, fp)]) :: jobs
  | Update.ArchiveFile _ when d <= !depth ->
      plain_copy source (abs fspathTo pt) (N.stat source).N.mtime_ns; jobs
  | Update.ArchiveDir (_, children) when d = !depth ->
      let files = Update.NameMap.fold (fun name child acc -> match child with
        | Update.ArchiveFile (_, fp, _, _) -> (Name.toString name, abs fspathFrom (Path.child pf name), fp) :: acc
        | _ -> transient "%s/%s: a packed directory holds files only" (Path.toString pt) (Name.toString name))
        children [] in
      if files = [] then jobs else (Path.toString pt, List.rev files) :: jobs
  | Update.ArchiveDir (_, children) when d < !depth ->
      let target = abs fspathTo pt in
      if not (is_dir target) then Unix.mkdir target 0o755;
      Update.NameMap.fold (fun name child jobs ->
        prepare fspathFrom fspathTo (Path.child pf name) (Path.child pt name) child jobs) children jobs
  | Update.ArchiveDir _ -> transient "%s: directories below the packed depth are not supported" (Path.toString pt)
  | Update.ArchiveSymlink _ -> transient "%s: symbolic links are not supported" (Path.toString pt)
  | Update.ArchiveFile _ | Update.NoArchive -> transient "%s: nothing to write" (Path.toString pt)

(* The archive for what the target now holds, read back through the hooks. *)
let rec archive_of fspathTo pt arch =
  match arch with
  | Update.ArchiveFile (desc, fp, _, _) -> file_arch fspathTo pt desc fp
  | Update.ArchiveDir (desc, children) ->
      Update.ArchiveDir (desc, Update.NameMap.mapi (fun name child -> archive_of fspathTo (Path.child pt name) child) children)
  | a -> a

let write fspathFrom fspathTo pf pt arch =
  let jobs = Util.convertUnixErrorsToTransient "writing into the packed root" (fun () ->
    List.rev (prepare fspathFrom fspathTo pf pt arch [])) in
  Lwt.bind (run_jobs fspathTo jobs) (fun () ->
    Lwt.return (Util.convertUnixErrorsToTransient "reading back the packed root" (fun () -> archive_of fspathTo pt arch)))

let copy rootFrom pathFrom uiFrom rootTo pathTo =
  let fspathFrom = snd rootFrom and fspathTo = snd rootTo in
  let pf = Update.translatePathLocal fspathFrom pathFrom in
  let pt = Update.translatePathLocal fspathTo pathTo in
  let arch = Update.updateArchive fspathFrom pf uiFrom in
  Lwt.bind (write fspathFrom fspathTo pf pt arch) (fun arch' ->
    Update.replaceArchiveLocal fspathTo pt arch';
    Files.updateSourceArchive rootFrom (pf, uiFrom, []))

(* A deletion on the packed root keeps the bytes: the member is marked
   retained and drops out of Unison's view. A whole container is never
   deleted. *)
let delete rootFrom pathFrom rootTo pathTo =
  let fspathTo = snd rootTo in
  let pt = Update.translatePathLocal fspathTo pathTo in
  if depth_of pt <> !depth + 1 || container_stat (abs fspathTo (Path.fromString (parent_of pt))) = None then
    transient "%s: only members are deleted, and they are kept as retained; use nodeletion for the rest"
      (Path.toString pt);
  let rel = parent_of pt in
  (* A plain file beside a container is a kept original: never deleted. *)
  if member_named fspathTo pt = None then
    transient "%s is a plain file beside a container (a kept original): never deleted; use nodeletion"
      (Path.toString pt);
  let p = abs fspathTo (Path.fromString rel) in
  mark_pending rel;
  let c = Packdir.open_ (p ^ ".sqlar") in
  let ms = Fun.protect ~finally:(fun () -> Packdir.close c) (fun () ->
    ignore (Packdir.apply c ~puts:[] ~retain:[name_of pt]); Packdir.members c) in
  wrote (p ^ ".sqlar") 0;
  (match container_stat p with
   | Some s -> Hashtbl.replace state rel ((s.N.ino, s.N.size, s.N.mtime_ns), ms); dirty := true
   | None -> ());
  Hashtbl.replace read_this_run rel ms;
  (* Both archives drop the path, as Files.delete does, so they stay identical. *)
  Update.replaceArchiveLocal fspathTo pt Update.NoArchive;
  Update.replaceArchive rootFrom pathFrom Update.NoArchive

let install fspath n =
  root := Some fspath; depth := n;
  state_path := Util.fileInUnisonDir ("pd" ^ Digest.to_hex (Digest.string (Fspath.toString fspath)));
  load_state ();
  load_pending ();
  (* The marker that makes any other packdir setting refuse this root. *)
  let m = abs fspath (Path.fromString PackdirConfig.marker) in
  (match PackdirConfig.marked_depth fspath with
   | Some d when d <> n -> raise (Util.Fatal (Printf.sprintf "%s: packed with packdepth = %d, not %d" (Fspath.toPrintString fspath) d n))
   | _ -> ());
  if PackdirConfig.marked_depth fspath = None then begin
    Out_channel.with_open_bin (m ^ ".tmp") (fun oc ->
      output_string oc (PackdirConfig.marker_text n); flush oc; Unix.fsync (Unix.descr_of_out_channel oc));
    Sys.rename (m ^ ".tmp") m
  end;
  at_exit save_state;
  PackdirConfig.before_commit := before_commit;
  PackdirConfig.after_commit := after_commit;
  PackdirHook.stat := stat;
  PackdirHook.children := children;
  PackdirHook.fingerprint := fingerprint
