(* Single-threaded native controls. Borrowed writers own no descriptor. *)
[@@@alert "-unsafe_multidomain"]
external setup : int -> unit = "positional_fixture_setup"
external set_dup : Unix.file_descr -> unit = "positional_fixture_dup"
external stats : unit -> int array = "positional_fixture_stats"
external attempt : int -> int64 array = "positional_fixture_attempt"
external fdcount : unit -> int = "positional_fixture_fdcount"
external dispatch_pending : unit -> unit = "positional_fixture_dispatch"
external raw : int -> string -> int -> int -> int64 -> int = "unison_semantic_pwrite"
external raw_prepare : int -> bool = "unison_semantic_prepare_writer"
let with_async_exns f = f ()
exception Cancelled
let checks = ref 0
let check condition message = incr checks; if not condition then failwith message
let cases = ref 0
let root = Sys.argv.(1)
let selected = if Array.length Sys.argv > 2 then Sys.argv.(2) else "all"
let path name = Filename.concat root name
let write_file name data = let c = open_out_bin name in Fun.protect ~finally:(fun () -> close_out c) (fun () -> output_string c data)
let read_file name = let c = open_in_bin name in Fun.protect ~finally:(fun () -> close_in c) (fun () -> really_input_string c (in_channel_length c))
let same a b = a.Unix.st_dev = b.Unix.st_dev && a.Unix.st_ino = b.Unix.st_ino
let run name f =
  if selected = "all" || selected = name then begin
    incr cases; setup 0; let before = fdcount () in
    Printf.printf "case %s\n%!" name;
    f ();
    check (fdcount () = before) (name ^ ": descriptor leak");
    Printf.printf "ok %d %s assertions=%d native=%s\n%!" !cases name !checks
      (String.concat "," (Array.to_list (Array.map string_of_int (stats ()))))
  end
let expect_error error phase f =
  match f () with
  | _ -> failwith ("expected " ^ Unix.error_message error ^ " at " ^ phase)
  | exception Unix.Unix_error(actual,operation,_) ->
    check (actual = error) ("wrong errno: " ^ Unix.error_message actual);
    check (operation = phase) ("wrong phase: " ^ operation)
let expect_invalid text f =
  match f () with
  | _ -> failwith ("accepted invalid " ^ text)
  | exception Invalid_argument actual -> check (actual = text) ("wrong validation: " ^ actual)
let with_output name bytes flags f =
  let name = path name in write_file name bytes;
  let fd = Unix.openfile name flags 0o600 in
  Fun.protect ~finally:(fun () -> Unix.close fd) (fun () -> f name fd)
let data = String.init 70000 (fun i -> Char.chr ((i * 73 + 29) land 255))
let offset fd = Unix.LargeFile.lseek fd 0L Unix.SEEK_CUR
let position fd p = ignore (Unix.LargeFile.lseek fd p Unix.SEEK_SET)
let no_pwrite () = check ((stats ()).(0) = 0 && (stats ()).(10) = 0) "rejection reached native pwrite"
let offset_preserved () =
  for index = 0 to (stats ()).(0) - 1 do
    let a = attempt index in check (a.(3) = a.(4)) "pwrite changed shared file offset"
  done
let copy_checks () =
  let s = stats () in
  check (s.(8) = 0) "released write used borrowed heap pointer";
  check (s.(7) = s.(0)) "pwrite executed with runtime held"
let patch original position data start count =
  let b = Bytes.of_string original in Bytes.blit_string data start b position count; Bytes.to_string b

module Generic = struct
  let profile = "org.unison.positional-write-test/0"
  let inspect _ = Ok {FormatExtension.regions=[{offset=5L;length=196610}]}
end
let ok = function Ok value -> value | Error reason -> failwith reason
let original = String.make 196630 'A'
(* Binary, nonuniform and never equal to the old 'A' byte. Every comparison
   window differs, and incorrect source-slice advancement cannot hide behind
   a repeated constant payload. *)
let target_packet = String.init 196610 (fun i ->
  let byte = (i * 73 + 29) mod 255 in Char.chr (if byte >= 65 then byte + 1 else byte))
let changed = patch original 5 target_packet 0 196610
let with_basis name check_cancel f =
  let fd = Unix.openfile name [Unix.O_RDONLY] 0 in
  Fun.protect ~finally:(fun () -> Unix.close fd)
    (fun () -> SemanticFile.with_fd ~check_cancel fd f)
