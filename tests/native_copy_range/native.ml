module C = CopyRange
let check condition message = if not condition then failwith message
let tests=ref 0 and serial=ref 0
let test name body =
  (try body () with error -> Printf.eprintf "FAIL %s\n%!" name;raise error);
  incr tests;Printf.printf "PASS %s\n%!" name
let fds () = Array.length (Sys.readdir "/dev/fd")
let bytes path = let input=open_in_bin path in
  Fun.protect ~finally:(fun () -> close_in input)
    (fun () -> really_input_string input (in_channel_length input))
let write_all fd text =
  let rec loop offset = if offset<String.length text then begin
    let n=Unix.write_substring fd text offset (String.length text-offset) in
    check (n>0) "fixture write stopped";loop (offset+n)
  end in loop 0
let stat_identity fd =
  let s=Unix.LargeFile.fstat fd in
  s.Unix.LargeFile.st_dev,s.st_ino,s.st_kind,s.st_size,s.st_perm,s.st_nlink,
    s.st_uid,s.st_gid,s.st_mtime,s.st_ctime
let fixture directory body =
  incr serial;
  let source=Filename.concat directory ("source-"^string_of_int !serial)
  and destination=Filename.concat directory ("destination-"^string_of_int !serial) in
  let input=Unix.openfile source [Unix.O_CREAT;Unix.O_EXCL;Unix.O_RDWR;Unix.O_CLOEXEC] 0o600 in
  let output=Unix.openfile destination [Unix.O_CREAT;Unix.O_EXCL;Unix.O_RDWR;Unix.O_CLOEXEC] 0o600 in
  Fun.protect ~finally:(fun () -> Unix.close input;Unix.close output;
    Unix.unlink source;Unix.unlink destination)
    (fun () ->
      write_all input (String.init 64 (fun i -> Char.chr ((i*73+19) land 255)));
      write_all output (String.make 97 '#');
      ignore (Unix.LargeFile.lseek input 3L Unix.SEEK_SET);
      ignore (Unix.LargeFile.lseek output 11L Unix.SEEK_SET);
      let before_source=bytes source and before_destination=bytes destination in
      let a=stat_identity input and b=stat_identity output in
      let verify () =
        check (stat_identity input=a && stat_identity output=b) "strict native call changed identity/EOF/metadata or closed a borrowed FD";
        check (Unix.LargeFile.lseek input 0L Unix.SEEK_CUR=3L &&
               Unix.LargeFile.lseek output 0L Unix.SEEK_CUR=11L) "strict native call changed borrowed FD position";
        check (bytes source=before_source && bytes destination=before_destination) "strict native call changed fixture bytes" in
      body input output source destination verify)
let result input output offset length =
  C.decode_native (NativeApi.copy_file_status input output offset length)
let failed phase errno = function
  | C.Native_failed (0,c) ->
      check (c.phase=phase && c.errno=Some errno && c.mutation=C.No_effect &&
             c.native_code>0L) "strict failure scope/errno/no-effect receipt changed"
  | _ -> failwith "invalid call became success/decline"
let declined = function
  | C.Native_declined (0,C.Platform_unavailable,c) ->
      check (c.backend=C.Platform && c.phase=C.Unavailable &&
             c.errno=None && c.mutation=C.No_effect && c.native_code=0L)
        "platform decline ABI/scope changed"
  | _ -> failwith "valid macOS operation did not produce platform decline"

