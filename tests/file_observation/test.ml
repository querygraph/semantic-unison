module F = FileObservation
external mode : int -> unit = "file_observation_fixture_mode"
external buffer : int -> bytes = "file_observation_fixture_buffer"
external parse : bytes -> string option = "file_observation_fixture_parse"
external protocol_errno : unit -> int = "file_observation_fixture_protocol_errno"
let check yes why = if not yes then failwith why
let count = ref 0
let test name f =
  (try f () with e -> Printf.eprintf "FAIL %s\n%!" name; raise e);
  incr count; Printf.printf "PASS %s\n%!" name
let fds () = Array.length (Sys.readdir "/dev/fd")
let hex digits value = String.length value=digits &&
  String.for_all (function '0'..'9'|'a'..'f' -> true | _ -> false) value
let identity (a:F.t) (b:F.t) = a.device_id=b.device_id && a.file_id=b.file_id &&
  a.filesystem_id=b.filesystem_id && a.volume_uuid=b.volume_uuid
let with_fd path f =
  let fd = Unix.openfile path [Unix.O_CREAT;Unix.O_EXCL;Unix.O_RDWR;Unix.O_CLOEXEC] 0o600 in
  Fun.protect ~finally:(fun () -> Unix.close fd; if Sys.file_exists path then Unix.unlink path) (fun () -> f fd)
let expect_error errno phase f =
  try ignore(f ()); failwith("expected native error at "^phase)
  with Unix.Unix_error (e,p,_) ->
    if e<>errno || p<>phase then failwith("expected "^Unix.error_message errno^" at "^phase^
      ", received "^Unix.error_message e^" at "^p)

