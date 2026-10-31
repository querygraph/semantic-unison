(* unison-packdir: the packed-directory prototype and its tools.

     unison-packdir pack-tree ROOT OUT [--depth N] [--workers N] [--wal] [--batch-mib M]
       keep every directory N levels under ROOT (default 2, the preview leaves
       <H>/<HHHH>) as OUT/<rel>.sqlar; N workers read and hash containers in
       parallel, one writes at a time; a rerun stores only new and changed
       files and marks the vanished ones retained
     unison-packdir list C.sqlar
     unison-packdir verify C.sqlar...
     unison-packdir restore C.sqlar OUT_DIR [--skip-retained] *)

let usage () =
  prerr_endline "usage: unison-packdir pack-tree ROOT OUT [--depth N] [--workers N] [--wal] [--batch-mib M]\n\
                \       unison-packdir list C.sqlar\n\
                \       unison-packdir verify C.sqlar...\n\
                \       unison-packdir restore C.sqlar OUT_DIR [--skip-retained]";
  exit 2

let rec dirs_at depth root rel =
  if depth = 0 then [rel] else
  let here = if rel = "" then root else Filename.concat root rel in
  List.concat_map (fun n ->
    let r = if rel = "" then n else Filename.concat rel n in
    match (Unix.lstat (Filename.concat root r)).Unix.st_kind with
    | Unix.S_DIR -> dirs_at (depth - 1) root r
    | _ -> [] | exception Unix.Unix_error _ -> [])
    (List.sort compare (Array.to_list (Sys.readdir here)))

(* One writer per output disk: the transactions of all workers take this lock;
   reading and hashing happen outside it. *)
let lock_file out =
  Dng_archive.Native.mkdir_p out;
  Unix.openfile (Filename.concat out ".packdir-writer.lock") [Unix.O_RDWR; Unix.O_CREAT] 0o644

let with_lock fd f =
  Unix.lockf fd Unix.F_LOCK 0;
  Fun.protect ~finally:(fun () -> Unix.lockf fd Unix.F_ULOCK 0) f

