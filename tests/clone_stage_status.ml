(* Native result/ABI qualification. All paths are supplied by the disposable
   Python driver; no live roots or registries are loaded. *)
type decline = Platform_unavailable | Non_regular_source | Source_flags
             | Cross_device | Operation_unsupported
type outcome = Shared_stage of (Unix.file_descr * Unix.file_descr)
             | Declined_stage of decline
external stage : string -> string -> outcome = "unison_clone_stage_status"
external compatibility_stage : string -> string ->
  (Unix.file_descr * Unix.file_descr) option = "unison_clone_stage"

let fds () = Array.length (Sys.readdir "/dev/fd")
let close_pair (basis, output) = Unix.close basis; Unix.close output
let require value reason = if not value then failwith reason

let () =
  let mode = Sys.argv.(1) and source = Sys.argv.(2) and output = Sys.argv.(3) in
  let before = fds () in
  (match mode with
   | "shared" ->
       (match stage source output with
        | Declined_stage Platform_unavailable
        | Declined_stage Operation_unsupported -> exit 77
        | Declined_stage _ -> failwith "unexpected clone decline"
        | Shared_stage ((basis, candidate) as pair) ->
            let a = Unix.fstat basis and b = Unix.fstat candidate in
            require (a.Unix.st_kind = Unix.S_REG && b.Unix.st_kind = Unix.S_REG)
              "shared descriptors must be regular";
            require (a.Unix.st_ino <> b.Unix.st_ino && a.Unix.st_nlink = 0 && b.Unix.st_nlink = 1)
              "clone identities/links";
            require (b.Unix.st_perm land 0o777 = 0o600) "private writable mode";
            close_pair pair);
       let saved = Digest.file output in
       for _ = 1 to 100 do
         (try ignore (stage source output); failwith "collision accepted"
          with Unix.Unix_error (Unix.EEXIST, phase, _) ->
            require (phase = "clone_stage: output clone") "collision phase lost")
       done;
       require (Digest.file output = saved) "collision changed existing output";
       let old = output ^ "-compatibility" in
       (match compatibility_stage source old with
        | Some pair -> close_pair pair; Unix.unlink old
        | None -> failwith "compatibility API changed native support")
   | "kind" | "flags" | "platform" ->
       let expected = match mode with
         | "kind" -> Non_regular_source | "flags" -> Source_flags
         | _ -> Platform_unavailable in
       for _ = 1 to 100 do
         (match stage source output with
          | Declined_stage observed -> require (observed = expected) "wrong decline scope"
          | Shared_stage pair -> close_pair pair; failwith "unsuitable clone accepted")
       done;
       require (not (Sys.file_exists output)) "decline created output"
   | "missing-parent" ->
       (try ignore (stage source output); failwith "missing parent accepted"
        with Unix.Unix_error (Unix.ENOENT, phase, _) ->
          require (phase = "clone_stage: destination parent") "parent error phase lost")
   | "symlink" ->
       (try ignore (stage source output); failwith "source symlink accepted"
        with Unix.Unix_error (Unix.ELOOP, phase, _) ->
          require (phase = "clone_stage: source open") "source error phase lost")
   | _ -> failwith "unknown fixture mode");
  Gc.full_major ();
  require (fds () = before) "native outcome leaked descriptors";
  Printf.printf "strict clone-stage %s: outcome, phase and descriptor ownership pass\n%!" mode