let () =
  let directory = Sys.argv.(1) in
  let path name = Filename.concat directory name in
  let fd = Unix.openfile (path "baseline") [Unix.O_RDONLY;Unix.O_CLOEXEC] 0 in
  (try ignore(F.observe fd) with Unix.Unix_error(Unix.ENOSYS,_,_) -> Unix.close fd; exit 77);
  Fun.protect ~finally:(fun () -> mode 0;Unix.close fd) (fun () ->
    test "native full-width IDs, flags and exact nanoseconds match independent Python stat" (fun () ->
      let before = fds () in
      ignore(Unix.LargeFile.lseek fd 43L Unix.SEEK_SET);
      let a = F.observe fd in
      check (a.device_id=Sys.argv.(2) && a.file_id=Sys.argv.(3) && a.kind=Unix.S_REG)
        "native file identity differs from independent stat";
      check (a.size=Int64.of_string Sys.argv.(4) && a.link_count=Int64.of_string Sys.argv.(5) &&
             a.file_flags=Int64.of_string Sys.argv.(6)) "size/link/flags observation mismatch";
      check (a.mtime_seconds=Int64.of_string Sys.argv.(7) && a.mtime_nanoseconds=int_of_string Sys.argv.(8) &&
             a.ctime_seconds=Int64.of_string Sys.argv.(9) && a.ctime_nanoseconds=int_of_string Sys.argv.(10))
        "timestamp precision was lost";
      check (hex 8 a.device_id && hex 16 a.file_id && hex 16 a.filesystem_id && a.mount_flags>=0L)
        "native identifier encoding or unsigned flags invalid";
      Option.iter (fun uuid -> check (hex 32 uuid) "UUID encoding invalid") a.volume_uuid;
      for _=1 to 200 do check (F.observe fd=a) "unchanged descriptor observation drifted" done;
      check (Unix.LargeFile.lseek fd 0L Unix.SEEK_CUR=43L && fds()=before)
        "observation moved offset or leaked descriptors");
    test "writes and truncation retain identity while reporting fresh size and stamps" (fun () ->
      with_fd (path "mutable") (fun fd ->
        let a = F.observe fd in
        ignore(Unix.write_substring fd "abcdef" 0 6);
        let b = F.observe fd in
        check (identity a b && b.size=6L && b.mtime_nanoseconds>=0 && b.mtime_nanoseconds<1000000000)
          "write produced stale identity/size";
        Unix.LargeFile.ftruncate fd 2L;
        let c = F.observe fd in
        check (identity b c && c.size=2L && Unix.LargeFile.lseek fd 0L Unix.SEEK_CUR=6L)
          "truncate observation stale or offset changed"));
    test "unlinked held file remains observable with zero links" (fun () ->
      with_fd (path "unlinked") (fun fd ->
        let a = F.observe fd in
        Unix.unlink (path "unlinked");
        let b = F.observe fd in
        check (identity a b && a.link_count=1L && b.link_count=0L) "held unlink identity/links wrong"));
    test "rename and same-name replacement observe held object rather than pathname" (fun () ->
      with_fd (path "old-name") (fun held ->
        let original = F.observe held in
        Unix.rename (path "old-name") (path "renamed");
        Fun.protect ~finally:(fun () -> Unix.unlink(path "renamed")) (fun () ->
          with_fd (path "old-name") (fun replacement ->
            let fresh = F.observe replacement and old = F.observe held in
            check (identity original old && fresh.file_id<>old.file_id)
              "observer resolved replacement path or cached identity"))));
    test "dup2 reuse changes observation without closing or moving borrowed descriptors" (fun () ->
      with_fd (path "first") (fun first -> with_fd (path "second") (fun second ->
        let original=F.observe first and replacement=F.observe second in
        ignore(Unix.LargeFile.lseek second 17L Unix.SEEK_SET);
        Unix.dup2 second first;
        check (identity (F.observe first) replacement && original.file_id<>replacement.file_id)
          "fd reuse returned cached old identity";
        check (Unix.LargeFile.lseek first 0L Unix.SEEK_CUR=17L &&
               Unix.LargeFile.lseek second 0L Unix.SEEK_CUR=17L) "observation moved shared offset")));
    test "directory kind and filesystem facts come from the held descriptor" (fun () ->
      let dirfd=Unix.openfile directory [Unix.O_RDONLY;Unix.O_CLOEXEC] 0 in
      Fun.protect ~finally:(fun () -> Unix.close dirfd) (fun () ->
        let a=F.observe dirfd and b=F.observe fd in
        check (a.kind=Unix.S_DIR && a.device_id=b.device_id && a.filesystem_id=b.filesystem_id &&
               a.volume_uuid=b.volume_uuid && a.file_id<>b.file_id) "directory/volume identity wrong"));
    test "closed fd errors remain EBADF and leak no descriptors" (fun () ->
      let dead=Unix.openfile (path "baseline") [Unix.O_RDONLY;Unix.O_CLOEXEC] 0 in
      Unix.close dead;
      let before=fds() in
      for _=1 to 200 do expect_error Unix.EBADF "file_observation.fstat" (fun () -> F.observe dead) done;
      check (fds()=before) "closed-fd errors leaked handles");
    let protocol=Unix.EUNKNOWNERR(protocol_errno()) in
    test "raw UUID parser distinguishes absent/zero and preserves exact nonzero bytes" (fun () ->
      check (parse(buffer 1)=None && parse(buffer 2)=None) "absent/zero UUID became identity";
      let expected=String.init 16 (fun i -> Char.chr(i+1)) in
      check (parse(buffer 3)=Some expected) "UUID parser changed byte order or width";
      let padded=Bytes.cat (buffer 3) (Bytes.make 8 '#') in
      check (parse padded=Some expected) "parser consumed capacity beyond returned length");
    test "raw parser rejects every truncated capacity and malformed returned mask" (fun () ->
      let valid=buffer 3 in
      for capacity=0 to 39 do
        expect_error protocol "fixture_parse" (fun () -> parse(Bytes.sub valid 0 capacity))
      done;
      List.iter (fun code -> expect_error protocol "fixture_parse" (fun () -> parse(buffer code)))
        [4;5;6;7;11;12;13;14]);
    test "native attribute availability and malformed-data errors never weaken identity" (fun () ->
      Fun.protect ~finally:(fun () -> mode 0) (fun () ->
        List.iter (fun code -> mode code;check ((F.observe fd).volume_uuid=None) "UUID absence not explicit") [1;2];
        mode 3;check ((F.observe fd).volume_uuid=Some "0102030405060708090a0b0c0d0e0f10") "native UUID formatting wrong";
        let before=fds() in
        List.iter (fun code -> mode code;
          for _=1 to 40 do expect_error protocol "file_observation.volume_attributes" (fun () -> F.observe fd) done)
          [4;5;6;7;11;12;13;14];
        mode 8;expect_error Unix.EACCES "file_observation.fgetattrlist" (fun () -> F.observe fd);
        mode 9;expect_error Unix.EIO "file_observation.fgetattrlist" (fun () -> F.observe fd);
        check (fds()=before && Unix.LargeFile.lseek fd 0L Unix.SEEK_CUR=43L)
          "attribute failures leaked handles or moved offset"));
    test "mutation during native filesystem query fails rather than returning mixed facts" (fun () ->
      with_fd (path "changed-during-query") (fun fd ->
        Fun.protect ~finally:(fun () -> mode 0) (fun () ->
          mode 10;
          expect_error Unix.EBUSY "file_observation.changed" (fun () -> F.observe fd);
          check ((Unix.LargeFile.fstat fd).Unix.LargeFile.st_size=1L) "fault seam did not mutate file"))));
  Printf.printf "FileObservation: %d disposable native-FD/parser tests passed\n%!" !count
