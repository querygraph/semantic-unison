module P = StagePublication
(* This isolated fixture uses one execution context and no threads or domains. *)
[@@@alert "-unsafe_multidomain"]
let with_async_exns f = f ()

external open_parent : string -> bool -> Unix.file_descr
  = "stage_publication_fixture_open_parent"
external fd_state : int -> int = "stage_publication_fixture_fd_state"
external fd_number : Unix.file_descr -> int = "stage_publication_fixture_fd_number"
external attribute_fault : int -> int -> unit = "stage_publication_fixture_attribute_fault"
external rename_fault : int -> unit = "stage_publication_fixture_rename_fault"
external native_errno : int -> int = "stage_publication_fixture_errno"
external identity_fault : int -> int -> unit = "stage_publication_fixture_identity_fault"
external dispatch_pending : unit -> unit = "stage_publication_fixture_dispatch_pending"
external toggle_directory_flag : Unix.file_descr -> unit
  = "stage_publication_fixture_toggle_directory_flag"
external native_fd_count : unit -> int = "stage_publication_fixture_fd_count" [@@noalloc]

let check condition message = if not condition then failwith message
let count = ref 0
let serial = ref 0
let payload = String.init 513 (fun i -> Char.chr ((i * 71 + 23) land 255))
let sentinel = "independent replacement sentinel\000\255"

let open_fds () =
  Array.to_list (Sys.readdir "/dev/fd")
  |> List.filter_map (fun name ->
    match int_of_string_opt name with
    | Some n when fd_state n >= 0 -> Some n
    | _ -> None)
  |> List.sort_uniq compare

let new_fds before = List.filter (fun n -> not (List.mem n before)) (open_fds ())
let check_closed descriptors =
  List.iter (fun n -> check (fd_state n = -1) "owned descriptor remained open") descriptors
let check_cloexec descriptors =
  List.iter (fun n -> check (fd_state n = 1) "owned descriptor lacks CLOEXEC") descriptors
let check_alive fd = ignore (Unix.fstat fd)
let close_noerr fd = try Unix.close fd with Unix.Unix_error (Unix.EBADF, _, _) -> ()

let write_file path bytes =
  let fd = Unix.openfile path [Unix.O_WRONLY; Unix.O_CREAT; Unix.O_EXCL; Unix.O_CLOEXEC] 0o600 in
  Fun.protect ~finally:(fun () -> Unix.close fd) (fun () ->
    let rec write offset =
      if offset < String.length bytes then
        let n = Unix.write_substring fd bytes offset (String.length bytes - offset) in
        check (n > 0) "fixture write made no progress";
        write (offset + n)
    in write 0)

let read_file path =
  let channel = open_in_bin path in
  Fun.protect ~finally:(fun () -> close_in channel)
    (fun () -> really_input_string channel (in_channel_length channel))

let exists path =
  try ignore (Unix.lstat path); true with Unix.Unix_error (Unix.ENOENT, _, _) -> false

let expect_unix ?phase error f =
  match f () with
  | () -> failwith "expected native operation to fail"
  | exception Unix.Unix_error (actual, actual_phase, _) ->
    check (actual = error) ("native errno differs: " ^ Unix.error_message actual);
    check (actual_phase <> "") "native error lost phase";
    Option.iter (fun expected -> check (actual_phase = expected) ("native phase differs: " ^ actual_phase)) phase

let expect_invalid f =
  match f () with
  | () -> failwith "invalid path/state was accepted"
  | exception Invalid_argument _ -> ()

let expect_bad_state f =
  match f () with
  | () -> failwith "invalid publication state was accepted"
  | exception Invalid_argument _ -> ()
  | exception Unix.Unix_error ((Unix.EINVAL | Unix.EBADF), phase, _) ->
    check (phase <> "") "state error lost phase"

let capture_unix ?closed_baseline f =
  match f () with
  | () -> failwith "expected native exception for classification"
  | exception (Unix.Unix_error (_, _, _) as error) ->
    (match closed_baseline with
     | Some expected -> check (native_fd_count () = expected) "native exception returned before owned descriptors closed"
     | None -> ());
    error

let unix_parts = function
  | Unix.Unix_error (code, phase, arg) -> code, phase, arg
  | _ -> failwith "fixture did not capture a native exception"

let rec remove_tree path =
  match (Unix.lstat path).Unix.st_kind with
  | Unix.S_DIR ->
    Unix.chmod path 0o700;
    Array.iter (fun name -> remove_tree (Filename.concat path name)) (Sys.readdir path);
    Unix.rmdir path
  | _ -> Unix.unlink path
  | exception Unix.Unix_error (Unix.ENOENT, _, _) -> ()

type fixture = {
  top : string;
  work : string;
  incoming : string;
  outgoing : string;
  stage_path : string;
  temporary_path : string;
  stage_fd : Unix.file_descr option ref;
  handles : P.t list ref;
}

let borrowed c = match !(c.stage_fd) with Some fd -> fd | None -> failwith "fixture stage closed"

let fixture directory f =
  incr serial;
  let top = Filename.concat directory ("publication-case-" ^ string_of_int !serial) in
  let work = Filename.concat top "work" in
  let incoming = Filename.concat work "incoming" in
  let outgoing = Filename.concat work "outgoing" in
  List.iter (fun path -> Unix.mkdir path 0o700) [top; work; incoming; outgoing];
  let stage_path = Filename.concat incoming "stage" in
  write_file stage_path payload;
  let stage = Unix.openfile stage_path [Unix.O_RDWR; Unix.O_CLOEXEC] 0 in
  ignore (Unix.LargeFile.lseek stage 37L Unix.SEEK_SET);
  let c = {top; work; incoming; outgoing; stage_path;
    temporary_path = Filename.concat outgoing "temporary";
    stage_fd = ref (Some stage); handles = ref []} in
  Fun.protect ~finally:(fun () ->
    List.iter P.close_noerr !(c.handles);
    Option.iter close_noerr !(c.stage_fd);
    remove_tree top) (fun () -> f c)

