(* Original deterministic native error controls. No production fault switch. *)
module C=ComponentHash
external configure : int -> unit = "unison_record_fault_configure"
external counts : unit -> int * int = "unison_record_fault_counts"
let checks=ref 0
let check yes why=incr checks;if not yes then failwith why
let () =
  if not(C.record_publication_available ()) then failwith "macOS fault control required";
  let before=Array.length(Sys.readdir "/dev/fd") in
  let checkpoint=Component_hash.with_input Component_hash.data (fun _ fd ->
    SemanticFile.with_fd fd (fun file -> C.with_snapshot ~max_read_bytes:8192L
      file Component_hash.layout C.checkpoint)) in
  List.iter(fun mode ->
    let path=Filename.temp_file "record-fault-directory-" "" in
    Sys.remove path;Unix.mkdir path 0o700;
    let directory=Unix.openfile path [Unix.O_RDONLY;Unix.O_CLOEXEC] 0 in
    Fun.protect ~finally:(fun () -> configure 0;Unix.close directory;
      Array.iter(fun name -> Sys.remove(Filename.concat path name)) (Sys.readdir path);
      Unix.rmdir path) (fun () ->
      let temporary=Filename.concat path "stage" in
      let stage=Unix.openfile temporary [Unix.O_CREAT;Unix.O_EXCL;Unix.O_RDWR;Unix.O_CLOEXEC] 0o600 in
      Fun.protect ~finally:(fun () -> Unix.close stage) (fun () ->
        let binding=SemanticHash.string("original fault binding "^string_of_int mode) in
        let digest=C.write_checkpoint_record ~binding checkpoint stage in
        let target=Filename.concat path (SemanticHash.hex digest) in
        let ticket=SemanticFile.with_fd stage (fun file -> C.prepare_record_publication
          ~directory ~stage ~temporary:"stage" ~expected_binding:binding
          ~expected_record_sha256:digest file) in
        configure mode;
        check(try C.publish_checkpoint_record ticket directory stage;false with
          | Unix.Unix_error(error,phase,_) ->
            error=(if mode=3 then Unix.EINTR else Unix.EIO) &&
            phase=(if mode=1 then "component record directory sync" else "component record stage sync"))
          "injected sync error was lost or attributed to wrong phase";
        check(counts()=(1,(if mode=1 then 1 else 0))) "native sync implicitly retried";
        check(C.record_published ticket=(mode=1)) "rename effect lost across sync failure";
        check(Sys.file_exists target=(mode=1) && Sys.file_exists temporary=(mode<>1))
          "error path changed publication namespace incorrectly";
        let loaded=SemanticFile.with_fd stage (fun file -> C.read_checkpoint_record
          ~expected_binding:binding ~expected_record_sha256:digest file) in
        check(C.checkpoint_bytes loaded=C.checkpoint_bytes checkpoint)
          "sync failure altered record bytes";
        check((Unix.fstat stage).Unix.st_kind=Unix.S_REG &&
          (Unix.fstat directory).Unix.st_kind=Unix.S_DIR) "publisher closed borrowed FD";
        if mode=1 then begin
          check(try C.publish_checkpoint_record ticket directory stage;false
            with Invalid_argument _ -> true) "post-rename error allowed ticket replay";
          check(C.record_published ticket && counts()=(1,1)) "replay lost native effect or issued another sync"
        end))) [1;2;3];
  let path=Filename.temp_file "quota-fault-directory-" "" in
  Sys.remove path;Unix.mkdir path 0o700;
  let directory=Unix.openfile path [Unix.O_RDONLY;Unix.O_CLOEXEC] 0 in
  Fun.protect ~finally:(fun () -> configure 0;Unix.close directory;
    Array.iter(fun name -> let leaf=Filename.concat path name in
      if (Unix.lstat leaf).Unix.st_kind=Unix.S_DIR then Unix.rmdir leaf else Sys.remove leaf) (Sys.readdir path);
    Unix.rmdir path) (fun () ->
    let prepare ()=C.prepare_metadata_quota ~directory ~max_bytes:2097152L ~max_entries:1 in
    configure 0;let quota=prepare () in configure 1;
    check(try ignore(C.reserve_metadata_slot quota directory);false
      with Unix.Unix_error(Unix.EIO,"component quota reservation",_) -> true)
      "quota directory-sync failure not reported";
    check(C.metadata_slot_reserved quota &&
      (Unix.lstat(Filename.concat path (C.metadata_slot_name quota))).Unix.st_kind=Unix.S_DIR)
      "quota slot creation lost across sync failure";
    check(counts()=(0,1)) "quota sync retried or synced unexpected FD";
    check(try ignore(C.reserve_metadata_slot quota directory);false
      with Invalid_argument _ -> true) "uncertain quota ticket replayed";
    configure 0;
    check(not(C.reserve_metadata_slot (prepare()) directory))
      "failed reservation was silently refunded");
  check(Array.length(Sys.readdir "/dev/fd")=before) "native fault controls leaked descriptors";
  Printf.printf "PASS %d record publication fault checks; postrename effect retained, stage EIO/EINTR not retried\n%!" !checks
