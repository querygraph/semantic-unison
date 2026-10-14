exception Cancelled
let check x why=if not x then failwith why
let expected i=Char.chr((i*113+29) land 255)
let () =
  let before=Array.length(Sys.readdir "/dev/fd") in
  let domains=List.init 4 (fun (id:int) -> Domain.Safe.spawn(fun () ->
    let path="input-"^string_of_int id^".bin" in
    let fd=Unix.openfile path [Unix.O_RDONLY;Unix.O_CLOEXEC] 0 in
    let cancellation=Atomic.make false and calls=ref 0 in
    let hook ()=incr calls;if Atomic.get cancellation then raise Cancelled in
    let digest=SemanticFile.with_fd ~check_cancel:hook fd (fun file ->
      check(SemanticFile.size file=131099L && SemanticFile.same_inode file fd) "identity/size";
      let sample=SemanticFile.read file 65530L 23 in
      String.iteri(fun i c ->check(c=expected(65530+i)) "read bytes") sample;
      check (try ignore(SemanticFile.read file 0L 1048577);false with SemanticFile.Invalid _ -> true) "read cap";
      check (try ignore(SemanticFile.read file 131098L 2);false with SemanticFile.Invalid _ -> true) "extent cap";
      let seen=ref 0 in
      SemanticFile.iter file 0L 131099L (fun b n ->
        check(n<=65536) "iteration cap";
        for i=0 to n-1 do check(Bytes.get b i=expected(!seen+i)) "iteration bytes" done;
        seen:= !seen+n);
      check(!seen=131099) "iteration missing data";
      SemanticHash.hex(SemanticFile.digest file)) in
    check(!calls>3) "cancellation hook bypassed";
    let ch=open_in(path^".sha256") in let expected_digest=input_line ch in close_in ch;
    check(digest=expected_digest) "digest differs from hashlib";
    Atomic.set cancellation true;
    check(try ignore(SemanticFile.with_fd ~check_cancel:hook fd SemanticFile.size);false with Cancelled -> true | _ -> false) "cancelled admission accepted";
    ignore(Unix.fstat fd);Unix.close fd;
    let output=Unix.openfile ("output-"^string_of_int id^".bin") [Unix.O_RDWR;Unix.O_CLOEXEC] 0 in
    ignore(Unix.LargeFile.lseek output 37L Unix.SEEK_SET);
    let writer=SemanticFile.prepare_writer output in
    let changed=String.make 60006 'q' in
    check(SemanticFile.write_at writer changed 0 60006 17L=60006) "short write";
    check(Unix.LargeFile.lseek output 0L Unix.SEEK_CUR=37L) "positional write changed cursor";
    check(try ignore(SemanticFile.write_at writer changed 0 65537 0L);false with Invalid_argument _ -> true) "write cap";
    check(try ignore(SemanticFile.write_at writer changed 0 1 Int64.max_int);false with Invalid_argument _ -> true) "write overflow";
    Unix.close output;
    let append=Unix.openfile path [Unix.O_WRONLY;Unix.O_APPEND;Unix.O_CLOEXEC] 0 in
    check(try ignore(SemanticFile.prepare_writer append);false with Unix.Unix_error(Unix.EINVAL,_,_) -> true) "append writer accepted";Unix.close append;
    let read_only=Unix.openfile path [Unix.O_RDONLY;Unix.O_CLOEXEC] 0 in
    check(try ignore(SemanticFile.prepare_writer read_only);false with Unix.Unix_error(Unix.EBADF,_,_) -> true) "readonly writer accepted";Unix.close read_only;
    let r,w=Unix.pipe ~cloexec:true () in
    check(try ignore(SemanticFile.with_fd r SemanticFile.size);false with SemanticFile.Invalid _ -> true) "nonregular accepted";
    Unix.close r;Unix.close w)) in
  List.iter Domain.join domains;
  check(Array.length(Sys.readdir "/dev/fd")=before) "file component leaked descriptors";
  print_endline "PASS checked file operations:4domains, independent hashes, exact reads/iteration, cancellation, positional writes and descriptor settlement"
