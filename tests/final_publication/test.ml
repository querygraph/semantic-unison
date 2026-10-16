module P = FinalPublication
[@@@alert "-unsafe_multidomain"]
let with_async_exns f = f ()
external fd_state : int -> int = "final_publication_fixture_fd_state"
external fd_number : Unix.file_descr -> int = "final_publication_fixture_fd_number"
external attribute_fault : int -> int -> unit = "final_publication_fixture_attribute_fault"
external rename_fault : int -> unit = "final_publication_fixture_rename_fault"
external auxiliary_fault : int -> unit = "final_publication_fixture_auxiliary_fault"
external unlink_fault : int -> unit = "final_publication_fixture_unlink_fault"
external immutable : string -> bool -> unit = "final_publication_fixture_immutable"
external identity_fault : int -> int -> unit = "final_publication_fixture_identity_fault"
external dispatch_pending : unit -> unit = "final_publication_fixture_dispatch_pending"
external native_fd_count : unit -> int = "final_publication_fixture_fd_count" [@@noalloc]
external attribute_write : string -> string -> bool -> unit
  = "final_publication_fixture_attribute_write"
external attribute_read : string -> bool -> string
  = "final_publication_fixture_attribute_read"

let check b m = if not b then failwith m
let count = ref 0
let serial = ref 0
let payload = String.init 513 (fun i -> Char.chr ((i * 71 + 23) land 255))
let sentinel = "independent replacement sentinel\000\255"
let write_file path bytes =
  let fd = Unix.openfile path [Unix.O_WRONLY; Unix.O_CREAT; Unix.O_EXCL; Unix.O_CLOEXEC] 0o600 in
  Fun.protect ~finally:(fun () -> Unix.close fd) (fun () ->
    let rec write offset = if offset < String.length bytes then begin
      let n = Unix.write_substring fd bytes offset (String.length bytes - offset) in
      check (n > 0) "fixture write stalled"; write (offset + n)
    end in write 0)
let read_file path =
  let ch = open_in_bin path in
  Fun.protect ~finally:(fun () -> close_in ch)
    (fun () -> really_input_string ch (in_channel_length ch))
let exists path =
  try ignore (Unix.lstat path); true with Unix.Unix_error (Unix.ENOENT, _, _) -> false
let expect_unix error f =
  match f () with
  | () -> failwith "expected native failure"
  | exception Unix.Unix_error (actual, phase, _) ->
      check (actual = error) ("unexpected native errno " ^ Unix.error_message actual);
      check (phase <> "") "native phase missing"
let expect_native f =
  match f () with
  | () -> failwith "expected native failure"
  | exception Unix.Unix_error (_, phase, _) -> check (phase <> "") "native phase missing"
let expect_invalid f =
  match f () with () -> failwith "expected invalid argument" | exception Invalid_argument _ -> ()
let rec remove_tree path =
  match (Unix.lstat path).Unix.st_kind with
  | Unix.S_DIR -> Unix.chmod path 0o700;
      Array.iter (fun name -> remove_tree (Filename.concat path name)) (Sys.readdir path);
      Unix.rmdir path
  | _ -> Unix.unlink path
  | exception Unix.Unix_error (Unix.ENOENT, _, _) -> ()
let open_fds () =
  Array.to_list (Sys.readdir "/dev/fd") |> List.filter_map (fun name ->
    match int_of_string_opt name with Some n when fd_state n >= 0 -> Some n | _ -> None)
  |> List.sort_uniq compare
let new_fds before = List.filter (fun n -> not (List.mem n before)) (open_fds ())
let check_closed fds = List.iter (fun n -> check (fd_state n = -1) "proof descriptor leaked") fds

