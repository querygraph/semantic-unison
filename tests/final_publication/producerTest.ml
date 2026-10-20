module P = struct
  include FinalPublication
  let publish context =
    if Array.exists ((=) "--timed") Sys.argv then ignore(FinalPublication.publish_timed context)
    else FinalPublication.publish context
end
open Test
let with_async_exns f = f ()
external duplicate_fault : int -> unit = "final_publication_fixture_duplicate_fault"
external regular_signal : int -> unit = "final_publication_fixture_regular_signal"
external toggle_flag : Unix.file_descr -> unit = "final_publication_fixture_toggle_directory_flag"

let with_output ?(flags=[Unix.O_RDWR; Unix.O_CLOEXEC]) c f =
  let descriptor = Unix.openfile c.candidate flags 0 in
  Fun.protect ~finally:(fun () ->
    duplicate_fault 0; regular_signal 0;
    (try Unix.close descriptor with Unix.Unix_error (Unix.EBADF, _, _) -> ()))
    (fun () -> f descriptor)
let producing c descriptor =
  let context = prepare c in P.adopt_mutable context ~candidate:descriptor; context
let frozen c descriptor =
  let context = producing c descriptor in P.freeze_producer context; context
let publish_frozen context = P.observe_target context; P.publish context; P.check_published context
let reject_adoption context descriptor =
  match P.adopt_mutable context ~candidate:descriptor with
  | () -> failwith "wrong producer descriptor admitted"
  | exception Unix.Unix_error (_, phase, _) -> check (phase <> "") "producer error lost phase"
let expect_unavailable_error context f =
  let error = try f (); failwith "producer identity error accepted"
    with Unix.Unix_error (_, _, _) as error -> error in
  check (not (P.preparation_unavailable error)) "producer failure permits fallback";
  check (not (P.producer_finalized context)) "failed producer became finalized"

