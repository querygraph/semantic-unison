(* unison-skeleton: list, check and restore the skeleton versions Unison keeps
   of replaced files (preferences skeleton, skeletonnot, maxskeletons and
   skeletondir; docs/skeleton-versions.md).

   It reads the store and the replica and writes one file only, the one named
   by --out, which may be neither inside the replica nor inside the store. *)

let usage = "usage: unison-skeleton list ROOT [PATH] [--skeletondir DIR]\n\
\       unison-skeleton restore ROOT PATH (--version N | --sha256 HEX) --out FILE [--skeletondir DIR]\n\
\       unison-skeleton verify ROOT [PATH] [--skeletondir DIR]\n\
\n\
ROOT is a replica root as the profile names it; PATH is a path inside it,\n\
relative to ROOT.  The store is --skeletondir, else $UNISONSKELETONDIR, else\n\
the directory skeletons in the Unison directory.  A version's number N is the\n\
one list prints; it stays the same when older versions are pruned.\n"

exception Die of string
let die fmt = Printf.ksprintf (fun m -> raise (Die m)) fmt

let canonical dir =
  try Fspath.toString (Fspath.canonize (Some dir)) with Util.Fatal _ | Util.Transient _ -> dir

let store_dir = function
  | Some dir -> canonical dir
  | None ->
      (match Sys.getenv_opt "UNISONSKELETONDIR" with
       | Some dir when dir <> "" -> canonical dir
       | _ -> canonical (Util.fileInUnisonDir "skeletons"))

let stamp t =
  let tm = Unix.localtime t in
  Printf.sprintf "%04d-%02d-%02d %02d:%02d:%02d" (tm.Unix.tm_year + 1900) (tm.Unix.tm_mon + 1)
    tm.Unix.tm_mday tm.Unix.tm_hour tm.Unix.tm_min tm.Unix.tm_sec

let how (v : SkeletonStore.version) =
  match v.SkeletonStore.kind, v.SkeletonStore.stored with
  | SkeletonStore.Whole, _ -> "whole file"
  | SkeletonStore.Skel, SkeletonStore.Delta base ->
      Printf.sprintf "skeleton (%s), delta against version %d" v.SkeletonStore.format base
  | SkeletonStore.Skel, _ -> Printf.sprintf "skeleton (%s), stored in full" v.SkeletonStore.format

let live root path = if path = "" then root else Filename.concat root path

let live_opt root path =
  let file = live root path in
  match Unix.stat file with
  | { Unix.st_kind = Unix.S_REG; _ } -> Some file
  | _ | exception Unix.Unix_error _ -> None

let paths_of ~store ~root = function
  | Some path -> [ path ]
  | None -> SkeletonStore.paths ~store ~root

let list ~store ~root path =
  List.iter (fun path ->
    match SkeletonStore.chain ~store ~root ~path with
    | None -> Printf.printf "%s\n  no versions kept\n" path
    | Some chain ->
        Printf.printf "%s\n" (if path = "" then "(the root itself)" else path);
        List.iter (fun (v : SkeletonStore.version) ->
          Printf.printf "  version %d  %s  %d bytes  sha256 %s  %s, %d bytes stored\n"
            v.SkeletonStore.seq (stamp v.SkeletonStore.time) v.SkeletonStore.size
            v.SkeletonStore.sha256 (how v) v.SkeletonStore.stored_bytes) chain.SkeletonStore.versions;
        (match chain.SkeletonStore.pending with
         | Some (seq, time) ->
             Printf.printf "  pending %d  %s  a replaced file kept whole until the next synchronization settles it\n"
               seq (stamp time)
         | None -> ());
        let records, blocks, wholes = SkeletonStore.stored_bytes ~store ~root ~path in
        Printf.printf "  store: %d bytes of records, %d bytes of kept blocks, %d bytes of whole files\n"
          records blocks wholes) (paths_of ~store ~root path)

let verify ~store ~root path =
  let failed = ref 0 and checked = ref 0 in
  List.iter (fun path ->
    match SkeletonStore.chain ~store ~root ~path with
    | None -> Printf.printf "%s: no versions kept\n" path
    | Some chain ->
        (match chain.SkeletonStore.pending with
         | Some (seq, _) -> Printf.printf "%s: pending %d is not settled yet\n" path seq
         | None -> ());
        List.iter (fun ((v : SkeletonStore.version), result) ->
          incr checked;
          match result with
          | None -> Printf.printf "%s: version %d ok\n" path v.SkeletonStore.seq
          | Some why ->
              incr failed;
              Printf.printf "%s: version %d CANNOT BE REBUILT: %s\n" path v.SkeletonStore.seq why)
          (try SkeletonStore.verify ~store ~root ~path ~live:(live_opt root path)
           with Failure why -> incr failed; Printf.printf "%s: %s\n" path why; []))
    (paths_of ~store ~root path);
  Printf.printf "%d versions checked, %d cannot be rebuilt\n" !checked !failed;
  if !failed > 0 then exit 1

