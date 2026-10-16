open WholeCommon
module Copy=CopyForTest
module N=Copy.WholeCloneForTest
module Fs=FsForTest
let directory=Sys.argv.(1)
let root=Fspath.canonize(Some directory)
let relative full=Path.fromString(Filename.basename full)
let reset ()=
  N.file_calls:=[];N.path_calls:=[];N.range_calls:=0;
  N.legacy_file_calls:=0;N.legacy_path_calls:=0;N.poison_legacy:=true;
  N.compatibility_open:=false;N.path_hook:=Fs.clone_path_status;
  Fault.configure "normal"(fun()->())
let copy f destination expected = Copy.copyByPath ~expected_length:expected
  root(relative f.source_path)root(relative destination)
let remainder prefix = Array.to_list(Sys.readdir directory)
  |>List.filter(fun name->String.starts_with ~prefix name)
let ()=
  let baseline=Fault.fd_count() in
  test "actual Copy named source publishes exactly one owned candidate"(fun()->
    reset();fixture directory ~length:4097(fun f->
      let destination=f.destination_path^"-candidate" in
      Fun.protect ~finally:(fun()->remove_owned destination)(fun()->
        check(copy f destination 4097L) "actual Copy declined native private APFS source";
        check(bytes destination=f.data &&List.length !(N.path_calls)=1 &&
              !(N.legacy_path_calls)=0) "Copy path bytes/strict routing differ";
        check(remainder(Filename.basename destination)=[Filename.basename destination])
          "successful Copy retained an intermediate stage")));
  test "Copy named wrong expected EOF never publishes candidate or falls back"(fun()->
    List.iter(fun expected->reset();fixture directory ~length:17(fun f->
      let destination=f.destination_path^"-candidate" in
      ignore(failed(fun()->ignore(copy f destination expected)));
      check(not(Sys.file_exists destination) &&
            remainder(Filename.basename destination)=[] &&List.length !(N.path_calls)=1)
        "wrong source EOF published a candidate or retained reservation"))
      [0L;16L;18L;Int64.max_int]);
  test "Copy path empty-source decline leaves normal exclusive empty creation"(fun()->
    reset();fixture directory ~length:0(fun f->
      let destination=f.destination_path^"-candidate" in
      Fun.protect ~finally:(fun()->remove_owned destination)(fun()->
        check(not(copy f destination 0L) &&not(Sys.file_exists destination))
          "empty path was falsely completed";
        let provenance=ref false in
        let output=Copy.openFileOut' ~clone_owned:provenance root(relative destination) `DATA Uutil.Filesize.zero in
        close_out output;
        check(!provenance &&bytes destination="") "ordinary empty exclusive creation lost ownership")));
  test "typed named decline and sharing contradictions fail after owned adoption"(fun()->
    List.iter(fun shared->reset();fixture directory(fun f->
      let destination=f.destination_path^"-typed" in
      N.path_hook:=(fun ~expected_length source output->
        if shared then match Fs.clone_path_status ~expected_length source output with
          |Fs.Created_path(receipt,witness,parent)->
              Fs.Created_path({receipt with WholeFileCloneForTest.completed=3L},witness,parent)
          |Fs.Declined_path _->failwith "private APFS typed-success control declined"
        else match N.W.platform_decline ~expected_length with
          |N.W.Declined(scope,receipt)->
              Fs.Declined_path(scope,{receipt with mutation=N.W.Indeterminate})
          |_->assert false);
      ignore(failed(fun()->ignore(copy f destination(Int64.of_int(String.length f.data)))));
      check(not(Sys.file_exists destination) &&remainder(Filename.basename destination)=[])
        "typed named inconsistency escaped caller guard or leaked adopted stage")) [false;true]);
  test "exclusive and O_TRUNC compatibility creation record distinct provenance"(fun()->
    List.iter(fun compatibility->reset();fixture directory ~length:17(fun f->
      let destination=f.destination_path^"-opened" in
      Fun.protect ~finally:(fun()->N.compatibility_open:=false;remove_owned destination)(fun()->
        N.compatibility_open:=compatibility;
        let provenance=ref true in
        let output=Copy.openFileOut' ~clone_owned:provenance root(relative destination) `DATA
          (Uutil.Filesize.ofInt 17) in
        Fun.protect ~finally:(fun()->close_out_noerr output)(fun()->
          check(!provenance=not compatibility) "compatibility O_TRUNC incorrectly granted private ownership";
          N.file_hook:=(fun ~expected_length _ _->
            if compatibility then raise Fault.primary else N.W.platform_decline ~expected_length);
          Copy.copyFile ~clone_owned:!provenance f.input output `DATA(Uutil.Filesize.ofInt 17)
            (fun remaining->Uutil.readWriteBounded f.input output remaining(fun _->()))(fun _->());
          flush output;
          check(bytes destination=f.data &&
                List.length !(N.file_calls)=(if compatibility then 0 else 1))
            "structural compatibility provenance did not suppress strict whole optimization")))) [false;true]);
  test "native adoption and post-rename exceptions retain owned cleanup until return"(fun()->
    List.iter(fun phase->reset();fixture directory(fun f->
      let destination=f.destination_path^"-candidate" in
      Fault.configure phase(fun()->());
      Fun.protect ~finally:(fun()->Fault.configure "normal"(fun()->());remove_owned destination)(fun()->
        let error=failed(fun()->ignore(copy f destination(Int64.of_int(String.length f.data)))) in
        check(error=Fault.primary && !(Fault.hits)=1) "Copy publication lost exact fault";
        check(not(Sys.file_exists destination) && remainder(Filename.basename destination)=[])
          "DESIGNATED Copy adoption/publication fault left owned stage/candidate")))
      ["copy-after-adopt";"copy-after-publish"]);
  test "actual nodump constraint falls back through ordinary owned DATA copying"(fun()->
    reset();fixture directory ~length:4097(fun f->
      let destination=f.destination_path^"-nodump-candidate" in
      Fun.protect ~finally:(fun()->Fault.nodump f.source_writer false;remove_owned destination)(fun()->
        Fault.nodump f.source_writer true;
        N.file_hook:=Fs.clone_file_status;
        Copy.copyContents root(relative f.source_path)root(relative destination)
          `DATA(Uutil.Filesize.ofInt 4097)None;
        check(bytes destination=f.data &&List.length !(N.path_calls)=1 &&
              List.length !(N.file_calls)=1 && !(N.range_calls)=1)
          "actual source constraint declined both named and ordinary macOS DATA incorrectly")));
  check(!(N.legacy_file_calls)=0 && !(N.legacy_path_calls)=0)
    "Copy path fixture reached poisoned legacy API";
  check(Fault.fd_count()=baseline) "actual Copy path fixture leaked descriptors";
  Printf.printf "Whole Copy named source: %d groups/%d assertions; actual APFS + owned synthetic compatibility\n%!"
    !groups !assertions