let prepare ?working_dir ?(stage="incoming/stage") ?(temporary="outgoing/temporary") c =
  let h = P.prepare ~working_dir:(Option.value working_dir ~default:c.work) ~stage ~temporary in
  c.handles := h :: !(c.handles);
  h

let adopt ?parent_path ?stage_fd c h =
  let parent = open_parent (Option.value parent_path ~default:c.incoming) false in
  P.adopt h ~parent ~stage:(Option.value stage_fd ~default:(borrowed c));
  parent

let check_borrowed c =
  let fd = borrowed c in
  check_alive fd;
  check (Unix.LargeFile.lseek fd 0L Unix.SEEK_CUR = 37L) "publication changed borrowed stage offset"

let completed c h =
  P.publish h;
  check (not (exists c.stage_path)) "published stage name remained";
  check (read_file c.temporary_path = payload) "published temporary bytes differ";
  check_borrowed c

let test name f =
  let before = open_fds () in
  Fun.protect ~finally:(fun () ->
    attribute_fault 0 0; rename_fault 0; identity_fault 1 0; identity_fault 2 0)
    (fun () -> try f () with error -> Printf.eprintf "FAIL %s\n%!" name; raise error);
  Gc.full_major ();
  check (open_fds () = before) ("descriptor leak or unrelated closure in " ^ name);
  incr count;
  Printf.printf "PASS %s\n%!" name

let with_attribute_fault mode trigger f =
  attribute_fault mode trigger;
  Fun.protect ~finally:(fun () -> attribute_fault 0 0) f

let toggle_path_flag path =
  let parent = open_parent path false in
  Fun.protect ~finally:(fun () -> Unix.close parent) (fun () -> toggle_directory_flag parent)

