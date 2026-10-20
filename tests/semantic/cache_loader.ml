module D=DngComponents
external mode : int -> unit = "unison_cache_control_mode"
external closes : unit -> int = "unison_cache_control_closes"
external opens : unit -> int = "unison_cache_control_opens"
let checks=ref 0
let check yes why=incr checks;if not yes then failwith why
let invalid f=try ignore(f());false with ComponentHash.Invalid _ -> true
let unix_failure f=try ignore(f());false with Unix.Unix_error _ -> true
let require_some=function Some value -> value | None -> failwith "expected retained value"
let write path bytes=
 let fd=Unix.openfile path [Unix.O_WRONLY;Unix.O_CREAT;Unix.O_TRUNC;Unix.O_CLOEXEC] 0o600 in
 let rec loop at=if at<String.length bytes then begin
  let n=Unix.write_substring fd bytes at (String.length bytes-at) in
  if n=0 then failwith "fixture write stalled";loop(at+n) end in
 Fun.protect ~finally:(fun () -> Unix.close fd) (fun () -> loop 0)
let flip bytes=let b=Bytes.of_string bytes in
 let at=Bytes.length b-1 in Bytes.set b at (Char.chr(Char.code(Bytes.get b at) lxor 1));Bytes.to_string b
let ()=
 let path=Filename.temp_file "component-loader-" "" in Sys.remove path;Unix.mkdir path 0o700;
 let data=Filename.concat path "original-fixture.bin" in
 write data (String.make 128 'p');
 let input=Unix.openfile data [Unix.O_RDONLY;Unix.O_CLOEXEC] 0 in
 let checkpoint=SemanticFile.with_borrowed_fd input (fun file ->
  ComponentHash.with_snapshot ~max_read_bytes:128L file
   {ComponentHash.id="dng";schema="dng-physical-partition/0";role=Structural;
    offset=0L;length=128L;children=[]}
   (fun session snapshot -> ComponentHash.checkpoint session snapshot)) in
 Unix.close input;
 let entry=D.make_owner_entry ~root_identity:"original-loader-root" ~path:"fixture.bin"
   ~generation_sha256:(SemanticHash.string "original-generation") ~checkpoint ~outcomes:[] in
 let ledger=match D.replace_owner_entry (D.empty_owner_index ~max_entries:4 ~max_bytes:524288)
   ~expected_entry_sha256:None entry with Ok value -> value | Error why -> failwith why in
 let binding=SemanticHash.string "original-owner-state" in
 let manifest=D.owner_index_bytes ~binding ledger in
 let manifest_digest=SemanticHash.string manifest in
 let record=ComponentHash.checkpoint_record ~binding:(D.owner_entry_binding entry) checkpoint in
 let leaf digest=Filename.concat path (SemanticHash.hex digest) in
 let manifest_path=leaf manifest_digest and entry_path=leaf(D.owner_entry_sha256 entry)
 and record_path=leaf(D.owner_entry_record_sha256 entry) in
 write manifest_path manifest;write entry_path (D.owner_entry_bytes entry);write record_path record;
 let directory=Unix.openfile path [Unix.O_RDONLY;Unix.O_CLOEXEC] 0 in
 let baseline=Array.length(Sys.readdir "/dev/fd") in
 let census ()=check(Array.length(Sys.readdir "/dev/fd")=baseline) "managed loader leaked descriptor" in
 let load ?(check_cancel=fun () -> ()) digest=D.load_owner_index ~check_cancel ~directory
   ~expected_manifest_sha256:digest ~binding ~max_entries:4 ~max_bytes:524288 () in
 let load_record ()=D.load_owner_record ~directory ~entry () in
 mode 0;
 let loaded=require_some(load manifest_digest) in
 check(D.owner_index_usage loaded=D.owner_index_usage ledger) "loaded ledger usage differs";
 check((match D.select_owner_entry loaded ~root_identity:"original-loader-root" ~path:"fixture.bin"
   ~generation_sha256:(SemanticHash.string "original-generation") with
   | Some value -> D.owner_entry_sha256 value=D.owner_entry_sha256 entry | None -> false))
   "loaded ledger owner binding differs";
 check(opens()=2 && closes()=2) "manifest/entry opens and normal closes differ";census();
 mode 0;check(load_record()=Some record && opens()=1 && closes()=1) "record loader altered metadata";census();
 mode 0;check(load(SemanticHash.string "absent-manifest")=None && opens()=0 && closes()=0)
   "absent manifest opened another object";census();
 Sys.rename record_path (record_path^".held");mode 0;
 check(load_record()=None && opens()=0) "missing record fabricated payload";
 Sys.rename (record_path^".held") record_path;census();
 write manifest_path (flip manifest);mode 0;
 check(invalid(fun () -> load manifest_digest) && opens()=1 && closes()=1) "corrupt manifest escaped";
 write manifest_path manifest;census();
 Sys.rename entry_path (entry_path^".held");mode 0;
 check(invalid(fun () -> load manifest_digest) && opens()=1 && closes()=1) "missing referenced entry became ledger";
 Sys.rename (entry_path^".held") entry_path;census();
 write entry_path (flip(D.owner_entry_bytes entry));mode 0;
 check(invalid(fun () -> load manifest_digest) && opens()=2 && closes()=2) "corrupt entry escaped or leaked";
 write entry_path (D.owner_entry_bytes entry);census();
 write record_path (flip record);mode 0;
 check(invalid load_record && opens()=1 && closes()=1) "corrupt owner record escaped";
 write record_path record;census();
 let held=manifest_path^".held" in
 Sys.rename manifest_path held;Unix.symlink held manifest_path;mode 0;
 check(unix_failure(fun () -> load manifest_digest) && opens()=0) "followed selected symlink";
 Sys.remove manifest_path;Sys.rename held manifest_path;census();
 Unix.link manifest_path held;mode 0;
 check(unix_failure(fun () -> load manifest_digest) && opens()=0) "accepted multiply linked metadata";
 Sys.remove held;census();
 Unix.chmod manifest_path 0o644;mode 0;
 check(unix_failure(fun () -> load manifest_digest) && opens()=0) "accepted nonprivate metadata";
 Unix.chmod manifest_path 0o600;census();
 Unix.chmod path 0o755;mode 0;
 check(unix_failure(fun () -> load manifest_digest) && opens()=0) "accepted nonprivate directory";
 Unix.chmod path 0o700;census();
 Sys.rename manifest_path held;Unix.mkfifo manifest_path 0o600;mode 0;
 check(unix_failure(fun () -> load manifest_digest) && opens()=0) "opened selected FIFO";
 Sys.remove manifest_path;Unix.mkdir manifest_path 0o700;mode 0;
 check(unix_failure(fun () -> load manifest_digest) && opens()=0) "opened selected directory";
 Unix.rmdir manifest_path;Sys.rename held manifest_path;census();
 mode 0;
 check((try ignore(load ~check_cancel:(fun () -> raise Exit) manifest_digest);false with Exit -> true)
   && opens()=0 && closes()=0) "cancelled loader opened metadata";census();
 let queries=ref 0 in mode 0;
 check((try ignore(load ~check_cancel:(fun () -> incr queries;if !queries=8 then raise Exit)
   manifest_digest);false with Exit -> true)) "loader ignored read cancellation";census();
 let uncertain run=
  try ignore(run());failwith "close failure became ordinary success/failure"
  with D.Cache_ownership_uncertain state -> state in
 let inspect state expected_cause expected_retained expected_closes=
  let failed=D.cache_uncertain_descriptors state in
  check(List.length failed=1 && List.length(D.cache_retained_descriptors state)=expected_retained)
    "uncertain/retained ownership inventory differs";
  check((D.cache_ownership_cause state<>None)=expected_cause) "lost original validation failure";
  check(closes()=expected_closes) "uncertain numeric descriptor retried";
  List.iter(fun ((_,identity),error) ->
   check(identity<>None) "missing observable preclose identity";
   check((match error with Unix.Unix_error(Unix.EIO,_,_)->true|_->false)) "close error changed") failed;
  let borrowed,identity=D.cache_borrowed_directory state in
  check(borrowed=directory && identity<>None && (Unix.fstat directory).Unix.st_kind=Unix.S_DIR)
    "borrowed directory closed or absent from retained evidence";
  (* These are known-held ancestors, not uncertain descriptors. The disposable
     shim actually closed the uncertain FD before reporting EIO; never retry it. *)
  List.iter(fun (fd,identity) ->
   check(identity<>None && (Unix.fstat fd).Unix.st_kind=Unix.S_REG) "retained ancestor not live";
   Unix.close fd) (D.cache_retained_descriptors state);
  census() in
 mode 1;inspect (uncertain load_record) false 0 1;
 write record_path (flip record);mode 1;
 let combined=uncertain load_record in
 check((match D.cache_ownership_cause combined with Some(ComponentHash.Invalid _)->true|_->false))
   "ordinary read failure not preserved with close uncertainty";
 inspect combined true 0 1;write record_path record;
 mode (-1);let lost=uncertain load_record in
 check((match D.cache_ownership_cause lost with Some(Unix.Unix_error(Unix.EBADF,_,_))->true|_->false))
   "descriptor loss erased original read/check failure";
 check((match D.cache_uncertain_descriptors lost with
   | [((_,Some _),Unix.Unix_error(Unix.EBADF,_,_))] -> true | _ -> false))
   "failed final stat erased known identity or close error";
 check(closes()=1 && D.cache_retained_descriptors lost=[])
   "lost descriptor retried or retention invented";census();
 mode 1;inspect (uncertain(fun () -> load manifest_digest)) false 1 1;
 mode 2;inspect (uncertain(fun () -> load manifest_digest)) false 0 2;
 write entry_path (flip(D.owner_entry_bytes entry));mode 2;
 inspect (uncertain(fun () -> load manifest_digest)) true 0 2;
 write entry_path (D.owner_entry_bytes entry);
 mode 1;let state=uncertain load_record in
 let fresh=Unix.openfile data [Unix.O_RDONLY;Unix.O_CLOEXEC] 0 in
 Gc.full_major();check((Unix.fstat fresh).Unix.st_size=128) "uncertainty finalizer closed reused FD";
 check(closes()=1 && List.length(D.cache_uncertain_descriptors state)=1) "uncertain close replayed";
 Unix.close fresh;census();
 mode 0;check(invalid(fun () -> load "bad") && opens()=0) "invalid manifest digest acquired FD";
 check((try ignore(D.load_owner_index ~directory ~expected_manifest_sha256:manifest_digest
   ~binding ~max_entries:0 ~max_bytes:524288 ());false with Invalid_argument _ -> true)
   && opens()=0) "invalid limits bypassed on load";
 census();Unix.close directory;
 Printf.printf "PASS %d managed cache loader checks; exact metadata, no-follow, cancellation, retained close uncertainty\n%!" !checks