type fixture = {
  top:string; root:string; work:string; incoming:string; outgoing:string;
  candidate:string; target:string; handles:P.t list ref;
}
let fixture directory f =
  incr serial;
  let top = Filename.concat directory ("final-case-" ^ string_of_int !serial) in
  let root = Filename.concat top "root" in
  let work = Filename.concat top "effective" in
  let incoming = Filename.concat work "incoming" in
  let outgoing = Filename.concat work "outgoing" in
  List.iter (fun p -> Unix.mkdir p 0o700) [top; root; work; incoming; outgoing];
  let c = { top; root; work; incoming; outgoing;
    candidate=Filename.concat incoming "candidate"; target=Filename.concat outgoing "target";
    handles=ref [] } in
  write_file c.candidate payload;
  Fun.protect ~finally:(fun () ->
    attribute_fault 0 0; identity_fault 1 0; identity_fault 2 0;
    rename_fault 0; auxiliary_fault 0; unlink_fault 0;
    List.iter P.close_noerr !(c.handles); remove_tree top) (fun () -> f c)
let prepare ?root ?work ?(candidate="incoming/candidate") ?(target="outgoing/target")
    ?(check_apple_double=true) c =
  let h = P.prepare ~logical_root:(Option.value root ~default:c.root)
    ~working_dir:(Option.value work ~default:c.work) ~candidate ~target ~check_apple_double in
  c.handles := h :: !(c.handles); h
let attached c = let h = prepare c in P.attach h; h
let observed c = let h = attached c in P.observe_target h; h
let recheck c h = P.recheck_resolution h ~working_dir:c.work ~target:"outgoing/target"
let test directory name f =
  Printf.printf "RUN %s\n%!" name;
  let before = native_fd_count () in
  fixture directory f;
  check (native_fd_count () = before) ("descriptor leak in " ^ name);
  incr count; Printf.printf "PASS %s\n%!" name
let mutate path =
  let fd = Unix.openfile path [Unix.O_WRONLY; Unix.O_CLOEXEC] 0 in
  Fun.protect ~finally:(fun () -> Unix.close fd)
    (fun () -> ignore (Unix.write_substring fd sentinel 0 (String.length sentinel)))

