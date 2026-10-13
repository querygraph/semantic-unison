module F = FileObservation
module L = CloneLease
module C = CloneRange
external copy_at : Unix.file_descr -> Unix.file_descr -> int64 -> int64 -> int -> int
  = "clone_lease_fixture_copy"
let check yes why = if not yes then failwith why
let count = ref 0
let test name f =
  (try f () with e -> Printf.eprintf "FAIL %s\n%!" name;raise e);
  incr count;Printf.printf "PASS %s\n%!" name
let get = function Ok x -> x | Error e -> raise e
let error_issue issue = function Error(L.Invalidated actual) -> actual=issue | _ -> false
let fds () = Array.length(Sys.readdir "/dev/fd")
let serial = ref 0
let owner () = incr serial;L.create_owner ~instance_id:("fixture-owner-"^string_of_int !serial)
let fixture directory f =
  incr serial;
  let source_path=Filename.concat directory ("source-"^string_of_int !serial) in
  let stage_path=Filename.concat directory ("stage-"^string_of_int !serial) in
  let source=Unix.openfile source_path [Unix.O_RDWR;Unix.O_CREAT;Unix.O_EXCL;Unix.O_CLOEXEC] 0o600 in
  let destination=Unix.openfile stage_path [Unix.O_RDWR;Unix.O_CREAT;Unix.O_EXCL;Unix.O_CLOEXEC] 0o600 in
  let basis=String.init 192 (fun i -> Char.chr((i*73+19) land 255)) in
  ignore(Unix.write_substring source basis 0 192);
  ignore(Unix.write_substring destination (String.make 192 '#') 0 192);
  ignore(Unix.LargeFile.lseek source 19L Unix.SEEK_SET);
  ignore(Unix.LargeFile.lseek destination 41L Unix.SEEK_SET);
  Fun.protect ~finally:(fun () ->
    Unix.close source;Unix.close destination;
    List.iter(fun path -> if Sys.file_exists path then Unix.unlink path) [source_path;stage_path])
    (fun () -> f source destination source_path stage_path basis)
let enroll ?observe root source destination =
  get(L.enroll ?observe root ~backend_revision:"positional-copy-fixture-v1" ~source ~destination)
let caps : C.capabilities = {native_whole=false;composed_whole=false;range=None;max_copy_bytes=7L}
let request : C.request = {source_offset=5L;destination_offset=33L;length=24L}
let execute ?check_cancel ?(notify=(fun _ _ -> ())) ?(before=(fun _ -> ())) lease source destination =
  let calls=ref [] and notices=ref 0L in
  let outcome=L.execute ?check_cancel lease ~capabilities:caps ~request
    ~perform:(fun ~source:held_source ~destination:held_destination op ->
      check(held_source=source && held_destination=destination) "lease selected or duplicated another descriptor";
      before op;
      calls:=op::!calls;
      C.Copied(Int64.of_int(copy_at held_source held_destination op.C.source_offset op.destination_offset (Int64.to_int op.length))))
    ~notify:(fun op p -> notices:=Int64.add !notices(Int64.add p.C.shared p.copied);notify op p) () in
  outcome,List.rev !calls,!notices
let stopped_observation issue completed = function
  | C.Stopped s -> s.receipt.progress.shared=0L && s.receipt.progress.copied=completed &&
    s.mutation=C.Known_prefix && (match s.fault with
      C.Observation_failed(L.Invalidated actual) -> actual=issue | _ -> false)
  | _ -> false
let read_file path = let ic=open_in_bin path in Fun.protect ~finally:(fun()->close_in ic)
  (fun () -> really_input_string ic (in_channel_length ic))
let verify_stage path basis completed =
  let stage=read_file path in
  for i=0 to 191 do check(stage.[i]=(if i>=33 && i<33+completed then basis.[5+i-33] else '#'))
    "stage prefix/sentinel bytes incorrect" done

