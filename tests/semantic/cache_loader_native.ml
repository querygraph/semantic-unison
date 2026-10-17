(* Normal production native object: no injected open/close wrapper or mode. *)
module D=DngComponents
let checks=ref 0
let check yes why=incr checks;if not yes then failwith why
let write path bytes=
 let fd=Unix.openfile path [Unix.O_WRONLY;Unix.O_CREAT;Unix.O_EXCL;Unix.O_CLOEXEC] 0o600 in
 Fun.protect ~finally:(fun () -> Unix.close fd) (fun () ->
  let rec loop at=if at<String.length bytes then
   let n=Unix.write_substring fd bytes at (String.length bytes-at) in
   if n=0 then failwith "fixture write stalled" else loop(at+n) in loop 0)
let ()=
 let baseline=Array.length(Sys.readdir "/dev/fd") in
 let path=Filename.temp_file "cache-loader-native-" "" in Sys.remove path;Unix.mkdir path 0o700;
 let source=Filename.concat path "original-fixture.bin" in write source (String.make 128 'n');
 let input=Unix.openfile source [Unix.O_RDONLY;Unix.O_CLOEXEC] 0 in
 let checkpoint=SemanticFile.with_borrowed_fd input (fun file ->
  ComponentHash.with_snapshot ~max_read_bytes:128L file
   {ComponentHash.id="dng";schema="dng-physical-partition/0";role=Structural;
    offset=0L;length=128L;children=[]}
   (fun session snapshot -> ComponentHash.checkpoint session snapshot)) in
 Unix.close input;
 let generation=SemanticHash.string "native-loader-generation" in
 let entries=List.map(fun name -> D.make_owner_entry ~root_identity:"native-loader-root"
   ~path:name ~generation_sha256:generation ~checkpoint ~outcomes:[]) ["one";"two"] in
 let ledger=List.fold_left(fun ledger entry ->
   match D.replace_owner_entry ledger ~expected_entry_sha256:None entry with
   | Ok value -> value | Error why -> failwith why)
   (D.empty_owner_index ~max_entries:4 ~max_bytes:524288) entries in
 let binding=SemanticHash.string "native-loader-binding" in
 let manifest=D.owner_index_bytes ~binding ledger in let digest=SemanticHash.string manifest in
 let leaf digest=Filename.concat path (SemanticHash.hex digest) in
 write (leaf digest) manifest;
 List.iter(fun entry ->
  write (leaf(D.owner_entry_sha256 entry)) (D.owner_entry_bytes entry);
  write (leaf(D.owner_entry_record_sha256 entry))
    (ComponentHash.checkpoint_record ~binding:(D.owner_entry_binding entry) checkpoint)) entries;
 let directory=Unix.openfile path [Unix.O_RDONLY;Unix.O_CLOEXEC] 0 in
 let loaded=match D.load_owner_index ~directory ~expected_manifest_sha256:digest ~binding
   ~max_entries:4 ~max_bytes:524288 () with Some value -> value | None -> failwith "normal index absent" in
 check(D.owner_index_usage loaded=D.owner_index_usage ledger) "production index usage differs";
 List.iter2(fun name entry ->
  let selected=match D.select_owner_entry loaded ~root_identity:"native-loader-root" ~path:name
    ~generation_sha256:generation with Some value -> value | None -> failwith "normal selection absent" in
  check(D.owner_entry_sha256 selected=D.owner_entry_sha256 entry) "production entry selection differs";
  let record=match D.load_owner_record ~directory ~entry:selected () with
   | Some bytes -> bytes | None -> failwith "normal record absent" in
  let recovered=D.checkpoint_for_owner_entry selected record in
  check(ComponentHash.checkpoint_sha256 recovered=ComponentHash.checkpoint_sha256 checkpoint)
    "production record checkpoint differs") ["one";"two"] entries;
 check(D.load_owner_index ~directory ~expected_manifest_sha256:(SemanticHash.string "missing-native-manifest")
   ~binding ~max_entries:4 ~max_bytes:524288 ()=None) "normal missing index fabricated";
 let namespace=D.prepare_cache_namespace ~parent:directory () in
 D.provision_cache_namespace namespace ~parent:directory;
 let entry=List.hd entries in
 let store=D.prepare_managed_cache_store ~entry ~checkpoint
   ~index:(D.empty_owner_index ~max_entries:4 ~max_bytes:524288)
   ~expected_entry_sha256:None ~binding ~max_bytes:4194304L ~max_entries:2 in
 check((try ignore(D.managed_cache_store_reference store);false with ComponentHash.Invalid _ -> true))
  "store exposed reference before completion";
 check(D.execute_managed_cache_store store ~namespace ~parent:directory) "store quota refused";
 check(D.managed_cache_store_effects store=(true,true,true,true,true)) "store effects incomplete";
 let stored_binding,stored_digest=D.managed_cache_store_reference store in
 check(stored_binding=binding) "store binding changed";
 let reopened=D.prepare_cache_namespace ~expected:(D.cache_namespace_identity namespace) ~parent:directory () in
 D.provision_cache_namespace reopened ~parent:directory;
 D.with_cache_namespace reopened ~parent:directory (fun directory ->
  let index=match D.load_owner_index ~directory ~expected_manifest_sha256:stored_digest
   ~binding ~max_entries:4 ~max_bytes:524288 () with
   | Some index -> index | None -> failwith "stored manifest absent" in
  check(D.owner_index_usage index=D.owner_index_usage(D.managed_cache_store_index store))
   "stored index differs");
 check((try ignore(D.execute_managed_cache_store store ~namespace ~parent:directory);false
  with ComponentHash.Invalid _ -> true)) "store replay accepted";
 Unix.close directory;
 check(Array.length(Sys.readdir "/dev/fd")=baseline) "normal native loader leaked FD";
 Printf.printf "PASS %d production native cache loader checks; two trusted entries/records and complete FD retirement\n%!" !checks