let inspect name = with_basis name (fun () -> ()) (fun file -> ok (SemanticDelta.inspect (module Generic) file))
let plan before after = ok (SemanticDelta.plan ~nonce:(String.make 32 'p') ~base:(inspect before) ~target:(inspect after))
let loop name mode expected calls prefix ?(cancel=false) ?(unchanged=false) () =
  run name (fun () ->
    let before = path (name ^ "-basis") and after = path (name ^ "-target")
    and stage = path (name ^ "-stage") and untouched = path (name ^ "-live") in
    write_file before original; Unix.chmod before 0o400;
    write_file after (if unchanged then original else changed);
    write_file stage original; write_file untouched "existing live file";
    let live = Unix.stat untouched and basis_stat = Unix.stat before in
    let plan = plan before after in
    let fd = Unix.openfile stage [Unix.O_RDWR] 0 in
    let duplicate = if mode = 8 then Some (Unix.dup ~cloexec:true fd) else None in
    Fun.protect ~finally:(fun () -> Option.iter Unix.close duplicate; Unix.close fd)
      (fun () ->
        setup mode; Option.iter set_dup duplicate;
        let check_cancel () = if cancel && (stats ()).(0) >= calls then raise Cancelled in
        let result = try
          Ok (with_basis before check_cancel (fun basis ->
            SemanticDelta.apply_report_with_extension ~check_cancel (module Generic) plan ~basis ~output:fd))
          with e -> Error e in
        (match expected,result with
         | "success",Ok report ->
           check (report.SemanticDelta.logical_bytes_written = prefix) "logical byte report differs from actual successful progress";
           check (report.SemanticDelta.write_calls = calls) "write attempts omit retry or short write";
           check (report.SemanticDelta.comparison_window = 4096) "comparison policy changed"
         | "cancelled",Error Cancelled -> ()
         | "zero",Error(SemanticFile.Invalid reason) -> check (reason = "metadata write made no progress") "wrong zero-progress rejection"
         | "invalid",Error(SemanticFile.Invalid reason) -> check (reason = "metadata write returned invalid progress") "wrong invalid-progress rejection"
         | "EIO",Error(Unix.Unix_error(Unix.EIO,"semantic pwrite",_)) -> ()
         | _,Error e -> raise e
         | _,Ok _ -> failwith "partial failure/cancellation returned a complete application");
        let s = stats () in
        check (s.(0) = calls) "native call count differs from production loop expectation";
        check (s.(1) = 1 && s.(2) = 1) "writer was not admitted exactly once";
        check (s.(3) = 0 && s.(4) = 0) "POSIX materializer used seek/write";
        copy_checks (); offset_preserved ();
        let complete = ref 0L in
        for index = 0 to calls - 1 do
          let a = attempt index in
          check (a.(0) = Int64.add 5L !complete) "short write or EINTR changed absolute patch offset";
          check (a.(1) > 0L && a.(1) <= 65536L) "native call escaped 64KiB bound";
          if a.(6) > 0L then complete := Int64.add !complete a.(6)
        done;
        check (!complete = Int64.of_int prefix) "actual syscall prefix differs from expected private mutation";
        let expected_stage = patch original 5 target_packet 0 prefix in
        check (read_file stage = expected_stage) "private output bytes escaped successful prefix";
        check (read_file before = original && same (Unix.stat before) basis_stat) "basis changed on materialization";
        check (read_file untouched = "existing live file" && same (Unix.stat untouched) live) "materializer touched an unrelated live name";
        (* This is a materializer-only bound. Actual receive/publication failure
           qualification is separate; no publisher is linked into this test. *)
        check ((Unix.fstat fd).Unix.st_nlink = 1) "caller FD closed or stage link changed"))
