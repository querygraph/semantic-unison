(* Independent direct ABI qualification. No threads and no OCaml callback from
   the private released-runtime native fault wrappers. *)
[@@@alert "-unsafe_multidomain"]
external setup : int -> string -> string -> string -> unit = "scratch_fixture_setup"
external stats : unit -> int array = "scratch_fixture_stats"
external generated_name : unit -> string = "scratch_fixture_name"
external recycled : unit -> bool = "scratch_fixture_recycled"
external fdcount : unit -> int = "scratch_fixture_fdcount"
external fdflags : Unix.file_descr -> int = "scratch_fixture_flags"
external parent_unchanged : unit -> bool = "scratch_fixture_parent_unchanged"
external filesystem : string -> string = "scratch_fixture_filesystem"

type api = Legacy | Strict | Handles
type result = Shared of Unix.file_descr * Unix.file_descr * Unix.file_descr option
            | Declined of Fs.clone_stage_decline option
type call_result = Result of result | Error of Unix.error * string
let label = function Legacy -> "legacy" | Strict -> "strict" | Handles -> "handles"
let invoke api source target = match api with
  | Legacy -> (match Fs.clone_stage source target with None -> Declined None | Some (a,b) -> Shared(a,b,None))
  | Strict -> (match Fs.clone_stage_status source target with Fs.Declined_stage d -> Declined(Some d) | Fs.Shared_stage(a,b) -> Shared(a,b,None))
  | Handles -> (match Fs.clone_stage_handles source target with Fs.Declined_stage_handles d -> Declined(Some d) | Fs.Shared_stage_handles(a,b,c) -> Shared(a,b,Some c))
let checks = ref 0
let check condition message = incr checks; if not condition then failwith message
let same a b = a.Unix.st_dev = b.Unix.st_dev && a.Unix.st_ino = b.Unix.st_ino
let write path bytes = let f = open_out_bin path in Fun.protect ~finally:(fun () -> close_out f) (fun () -> output_string f bytes)
let read_fd f =
  ignore (Unix.lseek f 0 Unix.SEEK_SET);
  let b = Bytes.create 16384 in let n = Unix.read f b 0 (Bytes.length b) in Bytes.sub_string b 0 n
let read path = let f = Unix.openfile path [Unix.O_RDONLY] 0 in Fun.protect ~finally:(fun () -> Unix.close f) (fun () -> read_fd f)
let inventory path = List.sort String.compare (Array.to_list (Sys.readdir path))
let metadata s = s.Unix.st_dev,s.Unix.st_ino,s.Unix.st_kind,s.Unix.st_perm,s.Unix.st_nlink,s.Unix.st_uid,s.Unix.st_gid,s.Unix.st_size,s.Unix.st_mtime,s.Unix.st_ctime
let root = Sys.argv.(1)
let selected = if Array.length Sys.argv > 2 then Sys.argv.(2) else "all"
let apis = if Array.length Sys.argv > 3 then
    [match Sys.argv.(3) with "legacy" -> Legacy | "strict" -> Strict | "handles" -> Handles | _ -> failwith "unknown ABI"]
  else [Legacy;Strict;Handles]
let payload = String.init 8192 (fun i -> Char.chr (i land 255))
let cases = ref 0

