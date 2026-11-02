(* Built with the packdir library (querygraph/packdir, SQLite through the
   opam sqlite3 binding): packed roots are supported.

   Update detection on the packed root goes through PackdirHook. A
   container X.sqlar, with no plain X/ beside it, is the directory X; its
   members are X's files, with the plain files of X/ when the two sit side
   by side (a member wins for a name in both). A container is read once per
   run, and not at all while its file is as a state file in the Unison
   directory records it. *)

module N = Packdir.Native
module Packdir = Packdir.Container

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
   committed; the list is cleared after the commit. A finished job adds a
   done line and a barrier adds a barrier line, so that a run cut short need
   not distrust what it already flushed: only a container whose job finished
   before a barrier is covered by it, since other jobs write through a
   barrier. A container still pending from an earlier run, or whose file no
   longer matches the state, may not have reached the platter whole: it is
   verified before use, and set aside when damaged, so the leaf reads as
   missing and is brought back. The list is one line per event:
     <rel>             about to write
     <tab>done <rel>   its job finished
     <tab>barrier      everything done so far is on the platter
   Losing a done or barrier line only costs a verification, so they are not
   synced; a <rel> line must be there before the write. *)
let pending_path () = !state_path ^ ".pending"
let suspects : (string, unit) Hashtbl.t = Hashtbl.create 64
let pending_this_run : (string, unit) Hashtbl.t = Hashtbl.create 1024
let failed_this_run : (string, unit) Hashtbl.t = Hashtbl.create 64
let since_barrier = ref 0
let last_written = ref ""

let listed = ref false
let done_marker = "\tdone "
let barrier_marker = "\tbarrier"

let load_pending () =
  let covered = Hashtbl.create 1024 in
  try List.iter (fun l ->
      listed := true;
      if l = barrier_marker then begin
        Hashtbl.iter (fun rel () -> Hashtbl.remove suspects rel) covered;
        Hashtbl.reset covered
      end else if String.starts_with ~prefix:done_marker l then begin
        let n = String.length done_marker in
        Hashtbl.replace covered (String.sub l n (String.length l - n)) ()
      end else if l <> "" && l.[0] <> '\t' then begin
        Hashtbl.remove covered l;
        Hashtbl.replace suspects l ()
      end)
      (In_channel.with_open_bin (pending_path ()) In_channel.input_lines)
  with Sys_error _ -> ()

let append_pending line ~sync =
  Out_channel.with_open_gen [Open_wronly; Open_creat; Open_append; Open_binary] 0o600 (pending_path ()) (fun oc ->
    output_string oc (line ^ "\n"); flush oc;
    if sync then Unix.fsync (Unix.descr_of_out_channel oc));
  listed := true

let mark_pending rel =
  if not (Hashtbl.mem pending_this_run rel) then begin
    append_pending rel ~sync:true;
    Hashtbl.replace pending_this_run rel ()
  end

(* A later write to the same container must list it again. *)
let mark_done rel =
  append_pending (done_marker ^ rel) ~sync:false;
  Hashtbl.remove pending_this_run rel

let barrier () =
  if !last_written <> "" then begin
    Packdir.barrier !last_written;
    append_pending barrier_marker ~sync:false;
    debug (fun () -> Util.msg "packdir: barrier after %d bytes\n" !since_barrier);
    since_barrier := 0
  end

let wrote path bytes =
  last_written := path;
  since_barrier := !since_barrier + bytes;
  (* packbarrier = 0: a barrier after every container write. *)
  if !since_barrier >= Prefs.read PackdirConfig.barrier_gib * 1073741824 then barrier ()

(* Set by the writer below: finish every queued container. *)
let finish_writes : (unit -> unit) ref = ref (fun () -> ())

let before_commit () =
  !finish_writes ();
  barrier ();
  save_state ();
  (* Tests: stop after the barrier, before Unison's archives are written. *)
  if Sys.getenv_opt "UNISON_PACKDIR_CRASH_BEFORE_COMMIT" <> None then Unix._exit 4

(* After the commit, only containers whose job failed stay pending: the next
   run verifies them before use. *)
let after_commit () =
  if !listed then begin
    Out_channel.with_open_bin (pending_path () ^ ".tmp") (fun oc ->
      Hashtbl.iter (fun rel () -> output_string oc (rel ^ "\n")) failed_this_run;
      flush oc; Unix.fsync (Unix.descr_of_out_channel oc));
    Sys.rename (pending_path () ^ ".tmp") (pending_path ());
    Hashtbl.reset pending_this_run; Hashtbl.reset suspects;
    Hashtbl.iter (fun rel () -> Hashtbl.replace suspects rel ()) failed_this_run;
    listed := Hashtbl.length failed_this_run > 0
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
                (if suspicious then begin
                   debug (fun () -> Util.msg "packdir: verifying %s\n" rel);
                   Packdir.verify c
                 end else []), Packdir.members c) in
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
  (* packmax: refuse, before anything is written, a container that would grow
     past it (0: no limit). Space freed by replaced members is not counted. *)
  let limit = Prefs.read PackdirConfig.max_gib in
  if limit > 0 then begin
    let existing = match container_stat p with Some s -> s.N.size | None -> 0L in
    let adding = List.fold_left (fun t (_, source, _) -> Int64.add t (N.stat source).N.size) 0L files in
    let total = Int64.add existing adding in
    if total > Int64.mul (Int64.of_int limit) 1073741824L then
      failwith (Printf.sprintf "would grow to %.1f GiB, past packmax = %d" (Int64.to_float total /. 1073741824.) limit)
  end;
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
  mark_done rel;
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
      (* The child inherits Unison's whole heap, gigabytes on a large root, and
         would spend most of its time marking it while it allocates file
         contents. It lives for one job and its memory goes with it, so it
         needs no collector to speak of (measured 2026-11-01). *)
      Gc.set { (Gc.get ()) with Gc.space_overhead = 1000000 };
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

