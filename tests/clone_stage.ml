(* Build in a disposable directory with copy_stubs.c and unix.cmxa.
   The Python driver owns all fixture paths. *)
external clone_stage : string -> string ->
  (Unix.file_descr * Unix.file_descr) option = "unison_clone_stage"

let read fd =
  ignore (Unix.lseek fd 0 Unix.SEEK_SET);
  let bytes = Bytes.create 4096 in
  let n = Unix.read fd bytes 0 4096 in
  Bytes.sub_string bytes 0 n

let () =
  let source = Sys.argv.(1) and output = Sys.argv.(2) in
  match clone_stage source output with
  | None -> exit 77
  | Some (basis, stage) ->
      let original = read basis in
      assert ((Unix.fstat basis).Unix.st_ino <> (Unix.fstat stage).Unix.st_ino);
      assert ((Unix.fstat basis).Unix.st_nlink = 0);
      assert ((Unix.fstat stage).Unix.st_perm land 0o777 = 0o600);
      (* The helper must not relax the live source's mode. *)
      assert ((Unix.stat source).Unix.st_perm land 0o777 = 0o400);
      if Array.length Sys.argv > 3 then begin
        (* This fixture's ACL denies writes even if its mode is relaxed. *)
        try let live = open_out_bin source in close_out live; assert false
        with Sys_error _ -> ()
      end else begin
        Unix.chmod source 0o600;
        let live = open_out_bin source in
        output_string live "modified live basis"; close_out live
      end;
      assert (read basis = original);
      ignore (Unix.lseek stage 5 Unix.SEEK_SET);
      assert (Unix.write_substring stage "PATCH" 0 5 = 5);
      assert (read basis = original);
      assert (read stage <> original);
      Unix.close basis; Unix.close stage;
      (* An existing destination must never be replaced. *)
      let saved = Digest.file output in
      for _ = 1 to 100 do
        (try ignore (clone_stage source output); assert false
         with Unix.Unix_error (Unix.EEXIST, _, _) -> ())
      done;
      assert (Digest.file output = saved);
      print_endline "clone snapshot, isolation, modes and exclusive output: ok"
