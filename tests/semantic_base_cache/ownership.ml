let check value message = if not value then failwith message
let fd_count () = let handle=Unix.opendir "/dev/fd" in
  Fun.protect ~finally:(fun () -> Unix.closedir handle) (fun () ->
    let rec loop n=match Unix.readdir handle with "."|".."->loop n
    | _->loop(n+1) | exception End_of_file->n in loop 0)
let () =
  Prefs.loadStrings["semanticmergebasecache = true"];
  let root=Fspath.canonize(Some(Sys.getcwd())) and path=Path.fromString "base.dng" in
  let fingerprint=Os.data_only_fingerprint(Fingerprint.file root path) in
  let fd=Unix.openfile "base.dng" [Unix.O_RDONLY;Unix.O_CLOEXEC] 0 in
  let proof=Fun.protect ~finally:(fun ()->Unix.close fd) (fun ()->
    SemanticFile.with_fd fd (fun file->match SemanticDelta.inspect(module DngSemantic) file with
    | Ok proof->proof | Error reason->failwith reason)) in
  let store ()=SemanticMergeCache.store ~root ~path ~fingerprint proof in
  store();
  let directory=Util.fileInUnisonDir "semantic-merge-bases-v1" in
  let names=Array.of_list(List.filter(fun n -> n<>".quota-v1")(Array.to_list(Sys.readdir directory))) in
  let shard=Filename.concat directory names.(0) in
  let record=Filename.concat shard (Sys.readdir shard).(0) in
  let baseline=fd_count() in
  List.iter(fun point->
    if point<>"read" && Sys.file_exists record then Unix.unlink record;
    if point="quota-root" || point="quota-shard" then
      Unix.truncate (Filename.concat directory ".quota-v1") 0;
    Unix.putenv "UNISON_PRIVATE_CACHE_FAULT" point;
    check((try (if point="read" then ignore(SemanticMergeCache.load ~root ~path ~fingerprint) else store());false
      with Out_of_memory->true)) (point^" fault was not reached");
    Unix.putenv "UNISON_PRIVATE_CACHE_FAULT" "";
    check(fd_count()=baseline) (point^" acquisition fault leaked descriptor");
    check(not(Array.exists(fun name->String.starts_with ~prefix:".base-" name)(Sys.readdir shard)))
      (point^" acquisition fault left temporary record");
    store();check(Option.is_some(SemanticMergeCache.load ~root ~path ~fingerprint))
      (point^" fault prevented fresh capture/load");
    print_endline("PASS "^point^" acquired-resource exception settlement"))
    ["read";"directory";"quota";"quota-root";"quota-shard";"temporary"]
