open WholeCommon
module W=WholeFileClone
let directory=Sys.argv.(1)
let path value=Fspath.canonize(Some value)
let created expected source destination body=
  match Fs.clone_path_status ~expected_length:expected (path source)(path destination) with
  | Fs.Created_path(receipt,output,parent)->
      Fun.protect ~finally:(fun()->Unix.close output;Unix.close parent)
        (fun()->body receipt output parent)
  | Fs.Declined_path _->failwith "actual private APFS named clone declined"
let require_failed body=
  match failed body with
  | Unix.Unix_error _->()
  | error->raise error
let ()=
  check(Fault.filesystem_type directory="apfs") "actual native fixture directory is not APFS";
  Printf.printf "Private native fixture filesystem: APFS (%s)\n%!" directory;
  let baseline=Fault.fd_count() in
  test "actual macOS FD absence preserves input/output bytes and cursors"(fun()->
    fixture directory(fun f->
      ignore(Unix.LargeFile.lseek f.source_fd 3L Unix.SEEK_SET);
      let result=Fs.clone_file_status ~expected_length:(Int64.of_int(String.length f.data))
        f.source_fd f.destination_fd in
      check((match result with W.Declined(W.Platform_unavailable,_)->true|_->false))
        "macOS existing-FD absence did not remain scoped decline";
      check(position f.source_fd=3L && position f.destination_fd=0L &&
            size f.destination_fd=0L && bytes f.destination_path="")
        "unavailable FD adapter mutated file/cursor"));
  test "zero regular distinct FD request is no-work without clone"(fun()->
    fixture directory ~length:0(fun f->
      check((match Fs.clone_file_status ~expected_length:0L f.source_fd f.destination_fd with
        W.No_work _->true|_->false)) "empty FD did not return no-work";
      check(position f.source_fd=0L && position f.destination_fd=0L &&size f.destination_fd=0L)
        "zero FD request mutated output"));
  test "expected EOF and signed Int64 extremes reject before effect"(fun()->
    List.iter(fun expected->fixture directory ~length:17(fun f->
      let result=Fs.clone_file_status ~expected_length:expected f.source_fd f.destination_fd in
      check((match result with W.Failed _->true|_->false)) "wrong source EOF received fallback authority";
      check(size f.destination_fd=0L && position f.destination_fd=0L && position f.source_fd=0L)
        "invalid request mutated output/cursor")) [0L;16L;18L;Int64.max_int]);
  test "negative expected request is rejected by Fs before native effect"(fun()->
    fixture directory(fun f->
      check((match failed(fun()->ignore(Fs.clone_file_status ~expected_length:(-1L)
        f.source_fd f.destination_fd))with Invalid_argument _->true|_->false))
        "negative expected length entered native operation";
      check(bytes f.destination_path="" &&position f.destination_fd=0L)
        "negative expected request mutated output"));
  test "native closed descriptors remain operational failures"(fun()->
    fixture directory(fun f->
      let closed=Unix.dup f.source_fd in Unix.close closed;
      let result=Fs.clone_file_status ~expected_length:(Int64.of_int(String.length f.data))
        closed f.destination_fd in
      check((match result with W.Failed _->true|_->false)) "closed source became unsupported";
      check(size f.destination_fd=0L) "closed descriptor changed output"));
  test "native aliases through separate descriptors reject before cloning"(fun()->
    fixture directory(fun f->
      let duplicate=Unix.dup f.source_writer in
      guarded_fd duplicate(fun()->
        check((match Fs.clone_file_status ~expected_length:(Int64.of_int(String.length f.data))
          f.source_fd duplicate with W.Failed _->true|_->false))
          "same inode received sharing or fallback authority")));
  test "native destination access/append/EOF/position preflight is terminal"(fun()->
    List.iter(fun kind->fixture directory(fun f->
      let extra=match kind with
        | "readonly"->Some(Unix.openfile f.destination_path[Unix.O_RDONLY;Unix.O_CLOEXEC]0)
        | "append"->Some(Unix.openfile f.destination_path[Unix.O_WRONLY;Unix.O_APPEND;Unix.O_CLOEXEC]0)
        | "nonempty"->Fault.write_at f.destination_fd 0L "KEEP";None
        | _->ignore(Unix.LargeFile.lseek f.destination_fd 3L Unix.SEEK_SET);None in
      Fun.protect ~finally:(fun()->Option.iter Unix.close extra)(fun()->
        let d=Option.value extra ~default:f.destination_fd in
        let before=bytes f.destination_path and cursor=position d in
        check((match Fs.clone_file_status ~expected_length:(Int64.of_int(String.length f.data))
          f.source_fd d with W.Failed _->true|_->false)) "invalid destination became scoped decline";
        check(bytes f.destination_path=before && position d=cursor)
          "preflight reset/truncated invalid output"))) ["readonly";"append";"nonempty";"shifted"]);
  test "native nonregular source/destination never receive fallback authority"(fun()->
    fixture directory(fun f->
      let input,output=Unix.pipe() in
      Fun.protect ~finally:(fun()->Unix.close input;Unix.close output)(fun()->
        List.iter(fun(s,d)->check((match Fs.clone_file_status ~expected_length:0L s d with
          W.Failed _->true|_->false)) "nonregular descriptor became unsupported")
          [input,f.destination_fd;f.source_fd,output])));
  test "actual APFS named creation transfers output and creation parent"(fun()->
    fixture directory(fun f->
      let destination=f.destination_path^"-named" in
      Fun.protect ~finally:(fun()->remove_owned destination)(fun()->
        let before=Fault.fd_count() in
        created (Int64.of_int(String.length f.data)) f.source_path destination(fun _ output parent->
          check(Fault.fd_count()=before+2 && bytes destination=f.data &&
                size output=Int64.of_int(String.length f.data) && position output=0L)
            "named witness bytes/EOF/position/FD accounting differ";
          let parent_stat=Unix.LargeFile.fstat parent and expected=Unix.LargeFile.stat directory in
          check(parent_stat.st_kind=Unix.S_DIR && parent_stat.st_dev=expected.st_dev &&
                parent_stat.st_ino=expected.st_ino) "native named result lost actual creation parent";
          let named=Unix.openfile destination[Unix.O_RDONLY;Unix.O_CLOEXEC]0 in
          guarded_fd named(fun()->check(same_object output named) "native witness differs from created name"));
        check(Fault.fd_count()=before) "named result leaked owned witness/parent")));
  test "named empty source declines absent, ordinary exclusive creation still required"(fun()->
    fixture directory ~length:0(fun f->
      let destination=f.destination_path^"-empty" in
      Fun.protect ~finally:(fun()->remove_owned destination)(fun()->
        check((match Fs.clone_path_status ~expected_length:0L(path f.source_path)(path destination) with
          Fs.Declined_path(W.Empty_source,_)->true|_->false)) "named zero falsely completed missing destination";
        check(not(Sys.file_exists destination)) "empty eligibility decline created a name";
        let output=Unix.openfile destination[Unix.O_WRONLY;Unix.O_CREAT;Unix.O_EXCL;Unix.O_CLOEXEC]0o600 in
        Unix.close output;check(bytes destination="") "ordinary zero-file creation failed")));
  test "actual named source symlink resolves regular DATA and preserves clone properties"(fun()->
    fixture directory(fun f->
      let link=f.source_path^"-source-link" and destination=f.destination_path^"-property" in
      Fault.set_xattr f.source_path "com.firstpair.wholeclone.fixture" "USER XATTR";
      Fault.set_xattr f.source_path "com.apple.ResourceFork" "OWN RESOURCE FORK";
      Unix.symlink f.source_path link;
      Fun.protect ~finally:(fun()->remove_owned link;remove_owned destination)(fun()->
        created (Int64.of_int(String.length f.data)) link destination(fun _ _ _->
          check((Unix.lstat destination).Unix.st_kind=Unix.S_REG &&bytes destination=f.data)
            "named adapter cloned symlink entry instead of approved resolved DATA";
          check((Unix.stat destination).Unix.st_perm=(Unix.stat f.source_path).Unix.st_perm &&
                Fault.get_xattr destination "com.firstpair.wholeclone.fixture"="USER XATTR" &&
                Fault.get_xattr destination "com.apple.ResourceFork"="OWN RESOURCE FORK")
            "named API silently substituted data-only metadata profile"))));
  test "named collision preserves preexisting file/symlink and reports failure"(fun()->
    List.iter(fun symbolic->fixture directory(fun f->
      let destination=f.destination_path^"-collision" in
      if symbolic then Unix.symlink f.live_path destination else write destination "FOREIGN NAME";
      Fun.protect ~finally:(fun()->remove_owned destination)(fun()->
        let before=Unix.lstat destination in
        require_failed(fun()->ignore(Fs.clone_path_status
          ~expected_length:(Int64.of_int(String.length f.data))(path f.source_path)(path destination)));
        let after=Unix.lstat destination in
        check(before.st_dev=after.st_dev &&before.st_ino=after.st_ino &&
              (if symbolic then Unix.readlink destination=f.live_path else bytes destination="FOREIGN NAME"))
          "failed named clone removed/replaced collision"))) [false;true]);
  test "named wrong EOF has no created name or owned FD leak"(fun()->
    List.iter(fun expected->fixture directory ~length:17(fun f->
      let destination=f.destination_path^"-wrong" in
      require_failed(fun()->ignore(Fs.clone_path_status ~expected_length:expected
        (path f.source_path)(path destination)));
      check(not(Sys.file_exists destination)) "stale expected EOF left admitted destination")) [0L;16L;18L;Int64.max_int]);
  test "actual nodump source has named constraints but macOS FD platform absence"(fun()->
    fixture directory(fun f->
      let destination=f.destination_path^"-nodump" in
      Fun.protect ~finally:(fun()->Fault.nodump f.source_writer false;remove_owned destination)(fun()->
        Fault.nodump f.source_writer true;
        check((match Fs.clone_file_status ~expected_length:(Int64.of_int(String.length f.data))
          f.source_fd f.destination_fd with W.Declined(W.Platform_unavailable,_)->true|_->false))
          "macOS FD platform absence was incorrectly constrained by source flags";
        check((match Fs.clone_path_status ~expected_length:(Int64.of_int(String.length f.data))
          (path f.source_path)(path destination) with Fs.Declined_path(W.Source_constraints,_)->true|_->false))
          "actual named nodump source did not remain precise constraint decline";
        check(not(Sys.file_exists destination) &&size f.destination_fd=0L)
          "source-constraint decline changed destination")));
  test "sized whole-source stage rejects EOF before destination reservation"(fun()->
    List.iter(fun expected->fixture directory ~length:17(fun f->
      let destination=f.destination_path^"-sized" in
      require_failed(fun()->ignore(Fs.clone_stage_handles_sized ~expected_length:expected
        (path f.source_path)(path destination)));
      check(not(Sys.file_exists destination)) "sized source mismatch reserved a stage"))
      [0L;16L;18L;Int64.max_int]);
  test "unsized receiver basis keeps independent target EOF reconstruction"(fun()->
    fixture directory ~length:17(fun f->
      let destination=f.destination_path^"-basis" in
      Fun.protect ~finally:(fun()->remove_owned destination)(fun()->
        match Fs.clone_stage_handles(path f.source_path)(path destination) with
        | Fs.Declined_stage_handles _->failwith "private APFS basis clone declined"
        | Fs.Shared_stage_handles(basis,output,parent)->
            Fun.protect ~finally:(fun()->List.iter Unix.close[basis;output;parent])(fun()->
              check(size basis=17L &&size output=17L) "unsized stage changed original basis EOF";
              Unix.LargeFile.ftruncate output 23L;Fault.write_at output 17L "TARGET";
              check(size basis=17L &&size output=23L &&bytes destination=f.data^"TARGET")
                "whole-source size rule was incorrectly imposed on basis reconstruction"))));
  test "legacy boolean APIs keep macOS FD absence and no-follow named semantics"(fun()->
    fixture directory(fun f->
      check(not(Fs.clone_file f.source_fd f.destination_fd) &&
            not(Fs.clone_file Unix.stdin Unix.stdout) &&size f.destination_fd=0L)
        "legacy macOS FD ABI behavior changed";
      let link=f.source_path^"-legacy-link" and destination=f.destination_path^"-legacy" in
      Unix.symlink f.source_path link;
      Fun.protect ~finally:(fun()->remove_owned link;remove_owned destination)(fun()->
        check(Fs.clone_path(path link)(path destination)) "legacy source-symlink clone changed";
        check((Unix.lstat destination).Unix.st_kind=Unix.S_LNK &&
              Unix.readlink destination=f.source_path) "legacy CLONE_NOFOLLOW profile changed")));
  check(Fault.fd_count()=baseline) "actual whole native fixture leaked descriptors";
  Printf.printf "Whole native macOS: %d groups/%d assertions; private APFS only\n%!" !groups !assertions
