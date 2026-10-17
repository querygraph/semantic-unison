module D=DngComponents
let checks=ref 0
let check yes why=incr checks;if not yes then failwith why
let ()=
 let baseline=Array.length(Sys.readdir "/dev/fd") in
 let path=Filename.temp_file "cache-namespace-native-" "" in Sys.remove path;Unix.mkdir path 0o700;
 let parent=Unix.openfile path [Unix.O_RDONLY;Unix.O_CLOEXEC] 0 in
 let t=D.prepare_cache_namespace ~parent () in
 D.provision_cache_namespace t ~parent;
 let expected=D.cache_namespace_identity t in
 check(D.cache_namespace_created t) "normal namespace not created";
 let first=D.with_cache_namespace t ~parent (fun directory ->
  let s=Unix.fstat directory in check((s.Unix.st_dev,s.st_ino)=expected) "normal namespace identity differs";
  let q=ComponentHash.prepare_metadata_quota ~directory ~max_bytes:4194304L ~max_entries:2 in
  check(ComponentHash.reserve_metadata_slot q directory) "normal initial quota refused";
  List.iter (fun role ->
   check(not(ComponentHash.metadata_stage_created q role)) "stage created before open";
   let fd=ComponentHash.open_metadata_stage q directory role in
   check(ComponentHash.metadata_stage_created q role) "stage creation not retained";
   let st=Unix.fstat fd in
   check(st.Unix.st_kind=Unix.S_REG && st.st_perm=0o600 && st.st_nlink=1 && st.st_size=0)
    "stage not private empty regular file";
   Unix.close fd;
   let refused=try let fd=ComponentHash.open_metadata_stage q directory role in
    Unix.close fd;false with Invalid_argument _ -> true in
   check refused "stage open replay accepted")
   [ComponentHash.Record_stage;ComponentHash.Entry_stage;ComponentHash.Manifest_stage];
  ComponentHash.metadata_slot_name q) in
 let reopen ()=let t=D.prepare_cache_namespace ~expected ~parent () in
  D.provision_cache_namespace t ~parent;check(not(D.cache_namespace_created t)) "normal reopen recreated directory";t in
 let second=D.with_cache_namespace (reopen ()) ~parent (fun directory ->
  let q=ComponentHash.prepare_metadata_quota ~directory ~max_bytes:4194304L ~max_entries:2 in
  check(ComponentHash.reserve_metadata_slot q directory) "normal retained quota refused";
  ComponentHash.metadata_slot_name q) in
 check(first<>second) "normal namespace quota repeated slot";
 D.with_cache_namespace (reopen ()) ~parent (fun directory ->
  let q=ComponentHash.prepare_metadata_quota ~directory ~max_bytes:4194304L ~max_entries:2 in
  check(not(ComponentHash.reserve_metadata_slot q directory)) "normal quota reset");
 Unix.close parent;
 check(Array.length(Sys.readdir "/dev/fd")=baseline) "normal namespace leaked FD";
 Printf.printf "PASS %d production namespace checks; real create/sync/open/close and quota reopen\n%!" !checks