let inside dir file =
  let dir = if dir <> "" && dir.[String.length dir - 1] = '/' then dir else dir ^ "/" in
  String.length file >= String.length dir && String.sub file 0 (String.length dir) = dir

let restore ~store ~root ~path ~pick ~out =
  let chain = match SkeletonStore.chain ~store ~root ~path with
    | Some chain -> chain
    | None -> die "%s has no versions in %s" path store in
  let versions = List.rev chain.SkeletonStore.versions in
  let v = match pick with
    | `Version n ->
        (match List.find_opt (fun (v : SkeletonStore.version) -> v.SkeletonStore.seq = n) versions with
         | Some v -> v
         | None -> die "version %d of %s is not kept" n path)
    | `Sha256 hex ->
        let hex = String.lowercase_ascii hex in
        if String.length hex < 8 then die "--sha256 needs at least 8 hex digits";
        (match List.filter (fun (v : SkeletonStore.version) ->
                 String.length v.SkeletonStore.sha256 >= String.length hex
                 && String.sub v.SkeletonStore.sha256 0 (String.length hex) = hex) versions with
         | v :: rest when List.for_all (fun (w : SkeletonStore.version) ->
                              w.SkeletonStore.sha256 = v.SkeletonStore.sha256) rest -> v
         | [] -> die "no kept version of %s has SHA-256 %s" path hex
         | _ -> die "SHA-256 prefix %s matches several versions of %s" hex path) in
  let target = Filename.concat (canonical (Filename.dirname out)) (Filename.basename out) in
  if inside root target || target = root then die "--out must not be inside the replica %s" root;
  if inside store target then die "--out must not be inside the store %s" store;
  if Sys.file_exists target then die "%s exists; choose another name" target;
  let tmp = Printf.sprintf "%s.unison-skeleton-%d.tmp" target (Unix.getpid ()) in
  let oc = open_out_gen [ Open_wronly; Open_creat; Open_excl; Open_binary ] 0o600 tmp in
  let finished = ref false in
  Fun.protect
    ~finally:(fun () -> close_out_noerr oc; if not !finished then (try Sys.remove tmp with Sys_error _ -> ()))
    (fun () ->
       (try
          SkeletonStore.restore ~store ~root ~path ~live:(live_opt root path) ~seq:v.SkeletonStore.seq
            ~write:(fun s o n -> output_substring oc s o n)
            ~reset:(fun () -> flush oc; Unix.ftruncate (Unix.descr_of_out_channel oc) 0; seek_out oc 0)
        with Failure why -> die "%s; nothing was written" why);
       close_out oc;
       (* The store checked the stream; check the file that was written too. *)
       if SkeletonStore.sha_of_file tmp <> v.SkeletonStore.sha256 then
         die "the written file does not have SHA-256 %s; nothing was kept" v.SkeletonStore.sha256;
       Unix.rename tmp target;
       finished := true);
  Printf.printf "%s: version %d of %s, %d bytes, sha256 %s\n" target v.SkeletonStore.seq
    (if path = "" then "the root" else path) v.SkeletonStore.size v.SkeletonStore.sha256

let () =
  let dir = ref None and version = ref None and sha = ref None and out = ref None in
  let rec parse acc = function
    | [] -> List.rev acc
    | ("--skeletondir" | "-skeletondir") :: v :: rest -> dir := Some v; parse acc rest
    | "--version" :: v :: rest ->
        (match int_of_string_opt v with
         | Some n -> version := Some n
         | None -> die "--version needs a number");
        parse acc rest
    | "--sha256" :: v :: rest -> sha := Some v; parse acc rest
    | "--out" :: v :: rest -> out := Some v; parse acc rest
    | ("-h" | "--help" | "-help") :: _ -> print_string usage; exit 0
    | arg :: _ when String.length arg > 1 && arg.[0] = '-' -> die "unknown option %s\n%s" arg usage
    | arg :: rest -> parse (arg :: acc) rest in
  try
    let args = parse [] (List.tl (Array.to_list Sys.argv)) in
    let store = store_dir !dir in
    match args with
    | [ "list"; root ] -> list ~store ~root:(canonical root) None
    | [ "list"; root; path ] -> list ~store ~root:(canonical root) (Some path)
    | [ "verify"; root ] -> verify ~store ~root:(canonical root) None
    | [ "verify"; root; path ] -> verify ~store ~root:(canonical root) (Some path)
    | [ "restore"; root; path ] ->
        let pick = match !version, !sha with
          | Some n, None -> `Version n
          | None, Some hex -> `Sha256 hex
          | _ -> die "restore needs one of --version N and --sha256 HEX" in
        let out = match !out with Some f -> f | None -> die "restore needs --out FILE" in
        restore ~store ~root:(canonical root) ~path ~pick ~out
    | _ -> prerr_string usage; exit 2
  with
  | Die why | Failure why | Sys_error why | Util.Fatal why | Util.Transient why ->
      prerr_endline ("unison-skeleton: " ^ why); exit 2
  | Unix.Unix_error (e, f, a) ->
      prerr_endline (Printf.sprintf "unison-skeleton: %s %s: %s" f a (Unix.error_message e)); exit 2