let run api fault name expected f =
  if selected = "all" || selected = name then (
    incr cases;
    let base = Filename.concat root (Printf.sprintf "%s-%03d-%s" (label api) !cases name) in
    Unix.mkdir base 0o700;
    let source = base ^ "-source" in write source payload; Unix.chmod source 0o400;
    let before = Unix.stat source in
    let moved = base ^ "-held" in
    let leaf = if fault = 54 then String.make 255 'z' else if fault = 60 then String.make 254 'z' else if fault = 55 then "étude-照片.dng" else "stage" in
    let target = if fault = 56 then leaf else Filename.concat base leaf in
    let count = fdcount () in setup fault base moved source;
    Printf.printf "case %s/%s\n%!" (label api) name;
    let cwd = Sys.getcwd () in
    if fault = 56 then Unix.chdir base;
    let result = Fun.protect ~finally:(fun () -> if fault = 56 then Unix.chdir cwd)
      (fun () -> try Result (invoke api source target) with Unix.Unix_error(e,p,_) -> Error(e,p)) in
    (match expected, result with
     | "success", Result(Shared(basis, output, parent)) ->
       let actual = if fault = 1 then moved else base in
       Fun.protect ~finally:(fun () ->
         Unix.close basis; Unix.close output; Option.iter Unix.close parent;
         let path = Filename.concat actual leaf in
         if Sys.file_exists path then Unix.unlink path)
         (fun () ->
           check (fdcount () = count + (if api = Handles then 3 else 2)) (name ^ ": returned FD count");
           let bs = Unix.fstat basis and out = Unix.fstat output in
           check (bs.Unix.st_kind = Unix.S_REG && out.Unix.st_kind = Unix.S_REG) "regular outputs";
           check (bs.Unix.st_nlink = (if fault = 36 then 1 else 0)) "basis unlinked before return";
           check (out.Unix.st_nlink = 1) "single output link";
           check (not (same bs out) && not (same bs before) && not (same out before)) "independent clone identities";
           check (fdflags basis = 4 && fdflags output = 6) "read-only basis, writable output, CLOEXEC";
           check (out.Unix.st_perm land 0o777 = 0o600) "normalized output mode";
           check (read_fd basis = payload && read_fd output = payload) "exact cloned bytes";
           ignore (Unix.lseek output 31 Unix.SEEK_SET);
           check (Unix.write_substring output "CHANGED" 0 7 = 7) "writable output";
           check (read_fd basis = payload && read_fd output <> payload) "copy on write independence";
           check ((parent <> None) = (api = Handles)) "ABI parent option";
           Option.iter (fun p -> check (same (Unix.fstat p) (Unix.stat actual)) "actual held parent returned") parent;
           f actual source)
     | _, Error(actual,operation) ->
       let error,phase = Scanf.sscanf expected "%s %s" (fun error phase -> error,phase) in
       let expected_error = match error with
         | "EIO" -> Unix.EIO | "EACCES" -> Unix.EACCES | "ENOSPC" -> Unix.ENOSPC
         | "EMFILE" -> Unix.EMFILE | "EEXIST" -> Unix.EEXIST | "EBUSY" -> Unix.EBUSY
         | "ENOENT" -> Unix.ENOENT | _ -> failwith (name ^ ": unexpected error " ^ expected) in
       let phase = String.map (fun c -> if c = '_' then ' ' else c) phase in
       check (actual = expected_error) (Printf.sprintf "%s: errno %s, expected %s" name (Unix.error_message actual) error);
       check (operation = (if api = Legacy then "clone_stage" else "clone_stage: " ^ phase)) (name ^ ": phase " ^ operation);
       f base source
     | expected, Result(Declined actual) when String.length expected >= 7 && String.sub expected 0 7 = "decline" ->
       let reason = match expected with
         | "decline unsupported" -> Fs.Operation_unsupported
         | "decline cross-device" -> Fs.Cross_device
         | "decline unavailable" -> Fs.Platform_unavailable
         | _ -> failwith expected in
       check (actual = (if api = Legacy then None else Some reason)) (name ^ ": decline reason"); f base source
     | _, Result(Declined _) -> failwith (name ^ ": unexpected unsupported decline")
     | _, Result(Shared(a,b,p)) -> Unix.close a; Unix.close b; Option.iter Unix.close p; failwith (name ^ ": unexpected success"));
    if fault = 28 || fault = 39 || fault = 40 || fault = 57 || fault = 58 || fault = 59 || (fault = 41 && api <> Handles) then
      check (recycled ()) "recycled descriptor was closed by stale slot";
    check (fdcount () = count) (name ^ ": descriptor leak");
    if fault = 38 then (
      check (read source = "replacement source") "source replacement preserved";
      check (read (source ^ "-displaced") = payload) "original held source preserved"
    ) else (
      check (read source = payload) (name ^ ": source data changed");
      check (metadata (Unix.stat source) = metadata before) (name ^ ": source metadata/identity changed"));
    let s = stats () in
    Printf.printf "ok %d %s/%s assertions=%d native=%s\n%!" !cases (label api) name !checks
      (String.concat "," (Array.to_list (Array.map string_of_int s)))
  )
