module P = FinalPublication
external arm : int -> string -> string -> string -> unit = "obsolete_fixture_arm"
external reused : unit -> Unix.file_descr = "obsolete_fixture_reused"
external disarm : unit -> unit = "obsolete_fixture_disarm"
let assertions = ref 0 and cases = ref 0
let check value message = incr assertions; if not value then failwith message
let write path data =
  let ch = open_out_bin path in
  Fun.protect ~finally:(fun () -> close_out ch) (fun () -> output_string ch data)
let read path =
  let ch = open_in_bin path in
  Fun.protect ~finally:(fun () -> close_in ch)
    (fun () -> really_input_string ch (in_channel_length ch))
let exists path = try ignore (Unix.lstat path); true with Unix.Unix_error (Unix.ENOENT,_,_) -> false
let count_fds () = Array.length (Sys.readdir "/dev/fd")
let error f = match f () with
  | () -> failwith "expected obsolete-cleanup error"
  | exception Unix.Unix_error (_,phase,_) -> check (phase <> "") "missing native error phase"
let old = "independent-old-stage\000" and live = "independent-live-target\255"
let replacement = "independent-replacement\000\255"
let fixture name f =
  let top = Filename.concat (Sys.getcwd ()) name in Unix.mkdir top 0o700;
  let root = top ^ "/root" and work = top ^ "/root/work" in
  Unix.mkdir root 0o700; Unix.mkdir work 0o700;
  let leaf = work ^ "/candidate" and target = work ^ "/target" in
  write target live;
  let before = count_fds () in
  let p = P.prepare ~logical_root:root ~working_dir:work ~candidate:"candidate"
    ~target:"target" ~check_apple_double:(name = "sidecar") in
  Fun.protect ~finally:(fun () -> disarm (); P.release p) (fun () ->
    f top root work leaf target p;
    check (read (if exists target then target else top ^ "/moved/work/target") = live)
      "live target bytes changed";
    P.release p;
    check (count_fds () = before) "obsolete cleanup leaked transient descriptors";
    incr cases; Printf.printf "PASS %s\n%!" name)
let clear p work path = P.clear_obsolete p ~working_dir:work ~path
let parent_rebound negative = fixture "parent-rebound" (fun top _root work leaf _target p ->
  write leaf old;
  Unix.rename work (top ^ "/held"); Unix.mkdir work 0o700;
  write leaf replacement; write (work ^ "/target") live;
  let outcome = try clear p work "candidate"; false with Unix.Unix_error _ -> true in
  if negative then begin
    check (exists leaf && read leaf = replacement && read (top ^ "/held/candidate") = old)
      "DESIGNATED pathname cleanup damaged replacement inventory"
  end else begin
    check outcome "parent rebind did not reject";
    check (read leaf = replacement && read (top ^ "/held/candidate") = old)
      "parent rebind changed either candidate"
  end)
