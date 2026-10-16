(* Single-threaded private fixture; no production mutable test controls. *)
[@@@alert "-unsafe_multidomain"]

external set_mode : int -> unit = "handles_fixture_mode"
external set_paths : string -> string -> unit = "handles_fixture_paths"
external fd_count : unit -> int = "handles_fixture_count"
external fd_flags : Unix.file_descr -> int = "handles_fixture_flags"
external matches : Unix.file_descr -> string -> Unix.file_descr -> bool = "handles_fixture_matches"
external unlink_matching : Unix.file_descr -> string -> Unix.file_descr -> bool = "handles_fixture_unlink"
external xattrs : Unix.file_descr -> int = "handles_fixture_xattrs"
external empty_acl : Unix.file_descr -> bool = "handles_fixture_empty_acl"

type api = Legacy | Strict | Handles
type result = Shared of Unix.file_descr * Unix.file_descr * Unix.file_descr option
            | Declined of Fs.clone_stage_decline option

let invoke api source stage = match api with
  | Legacy -> (match Fs.clone_stage source stage with
      | None -> Declined None | Some (a,b) -> Shared (a,b,None))
  | Strict -> (match Fs.clone_stage_status source stage with
      | Fs.Declined_stage reason -> Declined (Some reason)
      | Fs.Shared_stage (a,b) -> Shared (a,b,None))
  | Handles -> (match Fs.clone_stage_handles source stage with
      | Fs.Declined_stage_handles reason -> Declined (Some reason)
      | Fs.Shared_stage_handles (a,b,c) -> Shared (a,b,Some c))

let check yes message = if not yes then failwith message
let read fd =
  ignore (Unix.lseek fd 0 Unix.SEEK_SET);
  let bytes = Bytes.create 16384 in
  let count = Unix.read fd bytes 0 (Bytes.length bytes) in
  Bytes.sub_string bytes 0 count
let read_file path =
  let fd = Unix.openfile path [Unix.O_RDONLY] 0 in
  Fun.protect ~finally:(fun () -> Unix.close fd) (fun () -> read fd)
let write_file path text =
  let ch = open_out_bin path in
  Fun.protect ~finally:(fun () -> close_out ch) (fun () -> output_string ch text)
let same_object a b = a.Unix.st_dev = b.Unix.st_dev && a.Unix.st_ino = b.Unix.st_ino
let expect_error expected phase f =
  match f () with
  | _ -> failwith "expected Unix error"
  | exception Unix.Unix_error (error, operation, _) ->
      check (error = expected) ("wrong errno: " ^ Unix.error_message error);
      check (operation = phase) ("wrong phase: " ^ operation)

let root = Sys.argv.(1)
let source = Filename.concat root "source"
let original = read_file source
let cases = ref 0
let run name test =
  set_mode 0;
  let count = fd_count () in
  test ();
  set_mode 0;
  Gc.full_major ();
  check (fd_count () = count) (name ^ ": descriptor leak");
  check (read_file source = original) (name ^ ": live source changed");
  incr cases;
  Printf.printf "ok %d %s\n%!" !cases name
let directory name =
  let path = Filename.concat root name in Unix.mkdir path 0o700; path
let with_stage api source parent f =
  let path = Filename.concat parent "stage" in
  match invoke api source path with
  | Declined _ -> failwith "unexpected clone decline"
  | Shared (basis,stage,held_parent) ->
      Fun.protect ~finally:(fun () ->
        (match held_parent with
         | Some parent -> ignore (unlink_matching parent "stage" stage)
         | None -> if Sys.file_exists path then Unix.unlink path);
        Unix.close basis; Unix.close stage;
        Option.iter Unix.close held_parent)
        (fun () -> f path basis stage held_parent)
let parent = function Some parent -> parent | None -> failwith "missing parent"
let absent path = check (not (Sys.file_exists path)) ("unexpected path " ^ path)
let empty directory = check (Sys.readdir directory = [||]) ("leftovers in " ^ directory)

