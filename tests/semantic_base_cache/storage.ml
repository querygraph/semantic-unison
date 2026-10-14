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
  let dir=Util.fileInUnisonDir "semantic-merge-bases-v0" in
  let shards=Sys.readdir dir in check(Array.length shards=1) "unexpected shard count";
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