(* Clones (Xferhint.clones; docs/clone-preservation.md). The source of a
   packed root is local, so a file's APFS clone id is read directly. Each
   container's files are split: a file in a clone group whose bytes are
   already packed (this run, or an earlier one whose source is still in the
   group) becomes a reference to that member; any other file is stored as
   data, and the first of a group becomes its original. Data is written
   first, then the references, through packdir's apply_clones, which checks
   the SHA-256; references that don't check out are stored as data. *)
let clone_originals : (int64 * int64, string) Hashtbl.t = Hashtbl.create 64

(* The packed file holding a member's bytes: itself, or its clone's original. *)
let original_of fspathTo pt =
  let p = abs fspathTo (Path.fromString (parent_of pt)) in
  if not (Sys.file_exists (p ^ ".sqlar")) then None else
  let c = Packdir.open_ ~create:false ~read_only:true (p ^ ".sqlar") in
  Fun.protect ~finally:(fun () -> Packdir.close c) (fun () ->
    match Packdir.clone_of c (name_of pt) with
    | Some (original, _) -> Some (Packdir.normalize (Filename.concat p original))
    | None -> Some (Filename.concat p (name_of pt)))

(* An original packed by an earlier run: a hinted path with this fingerprint,
   current on the packed root, whose source file is still in the group. *)
let packed_original fspathFrom fspathTo key fp pt size =
  List.find_map (fun (fsp, path) ->
    if Fspath.toString fsp <> Fspath.toString fspathTo || Path.toString path = Path.toString pt then None
    else match member_named fspathTo path with
      | Some m when m.Packdir.size = size
                    && Os.fullfingerprintEqual (Os.data_only_fingerprint (Fingerprint.file fspathTo path)) fp
                    && N.clone_key (abs fspathFrom path) = Some key -> original_of fspathTo path
      | _ -> None) (Xferhint.cloneCandidates fp)

(* One container's files (name, source, fp): (data, references). *)
let split_clones fspathFrom fspathTo (rel, files) =
  if not (Xferhint.clonesEnabled ()) then files, [] else
  let p = abs fspathTo (Path.fromString rel) in
  let data, refs = List.fold_left (fun (data, refs) ((name, source, fp) as f) ->
    match N.clone_key source with
    | None -> f :: data, refs
    | Some key ->
        let self = Filename.concat p name in
        let original = match Hashtbl.find_opt clone_originals key with
          | Some o -> Some o
          | None -> packed_original fspathFrom fspathTo key fp (Path.fromString (rel ^ "/" ^ name)) (N.stat source).N.size in
        match original with
        | Some o when o <> self -> data, (f, o) :: refs
        | _ -> Hashtbl.replace clone_originals key self; f :: data, refs) ([], [])
    (List.sort (fun (a, _, _) (b, _, _) -> compare a b) files) in
  List.rev data, List.rev refs

(* Store [refs] in [rel]'s container as references; [false] when they don't
   check out, and nothing of them was stored. *)
let store_refs fspathTo rel refs =
  let p = abs fspathTo (Path.fromString rel) in
  mark_pending rel;
  match
    N.mkdir_p (Filename.dirname p);
    let c = with_lock (fun () -> Packdir.open_ (p ^ ".sqlar")) in
    Fun.protect ~finally:(fun () -> Packdir.close c) (fun () ->
      ignore (Packdir.apply_clones ~write_lock:with_lock c
        (List.map (fun ((name, source, _), original) ->
           { Packdir.clone = name; file = source; original = Packdir.relative ~from:p original }) refs));
      Packdir.members c)
  with
  | ms -> record fspathTo (rel, List.map fst refs) (0, ms); true
  | exception (Failure e | Sys_error e) ->
      debug (fun () -> Util.msg "packdir: clones in %s stored as data (%s)\n" rel e); false

(* Data jobs, then each container's references; references that don't check
   out become data jobs too. *)
let run_with_clones fspathFrom fspathTo jobs =
  let split = List.map (fun ((rel, _) as job) -> rel, split_clones fspathFrom fspathTo job) jobs in
  let data = List.filter_map (fun (rel, (d, _)) -> if d = [] then None else Some (rel, d)) split in
  Lwt.bind (if data = [] then Lwt.return () else run_jobs fspathTo data) (fun () ->
    let fallback = List.filter_map (fun (rel, (_, refs)) ->
      if refs = [] || store_refs fspathTo rel refs then None else Some (rel, List.map fst refs)) split in
    if fallback = [] then Lwt.return () else run_jobs fspathTo fallback)

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
  Lwt.bind (run_with_clones fspathFrom fspathTo jobs) (fun () ->
    Lwt.return (Util.convertUnixErrorsToTransient "reading back the packed root" (fun () -> archive_of fspathTo pt arch)))

(* Unison sends a leaf with a plain directory on the target (kept originals)
   file by file, and runs only maxthreads items at once. So a member item only
   joins its container's queue and returns; the queue becomes one job, one
   transaction, when items move on to another container, or at the commit.
   The archives are updated when the job succeeds, so a failed file stays
   unrecorded and is retried by the next run. *)
type queued = {
  q_root : Common.root; q_pf : Path.local; q_ui : Common.updateItem; q_pt : Path.local;
  q_source : string; q_desc : Props.t; q_fp : Os.fullfingerprint; q_id : Uutil.File.t;
}
let queues : (string, queued list) Hashtbl.t = Hashtbl.create 64
let filling = ref ""
let flushes : unit Lwt.t list ref = ref []
let not_stored = ref 0

let flush_queue fspathTo rel =
  match Hashtbl.find_opt queues rel with
  | None -> ()
  | Some rev_items ->
      Hashtbl.remove queues rel;
      let items = List.rev rev_items in
      let job = (rel, List.map (fun q -> (name_of q.q_pt, q.q_source, q.q_fp)) items) in
      let fspathFrom = match items with q :: _ -> snd q.q_root | [] -> fspathTo in
      let t = Lwt.try_bind (fun () -> run_with_clones fspathFrom fspathTo [job])
        (fun () -> Lwt_util.iter (fun q ->
           Update.replaceArchiveLocal fspathTo q.q_pt (file_arch fspathTo q.q_pt q.q_desc q.q_fp);
           Uutil.showProgress q.q_id (Props.length q.q_desc) "pack";
           Files.updateSourceArchive q.q_root (q.q_pf, q.q_ui, [])) items)
        (fun e ->
           not_stored := !not_stored + List.length items;
           Hashtbl.replace failed_this_run rel ();
           Util.warn (Printf.sprintf "packed root: %s: %d files not stored, retried next run: %s\n"
                        rel (List.length items) (Util.printException e));
           Lwt.return ()) in
      flushes := t :: !flushes

let rec total_size = function
  | Update.ArchiveFile (desc, _, _, _) -> Props.length desc
  | Update.ArchiveDir (_, children) ->
      Update.NameMap.fold (fun _ c n -> Uutil.Filesize.add n (total_size c)) children Uutil.Filesize.zero
  | _ -> Uutil.Filesize.zero

let copy rootFrom pathFrom uiFrom rootTo pathTo id =
  let fspathFrom = snd rootFrom and fspathTo = snd rootTo in
  let pf = Update.translatePathLocal fspathFrom pathFrom in
  let pt = Update.translatePathLocal fspathTo pathTo in
  let arch = Update.updateArchive fspathFrom pf uiFrom in
  match arch with
  | Update.ArchiveFile (desc, fp, _, _) when depth_of pt = !depth + 1 ->
      let rel = parent_of pt in
      if !filling <> "" && !filling <> rel then flush_queue fspathTo !filling;
      filling := rel;
      let q = { q_root = rootFrom; q_pf = pf; q_ui = uiFrom; q_pt = pt; q_source = abs fspathFrom pf;
                q_desc = desc; q_fp = fp; q_id = id } in
      Hashtbl.replace queues rel (q :: Option.value (Hashtbl.find_opt queues rel) ~default:[]);
      Lwt.return ()
  | _ ->
      Lwt.bind (write fspathFrom fspathTo pf pt arch) (fun arch' ->
        Update.replaceArchiveLocal fspathTo pt arch';
        Uutil.showProgress id (total_size arch) "pack";
        Files.updateSourceArchive rootFrom (pf, uiFrom, []))

let () = finish_writes := (fun () ->
  match !root with
  | None -> ()
  | Some fspathTo ->
      List.iter (flush_queue fspathTo) (Hashtbl.fold (fun rel _ l -> rel :: l) queues []);
      Lwt_unix.run (Lwt_util.join !flushes);
      flushes := [];
      if !not_stored > 0 then
        Util.warn (Printf.sprintf "packed root: %d files were not stored; run Unison again\n" !not_stored))

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