let () =
  let probe = directory "probe" in
  (match invoke Handles source (Filename.concat probe "stage") with
   | Declined (Some (Fs.Platform_unavailable | Fs.Operation_unsupported)) -> exit 77
   | Declined _ -> failwith "unexpected probe decline"
   | Shared (a,b,c) -> Unix.close a; Unix.close b; Option.iter Unix.close c;
       Unix.unlink (Filename.concat probe "stage"));

  run "three identities, modes, offsets, CLOEXEC and normalization" (fun () ->
    let dir = directory "identity" and before = fd_count () in
    with_stage Handles source dir (fun path basis stage directory ->
      let directory = parent directory in
      let src = Unix.stat source and bs = Unix.fstat basis
      and dst = Unix.fstat stage and pd = Unix.fstat directory in
      check (fd_count () = before + 3) "new ABI must own exactly three FDs";
      check (bs.Unix.st_kind = Unix.S_REG && dst.Unix.st_kind = Unix.S_REG && pd.Unix.st_kind = Unix.S_DIR) "kinds";
      check (not (same_object src bs) && not (same_object src dst) && not (same_object bs dst)) "distinct objects";
      check (bs.Unix.st_nlink = 0 && dst.Unix.st_nlink = 1) "link counts";
      check (same_object pd (Unix.stat dir) && same_object dst (Unix.stat path)) "named identities";
      check (Unix.lseek basis 0 Unix.SEEK_CUR = 0 && Unix.lseek stage 0 Unix.SEEK_CUR = 0) "initial offsets";
      check (fd_flags basis = 4 && fd_flags stage = 6 && fd_flags directory = 4) "access/CLOEXEC";
      check (dst.Unix.st_perm land 0o777 = 0o600 && src.Unix.st_perm land 0o777 = 0o400) "modes";
      check (xattrs stage = 0) "inherited xattrs/resource fork";
      check (empty_acl stage) "inherited ACL";
      let live = Unix.openfile source [Unix.O_RDONLY] 0 in
      Fun.protect ~finally:(fun () -> Unix.close live)
        (fun () -> check (not (empty_acl live)) "source ACL positive control");
      check (matches directory "stage" stage) "parent lookup";
      check (read basis = original && read stage = original) "initial bytes";
      expect_error Unix.EBADF "write" (fun () -> Unix.write_substring basis "x" 0 1);
      ignore (Unix.lseek stage 17 Unix.SEEK_SET);
      check (Unix.write_substring stage "PATCH" 0 5 = 5) "stage write";
      check (read basis = original && read stage <> original) "basis isolation"));

  run "retained parent after directory rename and same-path replacement" (fun () ->
    let dir = directory "renamed" in
    let moved = dir ^ "-old" in
    with_stage Handles source dir (fun path _ stage directory ->
      let directory = parent directory in
      Unix.rename dir moved; Unix.mkdir dir 0o700;
      write_file path "replacement sentinel";
      check (same_object (Unix.fstat directory) (Unix.stat moved)) "retained original parent";
      check (not (same_object (Unix.fstat directory) (Unix.stat dir))) "replacement parent differs";
      check (matches directory "stage" stage) "lookup after rename";
      check (unlink_matching directory "stage" stage) "relative cleanup";
      check (read_file path = "replacement sentinel") "replacement damaged";
      absent (Filename.concat moved "stage")));

  run "actual creation parent survives rebind inside native clone engine" (fun () ->
    let dir = directory "during-clone" in
    let moved = dir ^ "-old" in
    set_paths dir moved; set_mode 7;
    with_stage Handles source dir (fun path _ stage directory ->
      let directory = parent directory in
      check (same_object (Unix.fstat directory) (Unix.stat moved)) "returned a later lookup";
      check (matches directory "stage" stage && read stage = original) "wrong staged object";
      check (unlink_matching directory "stage" stage) "owned relative cleanup";
      check (read_file path = "replacement sentinel") "replacement damaged"));

  run "guarded fixture cleanup preserves replaced stage leaf" (fun () ->
    let dir = directory "replaced-leaf" in
    with_stage Handles source dir (fun path _ stage directory ->
      let directory = parent directory and moved = path ^ "-old" in
      Unix.rename path moved; write_file path "replacement sentinel";
      check (not (matches directory "stage" stage)) "replacement falsely matched";
      check (not (unlink_matching directory "stage" stage)) "replacement unlinked";
      check (read_file path = "replacement sentinel") "replacement damaged";
      Unix.unlink moved));

  List.iter (fun api ->
    let label = match api with Legacy -> "legacy" | Strict -> "strict" | Handles -> "handles" in
    run (label ^ " success ABI and descriptor count") (fun () ->
      let dir = directory (label ^ "-success") and count = fd_count () in
      with_stage api source dir (fun _ basis stage held ->
        check (fd_count () = count + (if api = Handles then 3 else 2)) "ABI FD count";
        check (read basis = original && read stage = original) "ABI bytes";
        check ((held <> None) = (api = Handles)) "ABI parent"));
    run (label ^ " source declines") (fun () ->
      let dir = directory (label ^ "-declines") in
      List.iter (fun (basis,expected) ->
        match invoke api basis (Filename.concat dir "stage") with
        | Declined reason -> check (reason = (if api = Legacy then None else Some expected)) "decline constructor"
        | Shared _ -> failwith "expected decline")
        [Filename.concat root "flagged", Fs.Source_flags; dir, Fs.Non_regular_source];
      empty dir);
    run (label ^ " native decline scopes") (fun () ->
      let dir = directory (label ^ "-native-declines") in
      List.iter (fun (mode,expected) ->
        set_mode mode;
        match invoke api source (Filename.concat dir "stage") with
        | Declined reason -> check (reason = (if api = Legacy then None else Some expected)) "native decline constructor"
        | Shared _ -> failwith "expected native decline")
        [1,Fs.Operation_unsupported; 2,Fs.Cross_device; 3,Fs.Platform_unavailable];
      empty dir);
    run (label ^ " operational failures close parent and file descriptors") (fun () ->
      let dir = directory (label ^ "-errors") in
      List.iter (fun (mode,error,phase) ->
        set_mode mode;
        expect_error error (if api = Legacy then "clone_stage" else phase)
          (fun () -> invoke api source (Filename.concat dir "stage"));
        empty dir)
        [4,Unix.EIO,"clone_stage: basis clone";
         5,Unix.EIO,"clone_stage: output clone";
         6,Unix.EACCES,"clone_stage: writable mode"]);
    run (label ^ " EEXIST and missing source/parent preserve existing files") (fun () ->
      let dir = directory (label ^ "-existing") in
      let stage = Filename.concat dir "stage" in
      write_file stage "existing sentinel";
      for _ = 1 to 20 do
        expect_error Unix.EEXIST (if api = Legacy then "clone_stage" else "clone_stage: output clone")
          (fun () -> invoke api source stage)
      done;
      check (read_file stage = "existing sentinel") "existing file damaged";
      check (Sys.readdir dir = [|"stage"|]) "scratch leftover";
      expect_error Unix.ENOENT (if api = Legacy then "clone_stage" else "clone_stage: source open")
        (fun () -> invoke api (Filename.concat dir "missing") (Filename.concat dir "unused"));
      expect_error Unix.ENOENT (if api = Legacy then "clone_stage" else "clone_stage: destination parent")
        (fun () -> invoke api source (Filename.concat dir "missing/stage")));
  ) [Legacy;Strict;Handles];

  run "repeated three-FD acquisition and exact cleanup" (fun () ->
    let dir = directory "repeated" in
    for _ = 1 to 64 do
      with_stage Handles source dir (fun _ _ stage directory ->
        check (matches (parent directory) "stage" stage) "repeat identity")
    done;
    empty dir);
  Printf.printf "All %d clone-handle cases passed\n%!" !cases