let empty base _ = check (inventory base = []) "unexpected private artifact"
let no_clones () = check ((stats ()).(2) = 0) "cloning began after reservation failure"
let scratch base = Filename.concat base (generated_name ())
let one_scratch base _ = check (inventory base = [generated_name ()]) "unproven private basis artifact inventory"; check (read (scratch base) = payload) "unproven cloned basis changed"
let output_artifact base _ = check (inventory base = ["stage"]) "unproven output artifact inventory"; check (read (Filename.concat base "stage") = payload) "unproven output clone changed"
let foreign_scratch base _ =
  check (inventory base = List.sort String.compare [generated_name ();"displaced-owned"]) "scratch replacement inventory";
  check (read (scratch base) = "foreign sentinel") "foreign scratch replacement removed/changed"
let foreign_output base _ =
  check (inventory base = ["displaced-owned";"stage"]) "output replacement inventory";
  check (read (Filename.concat base "stage") = "foreign sentinel") "foreign output replacement removed/changed";
  check (read (Filename.concat base "displaced-owned") = payload) "displaced admitted output changed"
let replacement_kind is_basis directory base _ =
  let leaf = if is_basis then generated_name () else "stage" in
  check (inventory base = List.sort String.compare [leaf;"displaced-owned"]) "nonregular replacement inventory";
  let path = Filename.concat base leaf in
  check ((Unix.lstat path).Unix.st_kind = (if directory then Unix.S_DIR else Unix.S_LNK)) "nonregular replacement kind changed";
  if directory then check (inventory path = []) "foreign replacement directory changed"
  else check (Unix.readlink path = "absent-target") "foreign replacement symlink changed"