let () =
  run "direct-offset" (fun () ->
    with_output "direct-offset-output" (String.make 128 'A') [Unix.O_RDWR] (fun name fd ->
      let writer = SemanticFile.prepare_writer fd in position fd 73L;
      let count = SemanticFile.write_at writer data 3 19 11L in
      check (count = 19) "direct write count";
      check (offset fd = 73L) "positional write changed caller offset";
      check (read_file name = patch (String.make 128 'A') 11 data 3 19) "direct absolute bytes";
      check ((stats ()).(0) = 1 && (stats ()).(1) = 1 && (stats ()).(2) = 1) "one write with one admission";
      copy_checks (); offset_preserved ()));
  run "shared-dup-offset" (fun () ->
    with_output "shared-dup-output" (String.make 128 'A') [Unix.O_RDWR] (fun name fd ->
      let writer = SemanticFile.prepare_writer fd in
      let duplicate = Unix.dup ~cloexec:true fd in
      Fun.protect ~finally:(fun () -> Unix.close duplicate) (fun () ->
        setup 8; set_dup duplicate; position fd 73L;
        check (SemanticFile.write_at writer data 4 17 7L = 17) "duplicate write count";
        check (offset fd = 102L && offset duplicate = 102L) "pwrite disturbed a sibling's shared offset";
        check (read_file name = patch (String.make 128 'A') 7 data 4 17) "shared offset selected wrong write extent";
        copy_checks (); offset_preserved (); check ((stats ()).(1) = 0 && (stats ()).(2) = 0) "writer repeats admission queries")));
  run "snapshot-copy" (fun () ->
    with_output "snapshot-copy-output" (String.make 128 'A') [Unix.O_RDWR] (fun name fd ->
      let writer = SemanticFile.prepare_writer fd in
      let outcome = try ignore (SemanticFile.write_at writer data 3 31 9L); true with Unix.Unix_error _ -> false in
      copy_checks ();
      check outcome "native copy was rejected";
      check (read_file name = patch (String.make 128 'A') 9 data 3 31) "copied binary payload bytes";
      check (data = String.init 70000 (fun i -> Char.chr ((i * 73 + 29) land 255))) "immutable input changed"));
  run "append-rejected" (fun () ->
    with_output "append-output" (String.make 128 'A') [Unix.O_RDWR;Unix.O_APPEND] (fun name fd ->
      let denied = try ignore (SemanticFile.prepare_writer fd); false
        with Unix.Unix_error(Unix.EINVAL,"semantic writer flags",_) -> true in
      check denied "append writer was admitted";
      no_pwrite (); check (read_file name = String.make 128 'A') "append admission changed bytes"));
  run "read-only-rejected" (fun () ->
    with_output "read-only-output" "source" [Unix.O_RDONLY] (fun _ fd ->
      expect_error Unix.EBADF "semantic writer flags" (fun () -> SemanticFile.prepare_writer fd); no_pwrite ()));
  run "write-only-admitted" (fun () ->
    with_output "write-only-output" "source" [Unix.O_WRONLY] (fun name fd ->
      let writer = SemanticFile.prepare_writer fd in position fd 4L;
      check (SemanticFile.write_at writer "X" 0 1 2L = 1) "write-only admission failed";
      check (offset fd = 4L && read_file name = "soXrce") "write-only positional result"; copy_checks ()));
  run "closed-descriptor-rejected" (fun () ->
    let name = path "closed-descriptor-output" in write_file name "source";
    let fd = Unix.openfile name [Unix.O_RDWR] 0 in Unix.close fd;
    expect_error Unix.EBADF "semantic writer flags" (fun () -> SemanticFile.prepare_writer fd);
    check ((stats ()).(1) = 1 && (stats ()).(2) = 0) "closed descriptor was not rejected by native flags admission"; no_pwrite ());
  run "pipe-rejected" (fun () ->
    let a,b = Unix.pipe ~cloexec:true () in
    Fun.protect ~finally:(fun () -> Unix.close a;Unix.close b) (fun () ->
      expect_error Unix.EINVAL "semantic writer identity" (fun () -> SemanticFile.prepare_writer b); no_pwrite ()));
  run "hardlink-rejected" (fun () ->
    with_output "hardlinked-output" "source" [Unix.O_RDWR] (fun name fd ->
      Unix.link name (name ^ "-alias");
      expect_error Unix.EBUSY "semantic writer identity" (fun () -> SemanticFile.prepare_writer fd); no_pwrite ();
      check (read_file name = "source" && read_file (name ^ "-alias") = "source") "hardlink admission mutated aliases"));
  List.iter (fun (mode,name,error,phase) ->
    run name (fun () ->
      with_output (name ^ "-output") "source" [Unix.O_RDWR] (fun _ fd ->
        setup mode; expect_error error phase (fun () -> SemanticFile.prepare_writer fd); no_pwrite ())))
    [12,"admission-flags-EIO",Unix.EIO,"semantic writer flags";
     14,"admission-stat-EIO",Unix.EIO,"semantic writer identity";
     15,"admission-flags-empty-errno",Unix.EIO,"semantic writer flags"];
  List.iter (fun (mode,name,flags,stat_calls) ->
    run name (fun () ->
      with_output (name ^ "-output") "source" [Unix.O_RDWR] (fun _ fd ->
        setup mode; ignore (SemanticFile.prepare_writer fd);
        check ((stats ()).(1) = flags && (stats ()).(2) = stat_calls) "admission EINTR retry counts"; no_pwrite ())))
    [13,"admission-flags-EINTR",2,1;20,"admission-stat-EINTR",2,2];
  run "admission-cancellation" (fun () ->
    with_output "admission-cancel-output" "source" [Unix.O_RDWR] (fun _ fd ->
      setup 19;
      let check_cancel () = if (stats ()).(1) = 1 then raise Cancelled in
      let denied = try ignore (SemanticFile.prepare_writer ~check_cancel fd); false with Cancelled -> true in
      check denied "admission EINTR ignored cancellation"; check ((stats ()).(1) = 1) "cancelled admission retried"; no_pwrite ()));
  run "admission-cancel-before-query" (fun () ->
    with_output "admission-cancel-before-output" "source" [Unix.O_RDWR] (fun _ fd ->
      let denied = try ignore (SemanticFile.prepare_writer ~check_cancel:(fun () -> raise Cancelled) fd); false with Cancelled -> true in
      check denied "admission ignored initial cancellation";
      check ((stats ()).(1) = 0 && (stats ()).(2) = 0) "cancelled admission queried descriptor"; no_pwrite ()));
  List.iter (fun descriptor ->
    run ("descriptor-" ^ string_of_int descriptor) (fun () ->
      expect_error Unix.EBADF "semantic writer descriptor" (fun () -> raw_prepare descriptor);
      expect_error Unix.EBADF "semantic pwrite descriptor" (fun () -> raw descriptor "x" 0 1 0L);
      no_pwrite (); check ((stats ()).(1) = 0 && (stats ()).(2) = 0) "invalid native descriptor reached queries"))
    [(-1);max_int;min_int];
  List.iteri (fun index (start,length) ->
    run ("slice-invalid-" ^ string_of_int index) (fun () ->
      with_output ("slice-" ^ string_of_int index) "source" [Unix.O_RDWR] (fun _ fd ->
        let writer = SemanticFile.prepare_writer fd in
        expect_invalid "SemanticFile.write_at slice" (fun () -> SemanticFile.write_at writer data start length 0L); no_pwrite ())))
    [(-1,1);(0,-1);(max_int,0);(min_int,0);(0,max_int);(0,min_int);
     (0,65537);(String.length data+1,0);(String.length data,1);(String.length data-1,2)];
  List.iteri (fun index (position,length) ->
    run ("offset-invalid-" ^ string_of_int index) (fun () ->
      with_output ("offset-" ^ string_of_int index) "source" [Unix.O_RDWR] (fun _ fd ->
        let writer = SemanticFile.prepare_writer fd in
        expect_invalid "SemanticFile.write_at offset" (fun () -> SemanticFile.write_at writer data 0 length position); no_pwrite ())))
    [(-1L,1);(Int64.min_int,0);(Int64.max_int,1);(Int64.sub Int64.max_int 4L,5)];
  run "slice-zero-end" (fun () ->
    with_output "zero-end-output" "source" [Unix.O_RDWR] (fun name fd ->
      let writer = SemanticFile.prepare_writer fd in position fd 3L;
      check (SemanticFile.write_at writer data (String.length data) 0 0L = 0) "empty slice result";
      check ((stats ()).(0) = 1 && (stats ()).(5) = 0) "zero-length attempt or copy count";
      check (offset fd = 3L && read_file name = "source") "empty slice changed source/offset"));
  run "slice-64KiB" (fun () ->
    with_output "64KiB-output" (String.make 65540 'A') [Unix.O_RDWR] (fun name fd ->
      let writer = SemanticFile.prepare_writer fd in position fd 13L;
      check (SemanticFile.write_at writer data 1 65536 2L = 65536) "64KiB write bound";
      check (offset fd = 13L && read_file name = patch (String.make 65540 'A') 2 data 1 65536) "64KiB exact result/offset";
      copy_checks ()));
  run "maximum-offset-zero-fault" (fun () ->
    with_output "maximum-offset-output" "source" [Unix.O_RDWR] (fun _ fd ->
      let writer = SemanticFile.prepare_writer fd in setup 6;
      check (SemanticFile.write_at writer "" 0 0 Int64.max_int = 0) "representable maximum offset rejected";
      check ((attempt 0).(0) = Int64.max_int && (stats ()).(10) = 0) "maximum offset conversion (injected no-write syscall)"));
  run "sparse-above-2GiB" (fun () ->
    with_output "large-sparse-output" "HEAD" [Unix.O_RDWR] (fun name fd ->
      let writer = SemanticFile.prepare_writer fd in position fd 2L;
      let address = Int64.add 2147483648L 123L in
      check (SemanticFile.write_at writer "TAIL" 0 4 address = 4) "large positional write result";
      check (offset fd = 2L) "large positional write changed current position";
      check ((Unix.LargeFile.fstat fd).Unix.LargeFile.st_size = Int64.add address 4L) "large offset narrowed/truncated";
      let read = Unix.openfile name [Unix.O_RDONLY] 0 in
      Fun.protect ~finally:(fun () -> Unix.close read) (fun () ->
        let b = Bytes.create 4 in ignore (Unix.read read b 0 4); check (Bytes.to_string b = "HEAD") "sparse prefix changed";
        ignore (Unix.LargeFile.lseek read (Int64.sub address 4L) Unix.SEEK_SET);
        let b = Bytes.create 8 in check (Unix.read read b 0 8 = 8 && Bytes.to_string b = "\000\000\000\000TAIL") "large sparse position bytes");
      copy_checks (); offset_preserved ()));
  List.iter (fun (mode,name,error) ->
    run name (fun () ->
      with_output (name ^ "-output") "source" [Unix.O_RDWR] (fun name fd ->
        let writer = SemanticFile.prepare_writer fd in setup mode; position fd 3L;
        expect_error error "semantic pwrite" (fun () -> SemanticFile.write_at writer data 0 3 0L);
        check ((stats ()).(0) = 1) "native primitive retried an error";
        check (offset fd = 3L && read_file name = "source") "native failed write changed bytes/offset"; copy_checks ())))
    [2,"direct-EINTR",Unix.EINTR;4,"direct-EIO",Unix.EIO;7,"direct-overcount",Unix.EIO;
     16,"direct-empty-errno",Unix.EIO;17,"direct-invalid-negative",Unix.EIO];
  run "direct-short" (fun () ->
    with_output "direct-short-output" (String.make 5000 'A') [Unix.O_RDWR] (fun name fd ->
      let writer = SemanticFile.prepare_writer fd in setup 1; position fd 17L;
      check (SemanticFile.write_at writer data 3 3000 7L = 997) "native short write was hidden or retried";
      check ((stats ()).(0) = 1 && read_file name = patch (String.make 5000 'A') 7 data 3 997) "native short prefix";
      check (offset fd = 17L) "short pwrite changed current position"; copy_checks ()));
  run "pending-copy-signal" (fun () ->
    with_output "pending-signal-output" (String.make 128 'A') [Unix.O_RDWR] (fun name fd ->
      let writer = SemanticFile.prepare_writer fd in setup 18; position fd 27L;
      let delivered = ref 0 and caught = ref false in
      Sys.set_signal Sys.sigusr1 (Sys.Signal_handle (fun _ -> incr delivered; raise Sys.Break));
      Fun.protect ~finally:(fun () -> Sys.set_signal Sys.sigusr1 Sys.Signal_ignore) (fun () ->
        (try with_async_exns (fun () -> ignore (SemanticFile.write_at writer data 3 19 11L)) with Sys.Break -> caught := true);
        (try with_async_exns dispatch_pending with Sys.Break -> caught := true);
        check (!caught && !delivered = 1) "pending signal lost/duplicated";
        check ((stats ()).(0) = 1 && (stats ()).(9) = 1) "pending signal entered before bounded native copy settled";
        copy_checks ();
        check (offset fd = 27L && read_file name = patch (String.make 128 'A') 11 data 3 19) "pending signal damaged caller FD or result")));
  loop "loop-full" 0 "success" 4 196610 ();
  loop "loop-short" 1 "success" 198 196610 ();
  loop "loop-EINTR-once" 2 "success" 5 196610 ();
  loop "loop-EINTR-twice" 3 "success" 6 196610 ();
  loop "loop-shared-dup" 8 "success" 4 196610 ();
  loop "loop-EIO-before-write" 4 "EIO" 1 0 ();
  loop "loop-partial-EIO" 5 "EIO" 2 997 ();
  loop "loop-zero" 6 "zero" 1 0 ();
  loop "loop-partial-zero" 10 "zero" 2 997 ();
  loop "loop-overcount" 7 "EIO" 1 0 ();
  loop "loop-partial-overcount" 11 "EIO" 2 997 ();
  loop "loop-cancel-short" 1 "cancelled" 1 997 ~cancel:true ();
  loop "loop-cancel-EINTR" 9 "cancelled" 1 0 ~cancel:true ();
  loop "loop-unchanged-admission" 0 "success" 0 0 ~unchanged:true ();
  run "loop-unchanged-append-rejected" (fun () ->
    let before = path "unchanged-append-basis" and stage = path "unchanged-append-stage" in
    write_file before original; write_file stage original;
    let plan = plan before before in
    let fd = Unix.openfile stage [Unix.O_RDWR;Unix.O_APPEND] 0 in
    Fun.protect ~finally:(fun () -> Unix.close fd) (fun () ->
      expect_error Unix.EINVAL "semantic writer flags" (fun () ->
        with_basis before (fun () -> ()) (fun basis ->
          SemanticDelta.apply_report_with_extension (module Generic) plan ~basis ~output:fd));
      no_pwrite (); check (read_file before = original && read_file stage = original) "unchanged append admission mutated a file"));
  (* This private C variant forwards impossible syscall counts to the unchanged
     production ML loop. The shipped native boundary rejects them as EIO. *)
  if selected = "ml-overcount" then loop "ml-overcount" 7 "invalid" 1 0 ();
  if selected = "ml-negative" then loop "ml-negative" 17 "invalid" 1 0 ();
  if selected = "fallback-interior-and-bounds" then run selected (fun () ->
    with_output "fallback-interior-output" (String.make 128 'A') [Unix.O_RDWR] (fun name fd ->
      let writer = SemanticFile.prepare_writer fd in position fd 73L;
      check (SemanticFile.write_at writer data 3 19 11L = 19) "fallback interior write count";
      check (offset fd = 30L) "fallback did not use seek/write position semantics";
      let expected = patch (String.make 128 'A') 11 data 3 19 in
      check (read_file name = expected) "fallback exact interior bytes";
      List.iter (fun (start,count) -> expect_invalid "SemanticFile.write_at slice"
        (fun () -> SemanticFile.write_at writer data start count 0L))
        [(-1,1);(0,-1);(max_int,0);(0,65537);(String.length data,1)];
      expect_invalid "SemanticFile.write_at offset"
        (fun () -> SemanticFile.write_at writer data 0 1 Int64.max_int);
      no_pwrite (); check (offset fd = 30L && read_file name = expected) "fallback bounds altered bytes/position"));
  List.iter (fun (name,unchanged) -> if selected = name then run name (fun () ->
    let before = path (name ^ "-basis") and after = path (name ^ "-target") and stage = path (name ^ "-stage") in
    write_file before original; write_file after (if unchanged then original else changed); write_file stage original;
    let delta = plan before after in
    let fd = Unix.openfile stage [Unix.O_RDWR] 0 in
    Fun.protect ~finally:(fun () -> Unix.close fd) (fun () ->
      let report = with_basis before (fun () -> ()) (fun basis ->
        SemanticDelta.apply_report_with_extension (module Generic) delta ~basis ~output:fd) in
      check (report.SemanticDelta.logical_bytes_written = (if unchanged then 0 else 196610)) "fallback logical byte report";
      check (report.SemanticDelta.write_calls = (if unchanged then 0 else 4)) "fallback write attempt report";
      check (read_file stage = (if unchanged then original else changed) && read_file before = original) "fallback materialization target/basis";
      no_pwrite ();
      check ((stats ()).(1) = 1 && (stats ()).(2) = 1) "forced-false preparation did not execute once";
      check ((Unix.fstat fd).Unix.st_nlink = 1) "fallback closed borrowed FD")))
    ["fallback-materialize",false;"fallback-unchanged",true];
  check (!cases > 0) "no case selected";
  Printf.printf "All %d positional-write cases passed; %d assertions\n%!" !cases !checks
