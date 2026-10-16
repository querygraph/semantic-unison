open WholeCommon
module Fs = FsForTest
let directory=Sys.argv.(1)
let path value=Fspath.canonize(Some value)
let call f destination=Fs.clone_path_status
  ~expected_length:(Int64.of_int(String.length f.data))
  (path f.source_path)(path destination)
let private_failure error=match error with
  | Fault.Primary -> true
  | _ -> false
let ()=
  let initial=Fault.fd_count() in
  test "actual named C owner survives result/source-close/finish/transfer failures"(fun()->
    List.iter(fun (phase,held)->fixture directory ~length:4097(fun f->
      let destination=f.destination_path^"-settle" in
      let baseline=Fault.fd_count() in
      Fun.protect ~finally:(fun()->Fault.configure "normal"(fun()->());remove_owned destination)
        (fun()->
          Fault.configure phase(fun()->
            check(Fault.fd_count()=baseline+held)
              "actual named owner did not retain exact native/facade FD ownership";
            check(bytes destination=f.data) "fault did not occur after actual native creation";
            (match !(Fault.parent) with Some parent->
              check((Unix.fstat parent).Unix.st_kind=Unix.S_DIR) "creation parent closed before settlement"
             |None->failwith "private parent observer missing"));
          let error=failed(fun()->ignore(call f destination)) in
          check(private_failure error && !(Fault.hits)=1) "named facade lost exact primary error";
          check(not(Sys.file_exists destination) && Fault.fd_count()=baseline)
            "DESIGNATED created output/FDs escaped failed named handoff")))
      ["after-run",4;"after-peek",4;"after-result",4;"before-finish",3;
       "after-finish",2;"before-transfer",2;"after-transfer",2]);
  test "source-close failure never closes a subsequently reused descriptor integer"(fun()->
    fixture directory(fun f->
      let destination=f.destination_path^"-reuse" in
      let baseline=Fault.fd_count() and replacement=ref None in
      Fun.protect ~finally:(fun()->
        Fault.configure "normal"(fun()->());Option.iter Unix.close !replacement;
        remove_owned destination)(fun()->
        Fault.configure "after-source-close"(fun()->
          let fd=Unix.openfile f.live_path[Unix.O_RDONLY;Unix.O_CLOEXEC]0 in
          replacement:=Some fd;
          check(Some fd= !(Fault.source)) "fixture did not reuse source close integer";
          check(Fault.fd_count()=baseline+4) "reuse fault native ownership census differs");
        let error=failed(fun()->ignore(call f destination)) in
        check(error=Fault.primary && !(Fault.hits)=1) "close fault primary changed";
        (match !replacement with
         |Some fd->check((Unix.fstat fd).Unix.st_kind=Unix.S_REG &&
             Fault.fd_count()=baseline+1) "DESIGNATED cleanup closed reused source FD"
         |None->failwith "source reuse fixture not reached");
        check(not(Sys.file_exists destination)) "source-close failure left own clone")));
  test "real pending signal observes settled source before post-close failure"(fun()->
    fixture directory(fun f->
      let destination=f.destination_path^"-pending" in
      let baseline=Fault.fd_count() and observed=ref false and still_live=ref false in
      let previous=Sys.signal Sys.sigusr1(Sys.Signal_handle(fun _->
        observed:=true;
        (match !(Fault.source) with
         |Some source->still_live:=Fault.fd_is_open source
         |None->failwith "pending source ownership observer missing"))) in
      Fun.protect ~finally:(fun()->ignore(Sys.signal Sys.sigusr1 previous);
        Fault.configure "normal"(fun()->());remove_owned destination)(fun()->
        Fault.configure "pending-source-close"(fun()->());
        let error=failed(fun()->ignore(call f destination);Fault.pending_dispatch()) in
        check(not !still_live)
          "DESIGNATED pending exception escaped after disarming a live source FD";
        check(error=Fault.primary && !observed && !(Fault.hits)=1)
          "real queued signal was not delivered as the exact primary failure";
        check(not(Sys.file_exists destination) &&Fault.fd_count()=baseline)
          "actual pending exception escaped owned named cleanup")));
  test "real native-completion signal plus ordinary fault precedes raw receipt allocation"(fun()->
    fixture directory(fun f->
      let destination=f.destination_path^"-native-signal" in
      let baseline=Fault.fd_count() and observed=ref false in
      let previous=Sys.signal Sys.sigusr1(Sys.Signal_handle(fun _->
        observed:=true;
        check(bytes destination=f.data &&Fault.fd_count()=baseline+4)
          "signal did not observe actual created output and all retained C/facade FDs")) in
      Fun.protect ~finally:(fun()->Fault.native_mode 0;ignore(Sys.signal Sys.sigusr1 previous);
        Fault.configure "normal"(fun()->());remove_owned destination)(fun()->
        Fault.configure "normal"(fun()->());Fault.native_mode 1;
        let error=failed(fun()->ignore(call f destination)) in
        check(error=Fault.primary && !observed) "native receipt-boundary signal replaced primary";
        check(not(Sys.file_exists destination) &&Fault.fd_count()=baseline)
          "native pre-receipt interruption leaked created name/native FDs")));
  test "pre-admission open failure retains honest residual without deleting an unproved name"(fun()->
    fixture directory(fun f->
      let destination=f.destination_path^"-open-fault" in
      let baseline=Fault.fd_count() in
      Fun.protect ~finally:(fun()->Fault.native_mode 0;remove_owned destination)(fun()->
        Fault.native_mode 2;
        let error=failed(fun()->ignore(call f destination)) in
        check((match error with Fs.Clone_path_cleanup_failed failure->
          errno Unix.EIO failure.primary &&failure.residual=Fs.Unqualified_entry_may_remain
          |_->false)) "open-before-admission failure invented settled name authority";
        check(bytes destination=f.data &&Fault.fd_count()=baseline)
          "pre-admission failure removed unproved residue or leaked transient FDs")));
  test "backup acquisition failure closes admitted native output and owned name"(fun()->
    fixture directory(fun f->
      let destination=f.destination_path^"-backup-fault" in
      let baseline=Fault.fd_count() in
      Fun.protect ~finally:(fun()->Fault.native_mode 0;remove_owned destination)(fun()->
        Fault.native_mode 3;
        let error=failed(fun()->ignore(call f destination)) in
        check(errno Unix.EMFILE error) "backup acquisition error/context was replaced";
        check(not(Sys.file_exists destination) &&Fault.fd_count()=baseline)
          "admitted backup failure leaked native output/name")));
  test "name replacement is preserved and residual cleanup uncertainty is explicit"(fun()->
    fixture directory(fun f->
      let destination=f.destination_path^"-replaced" and displaced=f.destination_path^"-displaced" in
      let baseline=Fault.fd_count() in
      Fun.protect ~finally:(fun()->Fault.configure "normal"(fun()->());
        remove_owned destination;remove_owned displaced)(fun()->
        Fault.configure "after-run"(fun()->Unix.rename destination displaced;
          write destination "FOREIGN REPLACEMENT");
        let error=failed(fun()->ignore(call f destination)) in
        check((match error with Fs.Clone_path_cleanup_failed failure->
          failure.primary=Fault.primary && failure.cleanup_error<>None &&
          failure.residual=Fs.Unqualified_entry_may_remain|_->false))
          "mismatched name falsely reported settled ownership";
        check(bytes destination="FOREIGN REPLACEMENT" && bytes displaced=f.data &&
              Fault.fd_count()=baseline) "named failure unlinked foreign name or leaked FD")));
  test "actual creation parent remains authoritative after its pathname is rebound"(fun()->
    fixture directory(fun f->
      let current=f.destination_path^"-parent" and displaced=f.destination_path^"-old-parent" in
      Unix.mkdir current 0o700;
      let destination=Filename.concat current "stage" and oldstage=Filename.concat displaced "stage" in
      let baseline=Fault.fd_count() in
      Fun.protect ~finally:(fun()->Fault.configure "normal"(fun()->());
        List.iter remove_owned [destination;oldstage];Unix.rmdir current;
        if Sys.file_exists displaced then Unix.rmdir displaced)(fun()->
        Fault.configure "after-run"(fun()->Unix.rename current displaced;Unix.mkdir current 0o700;
          write destination "FOREIGN NEW PARENT");
        let error=failed(fun()->ignore(call f destination)) in
        check(error=Fault.primary) "held-parent cleanup did not retain primary error";
        check(not(Sys.file_exists oldstage) && bytes destination="FOREIGN NEW PARENT" &&
              Fault.fd_count()=baseline) "cleanup followed rebound parent instead of owned descriptor")));
  test "followed source name retargeted after native completion remains terminal"(fun()->
    fixture directory(fun f->
      let destination=f.destination_path^"-source-race" and link=f.source_path^"-bound-link"
      and alternate=f.source_path^"-alternate" in
      write alternate f.data;Unix.symlink f.source_path link;
      let baseline=Fault.fd_count() in
      Fun.protect ~finally:(fun()->Fault.configure "normal"(fun()->());
        List.iter remove_owned[destination;link;alternate])(fun()->
        Fault.configure "after-run-observe"(fun()->Unix.unlink link;Unix.symlink alternate link);
        let error=failed(fun()->ignore(Fs.clone_path_status
          ~expected_length:(Int64.of_int(String.length f.data))(path link)(path destination))) in
        check(errno Unix.EBUSY error && !(Fault.hits)=1) "source path rebind escaped post-native fence";
        check(not(Sys.file_exists destination) &&bytes alternate=f.data &&Fault.fd_count()=baseline)
          "source path failure left owned destination or changed foreign source")));
  check(Fault.fd_count()=initial) "named settlement leaked fixture FDs";
  Printf.printf "Whole named settlement: %d groups/%d assertions; actual APFS creation\n%!"
    !groups !assertions