let () =
  let directory=Sys.argv.(1) in
  let initial=fds () in
  test "actual macOS native ABI reports platform decline with no file or FD effects" (fun () ->
    fixture directory (fun input output _ _ verify ->
      for _=1 to 100 do declined (result input output 5L 19) done;
      verify ()));
  test "platform decline does not extend destination EOF" (fun () ->
    fixture directory (fun input output source destination verify ->
      (* Eleven is the output cursor. A request of 64 bytes would extend a
         short output, but unavailable native acceleration must not do so. *)
      let shorter=Unix.openfile destination [Unix.O_WRONLY;Unix.O_CLOEXEC] 0 in
      Fun.protect ~finally:(fun () -> Unix.close shorter) (fun () ->
        Unix.LargeFile.ftruncate shorter 20L;
        let before=bytes destination and before_source=bytes source in
        let a=stat_identity input and b=stat_identity output in
        declined (result input output 0L 64);
        check ((Unix.LargeFile.fstat output).Unix.LargeFile.st_size=20L) "platform decline extended EOF";
        check (bytes destination=before && bytes source=before_source &&
               stat_identity input=a && stat_identity output=b) "platform decline changed files or closed a borrowed FD";
        check (Unix.LargeFile.lseek input 0L Unix.SEEK_CUR=3L &&
               Unix.LargeFile.lseek output 0L Unix.SEEK_CUR=11L) "platform decline moved cursor");
      ignore verify));
  test "zero request and exact source EOF have explicit no-effect success" (fun () ->
    fixture directory (fun input output _ _ verify ->
      List.iter (fun offset -> match result input output offset 0 with
        | C.Native_progress (0,c) -> check (c.phase=C.Arguments && c.errno=None &&
            c.mutation=C.No_effect && c.native_code=0L) "empty native result changed"
        | _ -> failwith "empty native result failed") [0L;64L];
      verify ()));
  test "negative arguments and source offset arithmetic overflow reject without effects" (fun () ->
    fixture directory (fun input output _ _ verify ->
      List.iter (fun (offset,length) -> failed C.Arguments Unix.EINVAL (result input output offset length))
        [-1L,1;0L,-1;Int64.max_int,1];verify ()));
  test "source EOF bounds reject without effects" (fun () ->
    fixture directory (fun input output _ _ verify ->
      List.iter (fun (offset,length) -> failed C.Arguments Unix.EINVAL (result input output offset length))
        [65L,0;64L,1;63L,2];verify ()));
  test "closed source descriptor is operational EBADF rather than unavailable" (fun () ->
    fixture directory (fun input output source _ verify ->
      let closed=Unix.openfile source [Unix.O_RDONLY;Unix.O_CLOEXEC] 0 in Unix.close closed;
      failed C.Descriptors Unix.EBADF (result closed output 5L 19);verify ();ignore input));
  test "closed destination descriptor is operational EBADF rather than unavailable" (fun () ->
    fixture directory (fun input output _ destination verify ->
      let closed=Unix.openfile destination [Unix.O_WRONLY;Unix.O_CLOEXEC] 0 in Unix.close closed;
      failed C.Descriptors Unix.EBADF (result input closed 5L 19);verify ();ignore output));
  test "write-only source and read-only destination reject without effects" (fun () ->
    fixture directory (fun input output source destination verify ->
      let write_only=Unix.openfile source [Unix.O_WRONLY;Unix.O_CLOEXEC] 0 in
      Fun.protect ~finally:(fun () -> Unix.close write_only)
        (fun () -> failed C.Descriptors Unix.EBADF (result write_only output 5L 19));
      let read_only=Unix.openfile destination [Unix.O_RDONLY;Unix.O_CLOEXEC] 0 in
      Fun.protect ~finally:(fun () -> Unix.close read_only)
        (fun () -> failed C.Descriptors Unix.EBADF (result input read_only 5L 19));verify ()));
  test "append destination is a no-effect descriptor error" (fun () ->
    fixture directory (fun input _ _ destination verify ->
      let append=Unix.openfile destination [Unix.O_WRONLY;Unix.O_APPEND;Unix.O_CLOEXEC] 0 in
      Fun.protect ~finally:(fun () -> Unix.close append)
        (fun () -> failed C.Descriptors Unix.EINVAL (result input append 5L 19));verify ()));
  test "same descriptor and separate descriptors for the same inode reject" (fun () ->
    fixture directory (fun input _ source _ verify ->
      failed C.Descriptors Unix.EINVAL (result input input 5L 19);
      let alias=Unix.openfile source [Unix.O_RDWR;Unix.O_CLOEXEC] 0 in
      Fun.protect ~finally:(fun () -> Unix.close alias)
        (fun () -> failed C.Descriptors Unix.EINVAL (result input alias 5L 19));verify ()));
  test "pipe source and destination are errors before any transfer" (fun () ->
    fixture directory (fun input output _ _ verify ->
      let pipe_read,pipe_write=Unix.pipe ~cloexec:true () in
      Fun.protect ~finally:(fun () -> Unix.close pipe_read;Unix.close pipe_write)
        (fun () -> failed C.Descriptors Unix.EINVAL (result pipe_read output 0L 1);
          failed C.Descriptors Unix.EINVAL (result input pipe_write 0L 1));verify ()));
  test "directory source and destination are errors before any transfer" (fun () ->
    fixture directory (fun input output _ _ verify ->
      let dir=Unix.openfile directory [Unix.O_RDONLY;Unix.O_CLOEXEC] 0 in
      Fun.protect ~finally:(fun () -> Unix.close dir)
        (fun () -> failed C.Descriptors Unix.EINVAL (result dir output 0L 1);
          failed C.Descriptors Unix.EINVAL (result input dir 0L 1));verify ()));
  test "legacy primitive retains its unavailable Unix_error ABI and no-effect behavior" (fun () ->
    fixture directory (fun input output _ _ verify ->
      let rejected=try ignore (NativeApi.copy_file input output 5L 19);false
        with Unix.Unix_error (Unix.ENOSYS,operation,_) -> operation="copy_file" in
      check rejected "legacy range API changed";verify ()));
  Gc.full_major ();check (fds ()=initial) "native ABI fixtures leaked descriptors";
  Printf.printf "Strict native range ABI: %d macOS groups; no other-platform or sharing claim\n%!" !tests
