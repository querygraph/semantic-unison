(* Original fault control: actual rename effects are not a completed owner hint. *)
external configure : int -> unit = "unison_record_fault_configure"
external counts : unit -> int * int = "unison_record_fault_counts"
let checks=ref 0
let check value reason=incr checks;if not value then failwith reason
let () =
 let before=Array.length(Sys.readdir "/dev/fd") in
 List.iter(fun selected ->
  let folder=Filename.temp_file "archive-reference-fault-" "" in
  Sys.remove folder;Unix.mkdir folder 0o700;
  let directory=Unix.openfile folder [Unix.O_RDONLY;Unix.O_CLOEXEC] 0 in
  Fun.protect ~finally:(fun () -> configure 0;Unix.close directory;
    Array.iter(fun name -> Sys.remove(Filename.concat folder name))(Sys.readdir folder);
    Unix.rmdir folder) (fun () ->
   let stage=Unix.openfile(Filename.concat folder "stage") [Unix.O_CREAT;Unix.O_EXCL;Unix.O_RDWR;Unix.O_CLOEXEC] 0o600 in
   Fun.protect ~finally:(fun () -> Unix.close stage) (fun () ->
    configure 0;
    let binding=SemanticHash.string("archive publication fault "^string_of_int selected) in
    let ledger=DngComponents.empty_owner_index ~max_entries:1 ~max_bytes:4096 in
    let digest=DngComponents.write_owner_index ~binding ledger stage in
    let publication=SemanticFile.with_borrowed_fd stage(fun file ->
      DngComponents.prepare_owner_index_publication ~binding ledger ~directory ~stage ~temporary:"stage" file) in
    configure selected;
    check(try DngComponents.publish_owner_index publication directory stage;selected=0
      with Unix.Unix_error((Unix.EIO|Unix.EINTR),_,_) -> selected<>0) "publication fault outcome differs";
    check(DngComponents.owner_index_published publication=(selected=0 || selected=1)) "actual rename flag differs";
    check((try DngComponents.owner_index_reference publication=(binding,digest)
      with ComponentHash.Invalid _ -> false)=(selected=0)) "failed normal completion authorized archive hint";
    let observed=counts () in
    check(observed=(1,(if selected=0 || selected=1 then 1 else 0))) "publication syscall replay differs";
    check(try DngComponents.publish_owner_index publication directory stage;false
      with ComponentHash.Invalid _ -> true) "publication fault ticket replayed";
    check(counts ()=observed && (Unix.fstat stage).Unix.st_size=80) "failed replay touched FD or syscalls";
    check(Sys.file_exists(Filename.concat folder (SemanticHash.hex digest))=(selected=0 || selected=1))
      "actual namespace effect differs"))
 ) [0;1;2;3];
 check(Array.length(Sys.readdir "/dev/fd")=before) "archive reference fault leaked descriptors";
 Printf.printf "PASS %d owner archive-reference publication fault checks\n%!" !checks