let () =
  if not (P.available ()) then exit 77;
  let directory = Sys.argv.(1) in
  let prior = !count in
  test directory "producer original descriptor survives close then commits" (fun c ->
    with_output c (fun descriptor ->
      let context = producing c descriptor in
      check (P.producer_origin context = P.Producer_descriptor) "actual output origin mislabeled";
      check (not (P.producer_finalized context)) "mutable producer already finalized";
      P.check_producer context;
      Unix.close descriptor;
      P.check_producer context; P.freeze_producer context;
      check (P.producer_finalized context) "producer freezing receipt absent";
      P.check_candidate context; publish_frozen context;
      P.release context;
      check (P.producer_finalized context && P.published context) "closed producer receipts lost";
      check (read_file c.target = payload) "producer bytes lost"));
  test directory "same-byte replacement before producer adoption" (fun c ->
    with_output c (fun descriptor ->
      let context = prepare c in
      let original = c.candidate ^ ".actual-producer" in Unix.rename c.candidate original;
      write_file c.candidate payload;
      reject_adoption context descriptor;
      check (P.producer_origin context = P.No_origin) "failed descriptor admission acquired origin";
      check (read_file c.candidate = payload && read_file original = payload) "failed adoption changed unproven names";
      ignore (Unix.fstat descriptor);
      P.close_noerr context;
      check (read_file c.candidate = payload) "failed adoption cleaned replacement"));
  test directory "same-byte unrelated descriptor rejected and borrowed fd retained" (fun c ->
    let other = Filename.concat c.top "other-output" in write_file other payload;
    let descriptor = Unix.openfile other [Unix.O_RDWR; Unix.O_CLOEXEC] 0 in
    Fun.protect ~finally:(fun () -> Unix.close descriptor) (fun () ->
      let before = native_fd_count () in let context = prepare c in
      reject_adoption context descriptor;
      check (native_fd_count () = before) "failed first adoption proof fds leaked";
      ignore (Unix.fstat descriptor);
      check (read_file c.candidate = payload && read_file other = payload) "wrong producer adoption deleted files";
      expect_unix Unix.EINVAL (fun () -> P.attach context)));
  test directory "producer same bytes replacement after adoption rejects and preserves live" (fun c ->
    write_file c.target sentinel;
    with_output c (fun descriptor ->
      let context = producing c descriptor in
      Unix.rename c.candidate (c.candidate ^ ".owned"); write_file c.candidate payload;
      expect_unix Unix.EBUSY (fun () -> P.check_producer context);
      expect_unix Unix.EBUSY (fun () -> P.freeze_producer context);
      expect_unix Unix.EBUSY (fun () -> P.abort_and_close context);
      check (not (P.producer_finalized context) && read_file c.target = sentinel && read_file c.candidate = payload)
        "replaced producer granted ownership"));
  test directory "producer mutable planned sizes modes ownership times flags pass" (fun c ->
    with_output c (fun descriptor ->
      let context = producing c descriptor in
      Unix.LargeFile.ftruncate descriptor 0L; P.check_producer context;
      ignore (Unix.write_substring descriptor payload 0 (String.length payload));
      Unix.chmod c.candidate 0o640;
      Unix.chown c.candidate (Unix.getuid ()) (Unix.getgid ());
      Unix.utimes c.candidate 1234567000.125 1234567890.875;
      toggle_flag descriptor;
      P.check_producer context; P.freeze_producer context; P.check_candidate context;
      publish_frozen context;
      check ((Unix.stat c.target).Unix.st_perm = 0o640 && read_file c.target = payload) "planned properties/bytes lost"));
  List.iter (fun resource -> test directory
    (if resource then "producer planned native resource fork passes" else "producer planned native xattr passes")
    (fun c -> with_output c (fun descriptor ->
      let context = producing c descriptor in
      attribute_write c.candidate sentinel resource;
      P.check_producer context; P.freeze_producer context; publish_frozen context;
      check (attribute_read c.target resource = sentinel) "producer native attribute lost"))) [false;true];
  test directory "producer AppleDouble can select explicit legacy before freeze" (fun c ->
    with_output c (fun descriptor ->
      let context = producing c descriptor in
      let sidecar = Filename.concat c.incoming "._candidate" in write_file sidecar sentinel;
      P.check_producer context;
      check (not (P.auxiliary_absent context)) "producer family addition not detected";
      expect_unix Unix.EOPNOTSUPP (fun () -> P.freeze_producer context);
      check (not (P.producer_finalized context)) "sidecar producer finalized";
      P.release context;
      check (read_file c.candidate = payload && read_file sidecar = sentinel) "explicit family handoff deleted objects"));
  List.iter (fun change -> test directory ("producer post-freeze mutation " ^ change)
    (fun c -> with_output c (fun descriptor ->
      write_file c.target sentinel;
      let context = frozen c descriptor in P.observe_target context;
      (match change with
       | "data" -> mutate c.candidate
       | "mode" -> Unix.chmod c.candidate 0o640
       | "time" -> Unix.utimes c.candidate 1000. 2000.
       | "flag" -> toggle_flag descriptor
       | "xattr" -> attribute_write c.candidate sentinel false
       | "resource" -> attribute_write c.candidate sentinel true
       | _ -> assert false);
      expect_unix Unix.EBUSY (fun () -> P.check_candidate context);
      expect_unix Unix.EBUSY (fun () -> P.publish context);
      check (not (P.published context) && read_file c.target = sentinel) "late producer mutation reached live")))
    ["data";"mode";"time";"flag";"xattr";"resource"];
  test directory "producer freeze is single-use and named attach cannot replace it" (fun c ->
    with_output c (fun descriptor ->
      let context = producing c descriptor in
      expect_unix Unix.EINVAL (fun () -> P.attach context);
      expect_unix Unix.EINVAL (fun () -> P.adopt_mutable context ~candidate:descriptor);
      P.check_producer context; P.freeze_producer context;
      expect_unix Unix.EINVAL (fun () -> P.freeze_producer context);
      expect_unix Unix.EINVAL (fun () -> P.check_producer context);
      expect_unix Unix.EINVAL (fun () -> P.attach context);
      expect_unix Unix.EINVAL (fun () -> P.adopt_mutable context ~candidate:descriptor);
      P.check_candidate context; publish_frozen context));
  test directory "legacy named attachment never grants producer receipt" (fun c ->
    let context = attached c in
    check (P.producer_origin context = P.No_origin) "legacy attachment labeled producer origin";
    check (not (P.producer_finalized context)) "legacy attach became producer";
    expect_unix Unix.EINVAL (fun () -> P.freeze_producer context);
    P.observe_target context; P.publish context; P.release context;
    check (not (P.producer_finalized context)) "legacy publication became producer");
  test directory "producer commit and target observe before freeze fail" (fun c ->
    with_output c (fun descriptor ->
      let context = producing c descriptor in
      expect_unix Unix.EINVAL (fun () -> P.observe_target context);
      expect_unix Unix.EINVAL (fun () -> P.publish context);
      expect_unix Unix.EINVAL (fun () -> P.check_candidate context);
      check (not (P.published context)) "mutable producer published";
      P.freeze_producer context; publish_frozen context));
  test directory "producer abort owns partial writes but preserves borrowed fd" (fun c ->
    with_output c (fun descriptor ->
      let context = producing c descriptor in
      Unix.LargeFile.ftruncate descriptor 17L; P.check_producer context;
      P.abort_and_close context; ignore (Unix.fstat descriptor);
      check (not (exists c.candidate)) "partial producer retained after abort"));
  test directory "producer quarantine owns partial writes" (fun c ->
    with_output c (fun descriptor ->
      let context = producing c descriptor in
      Unix.LargeFile.ftruncate descriptor 17L;
      P.quarantine_and_close context ~name:"producer-rejected";
      ignore (Unix.fstat descriptor);
      check (not (exists c.candidate) && not (exists (Filename.concat c.incoming "producer-rejected"))) "partial producer quarantine failed"));
  test directory "producer quarantine unlink failure isolates partial normal name" (fun c ->
    with_output c (fun descriptor ->
      let context = producing c descriptor in Unix.LargeFile.ftruncate descriptor 17L;
      unlink_fault 1;
      expect_unix Unix.EPERM (fun () -> P.quarantine_and_close context ~name:"producer-rejected");
      unlink_fault 0;
      check (not (exists c.candidate) && (Unix.stat (Filename.concat c.incoming "producer-rejected")).Unix.st_size = 17) "partial quarantine isolation lost"));
  test directory "producer quarantine foreign replacement preserved" (fun c ->
    with_output c (fun descriptor ->
      let context = producing c descriptor in
      Unix.rename c.candidate (c.candidate ^ ".owned"); write_file c.candidate sentinel;
      expect_unix Unix.EBUSY (fun () -> P.quarantine_and_close context ~name:"producer-rejected");
      check (read_file c.candidate = sentinel) "producer foreign replacement quarantined"));
  List.iter (fun (name, selected) -> test directory ("producer mutable " ^ name ^ " rebind")
    (fun c -> with_output c (fun descriptor ->
      let context = producing c descriptor in let original = selected c in
      Unix.rename original (original ^ ".held"); Unix.mkdir original 0o700;
      expect_unix Unix.EBUSY (fun () -> P.check_producer context);
      expect_unix Unix.EBUSY (fun () -> P.freeze_producer context);
      P.abort_and_close context)))
    ["logical root",(fun c -> c.root);"working directory",(fun c -> c.work);
     "candidate parent",(fun c -> c.incoming);"target parent",(fun c -> c.outgoing)];
  test directory "producer descriptor admits promoted different-parent object" (fun c ->
    let staging = Filename.concat c.top "actual-stage-parent" in Unix.mkdir staging 0o700;
    let stage = Filename.concat staging "stage" in
    Unix.rename c.candidate stage;
    let descriptor = Unix.openfile stage [Unix.O_RDWR; Unix.O_CLOEXEC] 0 in
    Fun.protect ~finally:(fun () -> Unix.close descriptor) (fun () ->
      let context = prepare c in
      Unix.rename stage c.candidate;
      P.adopt_mutable context ~candidate:descriptor;
      P.check_producer context; P.freeze_producer context; publish_frozen context;
      check (read_file c.target = payload) "different-parent promotion rejected"));
  test directory "producer descriptor position unchanged and owned duplicate CLOEXEC" (fun c ->
    with_output c (fun descriptor ->
      ignore (Unix.LargeFile.lseek descriptor 37L Unix.SEEK_SET);
      let before = open_fds () in let context = producing c descriptor in
      let owned = new_fds before in
      check (List.length owned = 5) "producer proof ownership count";
      List.iter (fun fd -> check (fd_state fd = 1) "producer proof fd lacks CLOEXEC") owned;
      P.check_producer context; P.freeze_producer context;
      check (Unix.LargeFile.lseek descriptor 0L Unix.SEEK_CUR = 37L) "producer observer changed offset";
      P.release context; check_closed owned; ignore (Unix.fstat descriptor)));
  test directory "producer original descriptor integer reuse cannot change witness" (fun c ->
    with_output c (fun descriptor ->
      let context = producing c descriptor in let original_number = fd_number descriptor in
      Unix.close descriptor;
      let other = Filename.concat c.top "unrelated" in write_file other sentinel;
      let fresh = Unix.openfile other [Unix.O_RDONLY; Unix.O_CLOEXEC] 0 in
      Fun.protect ~finally:(fun () -> Unix.close fresh) (fun () ->
        check (fd_number fresh = original_number) "fixture original fd not reused";
        P.check_producer context; P.freeze_producer context; publish_frozen context;
        P.release context; ignore (Unix.fstat fresh);
        check (read_file other = sentinel) "reused foreign fd changed")));
  test directory "producer write-only actual output descriptor is accepted" (fun c ->
    with_output ~flags:[Unix.O_WRONLY; Unix.O_CLOEXEC] c (fun descriptor ->
      let context = producing c descriptor in P.check_producer context;
      P.freeze_producer context; publish_frozen context));
  test directory "resumed read-only producer binds actual append writer" (fun c ->
    with_output ~flags:[Unix.O_RDONLY; Unix.O_CLOEXEC] c (fun descriptor ->
      let context = producing c descriptor in
      let writer = Unix.openfile c.candidate [Unix.O_WRONLY; Unix.O_APPEND; Unix.O_CLOEXEC] 0 in
      Fun.protect ~finally:(fun () -> Unix.close writer) (fun () ->
        ignore (Unix.LargeFile.lseek writer 17L Unix.SEEK_SET);
        P.check_producer_fd context ~candidate:writer;
        check (Unix.LargeFile.lseek writer 0L Unix.SEEK_CUR = 17L) "append writer matcher changed offset";
        ignore (Unix.write_substring writer sentinel 0 (String.length sentinel));
        P.check_producer_fd context ~candidate:writer;
        P.freeze_producer context; publish_frozen context;
        check (read_file c.target = payload ^ sentinel) "qualified resume append bytes differ")));
  test directory "resumed producer wrong identical-byte writer rejected" (fun c ->
    with_output ~flags:[Unix.O_RDONLY; Unix.O_CLOEXEC] c (fun descriptor ->
      let context = producing c descriptor in
      let other = Filename.concat c.top "wrong-append" in write_file other payload;
      let writer = Unix.openfile other [Unix.O_WRONLY; Unix.O_APPEND; Unix.O_CLOEXEC] 0 in
      Fun.protect ~finally:(fun () -> Unix.close writer) (fun () ->
        expect_unix Unix.EBUSY (fun () -> P.check_producer_fd context ~candidate:writer);
        ignore (Unix.fstat writer);
        check (read_file c.candidate = payload && read_file other = payload) "wrong append matcher wrote or removed objects";
        P.check_producer context)));
  test directory "resumed producer replacement append writer cannot refresh origin" (fun c ->
    with_output ~flags:[Unix.O_RDONLY; Unix.O_CLOEXEC] c (fun descriptor ->
      let context = producing c descriptor in
      Unix.rename c.candidate (c.candidate ^ ".original"); write_file c.candidate payload;
      let writer = Unix.openfile c.candidate [Unix.O_WRONLY; Unix.O_APPEND; Unix.O_CLOEXEC] 0 in
      Fun.protect ~finally:(fun () -> Unix.close writer) (fun () ->
        expect_unix Unix.EBUSY (fun () -> P.check_producer_fd context ~candidate:writer);
        expect_unix Unix.EBUSY (fun () -> P.abort_and_close context);
        check (read_file c.candidate = payload) "replacement append candidate removed")));
  test directory "producer writer matcher only admits mutable phase" (fun c ->
    with_output c (fun descriptor ->
      let context = prepare c in
      expect_unix Unix.EINVAL (fun () -> P.check_producer_fd context ~candidate:descriptor);
      P.adopt_mutable context ~candidate:descriptor;
      P.check_producer_fd context ~candidate:descriptor;
      P.freeze_producer context;
      expect_unix Unix.EINVAL (fun () -> P.check_producer_fd context ~candidate:descriptor);
      P.release context;
      expect_unix Unix.EINVAL (fun () -> P.check_producer_fd context ~candidate:descriptor)));
  test directory "producer writer matcher rejects late hardlink privacy" (fun c ->
    with_output c (fun descriptor ->
      let context = producing c descriptor in Unix.link c.candidate (c.candidate ^ ".alias");
      expect_unix Unix.EBUSY (fun () -> P.check_producer_fd context ~candidate:descriptor);
      ignore (Unix.fstat descriptor)));
  test directory "producer writer closed and reused FD cannot substitute origin" (fun c ->
    with_output c (fun descriptor ->
      let context = producing c descriptor in
      let writer = Unix.openfile c.candidate [Unix.O_WRONLY; Unix.O_APPEND; Unix.O_CLOEXEC] 0 in
      Unix.close writer;
      expect_unix Unix.EBADF (fun () -> P.check_producer_fd context ~candidate:writer);
      let other = Filename.concat c.top "reused-append" in write_file other payload;
      let replacement = Unix.openfile other [Unix.O_WRONLY; Unix.O_APPEND; Unix.O_CLOEXEC] 0 in
      Fun.protect ~finally:(fun () -> Unix.close replacement) (fun () ->
        check (fd_number replacement = fd_number writer) "append writer descriptor not reused";
        expect_unix Unix.EBUSY (fun () -> P.check_producer_fd context ~candidate:writer);
        ignore (Unix.fstat replacement); P.check_producer context)));
  test directory "producer duplicate failure closes proofs and preserves original" (fun c ->
    with_output c (fun descriptor ->
      let before = native_fd_count () in let context = prepare c in duplicate_fault 1;
      expect_unix Unix.EMFILE (fun () -> P.adopt_mutable context ~candidate:descriptor);
      duplicate_fault 0;
      check (native_fd_count () = before) "duplicate failure retained proof handles";
      ignore (Unix.fstat descriptor); check (exists c.candidate) "duplicate failure deleted normal name"));
  test directory "producer adoption owns original object before pending exception" (fun c ->
    with_output c (fun descriptor ->
      let context = prepare c in
      let old = Sys.signal Sys.sigusr1 (Sys.Signal_handle (fun _ -> raise Sys.Break)) in
      Fun.protect ~finally:(fun () -> duplicate_fault 0; ignore (Sys.signal Sys.sigusr1 old))
        (fun () -> duplicate_fault 2; let interrupted = ref false in
          (try with_async_exns (fun () -> P.adopt_mutable context ~candidate:descriptor)
           with Sys.Break -> interrupted := true);
          duplicate_fault 0;
          (try with_async_exns dispatch_pending with Sys.Break -> interrupted := true);
          check !interrupted "adoption pending exception was not delivered";
          P.check_producer context; ignore (Unix.fstat descriptor);
          P.abort_and_close context;
          check (not (exists c.candidate)) "pending adoption lost owned candidate")));
  test directory "producer freeze records origin before pending exception" (fun c ->
    with_output c (fun descriptor ->
      let context = producing c descriptor in
      let old = Sys.signal Sys.sigusr1 (Sys.Signal_handle (fun _ -> raise Sys.Break)) in
      Fun.protect ~finally:(fun () -> regular_signal 0; ignore (Sys.signal Sys.sigusr1 old))
        (fun () -> regular_signal 5; let interrupted = ref false in
          (try with_async_exns (fun () -> P.freeze_producer context) with Sys.Break -> interrupted := true);
          regular_signal 0;
          (try with_async_exns dispatch_pending with Sys.Break -> interrupted := true);
          check !interrupted "freeze pending exception was not delivered";
          check (P.producer_finalized context) "native freeze receipt lost to pending exception";
          P.check_candidate context;
          P.abort_and_close context; check (not (exists c.candidate)) "pending freeze lost owned candidate")));
  test directory "producer closed borrowed fd never becomes a named attachment" (fun c ->
    with_output c (fun descriptor ->
      let context = prepare c in Unix.close descriptor;
      expect_unix Unix.EBADF (fun () -> P.adopt_mutable context ~candidate:descriptor);
      check (exists c.candidate) "closed producer fd path fallback removed candidate"));
  test directory "producer preexisting hardlink privacy rejected before ownership" (fun c ->
    with_output c (fun descriptor ->
      Unix.link c.candidate (c.candidate ^ ".alias"); let context = prepare c in
      expect_unix Unix.EBUSY (fun () -> P.adopt_mutable context ~candidate:descriptor);
      check (exists c.candidate) "unadmitted linked producer removed"));
  test directory "producer late hardlink privacy rejected with alias preserved" (fun c ->
    with_output c (fun descriptor ->
      let context = producing c descriptor in let alias = c.candidate ^ ".alias" in
      Unix.link c.candidate alias;
      expect_unix Unix.EBUSY (fun () -> P.check_producer context);
      expect_unix Unix.EBUSY (fun () -> P.freeze_producer context);
      P.abort_and_close context; check (read_file alias = payload) "late foreign alias removed"));
  test directory "producer final-component symlink cannot replace original" (fun c ->
    with_output c (fun descriptor ->
      let context = prepare c in let actual = c.candidate ^ ".actual" in
      Unix.rename c.candidate actual; Unix.symlink actual c.candidate;
      expect_unix Unix.EBUSY (fun () -> P.adopt_mutable context ~candidate:descriptor);
      check ((Unix.lstat c.candidate).Unix.st_kind = Unix.S_LNK) "unadmitted symlink removed"));
  test directory "producer nonregular descriptor rejected without closing borrowed" (fun c ->
    let descriptor = Unix.openfile c.incoming [Unix.O_RDONLY; Unix.O_CLOEXEC] 0 in
    Fun.protect ~finally:(fun () -> Unix.close descriptor) (fun () ->
      let context = prepare c in
      expect_unix Unix.EBUSY (fun () -> P.adopt_mutable context ~candidate:descriptor);
      ignore (Unix.fstat descriptor); check (exists c.candidate) "nonregular admission deleted named candidate"));
  test directory "producer high inode disagreement with matching low bits rejected" (fun c ->
    with_output c (fun descriptor ->
      let context = prepare c in identity_fault 1 3;
      expect_unix Unix.EBUSY (fun () -> P.adopt_mutable context ~candidate:descriptor);
      identity_fault 1 0; check (exists c.candidate) "high-bit mismatch cleaned unadmitted object"));
  test directory "producer sibling changes and equivalent aliases allowed" (fun c ->
    with_output c (fun descriptor ->
      let context = producing c descriptor in
      List.iter (fun d -> write_file (Filename.concat d "sibling") sentinel)
        [c.root;c.work;c.incoming;c.outgoing];
      let alias = Filename.concat c.top "equivalent" in Unix.symlink c.work alias;
      Unix.symlink c.outgoing (Filename.concat c.work "out-alias");
      P.recheck_resolution context ~working_dir:alias ~target:"out-alias/target";
      P.check_producer context; P.freeze_producer context; publish_frozen context));
  List.iter (fun mode -> test directory ("producer adoption volume error " ^ string_of_int mode)
    (fun c -> with_output c (fun descriptor ->
      let context = prepare c in attribute_fault mode 9;
      expect_unavailable_error context (fun () -> P.adopt_mutable context ~candidate:descriptor);
      attribute_fault 0 0;
      check (exists c.candidate) "volume adoption failure removed unadmitted object"))) [1;3;6;12];
  List.iter (fun mode -> test directory ("producer mutable volume error " ^ string_of_int mode)
    (fun c -> with_output c (fun descriptor ->
      let context = producing c descriptor in attribute_fault mode 9;
      expect_unavailable_error context (fun () -> P.check_producer context);
      attribute_fault 0 0; P.abort_and_close context))) [1;3;6;12];
  test directory "producer freeze root rebind retains foreign candidate" (fun c ->
    with_output c (fun descriptor ->
      let context = producing c descriptor in Unix.rename c.incoming (c.incoming ^ ".held");
      Unix.mkdir c.incoming 0o700; write_file c.candidate sentinel;
      expect_unix Unix.EBUSY (fun () -> P.freeze_producer context);
      P.abort_and_close context; check (read_file c.candidate = sentinel) "freeze rebind cleanup removed foreign candidate"));
  test directory "producer finalized then same-byte reopen gap rejected" (fun c ->
    write_file c.target sentinel;
    with_output c (fun descriptor ->
      let context = frozen c descriptor in Unix.close descriptor;
      Unix.rename c.candidate (c.candidate ^ ".owned"); write_file c.candidate payload;
      expect_unix Unix.EBUSY (fun () -> P.check_candidate context);
      expect_unix Unix.EBUSY (fun () -> P.observe_target context);
      expect_unix Unix.EINVAL (fun () -> P.attach context);
      expect_unix Unix.EINVAL (fun () -> P.freeze_producer context);
      expect_unix Unix.EBUSY (fun () -> P.abort_and_close context);
      check (read_file c.target = sentinel && read_file c.candidate = payload) "finalized replacement reached live"));
  test directory "native resume existing complete candidate has honest origin" (fun c ->
    let context = prepare c in
    check (P.producer_origin context = P.No_origin) "unadmitted candidate has origin";
    P.adopt_resume context;
    check (P.producer_origin context = P.Admitted_resume && not (P.producer_finalized context)) "resume origin/phase mislabeled";
    P.check_producer context; check (read_file c.candidate = payload) "resume bytes differ";
    P.check_producer context; P.freeze_producer context; publish_frozen context;
    P.release context;
    check (P.producer_origin context = P.Admitted_resume && P.producer_finalized context) "closed resume receipt lost");
  test directory "native resume fences prefix read and actual append writer" (fun c ->
    let context = prepare c in P.adopt_resume context;
    let reader = Unix.openfile c.candidate [Unix.O_RDONLY; Unix.O_CLOEXEC] 0 in
    Fun.protect ~finally:(fun () -> Unix.close reader) (fun () ->
      P.check_producer_fd context ~candidate:reader;
      let bytes = Bytes.create 63 in
      check (Unix.read reader bytes 0 63 = 63 && Bytes.to_string bytes = String.sub payload 0 63) "prefix read mismatched admitted resume";
      P.check_producer_fd context ~candidate:reader;
      let writer = Unix.openfile c.candidate [Unix.O_WRONLY; Unix.O_APPEND; Unix.O_CLOEXEC] 0 in
      Fun.protect ~finally:(fun () -> Unix.close writer) (fun () ->
        P.check_producer_fd context ~candidate:writer;
        ignore (Unix.write_substring writer sentinel 0 (String.length sentinel));
        P.check_producer context; P.freeze_producer context; publish_frozen context;
        check (read_file c.target = payload ^ sentinel) "native resumed append differs")));
  test directory "native resume missing name fails without new-output fallback" (fun c ->
    let context = prepare c in Unix.unlink c.candidate;
    expect_unix Unix.ENOENT (fun () -> P.adopt_resume context);
    check (P.producer_origin context = P.No_origin) "failed missing resume acquired origin";
    write_file c.candidate payload;
    expect_unix Unix.EINVAL (fun () -> P.adopt_resume context);
    check (read_file c.candidate = payload) "failed resume reused name for ownership");
  test directory "native resume final symlink never followed or removed" (fun c ->
    let actual = c.candidate ^ ".foreign" in Unix.rename c.candidate actual;
    Unix.symlink actual c.candidate; let context = prepare c in
    expect_unix Unix.ELOOP (fun () -> P.adopt_resume context);
    P.close_noerr context;
    check ((Unix.lstat c.candidate).Unix.st_kind = Unix.S_LNK && read_file actual = payload) "native resume followed/deleted foreign symlink");
  test directory "native resume FIFO cannot block or become owned" (fun c ->
    Unix.unlink c.candidate; Unix.mkfifo c.candidate 0o600;
    let context = prepare c in expect_unix Unix.EBUSY (fun () -> P.adopt_resume context);
    check ((Unix.lstat c.candidate).Unix.st_kind = Unix.S_FIFO) "native resume removed unproven FIFO");
  test directory "native resume preexisting hardlink cannot become private" (fun c ->
    Unix.link c.candidate (c.candidate ^ ".alias"); let context = prepare c in
    expect_unix Unix.EBUSY (fun () -> P.adopt_resume context);
    check (exists c.candidate) "native resume removed unadmitted linked file");
  test directory "native resume parent rebound preserves foreign normal name" (fun c ->
    let context = prepare c in Unix.rename c.incoming (c.incoming ^ ".held");
    Unix.mkdir c.incoming 0o700; write_file c.candidate sentinel;
    expect_unix Unix.EBUSY (fun () -> P.adopt_resume context);
    check (read_file c.candidate = sentinel && read_file (Filename.concat (c.incoming ^ ".held") "candidate") = payload) "failed resume bound wrong parent");
  test directory "native resume logical root rebind fails before ownership" (fun c ->
    let context = prepare c in Unix.rename c.root (c.root ^ ".held"); Unix.mkdir c.root 0o700;
    expect_unix Unix.EBUSY (fun () -> P.adopt_resume context);
    check (exists c.candidate && P.producer_origin context = P.No_origin) "rebound resume root admitted object");
  test directory "native resume replacement after prefix read rejected without foreign cleanup" (fun c ->
    let context = prepare c in P.adopt_resume context;
    check (read_file c.candidate = payload) "prefix verification fixture failed"; P.check_producer context;
    Unix.rename c.candidate (c.candidate ^ ".admitted"); write_file c.candidate payload;
    expect_unix Unix.EBUSY (fun () -> P.check_producer context);
    expect_unix Unix.EBUSY (fun () -> P.freeze_producer context);
    expect_unix Unix.EBUSY (fun () -> P.abort_and_close context);
    check (read_file c.candidate = payload) "replaced resume candidate removed");
  test directory "native resume does not refresh descriptor-origin or frozen proof" (fun c ->
    with_output c (fun descriptor ->
      let context = producing c descriptor in
      expect_unix Unix.EINVAL (fun () -> P.adopt_resume context);
      check (P.producer_origin context = P.Producer_descriptor) "resume overwrote actual output origin";
      P.freeze_producer context;
      expect_unix Unix.EINVAL (fun () -> P.adopt_resume context);
      P.check_candidate context; P.release context;
      check (P.producer_origin context = P.Producer_descriptor) "closed actual output relabeled resume"));
  test directory "native resume read-only proof fds CLOEXEC close without deletion" (fun c ->
    let before = open_fds () in let context = prepare c in P.adopt_resume context;
    let owned = new_fds before in check (List.length owned = 5) "resume descriptor ownership count";
    List.iter (fun fd -> check (fd_state fd = 1) "resume proof fd missing CLOEXEC") owned;
    P.release context; check_closed owned;
    check (read_file c.candidate = payload && P.producer_origin context = P.Admitted_resume) "resume release deleted name/origin");
  test directory "prepared legacy handoff checks only captured namespace" (fun c ->
    let context = prepare c in write_file (Filename.concat c.incoming "._candidate") sentinel;
    P.check_handoff context;
    Unix.rename c.root (c.root ^ ".held"); Unix.mkdir c.root 0o700;
    expect_unix Unix.EBUSY (fun () -> P.check_handoff context));
  test directory "mutable legacy handoff permits planned sidecar but rejects replacement" (fun c ->
    with_output c (fun descriptor ->
      let context = producing c descriptor in
      write_file (Filename.concat c.incoming "._candidate") sentinel;
      P.check_handoff context;
      Unix.rename c.candidate (c.candidate ^ ".actual"); write_file c.candidate payload;
      expect_unix Unix.EBUSY (fun () -> P.check_handoff context);
      expect_unix Unix.EBUSY (fun () -> P.abort_and_close context)));
  test directory "frozen legacy handoff rejects mutation and new sidecar" (fun c ->
    with_output c (fun descriptor ->
      let context = frozen c descriptor in P.check_handoff context;
      write_file (Filename.concat c.incoming "._candidate") sentinel;
      expect_unix Unix.EOPNOTSUPP (fun () -> P.check_handoff context);
      Unix.unlink (Filename.concat c.incoming "._candidate"); mutate c.candidate;
      expect_unix Unix.EBUSY (fun () -> P.check_handoff context)));
  test directory "legacy named frozen handoff cannot bypass fullstat" (fun c ->
    let context = attached c in P.check_handoff context; Unix.chmod c.candidate 0o640;
    expect_unix Unix.EBUSY (fun () -> P.check_handoff context));
  test directory "published or closed legacy handoff rejected" (fun c ->
    with_output c (fun descriptor ->
      let context = frozen c descriptor in publish_frozen context;
      expect_unix Unix.EINVAL (fun () -> P.check_handoff context);
      P.release context; expect_unix Unix.EINVAL (fun () -> P.check_handoff context);
      check (P.published context && read_file c.target = payload) "rejected handoff affected live"));
  Printf.printf "%d retained producer cases passed (%d total including original regressions)\n%!"
    (!count - prior) !count
