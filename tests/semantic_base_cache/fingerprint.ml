let check value message = if not value then failwith message
let write name data = let channel=open_out_bin name in
  Fun.protect ~finally:(fun () -> close_out channel) (fun () -> output_string channel data)
let fd_count () = let handle=Unix.opendir "/dev/fd" in
  Fun.protect ~finally:(fun () -> Unix.closedir handle) (fun () ->
    let rec loop total = match Unix.readdir handle with
      | "." | ".." -> loop total | _ -> loop (total+1) | exception End_of_file -> total in loop 0)
let () =
  write "original.bin" (String.make 131072 'a');
  let root=Fspath.canonize (Some(Sys.getcwd())) in
  let named ()=Fingerprint.file root (Path.fromString "original.bin") in
  let expected=named () in
  let count=fd_count () in
  let fd=Unix.openfile "original.bin" [Unix.O_RDONLY;Unix.O_CLOEXEC] 0 in
  ignore(Unix.LargeFile.lseek fd 37L Unix.SEEK_SET);
  check(Fingerprint.equal expected (Fingerprint.file_descriptor fd)) "held/path archive MD5 differ";
  check(Unix.LargeFile.lseek fd 0L Unix.SEEK_CUR=37L) "borrowed cursor changed";
  Unix.rename "original.bin" "held-original.bin";
  write "original.bin" (String.make 131072 'b');
  check(Fingerprint.equal expected (Fingerprint.file_descriptor fd)) "replacement changed held MD5";
  check(not(Fingerprint.equal (named()) expected)) "replacement not distinguished";
  check(Unix.LargeFile.lseek fd 0L Unix.SEEK_CUR=37L) "replacement borrowed cursor changed";
  Unix.close fd;
  check(fd_count()=count) "descriptor leaked";
  write "empty.bin" "";
  let fd=Unix.openfile "empty.bin" [Unix.O_RDONLY;Unix.O_CLOEXEC] 0 in
  check(Fingerprint.equal (Fingerprint.file_descriptor fd)
    (Fingerprint.file root (Path.fromString "empty.bin"))) "empty archive MD5 differs";
  Unix.close fd;
  check(fd_count()=count) "empty descriptor leaked";
  print_endline "PASS 8 held-descriptor archive fingerprint/cursor/identity/lifetime controls"
