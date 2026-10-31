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

(* Members of the container for [rel] (relative to the root): from the
   state when its file is unchanged, else read from the container. *)
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
          let m = match Hashtbl.find_opt state rel with
            | Some (st', m) when st' = st -> m
            | _ ->
                let c = Packdir.open_ (p ^ ".sqlar") in
                let m = Fun.protect ~finally:(fun () -> Packdir.close c) (fun () -> Packdir.members c) in
                Hashtbl.replace state rel (st, m); dirty := true; m in
          Hashtbl.replace read_this_run rel m;
          Some m

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
  if d = !depth - 1 then begin
    let names = plain_names p in
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

(* Store [files] (name, source path, Unison's fingerprint from update
   detection) as members of the container for [rel]; a source whose bytes
   no longer match its fingerprint changed during synchronization. *)
let put_members fspathTo rel files =
  let p = abs fspathTo (Path.fromString rel) in
  N.mkdir_p (Filename.dirname p);
  let c = Packdir.open_ (p ^ ".sqlar") in
  let ms = Fun.protect ~finally:(fun () -> Packdir.close c) (fun () ->
    let puts = List.map (fun (name, source, _) -> { Packdir.member = name; source }) files in
    ignore (Packdir.apply c ~puts ~retain:[]);
    Packdir.members c) in
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

let rec write fspathFrom fspathTo pf pt arch =
  let d = depth_of pt in
  let source = abs fspathFrom pf in
  match arch with
  | Update.ArchiveFile (desc, fp, _, _) when d = !depth + 1 ->
      put_members fspathTo (parent_of pt) [(name_of pt, source, fp)];
      file_arch fspathTo pt desc fp
  | Update.ArchiveFile (desc, fp, _, _) when d <= !depth ->
      plain_copy source (abs fspathTo pt) (N.stat source).N.mtime_ns;
      file_arch fspathTo pt desc fp
  | Update.ArchiveDir (desc, children) when d = !depth ->
      let files = Update.NameMap.fold (fun name child acc -> match child with
        | Update.ArchiveFile (_, fp, _, _) -> (Name.toString name, abs fspathFrom (Path.child pf name), fp) :: acc
        | _ -> transient "%s/%s: a packed directory holds files only" (Path.toString pt) (Name.toString name))
        children [] in
      if files <> [] then put_members fspathTo (Path.toString pt) files;
      let children' = Update.NameMap.mapi (fun name child -> match child with
        | Update.ArchiveFile (cdesc, fp, _, _) -> file_arch fspathTo (Path.child pt name) cdesc fp
        | a -> a) children in
      Update.ArchiveDir (desc, children')
  | Update.ArchiveDir (desc, children) when d < !depth ->
      let target = abs fspathTo pt in
      if not (is_dir target) then Unix.mkdir target 0o755;
      Update.ArchiveDir (desc, Update.NameMap.mapi (fun name child ->
        write fspathFrom fspathTo (Path.child pf name) (Path.child pt name) child) children)
  | Update.ArchiveDir _ -> transient "%s: directories below the packed depth are not supported" (Path.toString pt)
  | Update.ArchiveSymlink _ -> transient "%s: symbolic links are not supported" (Path.toString pt)
  | Update.ArchiveFile _ | Update.NoArchive -> transient "%s: nothing to write" (Path.toString pt)

let copy rootFrom pathFrom uiFrom rootTo pathTo =
  let fspathFrom = snd rootFrom and fspathTo = snd rootTo in
  let pf = Update.translatePathLocal fspathFrom pathFrom in
  let pt = Update.translatePathLocal fspathTo pathTo in
  let arch = Update.updateArchive fspathFrom pf uiFrom in
  let arch' = Util.convertUnixErrorsToTransient "writing into the packed root" (fun () ->
    write fspathFrom fspathTo pf pt arch) in
  Update.replaceArchiveLocal fspathTo pt arch';
  Files.updateSourceArchive rootFrom (pf, uiFrom, [])

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
  let c = Packdir.open_ (p ^ ".sqlar") in
  let ms = Fun.protect ~finally:(fun () -> Packdir.close c) (fun () ->
    ignore (Packdir.apply c ~puts:[] ~retain:[name_of pt]); Packdir.members c) in
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
  at_exit save_state;
  PackdirHook.stat := stat;
  PackdirHook.children := children;
  PackdirHook.fingerprint := fingerprint