let () =
  let filesystem = filesystem root in
  Printf.printf "Filesystem %s\n%!" filesystem;
  if filesystem <> "apfs" then failwith "native scratch qualification requires APFS";
  List.iter (fun api ->
    run api 0 "normal" "success" (fun base _ ->
      check (inventory base = ["stage"]) "success retained scratch";
      let s = stats () in check (s.(0) = 1 && s.(1) = 1 && s.(2) = 2) "normal reserve/clone counters";
      check (s.(8) = 2 && s.(9) = 1) "source stability checks disappeared");
    run api 1 "held-parent-rebind" "success" (fun actual _ ->
      let original = String.sub actual 0 (String.length actual - 5) in
      check (inventory actual = ["stage"]) "held parent retains scratch";
      check (inventory original = ["parent-sentinel"]) "replacement parent changed";
      check ((stats ()).(13) = 0 && (stats ()).(14) = 0) "reservation escaped held parent";
      check (parent_unchanged ()) "replacement parent timestamps changed";
      check (read (Filename.concat original "parent-sentinel") = "foreign sentinel") "replacement parent sentinel damaged");
    run api 2 "three-collision-kinds" "success" (fun base _ ->
      let names = List.filter (fun name -> name <> "stage") (inventory base) in
      check (List.length names = 3) "collision names removed";
      check ((stats ()).(0) = 4 && (stats ()).(1) = 4) "wrong collision retry count";
      check (List.map (fun n -> (Unix.lstat (Filename.concat base n)).Unix.st_kind) names = [Unix.S_REG;Unix.S_LNK;Unix.S_DIR]) "collision kinds changed";
      check (read (Filename.concat base (List.hd names)) = "foreign sentinel") "collision file damaged";
      check (Unix.readlink (Filename.concat base (List.nth names 1)) = "absent-target") "collision symlink followed";
      check (inventory (Filename.concat base (List.nth names 2)) = []) "collision directory changed");
    run api 3 "128-collision-exhaustion" "EEXIST basis_reservation" (fun base _ ->
      check (List.length (inventory base) = 128) "exhaustion removed collision names";
      check ((stats ()).(0) = 128 && (stats ()).(1) = 128) "unbounded/wrong collision retry count";
      List.iter (fun name -> check (read (Filename.concat base name) = "foreign sentinel") "collision exhaustion sentinel damaged") (inventory base);
      no_clones ());
    run api 4 "reservation-replacement" "EBUSY reservation_removal" (fun base source -> foreign_scratch base source; check (read (Filename.concat base "displaced-owned") = "") "blank reservation modified"; no_clones ());
    run api 5 "reservation-missing" "ENOENT reservation_removal" (fun base source -> empty base source; no_clones ());
    List.iter (fun (fault,name,error) ->
      run api fault name (error ^ " basis_reservation") (fun base source -> empty base source; no_clones ()))
      [6,"reserve-EIO","EIO";7,"reserve-ENOSPC","ENOSPC";8,"reserve-EACCES","EACCES";9,"reserve-EMFILE","EMFILE"];
    run api 10 "reservation-stat-once" "EIO reservation_removal" (fun base source -> empty base source; no_clones ());
    run api 11 "reservation-stat-always" "EIO reservation_removal" (fun base _ -> check (inventory base = [generated_name ()]) "unwitnessed reservation inventory"; check (read (scratch base) = "") "unwitnessed reservation changed"; no_clones ());
    run api 12 "reservation-unlink-once" "EACCES reservation_removal" (fun base source -> empty base source; no_clones ());
    run api 13 "reservation-unlink-always" "EACCES reservation_removal" (fun base _ -> check (inventory base = [generated_name ()]) "failed removal private reservation missing"; check (read (scratch base) = "") "failed removal reservation changed"; no_clones ());
    List.iter (fun (fault,name,reason) -> run api fault name reason empty)
      [14,"basis-unsupported","decline unsupported";15,"basis-cross-device","decline cross-device";16,"basis-unavailable","decline unavailable"];
    run api 17 "basis-clone-EIO" "EIO basis_clone" empty;
    run api 18 "basis-first-open" "EIO basis_open" one_scratch;
    run api 19 "basis-first-stat" "EIO basis_identity" one_scratch;
    run api 20 "basis-replacement" "EBUSY basis_unlink" (fun base source -> foreign_scratch base source; check (read (Filename.concat base "displaced-owned") = payload) "displaced basis damaged");
    run api 21 "basis-missing" "ENOENT basis_unlink" empty;
    run api 22 "output-clone-EIO" "EIO output_clone" empty;
    run api 23 "output-first-open" "EIO output_read_open" output_artifact;
    run api 24 "output-first-stat" "EIO output_identity" output_artifact;
    run api 25 "output-replacement-preserves-primary" "EACCES writable_mode" foreign_output;
    run api 26 "output-missing-preserves-primary" "EACCES writable_mode" empty;
    run api 27 "output-mode-EACCES" "EACCES writable_mode" empty;
    run api 28 "clear-before-close-recycled-fd" "EIO reservation_close" (fun base source -> empty base source; no_clones ());
    run api 29 "output-write-open" "EIO output_write_open" empty;
    run api 30 "output-reopen-identity" "EBUSY output_reopen_identity" empty;
    run api 31 "basis-unlink-once" "EIO basis_unlink" empty;
    run api 32 "basis-unlink-always" "EIO basis_unlink" one_scratch;
    run api 33 "source-stat-EIO" "EIO source_stability" empty;
    run api 34 "source-name-EACCES" "EACCES source_stability" empty;
    run api 35 "reservation-alias-after-admission" "success" (fun base _ ->
      check (inventory base = ["owned-alias";"stage"]) "reservation alias cleanup authority";
      check (read (Filename.concat base "owned-alias") = "") "reservation alias damaged");
    run api 36 "basis-alias-after-admission" "success" (fun base _ ->
      check (inventory base = ["owned-alias";"stage"]) "basis alias cleanup authority";
      check (read (Filename.concat base "owned-alias") = payload) "basis alias damaged");
    run api 37 "output-alias-after-admission" "EACCES writable_mode" (fun base _ ->
      check (inventory base = ["owned-alias"]) "admitted output alias prevented owned-name cleanup";
      check (read (Filename.concat base "owned-alias") = payload) "output alias damaged");
    run api 38 "source-replacement" "EBUSY source_stability" empty;
    run api 39 "source-close-recycled-fd" "EIO source_close" empty;
    run api 40 "output-read-close-recycled-fd" "EIO output_read_close" empty;
    if api <> Handles then
      run api 41 "parent-close-recycled-fd" "EIO destination_parent_close" output_artifact;
    run api 42 "reservation-symlink-replacement" "EBUSY reservation_removal" (fun base source -> replacement_kind true false base source; check (read (Filename.concat base "displaced-owned") = "") "displaced reservation damaged"; no_clones ());
    run api 43 "reservation-directory-replacement" "EBUSY reservation_removal" (fun base source -> replacement_kind true true base source; check (read (Filename.concat base "displaced-owned") = "") "displaced reservation damaged"; no_clones ());
    run api 44 "basis-symlink-replacement" "EBUSY basis_unlink" (replacement_kind true false);
    run api 45 "basis-directory-replacement" "EBUSY basis_unlink" (replacement_kind true true);
    run api 46 "output-symlink-replacement" "EACCES writable_mode" (replacement_kind false false);
    run api 47 "output-directory-replacement" "EACCES writable_mode" (replacement_kind false true);
    run api 48 "reservation-mode-mtime-change" "success" (fun base _ -> check (inventory base = ["stage"]) "reservation mutable fields blocked cleanup");
    run api 49 "basis-mode-mtime-change" "success" (fun base _ -> check (inventory base = ["stage"]) "basis mutable fields blocked cleanup");
    run api 50 "output-mode-mtime-change" "EACCES writable_mode" empty;
    run api 51 "missing-cleanup-name-bad-witness" "ENOENT reservation_removal" (fun base source -> empty base source; check ((stats ()).(4) = 1) "missing_ok masked bad witness by looking up name"; no_clones ());
    run api 52 "basis-unproven-replaced-first-open" "EIO basis_open" (fun base source -> foreign_scratch base source; check (read (Filename.concat base "displaced-owned") = payload) "unproven basis displaced data changed");
    run api 53 "output-unproven-replaced-first-open" "EIO output_read_open" foreign_output;
    run api 54 "255-byte-output-leaf" "success" (fun base _ -> check (inventory base = [String.make 255 'z']) "long output leaf staging failed");
    run api 55 "unicode-output-leaf" "success" (fun base _ -> check (inventory base = ["étude-照片.dng"]) "Unicode output leaf staging failed");
    run api 56 "relative-output-leaf" "success" (fun base _ -> check (inventory base = ["stage"]) "relative output leaf staging failed");
    run api 57 "parent-close-preserves-primary" "EACCES writable_mode" empty;
    run api 58 "source-close-overrides-pure-decline" "EIO source_close" empty;
    run api 59 "read-close-preserves-primary" "EACCES writable_mode" empty;
    run api 60 "254-byte-output-leaf" "success" (fun base _ -> check (inventory base = [String.make 254 'z']) "long output leaf staging failed")
  ) apis;
  check (!cases > 0) "no designated fixture case selected";
  Printf.printf "All %d clone-scratch cases passed; %d assertions\n%!" !cases !checks
