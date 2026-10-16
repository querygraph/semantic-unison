let check value message = if not value then failwith message
let write name data = let channel=open_out_bin name in
  Fun.protect ~finally:(fun () -> close_out_noerr channel) (fun () -> output_string channel data)
let read name = let channel=open_in_bin name in
  Fun.protect ~finally:(fun () -> close_in_noerr channel) (fun () -> really_input_string channel (in_channel_length channel))
let fd_count () = let handle=Unix.opendir "/dev/fd" in
  Fun.protect ~finally:(fun () -> Unix.closedir handle) (fun () ->
    let rec loop n = match Unix.readdir handle with
    | "." | ".." -> loop n | _ -> loop(n+1) | exception End_of_file -> n in loop 0)
let () =
  Prefs.loadStrings ["semanticmergebasecache = true"];
  let root=Fspath.canonize(Some(Sys.getcwd())) and path=Path.fromString "base.dng" in
  let fingerprint=Os.data_only_fingerprint(Fingerprint.file root path) in
  let fd=Unix.openfile "base.dng" [Unix.O_RDONLY;Unix.O_CLOEXEC] 0 in
  let proof=Fun.protect ~finally:(fun () -> Unix.close fd) (fun () ->
    SemanticFile.with_fd fd (fun file -> match SemanticDelta.inspect (module DngSemantic) file with
    | Ok proof -> proof | Error reason -> failwith reason)) in
  let store ()=SemanticMergeCache.store ~root ~path ~fingerprint proof in
  let load ()=SemanticMergeCache.load ~root ~path ~fingerprint in
  store();
  let dir=Util.fileInUnisonDir "semantic-merge-bases-v1" in
  let shards=Array.of_list(List.filter(fun n -> n<>".quota-v1")(Array.to_list(Sys.readdir dir))) in check(Array.length shards=1) "unexpected shard count";
  let shard=Filename.concat dir shards.(0) in
  let entries=Sys.readdir shard in check(Array.length entries=1) "unexpected initial record count";
  let record=Filename.concat shard entries.(0) in
  let saved=read record in
  let restore ()=write record saved;Unix.chmod record 0o600 in
  let baseline=fd_count() in
  for _=1 to 256 do check(Option.is_some(load())) "valid load failed" done;
  check(fd_count()=baseline) "valid loads leaked descriptors";
  store();check(read record=saved) "idempotent store changed bytes";
  let reject name mutation =
    mutation();for _=1 to 32 do check(load()=None) (name^" accepted") done;
    check(fd_count()=baseline) (name^" leaked descriptors");
    Unix.unlink record;restore();print_endline("PASS "^name) in
  reject "checksum" (fun () -> write record (String.make(String.length saved) 'x'));
  reject "truncated" (fun () -> Unix.truncate record 71);
  reject "oversized" (fun () -> Unix.truncate record (SemanticDelta.max_base_cache_size+73));
  reject "permissive" (fun () -> Unix.chmod record 0o644);
  let alias="record-hardlink" in
  reject "hardlink" (fun () -> Unix.link record alias);Unix.unlink alias;
  let target="record-target" in
  reject "symlink" (fun () -> Unix.rename record target;Unix.symlink (Filename.concat(Sys.getcwd()) target) record);
  Unix.unlink target;
  Unix.unlink record;
  for _=1 to 32 do check(load()=None) "missing accepted" done;
  check(fd_count()=baseline) "missing loads leaked";restore();
  Unix.unlink record;Unix.mkdir record 0o700;
  for _=1 to 32 do check(load()=None) "directory accepted" done;
  Unix.rmdir record;restore();check(fd_count()=baseline) "directory load leaked";
  let changed=Bytes.of_string saved in Bytes.set changed 40 (Char.chr(Char.code(Bytes.get changed 40) lxor 1));
  write record(Bytes.to_string changed);
  check((try store();false with Util.Transient _ -> true)) "different existing record replaced";
  check(read record=Bytes.to_string changed) "conflict changed existing record";restore();
  Unix.chmod dir 0o755;check(load()=None) "permissive directory accepted";Unix.chmod dir 0o700;
  Unix.chmod shard 0o755;check(load()=None) "permissive shard accepted";Unix.chmod shard 0o700;
  let other=Path.fromString "other.dng" in
  check(SemanticMergeCache.load ~root ~path:other ~fingerprint=None) "other path reused base";
  let ledger=Filename.concat dir ".quota-v1" in
  let saved_ledger=read ledger in
  check(String.length saved_ledger=79) "quota ledger framing";
  store();check(read ledger=saved_ledger) "existing base charged again";
  let capture_other ()=SemanticMergeCache.store ~root ~path:other ~fingerprint proof in
  let quota_refuses label =
    let rejected=try capture_other();false with Util.Transient _ | Unix.Unix_error _ -> true in
    check rejected (label^" accepted new capture");
    check(load()<>None && read record=saved) (label^" lost existing recovery base");
    check(fd_count()=baseline) (label^" leaked descriptors") in
  Prefs.loadStrings ["semanticmergecachemaxentries = 1"];
  quota_refuses "entry quota";
  Prefs.loadStrings ["semanticmergecachemaxentries = 1048576"];
  let ledger_value entries bytes =
    let payload=Printf.sprintf "SBQ1 %020Ld %020Ld\n" entries bytes in
    payload ^ SemanticHash.string payload in
  Prefs.loadStrings ["semanticmergecachemaxmib = 1"];
  write ledger (ledger_value 1L 1048576L);quota_refuses "payload quota";
  Prefs.loadStrings ["semanticmergecachemaxmib = 1024"];
  write ledger (String.make 79 'x');quota_refuses "corrupt quota";
  write ledger (ledger_value 16777217L 0L);quota_refuses "out-of-range quota";
  let overflow_payload="SBQ1 99999999999999999999 00000000000000000000\n" in
  write ledger (overflow_payload ^ SemanticHash.string overflow_payload);
  quota_refuses "overflow quota";
  (* Every possible interrupted prefix of the fixed ledger is ambiguous.
     Existing records must prohibit initialization even for a zero-byte prefix. *)
  for length=0 to 78 do
    let prefix=String.sub saved_ledger 0 length in
    write ledger prefix;
    quota_refuses (Printf.sprintf "torn quota prefix %d" length);
    check(read ledger=prefix) "refused torn ledger was repaired or charged"
  done;
  print_endline "PASS79 interrupted ledger prefixes refuse capture without rewriting recovery state";
  write ledger saved_ledger;Unix.chmod ledger 0o644;
  quota_refuses "permissive quota";Unix.chmod ledger 0o600;
  let ledger_alias="quota-hardlink" in
  Unix.link ledger ledger_alias;quota_refuses "hardlinked quota";Unix.unlink ledger_alias;
  let ledger_target="quota-target" in
  Unix.rename ledger ledger_target;
  Unix.symlink (Filename.concat(Sys.getcwd()) ledger_target) ledger;
  quota_refuses "symlinked quota";
  Unix.unlink ledger;Unix.rename ledger_target ledger;
  Unix.unlink ledger;quota_refuses "lost quota with records";
  write ledger saved_ledger;Unix.chmod ledger 0o600;
  (* A separate process holds the real POSIX lock; capture must decline without
     waiting, releasing descriptors and leaving the ledger unchanged. *)
  let ready_r,ready_w=Unix.pipe () and release_r,release_w=Unix.pipe () in
  let child=Unix.fork () in
  if child=0 then begin
    Unix.close ready_r;Unix.close release_w;
    let fd=Unix.openfile ledger [Unix.O_RDWR] 0 in
    Unix.lockf fd Unix.F_LOCK 0;
    ignore(Unix.write_substring ready_w "R" 0 1);Unix.close ready_w;
    let readable,_,_=Unix.select [release_r] [] [] 5. in
    let byte=Bytes.create 1 in
    let ok=readable<>[] && Unix.read release_r byte 0 1=1 in
    Unix.close release_r;Unix.close fd;Unix._exit(if ok then 0 else 3)
  end;
  Unix.close ready_w;Unix.close release_r;
  let child_status=ref None in
  Fun.protect ~finally:(fun () ->
    (try ignore(Unix.write_substring release_w "X" 0 1) with _ -> ());
    Unix.close release_w;Unix.close ready_r;
    child_status:=Some(snd(Unix.waitpid [] child))) (fun () ->
      let readable,_,_=Unix.select [ready_r] [] [] 5. in
      let byte=Bytes.create 1 in
      check(readable<>[] && Unix.read ready_r byte 0 1=1) "child lock readiness";
      (* Baseline includes the two coordinator pipe descriptors in this scope. *)
      let before=fd_count() in
      check((try capture_other();false with Unix.Unix_error ((Unix.EACCES|Unix.EAGAIN),_,_) -> true))
        "busy ledger did not decline";
      check(fd_count()=before && read ledger=saved_ledger) "busy quota changed/leaked");
  check(!child_status=Some(Unix.WEXITED 0)) "quota lock child not cleanly reaped";
  check(fd_count()=baseline) "quota lock descriptors leaked";
  (* Existing v0 bases remain read-only fallback, never charged or rewritten. *)
  let legacy=Util.fileInUnisonDir "semantic-merge-bases-v0" in
  Unix.mkdir legacy 0o700;
  let legacy_shard=Filename.concat legacy shards.(0) in Unix.mkdir legacy_shard 0o700;
  let legacy_record=Filename.concat legacy_shard entries.(0) in
  write legacy_record saved;Unix.chmod legacy_record 0o600;
  Unix.unlink record;check(load()<>None) "legacy recovery base unreadable";
  check(read legacy_record=saved) "legacy recovery base changed";restore();
  print_endline "PASS global quota/idempotence/corruption/range/trust/missing-ledger/real process lock/legacy fallback";
  (* Fill the actual selected shard; failed publication must leave no temp files. *)
  for i=1 to 4095 do write(Filename.concat shard (Printf.sprintf "filler-%04d" i)) "" done;
  Unix.unlink record;
  (* 4096 unrelated entries force capacity refusal before temp acquisition. *)
  write(Filename.concat shard "filler-last") "";
  check((try store();false with Util.Transient _ -> true)) "full shard accepted new entry";
  check(not(Sys.file_exists record)) "capacity failure published a record";
  check(not(Array.exists(fun n -> String.starts_with ~prefix:".base-" n)(Sys.readdir shard))) "temporary leaked";
  restore();store();check(Option.is_some(load())) "full shard lost existing base";
  check(read record=saved) "full shard changed existing base";
  check(fd_count()=baseline) "storage failures leaked descriptors";
  print_endline "PASS private storage trust/capacity/idempotence and repeated descriptor settlement"
