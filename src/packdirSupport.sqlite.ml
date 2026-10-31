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
  | Some ms -> List.find_opt (fun (m : Packdir.member) -> m.name = Filename.basename rel) ms
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
    | Some ms -> Some (List.sort_uniq compare (List.map (fun (m : Packdir.member) -> m.name) ms @ plain_names p))
  else None

let fingerprint fspath path =
  if not (owns fspath) || depth_of path <> !depth + 1 then None else
  Option.map (fun (m : Packdir.member) -> m.fp) (member_named fspath path)

let install fspath n =
  root := Some fspath; depth := n;
  state_path := Util.fileInUnisonDir ("pd" ^ Digest.to_hex (Digest.string (Fspath.toString fspath)));
  load_state ();
  at_exit save_state;
  PackdirHook.stat := stat;
  PackdirHook.children := children;
  PackdirHook.fingerprint := fingerprint