let () =
  if not (P.available ()) then exit 77;
  let directory = Sys.argv.(1) in
  test "distinct-parent native rename is exclusive and descriptor-bound" (fun () ->
    fixture directory (fun c ->
      let before = open_fds () in
      let h = prepare c in
      let parent = adopt c h in
      let owned = new_fds before in
      check_cloexec owned;
      completed c h;
      P.abort_and_close h;
      check (not (exists c.temporary_path)) "abort left owned published temporary";
      check_closed owned;
      check (fd_state (fd_number parent) = -1) "adopted parent not consumed";
      check_borrowed c));
  test "same-parent stage and temporary names are supported" (fun () ->
    fixture directory (fun c ->
      let h = prepare ~temporary:"incoming/temporary" c in
      ignore (adopt c h);
      P.publish h;
      let temporary = Filename.concat c.incoming "temporary" in
      check (not (exists c.stage_path) && read_file temporary = payload) "same-parent publication failed";
      P.abort_and_close h;
      check (not (exists temporary)) "same-parent cleanup failed";
      check_borrowed c));
  test "ordinary followed directory ancestry selects captured physical parents" (fun () ->
    fixture directory (fun c ->
      Unix.symlink "incoming" (Filename.concat c.work "stage-alias");
      Unix.symlink "outgoing" (Filename.concat c.work "temporary-alias");
      let h = prepare ~stage:"stage-alias/stage" ~temporary:"temporary-alias/temporary" c in
      ignore (adopt ~parent_path:(Filename.concat c.work "stage-alias") c h);
      completed c h;
      P.disarm h;
      P.abort_and_close h;
      check (read_file c.temporary_path = payload) "disarm removed ordinary temporary"));
  test "Unicode names retain exact bytes" (fun () ->
    fixture directory (fun c ->
      let stage = "incoming/étape-星.dng" and temporary = "outgoing/画像-Δ.tmp" in
      let sp = Filename.concat c.work stage and tp = Filename.concat c.work temporary in
      Unix.rename c.stage_path sp;
      let h = prepare ~stage ~temporary c in
      ignore (adopt c h);
      P.publish h;
      check (not (exists sp) && read_file tp = payload) "Unicode path changed";
      P.abort_and_close h;
      check (not (exists tp)) "Unicode cleanup failed";
      check_borrowed c));
  test "working directory alias is resolved as an effective physical directory" (fun () ->
    fixture directory (fun c ->
      let alias = Filename.concat c.top "effective" in
      Unix.symlink "work" alias;
      let h = prepare ~working_dir:alias c in
      ignore (adopt c h);
      completed c h;
      P.abort_and_close h));
  test "directory sibling edits do not invalidate mutable directory metadata" (fun () ->
    fixture directory (fun c ->
      let h = prepare c in
      ignore (adopt c h);
      List.iter (fun parent ->
        let sibling = Filename.concat parent "new-sibling" in
        write_file sibling sentinel;
        let child = Filename.concat parent "new-directory" in
        Unix.mkdir child 0o700;
        Unix.rmdir child;
        check (read_file sibling = sentinel) "sibling bytes changed") [c.work; c.incoming; c.outgoing];
      completed c h;
      P.abort_and_close h));
  test "borrowed stage can close and its recycled descriptor remains untouched" (fun () ->
    fixture directory (fun c ->
      let h = prepare c in
      ignore (adopt c h);
      let original = borrowed c in
      Unix.close original;
      c.stage_fd := None;
      let path = Filename.concat c.top "recycled-borrowed-sentinel" in
      write_file path sentinel;
      let replacement = Unix.openfile path [Unix.O_RDWR; Unix.O_CLOEXEC] 0 in
      let recycled = original in
      Fun.protect ~finally:(fun () ->
        if replacement <> recycled then close_noerr recycled;
        close_noerr replacement) (fun () ->
        if replacement <> recycled then Unix.dup2 replacement recycled;
        ignore (Unix.LargeFile.lseek recycled 11L Unix.SEEK_SET);
        P.publish h;
        check (read_file c.temporary_path = payload) "retained witness selected recycled borrowed descriptor";
        P.abort_and_close h;
        check_alive recycled;
        check (read_file path = sentinel && Unix.LargeFile.lseek recycled 0L Unix.SEEK_CUR = 11L)
          "publication closed, wrote or moved recycled borrowed sentinel")));
  test "invalid absolute, empty, dot, dot-dot and NUL relative paths are rejected" (fun () ->
    fixture directory (fun c ->
      let before = open_fds () in
      List.iter (fun path ->
        expect_invalid (fun () -> ignore (prepare ~stage:path c));
        expect_invalid (fun () -> ignore (prepare ~temporary:path c)))
        [""; "/absolute"; "."; ".."; "incoming/."; "incoming/../stage";
         "incoming//stage"; "incoming/stage/"; "incoming/stage\000suffix"];
      expect_invalid (fun () -> ignore (prepare ~stage:"incoming/stage" ~temporary:"incoming/stage" c));
      List.iter (fun working_dir -> expect_invalid (fun () -> ignore (prepare ~working_dir c)))
        [""; "relative"; c.work ^ "\000suffix"];
      check (open_fds () = before && read_file c.stage_path = payload) "syntax failures opened handles or mutated stage"));
  test "prepare native missing-parent errno is preserved without leaked handles" (fun () ->
    fixture directory (fun c ->
      let before = open_fds () in
      for _ = 1 to 25 do
        expect_unix Unix.ENOENT (fun () -> ignore (prepare ~temporary:"missing/temporary" c))
      done;
      check (open_fds () = before && read_file c.stage_path = payload) "failed prepare leaked or removed unrelated stage"));
  test "native collision never overwrites an existing temporary file" (fun () ->
    fixture directory (fun c ->
      let h = prepare c in
      ignore (adopt c h);
      write_file c.temporary_path sentinel;
      expect_unix Unix.EEXIST (fun () -> P.publish h);
      check (read_file c.stage_path = payload && read_file c.temporary_path = sentinel) "collision changed stage or temporary";
      P.abort_and_close h;
      check (not (exists c.stage_path) && read_file c.temporary_path = sentinel) "collision cleanup removed replacement temporary";
      check_borrowed c));
  test "native collision preserves a temporary symlink and its target" (fun () ->
    fixture directory (fun c ->
      let target = Filename.concat c.top "symlink-target" in
      write_file target sentinel;
      let h = prepare c in
      ignore (adopt c h);
      Unix.symlink target c.temporary_path;
      expect_unix Unix.EEXIST (fun () -> P.publish h);
      P.abort_and_close h;
      check (Unix.readlink c.temporary_path = target && read_file target = sentinel) "collision followed or removed temporary symlink"));
  test "native collision preserves a temporary directory and independent contents" (fun () ->
    fixture directory (fun c ->
      let h = prepare c in
      ignore (adopt c h);
      Unix.mkdir c.temporary_path 0o700;
      let marker = Filename.concat c.temporary_path "marker" in
      write_file marker sentinel;
      expect_unix Unix.EEXIST (fun () -> P.publish h);
      P.abort_and_close h;
      check (read_file marker = sentinel) "collision removed temporary directory marker"));
  test "stage file substitution returns EBUSY and cleanup preserves replacement" (fun () ->
    fixture directory (fun c ->
      let before = open_fds () in
      let h = prepare c in
      ignore (adopt c h);
      let owned = new_fds before in
      let preserved = c.stage_path ^ "-original" in
      Unix.rename c.stage_path preserved;
      write_file c.stage_path sentinel;
      expect_unix Unix.EBUSY (fun () -> P.publish h);
      expect_unix Unix.EBUSY (fun () -> P.abort_and_close h);
      check_closed owned;
      check (read_file c.stage_path = sentinel && read_file preserved = payload && not (exists c.temporary_path))
        "stage substitution caused alien cleanup or publication";
      check_borrowed c));
  test "stage symlink substitution is never followed or removed" (fun () ->
    fixture directory (fun c ->
      let h = prepare c in
      ignore (adopt c h);
      let original = c.stage_path ^ "-original" in
      let target = Filename.concat c.top "stage-symlink-target" in
      Unix.rename c.stage_path original;
      write_file target sentinel;
      Unix.symlink target c.stage_path;
      expect_unix Unix.EBUSY (fun () -> P.publish h);
      expect_unix Unix.EBUSY (fun () -> P.abort_and_close h);
      check (Unix.readlink c.stage_path = target && read_file target = sentinel && read_file original = payload)
        "stage symlink substitution touched target or original"));
  test "missing stage retains native ENOENT and closes owned descriptors" (fun () ->
    fixture directory (fun c ->
      let before = open_fds () in
      let h = prepare c in
      ignore (adopt c h);
      let owned = new_fds before in
      Unix.unlink c.stage_path;
      expect_unix Unix.ENOENT (fun () -> P.publish h);
      P.close_noerr h;
      check_closed owned;
      check (not (exists c.temporary_path)) "missing stage generated temporary";
      check_borrowed c));
  test "rebound stage parent refuses publication but cleans held original name" (fun () ->
    fixture directory (fun c ->
      let h = prepare c in
      ignore (adopt c h);
      let old_parent = c.incoming ^ "-original" in
      Unix.rename c.incoming old_parent;
      Unix.mkdir c.incoming 0o700;
      write_file c.stage_path sentinel;
      expect_unix Unix.EBUSY (fun () -> P.publish h);
      P.abort_and_close h;
      check (read_file c.stage_path = sentinel && not (exists (Filename.concat old_parent "stage")))
        "stage-parent rebind cleanup selected replacement parent";
      check_borrowed c));
  test "rebound temporary parent refuses publication without touching replacement" (fun () ->
    fixture directory (fun c ->
      let h = prepare c in
      ignore (adopt c h);
      Unix.rename c.outgoing (c.outgoing ^ "-original");
      Unix.mkdir c.outgoing 0o700;
      write_file c.temporary_path sentinel;
      expect_unix Unix.EBUSY (fun () -> P.publish h);
      P.abort_and_close h;
      check (not (exists c.stage_path) && read_file c.temporary_path = sentinel)
        "temporary-parent rebind published or cleaned replacement"));
  test "rebound physical working directory refuses publication and preserves replacement tree" (fun () ->
    fixture directory (fun c ->
      let h = prepare c in
      ignore (adopt c h);
      let original = c.work ^ "-original" in
      Unix.rename c.work original;
      List.iter (fun path -> Unix.mkdir path 0o700) [c.work; c.incoming; c.outgoing];
      write_file c.stage_path sentinel;
      write_file c.temporary_path sentinel;
      expect_unix Unix.EBUSY (fun () -> P.publish h);
      P.abort_and_close h;
      check (read_file c.stage_path = sentinel && read_file c.temporary_path = sentinel &&
        not (exists (Filename.concat original "incoming/stage"))) "working-directory rebind touched replacement tree";
      check_borrowed c));
  test "followed parent alias rebind is detected before publication" (fun () ->
    fixture directory (fun c ->
      let alias = Filename.concat c.work "stage-alias" in
      let other = Filename.concat c.work "other-parent" in
      Unix.symlink "incoming" alias;
      Unix.mkdir other 0o700;
      let replacement = Filename.concat other "stage" in
      write_file replacement sentinel;
      let h = prepare ~stage:"stage-alias/stage" c in
      ignore (adopt c h);
      Unix.unlink alias;
      Unix.symlink "other-parent" alias;
      expect_unix Unix.EBUSY (fun () -> P.publish h);
      P.abort_and_close h;
      check (read_file replacement = sentinel && not (exists c.stage_path)) "alias rebind selected replacement stage"));
  test "wrong adopted parent consumes supplied FD and preserves alien stage sentinel" (fun () ->
    fixture directory (fun c ->
      let before = open_fds () in
      let h = prepare c in
      let other = Filename.concat c.work "other-parent" in
      Unix.mkdir other 0o700;
      let alien = Filename.concat other "stage" in
      write_file alien sentinel;
      let parent = open_parent other false in
      let owned = new_fds before in
      expect_unix Unix.EBUSY (fun () -> P.adopt h ~parent ~stage:(borrowed c));
      check_closed owned;
      check (read_file alien = sentinel) "wrong-parent failure removed alien sentinel";
      check_borrowed c;
      P.close_noerr h));
  test "wrong borrowed stage identity refuses adoption and preserves both files" (fun () ->
    fixture directory (fun c ->
      let path = Filename.concat c.top "wrong-stage-sentinel" in
      write_file path sentinel;
      let fd = Unix.openfile path [Unix.O_RDWR; Unix.O_CLOEXEC] 0 in
      Fun.protect ~finally:(fun () -> Unix.close fd) (fun () ->
        let before = open_fds () in
        let h = prepare c in
        let parent = open_parent c.incoming false in
        let owned = new_fds before in
        expect_unix Unix.EBUSY (fun () -> P.adopt h ~parent ~stage:fd);
        check_closed owned;
        check (fd_state (fd_number parent) = -1) "failed adoption kept supplied parent";
        check_alive fd;
        check (read_file path = sentinel && read_file c.stage_path = payload) "wrong-stage failure removed a file";
        P.close_noerr h;
        check_borrowed c)));
  test "closed borrowed stage preserves native EBADF and consumes parent" (fun () ->
    fixture directory (fun c ->
      let dead = Unix.openfile c.stage_path [Unix.O_RDONLY; Unix.O_CLOEXEC] 0 in
      let before = open_fds () in
      let h = prepare c in
      let parent = open_parent c.incoming false in
      let owned = new_fds before in
      Unix.close dead;
      expect_unix Unix.EBADF (fun () -> P.adopt h ~parent ~stage:dead);
      check_closed owned;
      check (fd_state (fd_number parent) = -1) "failed EBADF adoption kept parent";
      check (read_file c.stage_path = payload) "EBADF adoption removed unowned stage";
      check_borrowed c));
  test "failed adoption after parent rebind cleans held original stage only" (fun () ->
    fixture directory (fun c ->
      let before = open_fds () in
      let h = prepare c in
      let parent = open_parent c.incoming false in
      let owned = new_fds before in
      let original = c.incoming ^ "-original" in
      Unix.rename c.incoming original;
      Unix.mkdir c.incoming 0o700;
      write_file c.stage_path sentinel;
      expect_unix Unix.EBUSY (fun () -> P.adopt h ~parent ~stage:(borrowed c));
      check_closed owned;
      check (fd_state (fd_number parent) = -1) "failed rebound adoption kept parent";
      check (read_file c.stage_path = sentinel && not (exists (Filename.concat original "stage")))
        "failed rebound adoption selected wrong cleanup name";
      check_borrowed c));
  test "unadopted handle cleanup does not own any stage name" (fun () ->
    fixture directory (fun c ->
      let before = open_fds () in
      let h = prepare c in
      let owned = new_fds before in
      P.abort_and_close h;
      check_closed owned;
      check (read_file c.stage_path = payload && not (exists c.temporary_path)) "unadopted cleanup removed stage";
      check_borrowed c));
  test "disarm before publication is rejected without losing stage ownership" (fun () ->
    fixture directory (fun c ->
      let h = prepare c in
      ignore (adopt c h);
      expect_bad_state (fun () -> P.disarm h);
      completed c h;
      P.abort_and_close h));
  test "second publish is rejected and explicit abort still removes owned temporary" (fun () ->
    fixture directory (fun c ->
      let h = prepare c in
      ignore (adopt c h);
      completed c h;
      expect_bad_state (fun () -> P.publish h);
      check (read_file c.temporary_path = payload) "second publish changed temporary";
      P.abort_and_close h;
      check (not (exists c.temporary_path)) "rejected second publish lost cleanup ownership"));
  test "second adoption consumes new parent on state rejection" (fun () ->
    fixture directory (fun c ->
      let h = prepare c in
      ignore (adopt c h);
      let parent = open_parent c.incoming false in
      expect_bad_state (fun () -> P.adopt h ~parent ~stage:(borrowed c));
      check (fd_state (fd_number parent) = -1) "rejected second adoption leaked new parent";
      P.close_noerr h;
      check_borrowed c));
  test "unpublished abort removes only identity-bound owned stage" (fun () ->
    fixture directory (fun c ->
      let h = prepare c in
      ignore (adopt c h);
      let marker = Filename.concat c.incoming "marker" in
      write_file marker sentinel;
      P.abort_and_close h;
      check (not (exists c.stage_path) && read_file marker = sentinel && not (exists c.temporary_path))
        "unpublished abort cleaned unrelated name";
      check_borrowed c));
  test "disarm closes proof descriptors and leaves ordinary temporary ownership" (fun () ->
    fixture directory (fun c ->
      let before = open_fds () in
      let h = prepare c in
      ignore (adopt c h);
      let owned = new_fds before in
      completed c h;
      P.disarm h;
      check_closed owned;
      P.abort_and_close h;
      P.close_noerr h;
      check (read_file c.temporary_path = payload) "disarmed handle removed ordinary temporary";
      check_borrowed c));
  test "published temporary file substitution is never removed by abort" (fun () ->
    fixture directory (fun c ->
      let before = open_fds () in
      let h = prepare c in
      ignore (adopt c h);
      let owned = new_fds before in
      completed c h;
      let original = c.temporary_path ^ "-original" in
      Unix.rename c.temporary_path original;
      write_file c.temporary_path sentinel;
      expect_unix Unix.EBUSY (fun () -> P.abort_and_close h);
      check_closed owned;
      check (read_file c.temporary_path = sentinel && read_file original = payload)
        "published replacement was removed";
      P.close_noerr h;
      check_borrowed c));
  test "published temporary symlink substitution is never followed or removed" (fun () ->
    fixture directory (fun c ->
      let h = prepare c in
      ignore (adopt c h);
      completed c h;
      let original = c.temporary_path ^ "-original" in
      let target = Filename.concat c.top "published-symlink-target" in
      Unix.rename c.temporary_path original;
      write_file target sentinel;
      Unix.symlink target c.temporary_path;
      expect_unix Unix.EBUSY (fun () -> P.abort_and_close h);
      check (Unix.readlink c.temporary_path = target && read_file target = sentinel && read_file original = payload)
        "published symlink substitution was followed or removed"));
  test "published temporary parent rebind cleanup uses held original directory" (fun () ->
    fixture directory (fun c ->
      let h = prepare c in
      ignore (adopt c h);
      completed c h;
      let original = c.outgoing ^ "-original" in
      Unix.rename c.outgoing original;
      Unix.mkdir c.outgoing 0o700;
      write_file c.temporary_path sentinel;
      P.abort_and_close h;
      check (read_file c.temporary_path = sentinel && not (exists (Filename.concat original "temporary")))
        "published parent rebind cleanup selected replacement"));
  test "explicit cleanup closes all handles even on native permission error" (fun () ->
    fixture directory (fun c ->
      check (Unix.geteuid () <> 0) "permission qualification requires an unprivileged user";
      let before = open_fds () in
      let h = prepare c in
      ignore (adopt c h);
      let owned = new_fds before in
      Unix.chmod c.incoming 0o500;
      Fun.protect ~finally:(fun () -> Unix.chmod c.incoming 0o700) (fun () ->
        expect_unix Unix.EACCES (fun () -> P.abort_and_close h);
        check_closed owned);
      P.abort_and_close h;
      check (read_file c.stage_path = payload) "repeat close retried unowned namespace cleanup";
      check_borrowed c));
  test "publish native permission errno does not degrade into pathname fallback" (fun () ->
    fixture directory (fun c ->
      check (Unix.geteuid () <> 0) "permission qualification requires an unprivileged user";
      let h = prepare c in
      ignore (adopt c h);
      Unix.chmod c.outgoing 0o500;
      Fun.protect ~finally:(fun () -> Unix.chmod c.outgoing 0o700) (fun () ->
        expect_unix Unix.EACCES (fun () -> P.publish h));
      check (read_file c.stage_path = payload && not (exists c.temporary_path)) "permission failure moved stage";
      P.abort_and_close h));
  test "search-only native directory probes permit write-and-search parents without read" (fun () ->
    fixture directory (fun c ->
      check (Unix.geteuid () <> 0) "search-only qualification requires an unprivileged user";
      Unix.chmod c.work 0o100;
      Unix.chmod c.incoming 0o300;
      Unix.chmod c.outgoing 0o300;
      Fun.protect ~finally:(fun () ->
        Unix.chmod c.work 0o700;
        Unix.chmod c.incoming 0o700;
        Unix.chmod c.outgoing 0o700) (fun () ->
        let h = prepare c in
        let parent = open_parent c.incoming true in
        P.adopt h ~parent ~stage:(borrowed c);
        completed c h;
        P.abort_and_close h;
        check (not (exists c.temporary_path)) "search-only cleanup failed")));
  test "repeated close and collection never close recycled owned descriptor numbers" (fun () ->
    fixture directory (fun c ->
      let h = prepare c in
      let parent = adopt c h in
      P.abort_and_close h;
      check (fd_state (fd_number parent) = -1) "parent not closed before reuse";
      let path = Filename.concat c.top "recycled-owned-sentinel" in
      write_file path sentinel;
      let replacement = Unix.openfile path [Unix.O_RDWR; Unix.O_CLOEXEC] 0 in
      Fun.protect ~finally:(fun () ->
        if replacement <> parent then close_noerr parent;
        close_noerr replacement) (fun () ->
        if replacement <> parent then Unix.dup2 replacement parent;
        ignore (Unix.LargeFile.lseek parent 9L Unix.SEEK_SET);
        P.abort_and_close h;
        P.close_noerr h;
        c.handles := [];
        Gc.full_major ();
        check_alive parent;
        check (read_file path = sentinel && Unix.LargeFile.lseek parent 0L Unix.SEEK_CUR = 9L)
          "repeated close affected recycled owned descriptor sentinel")));
  test "abandoned adopted handle finalizer closes only and preserves stage name" (fun () ->
    fixture directory (fun c ->
      let before = open_fds () in
      let abandon () =
        let h = P.prepare ~working_dir:c.work ~stage:"incoming/stage" ~temporary:"outgoing/temporary" in
        let parent = open_parent c.incoming false in
        P.adopt h ~parent ~stage:(borrowed c);
        check_cloexec (new_fds before)
      in
      abandon ();
      Gc.full_major ();
      Gc.full_major ();
      check (open_fds () = before && read_file c.stage_path = payload) "finalizer leaked descriptors or removed stage";
      check_borrowed c));
  test "abandoned published handle finalizer preserves temporary name" (fun () ->
    fixture directory (fun c ->
      let before = open_fds () in
      let abandon () =
        let h = P.prepare ~working_dir:c.work ~stage:"incoming/stage" ~temporary:"outgoing/temporary" in
        let parent = open_parent c.incoming false in
        P.adopt h ~parent ~stage:(borrowed c);
        P.publish h
      in
      abandon ();
      Gc.full_major ();
      Gc.full_major ();
      check (open_fds () = before && read_file c.temporary_path = payload) "finalizer leaked descriptors or removed temporary";
      check_borrowed c));
  test "hardlink before adoption fails private-stage policy and preserves foreign link" (fun () ->
    fixture directory (fun c ->
      let before = open_fds () in
      let h = prepare c in
      let foreign = Filename.concat c.top "foreign-stage-link" in
      Unix.link c.stage_path foreign;
      let parent = open_parent c.incoming false in
      let owned = new_fds before in
      expect_unix Unix.EBUSY (fun () -> P.adopt h ~parent ~stage:(borrowed c));
      check_closed owned;
      check (not (exists c.stage_path) && read_file foreign = payload && not (exists c.temporary_path))
        "failed hardlink adoption removed foreign alias or retained owned stage";
      check_borrowed c));
  test "hardlink before publication fails private-stage policy but permits owned-leaf cleanup" (fun () ->
    fixture directory (fun c ->
      let before = open_fds () in
      let h = prepare c in
      ignore (adopt c h);
      let owned = new_fds before in
      let foreign = Filename.concat c.top "foreign-publication-link" in
      Unix.link c.stage_path foreign;
      expect_unix Unix.EBUSY (fun () -> P.publish h);
      P.abort_and_close h;
      check_closed owned;
      check (not (exists c.stage_path) && read_file foreign = payload && not (exists c.temporary_path))
        "hardlink publication cleanup removed foreign alias or created temporary";
      check_borrowed c));
  let fault_modes = [1, Unix.EUNKNOWNERR (native_errno 1); 2, Unix.EUNKNOWNERR (native_errno 1);
    3, Unix.EUNKNOWNERR (native_errno 2); 4, Unix.EUNKNOWNERR (native_errno 2);
    5, Unix.EUNKNOWNERR (native_errno 2); 8, Unix.EUNKNOWNERR (native_errno 2);
    6, Unix.EIO; 7, Unix.EACCES] in
  test "every prepare directory rejects missing UUID malformed replies and native errors" (fun () ->
    List.iter (fun (mode, error) -> List.iter (fun trigger -> fixture directory (fun c ->
      let before = open_fds () in
      with_attribute_fault mode trigger (fun () -> expect_unix error (fun () -> ignore (prepare c)));
      check (open_fds () = before && read_file c.stage_path = payload) "faulted prepare leaked descriptors or claimed stage";
      check_borrowed c)) [1; 2; 3]) fault_modes);
  test "every adoption directory rejects missing UUID malformed replies and native errors" (fun () ->
    List.iter (fun (mode, error) -> List.iter (fun trigger -> fixture directory (fun c ->
      let before = open_fds () in
      let h = prepare c in
      let parent = open_parent c.incoming false in
      let owned = new_fds before in
      with_attribute_fault mode trigger (fun () ->
        expect_unix error (fun () -> P.adopt h ~parent ~stage:(borrowed c)));
      check_closed owned;
      check (not (exists c.stage_path) && not (exists c.temporary_path)) "failed adoption did not clean owned stage";
      check_borrowed c)) [1; 2; 3; 4; 5; 6]) fault_modes);
  test "every publication directory rejects missing UUID malformed replies and native errors" (fun () ->
    List.iter (fun (mode, error) -> List.iter (fun trigger -> fixture directory (fun c ->
      let before = open_fds () in
      let h = prepare c in
      ignore (adopt c h);
      let owned = new_fds before in
      with_attribute_fault mode trigger (fun () -> expect_unix error (fun () -> P.publish h));
      check (read_file c.stage_path = payload && not (exists c.temporary_path)) "faulted publication changed names";
      P.abort_and_close h;
      check_closed owned;
      check (not (exists c.stage_path)) "faulted publication lost stage cleanup ownership";
      check_borrowed c)) [1; 2; 3; 4; 5; 6]) fault_modes);
  test "changed full-width volume UUID is never promoted to a current binding" (fun () ->
    List.iter (fun mode -> List.iter (fun trigger -> fixture directory (fun c ->
      let h = prepare c in
      ignore (adopt c h);
      with_attribute_fault mode trigger (fun () -> expect_unix Unix.EBUSY (fun () -> P.publish h));
      check (read_file c.stage_path = payload && not (exists c.temporary_path)) "UUID drift selected publication";
      P.abort_and_close h)) [1; 2; 3; 4; 5; 6]) [9; 11]);
  test "real root and parent flag changes refuse publication" (fun () ->
    List.iter (fun select -> fixture directory (fun c ->
      let h = prepare c in
      ignore (adopt c h);
      toggle_path_flag (select c);
      expect_unix Unix.EBUSY (fun () -> P.publish h);
      check (read_file c.stage_path = payload && not (exists c.temporary_path)) "directory flag drift selected publication";
      P.abort_and_close h;
      check_borrowed c)) [(fun c -> c.work); (fun c -> c.incoming); (fun c -> c.outgoing)]);
  test "real flag change inside each directory probe fails its native recheck" (fun () ->
    List.iter (fun trigger -> fixture directory (fun c ->
      let before = open_fds () in
      with_attribute_fault 10 trigger (fun () ->
        expect_unix Unix.EBUSY (fun () -> ignore (prepare c)));
      check (open_fds () = before && read_file c.stage_path = payload) "mid-probe flag change leaked or claimed stage")) [1; 2; 3]);
  test "native rename EIO preserves phase names bytes and cleanup ownership" (fun () ->
    fixture directory (fun c ->
      let h = prepare c in
      ignore (adopt c h);
      rename_fault 1;
      Fun.protect ~finally:(fun () -> rename_fault 0) (fun () ->
        expect_unix ~phase:"stage_publication.publish.rename" Unix.EIO (fun () -> P.publish h));
      check (read_file c.stage_path = payload && not (exists c.temporary_path)) "native EIO lost stage or selected fallback";
      P.abort_and_close h));
  test "native exclusive rename protects a destination introduced after lookup" (fun () ->
    fixture directory (fun c ->
      let h = prepare c in
      ignore (adopt c h);
      rename_fault 2;
      Fun.protect ~finally:(fun () -> rename_fault 0) (fun () ->
        expect_unix ~phase:"stage_publication.publish.rename" Unix.EEXIST (fun () -> P.publish h));
      check (read_file c.stage_path = payload && read_file c.temporary_path = "exclusive native race sentinel")
        "exclusive rename overwrote race sentinel";
      P.abort_and_close h;
      check (read_file c.temporary_path = "exclusive native race sentinel") "race collision cleanup removed destination"));
  test "high inode device and flags bits remain significant for held object bindings" (fun () ->
    List.iter (fun mode -> fixture directory (fun c ->
      let h = prepare c in
      ignore (adopt c h);
      identity_fault 1 mode;
      Fun.protect ~finally:(fun () -> identity_fault 1 0) (fun () ->
        expect_unix Unix.EBUSY (fun () -> P.publish h));
      check (read_file c.stage_path = payload && not (exists c.temporary_path)) "high object-identity bits were truncated";
      P.abort_and_close h;
      check_borrowed c)) [1; 2; 3; 4; 5]);
  test "both filesystem ID words and unsigned mount flag bits remain significant" (fun () ->
    List.iter (fun mode -> fixture directory (fun c ->
      let h = prepare c in
      ignore (adopt c h);
      identity_fault 2 mode;
      Fun.protect ~finally:(fun () -> identity_fault 2 0) (fun () ->
        expect_unix Unix.EBUSY (fun () -> P.publish h));
      check (read_file c.stage_path = payload && not (exists c.temporary_path)) "filesystem identity or mount flags were truncated";
      P.abort_and_close h)) [1; 2; 3]);
  test "legitimate stage writes before publication do not become frozen content policy" (fun () ->
    fixture directory (fun c ->
      let h = prepare c in
      ignore (adopt c h);
      let fd = borrowed c in
      ignore (Unix.LargeFile.lseek fd 0L Unix.SEEK_END);
      ignore (Unix.write_substring fd sentinel 0 (String.length sentinel));
      ignore (Unix.LargeFile.lseek fd 37L Unix.SEEK_SET);
      P.publish h;
      check (read_file c.temporary_path = payload ^ sentinel) "current stage facts became adoption-time content snapshot";
      P.abort_and_close h;
      check_borrowed c));
  test "pending Sys.Break after native rename retains temporary cleanup ownership" (fun () ->
    fixture directory (fun c ->
      let before = open_fds () in
      let h = prepare c in
      ignore (adopt c h);
      let owned = new_fds before in
      let delivered = ref 0 and saw_break = ref false in
      let previous = Sys.signal Sys.sigusr1
        (Sys.Signal_handle (fun _ -> incr delivered; raise Sys.Break)) in
      Fun.protect ~finally:(fun () -> rename_fault 0; Sys.set_signal Sys.sigusr1 previous) (fun () ->
        rename_fault 3;
        (try with_async_exns (fun () -> P.publish h) with Sys.Break -> saw_break := true);
        rename_fault 0;
        (try with_async_exns dispatch_pending with Sys.Break -> saw_break := true);
        check (!saw_break && !delivered = 1) "post-rename pending signal was lost or duplicated";
        check (not (exists c.stage_path) && read_file c.temporary_path = payload) "native rename did not complete before signal";
        P.abort_and_close h;
        check_closed owned;
        check (not (exists c.temporary_path)) "pending exception lost published temporary ownership";
        check_borrowed c)));
  let identity_phases = [
    "stage_publication.prepare.working_identity";
    "stage_publication.prepare.stage_identity";
    "stage_publication.prepare.temporary_identity"] in
  let unavailable_modes = [1; 2; 12; 13; 14] in
  test "only missing UUID and unsupported preparation identity queries permit fallback" (fun () ->
    List.iter (fun mode -> List.iteri (fun index expected_phase -> fixture directory (fun c ->
      let before = native_fd_count () in
      check (before >= 0) "native FD enumeration unavailable";
      let error = with_attribute_fault mode (index + 1) (fun () ->
        capture_unix ~closed_baseline:before (fun () -> ignore (prepare c))) in
      let _, actual_phase, _ = unix_parts error in
      check (actual_phase = expected_phase) "fault was not in the requested preparation identity phase";
      check (P.preparation_unavailable error) "eligible preparation identity failure was not classified";
      check (read_file c.stage_path = payload && not (exists c.temporary_path)) "classified preparation failure changed stage names";
      check_borrowed c)) identity_phases) unavailable_modes);
  test "eligible native errno never qualifies open path later or lookalike phases" (fun () ->
    let forbidden_phases = [
      ""; "stage_publication.prepare"; "stage_publication.prepare.working_directory";
      "stage_publication.prepare.stage_parent"; "stage_publication.prepare.temporary_parent";
      "stage_publication.prepare.paths"; "stage_publication.prepare.mutex";
      "stage_publication.prepare.aliased_names"; "stage_publication.adopt.actual_parent";
      "stage_publication.adopt.stage_name"; "stage_publication.adopt.witness";
      "stage_publication.binding.working_directory"; "stage_publication.binding.stage_parent";
      "stage_publication.binding.temporary_parent"; "stage_publication.publish.held_stage_parent";
      "stage_publication.publish.stage_name"; "stage_publication.publish.temporary_lookup";
      "stage_publication.publish.rename"; "stage_publication.cleanup.owned_name";
      "stage_publication.close.working_directory"; "stage_publication.platform"] @
      List.concat_map (fun phase -> [phase ^ ".suffix"; phase ^ "\000suffix";
        "prefix." ^ phase; phase ^ " "; String.uppercase_ascii phase]) identity_phases in
    List.iter (fun mode -> fixture directory (fun c ->
      let before = native_fd_count () in
      let error = with_attribute_fault mode 1 (fun () ->
        capture_unix ~closed_baseline:before (fun () -> ignore (prepare c))) in
      let code, _, arg = unix_parts error in
      List.iter (fun phase ->
        check (not (P.preparation_unavailable (Unix.Unix_error (code, phase, arg))))
          ("ineligible native phase permitted fallback: " ^ phase)) forbidden_phases;
      List.iter (fun phase ->
        check (P.preparation_unavailable (Unix.Unix_error (code, phase, arg)))
          "eligible native errno failed an exact allowed phase") identity_phases;
      check_borrowed c)) unavailable_modes);
  test "operational malformed and unstable preparation errors never permit fallback" (fun () ->
    List.iter (fun mode -> List.iter (fun trigger -> fixture directory (fun c ->
      let before = native_fd_count () in
      let error = with_attribute_fault mode trigger (fun () ->
        capture_unix ~closed_baseline:before (fun () -> ignore (prepare c))) in
      check (not (P.preparation_unavailable error)) "operational or malformed identity error permitted fallback";
      check (read_file c.stage_path = payload && not (exists c.temporary_path)) "unclassified prepare error changed names";
      check_borrowed c)) [1; 2; 3]) [3; 4; 5; 8; 6; 7; 10]);
  test "actual missing open paths and syntax failures never permit fallback" (fun () ->
    fixture directory (fun c ->
      let before = native_fd_count () in
      List.iter (fun f ->
        let error = capture_unix ~closed_baseline:before f in
        check (not (P.preparation_unavailable error)) "native path error permitted fallback")
        [(fun () -> ignore (prepare ~working_dir:(Filename.concat c.top "absent") c));
         (fun () -> ignore (prepare ~stage:"absent/stage" c));
         (fun () -> ignore (prepare ~temporary:"absent/temporary" c))];
      let syntax_error =
        try ignore (prepare ~stage:"incoming/../stage" c); failwith "syntax was accepted"
        with Invalid_argument _ as error -> error in
      check (not (P.preparation_unavailable syntax_error)) "syntax error permitted fallback";
      check_borrowed c));
  test "actual unsupported and missing UUID after preparation never permit fallback" (fun () ->
    List.iter (fun mode -> List.iter (fun trigger ->
      fixture directory (fun c ->
        let before = native_fd_count () in
        let h = prepare c in
        let parent = open_parent c.incoming false in
        let error = with_attribute_fault mode trigger (fun () ->
          capture_unix ~closed_baseline:before (fun () -> P.adopt h ~parent ~stage:(borrowed c))) in
        check (not (P.preparation_unavailable error)) "actual adoption identity failure permitted fallback";
        check (not (exists c.stage_path) && not (exists c.temporary_path)) "failed adoption lost private-stage cleanup";
        check_borrowed c);
      fixture directory (fun c ->
        let h = prepare c in
        ignore (adopt c h);
        let error = with_attribute_fault mode trigger (fun () ->
          capture_unix (fun () -> P.publish h)) in
        check (not (P.preparation_unavailable error)) "actual publication identity failure permitted fallback";
        check (read_file c.stage_path = payload && not (exists c.temporary_path)) "publication identity error changed names";
        P.abort_and_close h;
        check_borrowed c)) [1; 2; 3; 4; 5; 6]) unavailable_modes);
  test "non-native exceptions and other Unix errnos never permit fallback" (fun () ->
    List.iter (fun error -> check (not (P.preparation_unavailable error)) "non-native exception permitted fallback")
      [Failure "unavailable"; Invalid_argument "stage path"; Out_of_memory; Exit; Sys.Break];
    List.iter (fun code -> List.iter (fun phase ->
      check (not (P.preparation_unavailable (Unix.Unix_error (code, phase, "fixture"))))
        "unqualified Unix errno permitted fallback") identity_phases)
      [Unix.EIO; Unix.EACCES; Unix.EBUSY; Unix.EEXIST; Unix.EBADF; Unix.EINVAL;
       Unix.ENOENT; Unix.ENOMEM; Unix.EUNKNOWNERR 0; Unix.EUNKNOWNERR (-1)]);
  Printf.printf "StagePublication: %d private native tests passed; final commit and durability remain separate\n%!" !count