let () =
  if not (P.available ()) then exit 77;
  let directory = Sys.argv.(1) in
  test directory "absent exclusive publication and readback" (fun c ->
    let h = observed c in recheck c h; P.check h; P.publish h;
    check (P.published h) "native publication not tracked";
    P.check_published h; recheck c h;
    check (not (exists c.candidate) && read_file c.target = payload) "publication bytes/name";
    P.release h; check (P.published h) "released publication lost state";
    P.close_noerr h; check (read_file c.target = payload) "cleanup deleted live");
  test directory "regular expected replacement" (fun c ->
    write_file c.target sentinel;
    let h = observed c in P.check h; P.publish h; P.check_published h;
    check (read_file c.target = payload) "replacement failed");
  test directory "expected target hardlinks remain legal" (fun c ->
    write_file c.target sentinel;
    let alias = Filename.concat c.outgoing "old-alias" in Unix.link c.target alias;
    let h = observed c in P.publish h; P.check_published h;
    check (read_file c.target = payload && read_file alias = sentinel) "hardlink target handling");
  test directory "expected symlink replaced without following" (fun c ->
    let victim = Filename.concat c.top "victim" in write_file victim sentinel;
    Unix.symlink victim c.target;
    let h = observed c in P.publish h; P.check_published h;
    check (read_file victim = sentinel && read_file c.target = payload) "followed symlink target");
  test directory "candidate check before target observation" (fun c ->
    let h = attached c in P.check_candidate h; recheck c h;
    expect_unix Unix.EINVAL (fun () -> P.check h);
    P.observe_target h; P.check h);
  test directory "target observation cannot refresh expected identity" (fun c ->
    let h = observed c in expect_unix Unix.EINVAL (fun () -> P.observe_target h));
  test directory "candidate mutation after attach" (fun c ->
    write_file c.target sentinel;
    let h = observed c in mutate c.candidate;
    expect_unix Unix.EBUSY (fun () -> P.publish h);
    check (not (P.published h) && exists c.candidate && read_file c.target = sentinel)
      "candidate mutation was published";
    P.abort_and_close h; check (not (exists c.candidate)) "mutated owned candidate retained");
  test directory "candidate chmod after attach" (fun c ->
    let h = observed c in Unix.chmod c.candidate 0o640;
    expect_unix Unix.EBUSY (fun () -> P.check_candidate h));
  test directory "candidate finalized chmod before attach" (fun c ->
    let h = prepare c in Unix.chmod c.candidate 0o640; P.attach h; P.observe_target h;
    P.publish h; P.check_published h;
    check ((Unix.stat c.target).Unix.st_perm = 0o640) "final properties lost");
  test directory "candidate read permits atime change" (fun c ->
    let h = observed c in check (read_file c.candidate = payload) "read fixture";
    P.check_candidate h; P.publish h; P.check_published h);
  List.iter (fun resource -> test directory
    (if resource then "finalized native resource fork preserved" else "finalized native extended attribute preserved")
    (fun c -> attribute_write c.candidate payload resource;
      let h = observed c in P.publish h; P.check_published h;
      check (attribute_read c.target resource = payload) "native attribute lost on publication")) [false;true];
  List.iter (fun resource -> test directory
    (if resource then "late native resource fork mutation rejected" else "late native extended attribute mutation rejected")
    (fun c -> let h = observed c in attribute_write c.candidate sentinel resource;
      expect_unix Unix.EBUSY (fun () -> P.check_candidate h))) [false;true];
  test directory "auxiliary absence admission query" (fun c ->
    let h = prepare c in check (P.auxiliary_absent h) "absent sidecars declined";
    write_file (Filename.concat c.incoming "._candidate") sentinel;
    check (not (P.auxiliary_absent h)) "candidate sidecar not detected";
    expect_unix Unix.EOPNOTSUPP (fun () -> P.attach h);
    P.abort_and_close h;
    check (exists c.candidate) "sidecar gate owned an unadmitted candidate");
  test directory "Finder-only target sidecar gates legacy handoff" (fun c ->
    write_file (Filename.concat c.outgoing "._target") sentinel;
    let h = prepare c in check (not (P.auxiliary_absent h)) "target sidecar not detected";
    P.release h; check (read_file (Filename.concat c.outgoing "._target") = sentinel) "target sidecar changed");
  test directory "dangling auxiliary symlink is present" (fun c ->
    Unix.symlink "missing" (Filename.concat c.outgoing "._target");
    let h = prepare c in check (not (P.auxiliary_absent h)) "followed dangling sidecar");
  test directory "late candidate sidecar invalidates frozen candidate" (fun c ->
    let h = observed c in write_file (Filename.concat c.incoming "._candidate") sentinel;
    expect_unix Unix.EOPNOTSUPP (fun () -> P.check_candidate h);
    P.abort_and_close h; check (read_file (Filename.concat c.incoming "._candidate") = sentinel) "auxiliary was deleted");
  test directory "late target sidecar blocks native publish" (fun c ->
    let h = observed c in P.check h;
    write_file (Filename.concat c.outgoing "._target") sentinel;
    expect_unix Unix.EOPNOTSUPP (fun () -> P.publish h);
    check (not (P.published h)) "sidecar blocked rename marked published");
  test directory "published sidecar blocks readback but never removes live" (fun c ->
    let h = observed c in P.publish h;
    write_file (Filename.concat c.outgoing "._target") sentinel;
    expect_unix Unix.EOPNOTSUPP (fun () -> P.check_published h);
    P.abort_and_close h; check (read_file c.target = payload) "late-sidecar cleanup removed live");
  test directory "explicit disabled auxiliary policy preserves ignored sidecars" (fun c ->
    write_file (Filename.concat c.incoming "._candidate") sentinel;
    write_file (Filename.concat c.outgoing "._target") sentinel;
    let h = prepare ~check_apple_double:false c in check (P.auxiliary_absent h) "disabled policy queried sidecars";
    P.attach h; P.observe_target h; P.publish h; P.check_published h;
    check (read_file (Filename.concat c.outgoing "._target") = sentinel) "disabled auxiliary policy changed sidecar");
  List.iter (fun (mode, error) -> test directory ("auxiliary operational error " ^ string_of_int mode)
    (fun c -> let h = prepare c in auxiliary_fault mode;
      expect_unix error (fun () -> ignore (P.auxiliary_absent h));
      expect_unix error (fun () -> P.attach h); auxiliary_fault 0;
      check (exists c.candidate) "auxiliary error removed unadmitted candidate"))
    [1, Unix.EACCES; 2, Unix.EIO];
  test directory "candidate inode replacement with same bytes" (fun c ->
    let h = observed c in Unix.rename c.candidate (c.candidate ^ ".owned");
    write_file c.candidate payload;
    expect_unix Unix.EBUSY (fun () -> P.publish h);
    expect_unix Unix.EBUSY (fun () -> P.abort_and_close h);
    check (read_file c.candidate = payload) "foreign replacement removed");
  test directory "candidate late hardlink rejected but alias preserved" (fun c ->
    let h = observed c in let alias = c.candidate ^ ".alias" in Unix.link c.candidate alias;
    expect_unix Unix.EBUSY (fun () -> P.publish h);
    P.abort_and_close h; check (read_file alias = payload) "foreign hardlink removed");
  test directory "candidate symlink never admitted or removed" (fun c ->
    Unix.unlink c.candidate; Unix.symlink c.target c.candidate;
    let h = prepare c in expect_native (fun () -> P.attach h);
    P.abort_and_close h; check ((Unix.lstat c.candidate).Unix.st_kind = Unix.S_LNK) "unproven symlink removed");
  test directory "candidate FIFO never blocks or becomes owned" (fun c ->
    Unix.unlink c.candidate; Unix.mkfifo c.candidate 0o600;
    let h = prepare c in expect_unix Unix.EBUSY (fun () -> P.attach h);
    P.abort_and_close h; check ((Unix.lstat c.candidate).Unix.st_kind = Unix.S_FIFO) "unproven FIFO removed");
  test directory "candidate preexisting hardlinks never admitted" (fun c ->
    Unix.link c.candidate (c.candidate ^ ".alias");
    let h = prepare c in expect_unix Unix.EBUSY (fun () -> P.attach h);
    P.abort_and_close h; check (exists c.candidate) "unproven multiply-linked candidate removed");
  test directory "existing directory target excluded" (fun c ->
    Unix.mkdir c.target 0o700;
    let h = attached c in expect_unix Unix.EOPNOTSUPP (fun () -> P.observe_target h));
  test directory "target appearance after absent observation" (fun c ->
    let h = observed c in write_file c.target sentinel;
    expect_unix Unix.EBUSY (fun () -> P.publish h);
    P.abort_and_close h; check (read_file c.target = sentinel) "unexpected target removed");
  test directory "target disappearance after existing observation" (fun c ->
    write_file c.target sentinel; let h = observed c in Unix.unlink c.target;
    expect_unix Unix.EBUSY (fun () -> P.publish h));
  test directory "target mutation after existing observation" (fun c ->
    write_file c.target sentinel; let h = observed c in mutate c.target;
    expect_unix Unix.EBUSY (fun () -> P.check h));
  test directory "target inode replacement with same bytes" (fun c ->
    write_file c.target sentinel; let h = observed c in
    Unix.rename c.target (c.target ^ ".prior"); write_file c.target sentinel;
    expect_unix Unix.EBUSY (fun () -> P.publish h));
  test directory "target mode change invalidates expectation" (fun c ->
    write_file c.target sentinel; let h = observed c in Unix.chmod c.target 0o640;
    expect_unix Unix.EBUSY (fun () -> P.check h));
  List.iter (fun (name, field) -> test directory name (fun c ->
    let h = observed c in
    let old = field c in let moved = old ^ ".held" in
    Unix.rename old moved; Unix.mkdir old 0o700;
    expect_unix Unix.EBUSY (fun () -> P.publish h);
    P.abort_and_close h;
    let held_candidate = if old = c.incoming then Filename.concat moved "candidate"
      else if old = c.work then Filename.concat moved "incoming/candidate" else c.candidate in
    check (not (exists held_candidate)) "held owned candidate cleanup failed"))
    ["logical root rebound", (fun c -> c.root);
     "effective directory rebound", (fun c -> c.work);
     "candidate parent rebound", (fun c -> c.incoming);
     "target parent rebound", (fun c -> c.outgoing)];
  test directory "rebound candidate parent foreign sentinel preserved" (fun c ->
    let h = observed c in Unix.rename c.incoming (c.incoming ^ ".held");
    Unix.mkdir c.incoming 0o700; write_file c.candidate sentinel;
    expect_unix Unix.EBUSY (fun () -> P.check_candidate h);
    P.abort_and_close h; check (read_file c.candidate = sentinel) "foreign rebound candidate deleted");
  test directory "sibling creation and directory timestamps allowed" (fun c ->
    let h = observed c in List.iter (fun d -> write_file (Filename.concat d "sibling") sentinel)
      [c.root; c.work; c.incoming; c.outgoing];
    recheck c h; P.check h; P.publish h; P.check_published h);
  test directory "fresh physically equivalent working and parent aliases" (fun c ->
    let h = observed c in let alias = Filename.concat c.top "alias" in Unix.symlink c.work alias;
    Unix.symlink c.outgoing (Filename.concat c.work "out-alias");
    P.recheck_resolution h ~working_dir:alias ~target:"out-alias/target";
    P.publish h; P.check_published h);
  test directory "fresh different working directory rejected" (fun c ->
    let h = observed c in expect_unix Unix.EBUSY (fun () ->
      P.recheck_resolution h ~working_dir:c.root ~target:"outgoing/target"));
  test directory "fresh same basename wrong parent rejected" (fun c ->
    let h = observed c in expect_unix Unix.EBUSY (fun () ->
      P.recheck_resolution h ~working_dir:c.work ~target:"incoming/target"));
  test directory "fresh same parent wrong basename rejected" (fun c ->
    let h = observed c in expect_unix Unix.EBUSY (fun () ->
      P.recheck_resolution h ~working_dir:c.work ~target:"outgoing/other"));
  test directory "followed directory ancestry allowed" (fun c ->
    let root_alias = Filename.concat c.top "root-alias" in Unix.symlink c.root root_alias;
    let work_alias = Filename.concat c.top "work-alias" in Unix.symlink c.work work_alias;
    let h = prepare ~root:root_alias ~work:work_alias c in P.attach h; P.observe_target h;
    P.publish h; P.check_published h);
  test directory "saved followed effective alias rebind rejected" (fun c ->
    let alias = Filename.concat c.top "alias" in Unix.symlink c.work alias;
    let h = prepare ~work:alias c in P.attach h; P.observe_target h;
    Unix.unlink alias; Unix.symlink c.root alias;
    expect_unix Unix.EBUSY (fun () -> P.publish h));
  test directory "exclusive rename closes lookup-to-rename collision" (fun c ->
    let h = observed c in rename_fault 2;
    expect_unix Unix.EEXIST (fun () -> P.publish h); rename_fault 0;
    check (not (P.published h)) "failed rename marked published";
    check (read_file c.target = "exclusive native race sentinel") "exclusive collision overwritten");
  test directory "rename operational failure retains old target" (fun c ->
    write_file c.target sentinel; let h = observed c in rename_fault 1;
    expect_unix Unix.EIO (fun () -> P.publish h); rename_fault 0;
    check (not (P.published h) && read_file c.target = sentinel) "failed replace changed target");
  test directory "post-rename observation failure retains published state" (fun c ->
    let h = observed c in rename_fault 4;
    expect_unix Unix.EIO (fun () -> P.publish h); rename_fault 0;
    check (P.published h) "success lost after result-stat failure";
    expect_unix Unix.EBUSY (fun () -> P.check_published h);
    P.abort_and_close h; check (read_file c.target = payload) "uncertain live output removed";
    check (P.published h) "cleanup reset published state");
  List.iter (fun existing -> test directory
    (if existing then "replacement post-rename pending exception" else "exclusive post-rename pending exception")
    (fun c ->
      if existing then write_file c.target sentinel;
      let h = observed c in
      let old = Sys.signal Sys.sigusr1 (Sys.Signal_handle (fun _ -> raise Sys.Break)) in
      Fun.protect ~finally:(fun () -> ignore (Sys.signal Sys.sigusr1 old); rename_fault 0)
        (fun () -> rename_fault 3;
          let interrupted = ref false in
          (try with_async_exns (fun () -> P.publish h) with Sys.Break -> interrupted := true);
          rename_fault 0;
          (try with_async_exns dispatch_pending with Sys.Break -> interrupted := true);
          check !interrupted "pending exception did not reach fixture";
          check (P.published h) "pending exception lost native success";
          P.check_published h; P.abort_and_close h;
          check (read_file c.target = payload) "pending-exception cleanup deleted live"))) [false; true];
  test directory "published candidate mutation blocks archive proof" (fun c ->
    let h = observed c in P.publish h; mutate c.target;
    expect_unix Unix.EBUSY (fun () -> P.check_published h);
    P.abort_and_close h; check (exists c.target) "published mutation cleanup deleted live");
  test directory "published target replacement foreign sentinel retained" (fun c ->
    let h = observed c in P.publish h; Unix.rename c.target (c.target ^ ".owned");
    write_file c.target sentinel;
    expect_unix Unix.EBUSY (fun () -> P.check_published h);
    P.abort_and_close h; check (read_file c.target = sentinel) "published foreign replacement deleted");
  test directory "published namespace rebound blocks readback and never deletes" (fun c ->
    let h = observed c in P.publish h; Unix.rename c.work (c.work ^ ".held");
    Unix.mkdir c.work 0o700;
    expect_unix Unix.EBUSY (fun () -> P.check_published h);
    P.abort_and_close h;
    check (read_file (Filename.concat (c.work ^ ".held") "outgoing/target") = payload) "published held target deleted");
  test directory "proof descriptors CLOEXEC and repeat close handles FD reuse" (fun c ->
    let before = open_fds () in let h = attached c in let owned = new_fds before in
    check (List.length owned = 5) "expected four directory proofs plus candidate";
    List.iter (fun n -> check (fd_state n = 1) "proof fd not CLOEXEC") owned;
    P.release h; check_closed owned;
    let fresh = Unix.openfile c.candidate [Unix.O_RDONLY; Unix.O_CLOEXEC] 0 in
    Fun.protect ~finally:(fun () -> Unix.close fresh) (fun () ->
      check (List.mem (fd_number fresh) owned) "fixture did not reuse released descriptor";
      P.release h; P.close_noerr h; ignore (Unix.fstat fresh));
    check (exists c.candidate) "release removed candidate");
  test directory "native cleanup failure closes proof fds before exception" (fun c ->
    let before = open_fds () in let h = attached c in let owned = new_fds before in
    Unix.rename c.candidate (c.candidate ^ ".held"); write_file c.candidate sentinel;
    expect_unix Unix.EBUSY (fun () -> P.abort_and_close h); check_closed owned);
  test directory "unattached abort never owns candidate" (fun c ->
    let h = prepare c in P.abort_and_close h; check (exists c.candidate) "unattached candidate removed");
  test directory "quarantine rejects mutated candidate via owned parent then removes" (fun c ->
    let h = attached c in mutate c.candidate;
    P.quarantine_and_close h ~name:"validation-rejected";
    check (not (exists c.candidate) && not (exists (Filename.concat c.incoming "validation-rejected"))) "quarantine did not remove owned candidate");
  test directory "quarantine unlink EPERM isolates normal candidate name" (fun c ->
    let h = attached c in let before = open_fds () in
    unlink_fault 1;
    expect_unix Unix.EPERM (fun () -> P.quarantine_and_close h ~name:"validation-rejected");
    unlink_fault 0;
    check (not (exists c.candidate)) "normal candidate name remained after successful quarantine";
    check (read_file (Filename.concat c.incoming "validation-rejected") = payload) "owned quarantine missing";
    check (List.length (open_fds ()) = List.length before - 5) "quarantine unlink failure leaked proofs");
  test directory "real immutable candidate forbids quarantine without clearing flags" (fun c ->
    let h = attached c in immutable c.candidate true;
    Fun.protect ~finally:(fun () -> immutable c.candidate false) (fun () ->
      expect_unix Unix.EPERM (fun () -> P.quarantine_and_close h ~name:"validation-rejected");
      check (exists c.candidate && not (exists (Filename.concat c.incoming "validation-rejected"))) "immutable candidate changed despite OS refusal"));
  test directory "quarantine remains bound after candidate parent rebound" (fun c ->
    let h = attached c in Unix.rename c.incoming (c.incoming ^ ".held");
    Unix.mkdir c.incoming 0o700; write_file c.candidate sentinel;
    P.quarantine_and_close h ~name:"validation-rejected";
    check (read_file c.candidate = sentinel) "rebound foreign candidate deleted";
    check (not (exists (Filename.concat (c.incoming ^ ".held") "candidate"))) "held candidate not quarantined");
  test directory "quarantine existing collision preserved" (fun c ->
    let h = attached c in let rejected = Filename.concat c.incoming "validation-rejected" in
    write_file rejected sentinel;
    expect_unix Unix.EEXIST (fun () -> P.quarantine_and_close h ~name:"validation-rejected");
    check (read_file c.candidate = payload && read_file rejected = sentinel) "quarantine collision overwritten");
  test directory "quarantine foreign candidate replacement preserved" (fun c ->
    let h = attached c in Unix.rename c.candidate (c.candidate ^ ".owned");
    write_file c.candidate sentinel;
    expect_unix Unix.EBUSY (fun () -> P.quarantine_and_close h ~name:"validation-rejected");
    check (read_file c.candidate = sentinel) "foreign candidate quarantined");
  test directory "quarantine native collision after lookup remains exclusive" (fun c ->
    let h = attached c in rename_fault 2;
    expect_unix Unix.EEXIST (fun () -> P.quarantine_and_close h ~name:"validation-rejected");
    rename_fault 0;
    check (read_file c.candidate = payload) "exclusive quarantine collision removed candidate";
    check (read_file (Filename.concat c.incoming "validation-rejected") = "exclusive native race sentinel") "quarantine collision overwritten");
  test directory "quarantine post-rename pending exception closes resources" (fun c ->
    let h = attached c in let owned = open_fds () in
    let old = Sys.signal Sys.sigusr1 (Sys.Signal_handle (fun _ -> raise Sys.Break)) in
    Fun.protect ~finally:(fun () -> ignore (Sys.signal Sys.sigusr1 old); rename_fault 0)
      (fun () -> rename_fault 3; let interrupted = ref false in
        (try with_async_exns (fun () -> P.quarantine_and_close h ~name:"validation-rejected")
         with Sys.Break -> interrupted := true);
        rename_fault 0;
        (try with_async_exns dispatch_pending with Sys.Break -> interrupted := true);
        check !interrupted "quarantine pending exception not delivered";
        check (List.length (open_fds ()) = List.length owned - 5) "quarantine pending exception leaked proofs";
        check (not (exists c.candidate) && not (exists (Filename.concat c.incoming "validation-rejected"))) "pending cleanup lost quarantine ownership"));
  test directory "quarantine post-rename observation failure retains isolated name" (fun c ->
    let h = attached c in rename_fault 4;
    expect_unix Unix.EIO (fun () -> P.quarantine_and_close h ~name:"validation-rejected"); rename_fault 0;
    check (not (exists c.candidate) && read_file (Filename.concat c.incoming "validation-rejected") = payload) "failed quarantine cleanup lost isolated name");
  test directory "published candidate never quarantined" (fun c ->
    let h = observed c in P.publish h;
    P.quarantine_and_close h ~name:"validation-rejected";
    check (P.published h && read_file c.target = payload) "live publication quarantined");
  test directory "quarantine basename validation" (fun c ->
    let h = attached c in List.iter (fun name ->
      expect_invalid (fun () -> P.quarantine_and_close h ~name)) ["";".";"..";"a/b";"/absolute";"x\000y"];
    expect_unix Unix.EINVAL (fun () -> P.quarantine_and_close h ~name:"candidate");
    check (exists c.candidate) "invalid quarantine deleted candidate");
  test directory "closed state rejected but published remains queryable" (fun c ->
    let h = attached c in P.release h; check (not (P.published h)) "unpublished release became success";
    expect_unix Unix.EINVAL (fun () -> P.attach h);
    expect_unix Unix.EINVAL (fun () -> P.check_candidate h);
    expect_unix Unix.EBUSY (fun () -> P.check_published h));
  List.iter (fun mode -> test directory ("high native file identity/flags " ^ string_of_int mode)
    (fun c -> let h = observed c in identity_fault 1 mode;
      expect_unix Unix.EBUSY (fun () -> P.check_candidate h); identity_fault 1 0)) [3;4;5;6;7;8;9;10;11;12];
  List.iter (fun mode -> test directory ("high native filesystem identity " ^ string_of_int mode)
    (fun c -> let h = observed c in identity_fault 2 mode;
      expect_unix Unix.EBUSY (fun () -> P.check_candidate h); identity_fault 2 0)) [1;2;3];
  List.iteri (fun index phase -> test directory ("preparation missing UUID phase " ^ phase)
    (fun c -> let baseline = native_fd_count () in attribute_fault 1 (index + 1);
      let error = try ignore (prepare c); failwith "missing UUID accepted" with Unix.Unix_error (_, _, _) as e -> e in
      attribute_fault 0 0;
      check (P.preparation_unavailable error) "initial missing UUID did not decline";
      check (native_fd_count () = baseline) "prepare failure leaked before GC";
      match error with Unix.Unix_error (_, actual, _) ->
        check (actual = "final_publication.prepare." ^ phase ^ "_identity") "wrong preparation identity phase" | _ -> assert false))
    ["root";"working";"candidate";"target"];
  List.iter (fun mode -> test directory ("initial identity errors scoped " ^ string_of_int mode)
    (fun c -> attribute_fault mode 1;
      let error = try ignore (prepare c); failwith "identity fault accepted" with Unix.Unix_error (_, _, _) as e -> e in
      attribute_fault 0 0;
      check (P.preparation_unavailable error = List.mem mode [2;12;13;14]) "wrong initial decline classification"))
    [2;3;4;5;6;7;8;12;13;14];
  test directory "late missing UUID never declines" (fun c ->
    let h = observed c in attribute_fault 1 1;
    let error = try P.check_candidate h; failwith "late UUID fault accepted" with Unix.Unix_error (_, _, _) as e -> e in
    attribute_fault 0 0; check (not (P.preparation_unavailable error)) "late fault classified as fallback");
  test directory "path validation and classifier exact phases" (fun c ->
    List.iter (fun p -> expect_invalid (fun () -> ignore (prepare ~candidate:p c)))
      ["";"/absolute";"a//b";"./candidate";"a/../b";"a\000b"];
    expect_invalid (fun () -> ignore (prepare ~target:"incoming/candidate" c));
    let h = attached c in expect_invalid (fun () -> P.recheck_resolution h ~working_dir:"relative" ~target:"outgoing/target");
    List.iter (fun phase -> check (not (P.preparation_unavailable (Unix.Unix_error (Unix.ENOSYS, phase, "")))) "classifier accepted near-miss")
      ["final_publication.prepare.root_identity.extra";"final_publication.prepare.root_identity\000";
       "final_publication.attach.candidate";"final_publication.prepare.logical_root"]);
  test directory "aliased initial candidate and target rejected" (fun c ->
    Unix.symlink c.incoming (Filename.concat c.work "alias");
    expect_unix Unix.EINVAL (fun () -> ignore (prepare ~target:"alias/candidate" c)));
  Printf.printf "%d final publication cases passed\n%!" !count