(* OUT/.packdir-state: for each container, its file's (inode, size, mtime)
   after the last run and its members then. A prototype's stand-in for
   Unison's archive; losing it only costs a full re-read. *)
let state_file out = Filename.concat out ".packdir-state"
let load_state out : (string, (int64 * int64 * int64) * Packdir.member list) Hashtbl.t =
  try In_channel.with_open_bin (state_file out) (fun ic -> Marshal.from_channel ic)
  with Sys_error _ | End_of_file | Failure _ -> Hashtbl.create 1024
let save_state out state =
  let temp = state_file out ^ ".tmp" in
  Out_channel.with_open_bin temp (fun oc -> Marshal.to_channel oc state []);
  Sys.rename temp (state_file out)

let pack_tree root out ~depth ~journal ~batch_bytes ~workers =
  let t0 = Unix.gettimeofday () in
  let state = load_state out in
  let opened = ref 0 and scan_seconds = ref 0. in
  let fd = lock_file out in
  let write_lock f = with_lock fd f in
  let one rel =
    let target = Filename.concat out rel ^ ".sqlar" in
    (* A plain directory beside the container is pre-existing content, never
       touched. A file named like one of its files is not packed while the
       bytes are the same (present-plain); once they differ, the newer bytes
       are kept updated in the container beside the plain original (user,
       2026-10-31). *)
    let plain = Filename.concat out rel in
    let same = if Sys.file_exists plain && Sys.is_directory plain then begin
        Printf.printf "note: plain %s/ beside %s.sqlar is left as it is\n" rel rel;
        List.filter (fun n ->
          let mine = Filename.concat (Filename.concat root rel) n and theirs = Filename.concat plain n in
          let module N = Dng_archive.Native in
          Sys.file_exists mine && not (Sys.is_directory theirs) &&
          if (N.stat mine).N.size = (N.stat theirs).N.size && N.sha_file mine = N.sha_file theirs then
            (Printf.printf "present-plain: %s/%s\n" rel n; true)
          else (Printf.printf "packed-beside-plain: %s/%s (the plain original differs and stays)\n" rel n; false))
          (Array.to_list (Sys.readdir plain))
      end else [] in
    let skip = same in
    (* A container whose file is as recorded after the last run needs no
       opening: its members come from the state, the role Unison's archive
       plays. Only containers with something to store are opened. *)
    let stamp () = match Dng_archive.Native.stat target with
      | s -> Some (s.Dng_archive.Native.ino, s.Dng_archive.Native.size, s.Dng_archive.Native.mtime_ns)
      | exception Unix.Unix_error _ -> None in
    let src = Filename.concat root rel in
    (* The scan: this container's stamp, and its plan against the plain side. *)
    let t = Unix.gettimeofday () in
    let unchanged = match Hashtbl.find_opt state rel with
      | Some (st, known) -> Some st = stamp () && Packdir.plan ~skip known src = ([], [])
      | None -> false in
    scan_seconds := !scan_seconds +. (Unix.gettimeofday () -. t);
    if unchanged then (0, 0, 0), None
    else begin
        incr opened;
        let c = write_lock (fun () -> Dng_archive.Native.mkdir_p (Filename.dirname target); Packdir.open_ ~journal target) in
        let result, members = Fun.protect ~finally:(fun () -> Packdir.close c) (fun () ->
          let r = Packdir.update ~batch_bytes ~write_lock ~skip c src in r, Packdir.members c) in
        result, Option.map (fun st -> rel, (st, members)) (stamp ())
    end in
  let dirs = Array.of_list (dirs_at depth root "") in
  let containers = Array.length dirs and stored = ref 0 and retained = ref 0 and bytes = ref 0 in
  let updates = ref [] in
  let add ((s, r, b), u) =
    stored := !stored + s; retained := !retained + r; bytes := !bytes + b;
    Option.iter (fun u -> updates := u :: !updates) u in
  if workers <= 1 then Array.iter (fun rel -> add (one rel)) dirs
  else begin
    (* Worker k takes containers k, k+workers, ... and sends back its totals. *)
    flush stdout;
    let children = List.init (min workers (max 1 containers)) (fun k ->
      let rd, wr = Unix.pipe ~cloexec:true () in
      match Unix.fork () with
      | 0 ->
          Unix.close rd;
          let total = ref ((0, 0, 0), []) and i = ref k in
          (try
             while !i < containers do
               let (s, r, b), u = one dirs.(!i) and ((s0, r0, b0), us) = !total in
               total := ((s0 + s, r0 + r, b0 + b), Option.to_list u @ us); i := !i + workers
             done
           with e -> prerr_endline ("unison-packdir: " ^ Printexc.to_string e); flush stdout; Unix._exit 1);
          let oc = Unix.out_channel_of_descr wr in
          Marshal.to_channel oc (!total, !opened, !scan_seconds) []; close_out oc; flush stdout; Unix._exit 0
      | pid -> Unix.close wr; pid, Unix.in_channel_of_descr rd) in
    let failed = ref 0 in
    List.iter (fun (pid, ic) ->
      (match Marshal.from_channel ic with
       | ((t, us), o, sc) -> add (t, None); updates := us @ !updates; opened := !opened + o; scan_seconds := !scan_seconds +. sc
       | exception End_of_file -> ());
      close_in ic;
      match snd (Unix.waitpid [] pid) with
      | Unix.WEXITED 0 -> () | Unix.WEXITED n -> failed := n | _ -> failed := 1) children;
    if !failed <> 0 then exit !failed
  end;
  List.iter (fun (rel, e) -> Hashtbl.replace state rel e) !updates;
  save_state out state;
  let dt = Unix.gettimeofday () -. t0 in
  (* scan_seconds is summed over workers: the time spent stating containers
     and planning against the plain side, apart from opening and writing. *)
  Printf.printf "{\"containers\": %d, \"opened\": %d, \"stored\": %d, \"retained\": %d, \"bytes\": %d, \"seconds\": %.3f, \"scan_seconds\": %.3f, \"mib_per_s\": %.1f, \"files_per_s\": %.1f}\n"
    containers !opened !stored !retained !bytes dt !scan_seconds (float !bytes /. 1048576. /. dt) (float !stored /. dt)

let () =
  let args = List.tl (Array.to_list Sys.argv) in
  let flag f = List.mem f args in
  let value f d = let rec go = function a :: v :: _ when a = f -> v | _ :: r -> go r | [] -> d in go args in
  let pos = let rec go = function
      | [] -> [] | ("--depth" | "--batch-mib" | "--workers") :: _ :: r -> go r
      | a :: r when String.length a > 2 && String.sub a 0 2 = "--" -> go r | a :: r -> a :: go r in go args in
  try match pos with
    | ["pack-tree"; root; out] ->
        pack_tree root out ~depth:(int_of_string (value "--depth" "2"))
          ~journal:(if flag "--wal" then Packdir.Wal else Packdir.Delete)
          ~batch_bytes:(int_of_string (value "--batch-mib" "256") * 1048576)
          ~workers:(int_of_string (value "--workers" "1"))
    | ["list"; path] ->
        let c = Packdir.open_ path in
        List.iter (fun (m : Packdir.member) ->
          Printf.printf "%s\t%Ld\t%Ld\t%s%s\n" m.name m.size m.mtime_ns (Dng_archive.Native.base64_encode m.sha256)
            (if m.retained then "\tretained" else "")) (Packdir.members c);
        Packdir.close c
    | "verify" :: (_ :: _ as paths) ->
        let bad = List.fold_left (fun bad p ->
          let c = Packdir.open_ p in
          let problems = Packdir.verify c in
          Packdir.close c;
          List.iter (fun e -> Printf.printf "%s: %s\n" p e) problems;
          if problems = [] then Printf.printf "%s: ok, %d members\n" p (List.length (Packdir.members (Packdir.open_ p)));
          bad + List.length problems) 0 paths in
        if bad > 0 then exit 1
    | ["restore"; path; out] ->
        let c = Packdir.open_ path in
        Fun.protect ~finally:(fun () -> Packdir.close c) (fun () ->
          Packdir.restore ~skip_retained:(flag "--skip-retained") c out)
    | _ -> usage ()
  with Failure e | Sys_error e -> prerr_endline ("unison-packdir: " ^ e); exit 1
     | Unix.Unix_error (e, f, a) -> Printf.eprintf "unison-packdir: %s: %s %s\n" f (Unix.error_message e) a; exit 1