let main () =
  check (P.available ()) "native publication unavailable";
  if Array.length Sys.argv > 1 then parent_rebound true else begin
    fixture "absent" (fun _ _ work _ _ p -> clear p work "candidate"; clear p work "candidate");
    fixture "regular" (fun _ _ work leaf _ p -> write leaf old; clear p work "candidate";
      check (not (exists leaf)) "regular obsolete leaf retained";
      let fd = Unix.openfile leaf [Unix.O_WRONLY;Unix.O_CREAT;Unix.O_EXCL] 0o600 in
      Unix.close fd; P.attach p; P.observe_target p; P.check p);
    fixture "scratch" (fun _ _ work leaf _ p -> write leaf old; write (work ^ "/scratch") replacement;
      clear p work "scratch"; check (read leaf = old && not (exists (work ^ "/scratch"))) "scratch cleanup mismatch");
    fixture "mode-zero" (fun _ _ work leaf _ p -> write leaf old; Unix.chmod leaf 0;
      clear p work "candidate"; check (not (exists leaf)) "mode-zero cleanup required chmod/read");
    fixture "hardlink" (fun _ _ work leaf target p -> Unix.link target leaf;
      error (fun () -> clear p work "candidate"); check (exists leaf) "hardlink was deleted";
      check ((Unix.stat target).Unix.st_nlink = 2) "live link metadata changed");
    fixture "symlink" (fun _ _ work leaf target p -> Unix.symlink target leaf;
      error (fun () -> clear p work "candidate"); check (Unix.readlink leaf = target) "symlink was changed");
    fixture "directory" (fun _ _ work leaf _ p -> Unix.mkdir leaf 0o700; write (leaf ^ "/sentinel") old;
      error (fun () -> clear p work "candidate"); check (read (leaf ^ "/sentinel") = old) "directory was traversed");
    fixture "fifo" (fun _ _ work leaf _ p -> Unix.mkfifo leaf 0o600;
      error (fun () -> clear p work "candidate"); check ((Unix.lstat leaf).Unix.st_kind = Unix.S_FIFO) "FIFO changed");
    fixture "sidecar" (fun _ _ work leaf _ p -> write leaf old; write (work ^ "/._candidate") replacement;
      error (fun () -> clear p work "candidate"); check (read leaf = old && read (work ^ "/._candidate") = replacement) "sidecar family changed");
    fixture "wrong-parent" (fun _ _ work leaf _ p -> write leaf old; Unix.mkdir (work ^ "/other") 0o700;
      write (work ^ "/other/candidate") replacement;
      error (fun () -> clear p work "other/candidate");
      check (read leaf = old && read (work ^ "/other/candidate") = replacement) "foreign parent changed");
    fixture "live-name" (fun _ _ work _ _ p -> error (fun () -> clear p work "target"));
    fixture "live-case-alias" (fun _ _ work _ target p ->
      if exists (work ^ "/TARGET") then begin
        check ((Unix.stat (work ^ "/TARGET")).Unix.st_ino = (Unix.stat target).Unix.st_ino)
          "case-alias fixture did not bind actual live entry";
        error (fun () -> clear p work "TARGET")
      end else clear p work "TARGET");
    fixture "working-alias" (fun top _ work leaf _ p -> write leaf old; Unix.symlink work (top ^ "/alias");
      clear p (top ^ "/alias") "candidate"; check (not (exists leaf)) "equivalent working alias refused");
    fixture "invalid-paths" (fun _ _ work leaf _ p -> write leaf old;
      List.iter (fun path -> match clear p work path with
        | () -> failwith "invalid path admitted" | exception Invalid_argument _ -> ()) ["";"/candidate";"../candidate";"./candidate";"a//b";"a\000b"];
      check (read leaf = old) "invalid path changed old leaf");
    parent_rebound false;
    fixture "root-rebound" (fun top root work leaf _ p -> write leaf old; Unix.rename root (top ^ "/moved");
      Unix.mkdir root 0o700; Unix.mkdir work 0o700; write leaf replacement; write (work ^ "/target") live;
      error (fun () -> clear p work "candidate");
      check (read leaf = replacement && read (top ^ "/moved/work/candidate") = old) "root rebind changed old/new leaf");
    fixture "producing" (fun _ _ work leaf _ p -> write leaf old;
      let fd = Unix.openfile leaf [Unix.O_WRONLY] 0 in P.adopt_mutable p ~candidate:fd; Unix.close fd;
      error (fun () -> clear p work "candidate"); check (read leaf = old) "owned producer removed");
    fixture "closed" (fun _ _ work leaf _ p -> write leaf old; P.release p;
      error (fun () -> clear p work "candidate"); check (read leaf = old) "closed context removed leaf";
      ignore work);
    fixture "leaf-race" (fun top _ work leaf _ p -> write leaf old; write (top ^ "/replacement") replacement;
      arm 1 leaf (top ^ "/saved") (top ^ "/replacement"); error (fun () -> clear p work "candidate");
      check (read leaf = replacement && read (top ^ "/saved") = old) "leaf replacement was deleted");
    fixture "parent-race" (fun top _ work leaf _ p -> write leaf old; Unix.mkdir (top ^ "/replacement-parent") 0o700;
      write (top ^ "/replacement-parent/candidate") replacement; write (top ^ "/replacement-parent/target") live;
      arm 2 work (top ^ "/saved-parent") (top ^ "/replacement-parent"); error (fun () -> clear p work "candidate");
      check (read leaf = replacement && read (top ^ "/saved-parent/candidate") = old) "parent replacement inventory changed");
    fixture "unlink-error" (fun _ _ work leaf _ p -> write leaf old; arm 3 "" "" "";
      error (fun () -> clear p work "candidate"); check (read leaf = old) "unlink failure deleted stage");
    fixture "close-error" (fun _ _ work leaf _ p -> write leaf old; arm 4 "" "" "";
      error (fun () -> clear p work "candidate"); check (not (exists leaf)) "post-unlink close failure lost its effect";
      let marker = reused () in check ((Unix.fstat marker).Unix.st_kind = Unix.S_CHR) "reused fd closed again";
      Unix.close marker);
    Printf.printf "PASSED cases=%d assertions=%d\n%!" !cases !assertions
  end
let () = try main () with Failure message -> Printf.eprintf "%s\n%!" message; exit 2
