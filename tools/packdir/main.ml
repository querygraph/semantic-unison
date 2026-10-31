(* unison-packdir: the packed-directory prototype and its tools.

     unison-packdir pack-tree ROOT OUT [--depth N] [--wal] [--batch-mib M]
       keep every directory N levels under ROOT (default 2, the preview leaves
       <H>/<HHHH>) as OUT/<rel>.sqlar, one container at a time; a rerun stores
       only new and changed files and marks the vanished ones retained
     unison-packdir list C.sqlar
     unison-packdir verify C.sqlar...
     unison-packdir restore C.sqlar OUT_DIR [--skip-retained] *)

let usage () =
  prerr_endline "usage: unison-packdir pack-tree ROOT OUT [--depth N] [--wal] [--batch-mib M]\n\
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

let pack_tree root out ~depth ~journal ~batch_bytes =
  let t0 = Unix.gettimeofday () in
  let containers = ref 0 and stored = ref 0 and retained = ref 0 and bytes = ref 0 in
  List.iter (fun rel ->
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
    Dng_archive.Native.mkdir_p (Filename.dirname target);
    let c = Packdir.open_ ~journal target in
    Fun.protect ~finally:(fun () -> Packdir.close c) (fun () ->
      let s, r, b = Packdir.update ~batch_bytes ~skip c (Filename.concat root rel) in
      incr containers; stored := !stored + s; retained := !retained + r; bytes := !bytes + b)) (dirs_at depth root "");
  let dt = Unix.gettimeofday () -. t0 in
  Printf.printf "{\"containers\": %d, \"stored\": %d, \"retained\": %d, \"bytes\": %d, \"seconds\": %.3f, \"mib_per_s\": %.1f, \"files_per_s\": %.1f}\n"
    !containers !stored !retained !bytes dt (float !bytes /. 1048576. /. dt) (float !stored /. dt)

let () =
  let args = List.tl (Array.to_list Sys.argv) in
  let flag f = List.mem f args in
  let value f d = let rec go = function a :: v :: _ when a = f -> v | _ :: r -> go r | [] -> d in go args in
  let pos = let rec go = function
      | [] -> [] | ("--depth" | "--batch-mib") :: _ :: r -> go r
      | a :: r when String.length a > 2 && String.sub a 0 2 = "--" -> go r | a :: r -> a :: go r in go args in
  try match pos with
    | ["pack-tree"; root; out] ->
        pack_tree root out ~depth:(int_of_string (value "--depth" "2"))
          ~journal:(if flag "--wal" then Packdir.Wal else Packdir.Delete)
          ~batch_bytes:(int_of_string (value "--batch-mib" "256") * 1048576)
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