;
  (* Two independent owners compete for the single remaining quota entry.
     Gate both on the same pipe so neither relies on a startup sleep. *)
  for i=1 to 4095 do Unix.unlink(Filename.concat shard (Printf.sprintf "filler-%04d" i)) done;
  Unix.unlink(Filename.concat shard "filler-last");
  Prefs.loadStrings ["semanticmergecachemaxentries = 2"];
  let start_r,start_w=Unix.pipe () in
  let children=List.init 2 (fun index ->
    let pid=Unix.fork () in
    if pid=0 then begin
      Unix.close start_w;
      let ready,_,_=Unix.select [start_r] [] [] 5. in
      let byte=Bytes.create 1 in
      if ready=[] || Unix.read start_r byte 0 1<>1 then Unix._exit 90;
      Unix.close start_r;
      let selected=Path.fromString(Printf.sprintf "concurrent-%d.dng" index) in
      let code=try SemanticMergeCache.store ~root ~path:selected ~fingerprint proof; 0
        with Util.Transient _ -> 75
           | Unix.Unix_error ((Unix.EACCES|Unix.EAGAIN),_,_) -> 75 in
      Unix._exit code
    end;
    pid) in
  Unix.close start_r;
  check(Unix.write_substring start_w "XX" 0 2=2) "concurrent start framing";
  Unix.close start_w;
  let statuses=List.map(fun pid -> let waited,status=Unix.waitpid [] pid in
    check(waited=pid) "concurrent child wait identity"; status) children in
  check(List.length(List.filter((=)(Unix.WEXITED 0)) statuses)=1 &&
        List.length(List.filter((=)(Unix.WEXITED 75)) statuses)=1)
    "concurrent quota either overcommitted or admitted no owner";
  let final_ledger=read ledger in
  check(final_ledger=ledger_value 2L (Int64.of_int(2*String.length saved)))
    "concurrent ledger charge is not exactly two records";
  let selected_records=List.filter_map(fun index ->
    let selected=Path.fromString(Printf.sprintf "concurrent-%d.dng" index) in
    SemanticMergeCache.load ~root ~path:selected ~fingerprint) [0;1] in
  check(List.length selected_records=1) "concurrent durable capture count differs from quota";
  check(load()<>None && read record=saved) "concurrent capture lost original recovery base";
  check(fd_count()=baseline) "concurrent quota leaked parent descriptors";
  print_endline "PASS concurrent process quota reservation preserves exactly one remaining entry"