let () =
  let directory=Sys.argv.(1) in
  fixture directory (fun s _ _ _ _ ->
    try ignore(F.observe s) with Unix.Unix_error(Unix.ENOSYS,_,_) -> exit 77);
  let before=fds() in
  test "fresh native lease completes bounded positional copying on the same borrowed FDs" (fun () ->
    fixture directory (fun s d sp dp basis ->
      let root=owner() in let lease=enroll root s d in
      check(get(L.observe lease)=L.expected lease) "fresh native binding differed";
      let outcome,calls,noticed=execute lease s d in
      (match outcome with C.Complete r -> check(r.progress.copied=24L && r.progress.shared=0L) "ordinary copy claimed sharing"
       | _ -> failwith "valid native bridge stopped");
      check(List.map(fun op->op.C.length) calls=[7L;7L;7L;3L] && noticed=24L) "copy bounds/progress wrong";
      verify_stage dp basis 24;
      check(read_file sp=basis && Unix.LargeFile.lseek s 0L Unix.SEEK_CUR=19L &&
        Unix.LargeFile.lseek d 0L Unix.SEEK_CUR=41L) "borrowed source/offset changed";
      check(get(L.observe lease)=L.expected lease) "destination write timestamps invalidated lease"));
  test "owner invalidate/close and lease invalidate never close borrowed descriptors" (fun () ->
    fixture directory (fun s d _ _ _ ->
      let root=owner() in let lease=enroll root s d in
      L.invalidate lease;check(error_issue L.Lease_invalidated(L.observe lease)) "lease invalidation ignored";
      let next=enroll root s d in L.invalidate_owner root;
      check(error_issue L.Owner_invalidated(L.observe next)) "owner epoch ignored";
      let renewed=enroll root s d in
      check((L.expected renewed).source.generation<>(L.expected next).source.generation) "owner epoch reused";
      L.close_owner root;check(error_issue L.Owner_closed(L.observe renewed)) "owner close ignored";
      check(error_issue L.Owner_closed(L.enroll root ~backend_revision:"fixture" ~source:s ~destination:d)) "closed owner enrolled";
      ignore(Unix.fstat s);ignore(Unix.fstat d)));
  test "owner epoch fence detects invalidation during either enrollment observation" (fun () ->
    List.iter(fun at -> fixture directory(fun s d _ _ _ ->
      let root=owner() and calls=ref 0 in
      let observe fd=let result=F.observe fd in incr calls;if !calls=at then L.invalidate_owner root;result in
      check(error_issue L.Owner_invalidated(L.enroll ~observe root ~backend_revision:"fixture" ~source:s ~destination:d))
        "enrollment accepted an epoch changed inside observer";
      ignore(Unix.fstat s);ignore(Unix.fstat d))) [1;2]);
  test "owner epoch fence detects invalidation during refresh and after completion" (fun () ->
    fixture directory(fun s d _ dp basis ->
      let root=owner() and invalidate=ref false in
      let observe fd=let result=F.observe fd in if !invalidate then(invalidate:=false;L.invalidate_owner root);result in
      let lease=enroll ~observe root s d in invalidate:=true;
      check(error_issue L.Owner_invalidated(L.observe lease)) "refresh epoch fence missed invalidation";
      let next=enroll root s d in let outcome,_,_=execute next s d in
      (match outcome with C.Complete _ -> ()|_ -> failwith "follow-up work failed");
      verify_stage dp basis 24;L.invalidate_owner root;
      check(error_issue L.Owner_invalidated(L.observe next)) "completed receipt bypassed fresh precommit epoch check"));
  test "same-file alias is refused even for different duplicate descriptor numbers" (fun () ->
    fixture directory(fun s _ _ _ _ ->
      let duplicate=Unix.dup s in Fun.protect ~finally:(fun()->Unix.close duplicate) (fun()->
        check(error_issue L.Aliased_objects(L.enroll (owner()) ~backend_revision:"fixture" ~source:s ~destination:duplicate))
          "same object aliases were enrolled";ignore(Unix.fstat s);ignore(Unix.fstat duplicate))));
  test "source write and unlink invalidate stable-source stamps" (fun () ->
    List.iter(fun unlink -> fixture directory(fun s d sp _ _ ->
      let lease=enroll(owner()) s d in
      if unlink then Unix.unlink sp else(ignore(Unix.LargeFile.lseek s 0L Unix.SEEK_SET);ignore(Unix.write_substring s "!" 0 1));
      check(error_issue L.Source_changed(L.observe lease)) "source write/link change became a valid observation")) [false;true]);
  test "unlinked immutable basis can enroll before its stable zero-link snapshot" (fun () ->
    fixture directory(fun s d sp _ _ ->
      Unix.unlink sp;let lease=enroll(owner()) s d in
      check(get(L.observe lease)=L.expected lease) "unlinked basis was rejected or drifted"));
  test "source/destination truncation returns changed bounds and stops range copying" (fun () ->
    List.iter(fun source_side -> fixture directory(fun s d _ dp basis ->
      let lease=enroll(owner()) s d in Unix.LargeFile.ftruncate (if source_side then s else d) 191L;
      let current=get(L.observe lease) in
      check((if source_side then current.source.size else current.destination.size)=191L && current<>L.expected lease)
        "truncation did not return actual bounds";
      let outcome,calls,noticed=execute lease s d in
      (match outcome with C.Stopped{fault=C.Binding_changed _;_}->()|_->failwith "bounds change did not stop executor");
      check(calls=[] && noticed=0L) "stale bounds were copied";
      if source_side then verify_stage dp basis 0)) [false;true]);
  test "mid-transfer source write stops after known prefix and never copies suffix" (fun () ->
    fixture directory(fun s d _ dp basis ->
      let lease=enroll(owner()) s d in
      let notify _ _=ignore(Unix.LargeFile.lseek s 0L Unix.SEEK_SET);ignore(Unix.write_substring s "!" 0 1) in
      let outcome,calls,noticed=execute ~notify lease s d in
      check(stopped_observation L.Source_changed 7L outcome && List.length calls=1 && noticed=7L)
        "source mutation authorized another chunk";verify_stage dp basis 7));
  test "mid-transfer destination fd replacement never writes or closes the replacement sentinel" (fun () ->
    fixture directory(fun s d _ dp basis ->
      fixture directory(fun _ replacement _ rp sentinel ->
        ignore(Unix.LargeFile.lseek replacement 0L Unix.SEEK_SET);
        ignore(Unix.write_substring replacement sentinel 0 192);
        ignore(Unix.LargeFile.lseek replacement 123L Unix.SEEK_SET);
        let lease=enroll(owner()) s d in
        let notify _ _=Unix.dup2 replacement d in
        let outcome,calls,noticed=execute ~notify lease s d in
        (match outcome with C.Stopped{fault=C.Binding_changed _;_}->()|_->failwith "fd reuse binding accepted");
        check(List.length calls=1 && noticed=7L && read_file rp=sentinel) "replacement fd received stale I/O";
        verify_stage dp basis 7;L.invalidate lease;ignore(Unix.fstat d);ignore(Unix.fstat replacement);
        check(Unix.LargeFile.lseek d 0L Unix.SEEK_CUR=123L) "lease moved/closed reused descriptor")));
  test "rename/path replacement preserves the enrolled held source and does not select new path" (fun () ->
    fixture directory(fun s d sp _ _ ->
      let moved=sp^"-moved" in Unix.rename sp moved;
      Fun.protect ~finally:(fun()->Unix.unlink moved) (fun()->
        let lease=enroll(owner()) s d in
        let fresh=Unix.openfile sp [Unix.O_CREAT;Unix.O_EXCL;Unix.O_RDWR;Unix.O_CLOEXEC] 0o600 in
        Fun.protect ~finally:(fun()->Unix.close fresh) (fun()->
          check((F.observe fresh).file_id<>(F.observe s).file_id && get(L.observe lease)=L.expected lease)
            "lease reopened source pathname"))));
  test "source fd replacement returns actual identity and stops before any copy" (fun () ->
    fixture directory(fun s d sp dp basis -> fixture directory(fun replacement _ rp _ sentinel ->
      let lease=enroll(owner()) s d in Unix.dup2 replacement s;
      check(get(L.observe lease)<>L.expected lease) "replacement source returned stale binding";
      let outcome,calls,noticed=execute lease s d in
      (match outcome with C.Stopped{fault=C.Binding_changed _;_}->()|_->failwith "replacement source was accepted");
      check(calls=[] && noticed=0L && read_file sp=basis && read_file rp=sentinel)
        "rebound source selected stale I/O or changed source";
      verify_stage dp basis 0;L.invalidate lease;ignore(Unix.fstat s);ignore(Unix.fstat replacement))));
  test "missing volume identity is refused at enrollment and cannot disappear after enrollment" (fun () ->
    List.iter(fun source_side -> fixture directory(fun s d _ _ _ ->
      let unavailable=ref true in
      let observe fd=let native=F.observe fd in
        if !unavailable && fd=(if source_side then s else d) then {native with F.volume_uuid=None} else native in
      let root=owner() and endpoint=if source_side then L.Source else L.Destination in
      check(error_issue(L.Identity_unavailable endpoint)(L.enroll ~observe root ~backend_revision:"fixture" ~source:s ~destination:d))
        "missing UUID became weaker identity";
      unavailable:=false;let lease=enroll ~observe root s d in unavailable:=true;
      check(error_issue(L.Identity_unavailable endpoint)(L.observe lease)) "enrolled UUID disappeared without error")) [true;false]);
  test "malformed native sizes/flags/links/nanoseconds are rejected independently" (fun () ->
    let mutations=[
      (fun(o:F.t)->{o with size=(-1L)});(fun o->{o with F.link_count=(-1L)});
      (fun o->{o with F.file_flags=(-1L)});(fun o->{o with F.mount_flags=(-1L)});
      (fun o->{o with F.mtime_nanoseconds=(-1)});(fun o->{o with F.mtime_nanoseconds=1000000000});
      (fun o->{o with F.ctime_nanoseconds=(-1)});(fun o->{o with F.ctime_nanoseconds=1000000000});
      (fun o->{o with F.device_id=""});(fun o->{o with F.file_id=""});(fun o->{o with F.filesystem_id=""})] in
    List.iter(fun source_side -> List.iter(fun mutate -> fixture directory(fun s d _ _ _ ->
      let endpoint=if source_side then L.Source else L.Destination in
      let observe fd=let native=F.observe fd in if fd=(if source_side then s else d) then mutate native else native in
      match L.enroll ~observe(owner()) ~backend_revision:"fixture" ~source:s ~destination:d with
      | Error(L.Invalidated(L.Invalid_observation(actual,_))) ->check(actual=endpoint) "malformed observation endpoint lost"
      | _ ->failwith "malformed observation enrolled")) mutations) [true;false]);
  test "nonregular source/destination observations are refused" (fun () ->
    List.iter(fun source_side -> fixture directory(fun s d _ _ _ ->
      let endpoint=if source_side then L.Source else L.Destination in
      let observe fd=let native=F.observe fd in
        if fd=(if source_side then s else d) then {native with F.kind=Unix.S_DIR} else native in
      check(error_issue(L.Not_regular endpoint)(L.enroll ~observe(owner()) ~backend_revision:"fixture" ~source:s ~destination:d))
        "nonregular object enrolled")) [true;false]);
  test "source timestamp/flags/links/mount changes stop while destination write timestamps are permitted" (fun () ->
    let changes=[
      (fun(o:F.t)->{o with mtime_seconds=Int64.succ o.mtime_seconds});
      (fun o->{o with F.mtime_nanoseconds=(o.mtime_nanoseconds+1) mod 1000000000});
      (fun o->{o with F.ctime_seconds=Int64.succ o.ctime_seconds});
      (fun o->{o with F.ctime_nanoseconds=(o.ctime_nanoseconds+1) mod 1000000000});
      (fun o->{o with F.file_flags=Int64.logxor o.file_flags 1L});
      (fun o->{o with F.link_count=Int64.succ o.link_count});
      (fun o->{o with F.mount_flags=Int64.logxor o.mount_flags 1L})] in
    List.iter(fun mutate -> fixture directory(fun s d _ _ _ ->
      let changed=ref false in
      let observe fd=let native=F.observe fd in if !changed && fd=s then mutate native else native in
      let lease=enroll ~observe(owner()) s d in changed:=true;
      check(error_issue L.Source_changed(L.observe lease)) "source stability field ignored")) changes;
    fixture directory(fun s d _ _ _ ->
      let changed=ref false in
      let observe fd=let native=F.observe fd in if !changed && fd=d then
        {native with F.mtime_seconds=Int64.succ native.mtime_seconds;ctime_nanoseconds=(native.ctime_nanoseconds+1) mod 1000000000}
        else native in
      let lease=enroll ~observe(owner()) s d in changed:=true;
      check(get(L.observe lease)=L.expected lease) "own destination write stamps became a source stability rule"));
  test "destination links/flags/mount constraints remain fixed despite permitting write stamps" (fun () ->
    List.iter(fun mutate -> fixture directory(fun s d _ _ _ ->
      let changed=ref false in
      let observe fd=let native=F.observe fd in if !changed && fd=d then mutate native else native in
      let lease=enroll ~observe(owner()) s d in changed:=true;
      check(error_issue L.Destination_constraints_changed(L.observe lease)) "destination constraint drift ignored"))
      [(fun(o:F.t)->{o with link_count=Int64.succ o.link_count});
       (fun o->{o with F.file_flags=Int64.logxor o.file_flags 1L});
       (fun o->{o with F.mount_flags=Int64.logxor o.mount_flags 1L})]);
  test "native/backend errors preserve exception identity at both enrollment and refresh" (fun () ->
    List.iter(fun thrown -> List.iter(fun at -> fixture directory(fun s d _ _ _ ->
      let calls=ref 0 in
      let observe fd=incr calls;if !calls=at then raise thrown else F.observe fd in
      (match L.enroll ~observe(owner()) ~backend_revision:"fixture" ~source:s ~destination:d with
       | Error e->check(e==thrown) "native error exception was replaced"|Ok _->failwith "native error was ignored");
      ignore(Unix.fstat s);ignore(Unix.fstat d);
      let fail=ref false in
      let observe fd=if !fail then raise thrown else F.observe fd in
      let lease=enroll ~observe(owner()) s d in fail:=true;
      (match L.observe lease with Error e->check(e==thrown) "refresh error exception was replaced"|Ok _->failwith "refresh ignored native failure");
      let next=enroll(owner()) s d in check(get(L.observe next)=L.expected next) "failed observer prevented follow-up work")) [1;2])
      [Failure "injected native observer";Out_of_memory;Unix.Unix_error(Unix.EIO,"injected observation","fixture")]);
  test "closed descriptors fail enrollment with original EBADF and no handle leaks" (fun () ->
    fixture directory(fun _ d sp _ _ ->
      let dead=Unix.openfile sp [Unix.O_RDONLY;Unix.O_CLOEXEC] 0 in Unix.close dead;
      let before=fds() in
      for _=1 to 100 do match L.enroll(owner()) ~backend_revision:"fixture" ~source:dead ~destination:d with
        | Error(Unix.Unix_error(Unix.EBADF,_,_))->()|_->failwith "closed fd became a valid/unsupported lease"
      done;check(fds()=before) "failed enrollment leaked descriptors"));
  test "cancellation and adapter/notification exceptions preserve borrowing and exact prefix" (fun () ->
    List.iter(fun location -> fixture directory(fun s d _ dp basis ->
      let lease=enroll(owner()) s d in let steps=ref 0 in
      let escaped=try
        ignore(match location with
          | "before" -> execute ~check_cancel:(fun()->raise Exit) lease s d
          | "between" -> execute ~check_cancel:(fun()->if !steps=1 then raise Exit)
              ~before:(fun _->incr steps) lease s d
          | "adapter" -> execute ~before:(fun _->raise Exit) lease s d
          | _ -> execute ~notify:(fun _ _->raise Exit) lease s d);false with Exit->true in
      check escaped "callback exception was classified or swallowed";
      verify_stage dp basis (if location="between" || location="notify" then 7 else 0);
      L.invalidate lease;ignore(Unix.fstat s);ignore(Unix.fstat d))) ["before";"between";"adapter";"notify"]);
  test "late invalidation and collection never close a reused borrowed sentinel fd" (fun () ->
    fixture directory(fun s d _ _ _ ->fixture directory(fun _ replacement _ _ _ ->
      let root=owner() in
      let abandon ()=let lease=enroll root s d in L.invalidate lease in abandon();
      Unix.dup2 replacement d;L.close_owner root;Gc.full_major();
      ignore(Unix.fstat d);ignore(Unix.fstat replacement))));
  Gc.full_major();check(fds()=before) "lease tests leaked or closed unrelated descriptors";
  Printf.printf "CloneLease: %d independent native/injected bridge tests passed; no publication/sharing claim\n%!" !count
