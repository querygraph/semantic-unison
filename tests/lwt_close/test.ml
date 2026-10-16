module U = Lwt_unix_impl

let check value message = if not value then failwith message
let pending operation = check (Lwt.poll operation = None) "I/O did not block"
let failed operation =
  let failed = try ignore (Lwt.poll operation); false
    with Unix.Unix_error (Unix.EBADF, _, _) -> true in
  check failed "closed I/O did not settle with EBADF"
let succeeded operation = check (Lwt.poll operation = Some ()) "continuation did not settle"
let closed fd =
  let closed = try ignore (Unix.fstat fd); false
    with Unix.Unix_error (Unix.EBADF, _, _) -> true in
  check closed "descriptor not closed before continuation"
let tick () = U.run (U.yield ())
let marker = "new descriptor bytes"
let fill fd =
  let buffer = Bytes.make 8192 'x' in
  let rec loop () =
    try
      check (Unix.write fd buffer 0 (Bytes.length buffer) > 0) "pipe write made no progress";
      loop ()
    with Unix.Unix_error ((Unix.EAGAIN | Unix.EWOULDBLOCK), _, _) -> () in
  loop ()
let empty fd =
  let buffer = Bytes.create 128 in
  let empty = try ignore (Unix.read fd buffer 0 (Bytes.length buffer)); false
    with Unix.Unix_error ((Unix.EAGAIN | Unix.EWOULDBLOCK), _, _) -> true in
  check empty "old operation wrote to reused descriptor"
let write_marker fd =
  check (Unix.write_substring fd marker 0 (String.length marker) = String.length marker)
    "short fixture write"
let read_marker fd =
  let buffer = Bytes.create 128 in
  let count = Unix.read fd buffer 0 (Bytes.length buffer) in
  check (Bytes.sub_string buffer 0 count = marker) "old operation consumed or changed new bytes"

let with_descriptors test =
  let descriptors = ref [] in
  let remember fd = descriptors := fd :: !descriptors; fd in
  let pipe () = let r, w = Unix.pipe ~cloexec:true () in remember r, remember w in
  let socketpair () =
    let a, b = Unix.socketpair Unix.PF_UNIX Unix.SOCK_STREAM 0 in remember a, remember b in
  let cleanup () = List.iter (fun fd -> try Unix.close fd with Unix.Unix_error _ -> ()) !descriptors in
  match test remember pipe socketpair with
  | value -> cleanup (); value
  | exception e -> cleanup (); raise e

let test name run =
  with_descriptors run;
  check (!U.inputs = [] && !U.outputs = []) "closed I/O registration retained";
  Printf.printf "PASS %s\n%!" name

let () =
  test "all blocked pipe reads and readiness waiters settle immediately" (fun _ pipe _ ->
    let reader, _ = pipe () in
    let reader = U.of_unix_file_descr reader in
    let first = U.read reader (Bytes.create 8) 0 8 in
    let second = U.read reader (Bytes.create 8) 0 8 in
    let ready = U.wait_read reader in
    pending first; pending second; pending ready;
    U.close reader;
    failed first; failed second; failed ready);
  test "blocked byte/string writes and readiness waiter settle immediately" (fun _ pipe _ ->
    let _, writer = pipe () in
    let writer = U.of_unix_file_descr writer in
    fill writer;
    let first = U.write writer (Bytes.of_string "old bytes") 0 9 in
    let second = U.write_substring writer "old string" 0 10 in
    let ready = U.wait_write writer in
    pending first; pending second; pending ready;
    U.close writer;
    failed first; failed second; failed ready);
  test "completed write readiness is removed before a later close" (fun _ pipe _ ->
    let _, writer = pipe () in
    let writer = U.of_unix_file_descr writer in
    let ready = U.wait_write writer in
    pending ready; tick (); succeeded ready;
    (* A completed wait must leave the output queue. Otherwise close attempts
       to settle it twice, and a reused fd can inherit its stale registration. *)
    U.close writer;
    succeeded ready);
  test "one socket close settles both input and output registries" (fun _ _ socketpair ->
    let socket, _ = socketpair () in
    let socket = U.of_unix_file_descr socket in
    let reading = U.read socket (Bytes.create 8) 0 8 in
    fill socket;
    let writing = U.write socket (Bytes.of_string "old") 0 3 in
    let input_ready = U.wait_read socket and output_ready = U.wait_write socket in
    let connection = U.check_socket socket in
    pending reading; pending writing;
    U.close socket;
    failed reading; failed writing; failed input_ready; failed output_ready; failed connection);
  test "close settles a pending accept" (fun remember _ _ ->
    let socket = remember (Unix.socket Unix.PF_INET Unix.SOCK_STREAM 0) in
    let socket = U.of_unix_file_descr socket in
    U.bind socket (Unix.ADDR_INET (Unix.inet_addr_loopback, 0)); U.listen socket 1;
    let accepting = U.accept socket in
    pending accepting; U.close socket; failed accepting);
  test "throwing continuation cannot skip sibling I/O settlement" (fun _ _ socketpair ->
    let socket, _ = socketpair () in
    let socket = U.of_unix_file_descr socket in
    let first = U.read socket (Bytes.create 8) 0 8 in
    let second = U.read socket (Bytes.create 8) 0 8 in
    fill socket;
    let writing = U.write socket (Bytes.of_string "old") 0 3 in
    let released = ref false in
    let cleanup = Lwt.catch (fun () -> first)
      (fun _ -> released := true; Lwt.return 0) in
    let throwing = Lwt.catch (fun () -> second)
      (fun _ -> Lwt.fail (Failure "synthetic close continuation")) in
    Lwt.ignore_result throwing;
    let propagated = try U.close socket; false
      with Failure message -> message = "synthetic close continuation" in
    check propagated "continuation error not propagated after close";
    closed socket; failed first; failed second; failed writing;
    check (!released && Lwt.poll cleanup = Some 0) "sibling cleanup skipped");
  test "close syscall error takes precedence after waiters settle" (fun _ pipe _ ->
    let reader, _ = pipe () in
    let reader = U.of_unix_file_descr reader in
    let reading = U.read reader (Bytes.create 8) 0 8 in
    let ready = U.wait_read reader in
    let throwing = Lwt.catch (fun () -> reading)
      (fun _ -> Lwt.fail (Failure "must not replace close error")) in
    Lwt.ignore_result throwing;
    Unix.close reader;
    let preserved = try U.close reader; false
      with Unix.Unix_error (Unix.EBADF, "close", _) -> true in
    check preserved "close syscall error lost";
    failed reading; failed ready);
  test "closed reads never consume bytes from an exactly reused fd" (fun _ pipe _ ->
    let reader, _ = pipe () in
    let reader = U.of_unix_file_descr reader in
    let before = Bytes.make 128 '_' in
    let reading = U.read reader before 0 (Bytes.length before) in
    let fresh_reader, fresh_writer = pipe () in
    U.close reader;
    Unix.dup2 ~cloexec:true fresh_reader reader; Unix.close fresh_reader;
    write_marker fresh_writer; tick ();
    check (before = Bytes.make 128 '_') "old read touched reused fd";
    read_marker reader; failed reading);
  test "closed writes never put bytes onto an exactly reused fd" (fun _ pipe _ ->
    let _, writer = pipe () in
    let writer = U.of_unix_file_descr writer in
    fill writer;
    let writing = U.write writer (Bytes.of_string "old write") 0 9 in
    let text = U.write_substring writer "old string" 0 10 in
    let fresh_reader, fresh_writer = pipe () in
    Unix.set_nonblock fresh_reader;
    U.close writer;
    Unix.dup2 ~cloexec:true fresh_writer writer; Unix.close fresh_writer;
    tick (); empty fresh_reader;
    write_marker writer; read_marker fresh_reader;
    failed writing; failed text);
  test "reentrant close and fresh registration survive old sibling settlement" (fun _ pipe _ ->
    let reader, _ = pipe () in
    let reader = U.of_unix_file_descr reader in
    let before = Bytes.make 128 '_' in
    let sibling = U.read reader before 0 (Bytes.length before) in
    let reading = U.read reader (Bytes.create 8) 0 8 in
    let fresh_reader, fresh_writer = pipe () in
    Unix.set_nonblock fresh_reader;
    let buffer = Bytes.create 128 and fresh = ref None in
    let cleanup = Lwt.catch (fun () -> reading)
      (fun _ ->
        closed reader;
        let reentrant = try U.close reader; false
          with Unix.Unix_error (Unix.EBADF, _, _) -> true in
        check reentrant "reentrant close lost syscall error";
        Unix.dup2 ~cloexec:true fresh_reader reader; Unix.close fresh_reader;
        fresh := Some (U.read reader buffer 0 (Bytes.length buffer));
        Lwt.return 0) in
    U.close reader;
    check (Lwt.poll cleanup = Some 0) "reentrant continuation failed";
    let fresh = match !fresh with Some operation -> operation | None -> failwith "fresh I/O not registered" in
    pending fresh; failed reading; failed sibling;
    write_marker fresh_writer;
    let count = U.run fresh in
    check (Bytes.sub_string buffer 0 count = marker) "fresh I/O registration lost";
    check (before = Bytes.make 128 '_') "old sibling accessed fresh descriptor";
    U.close reader);
  print_endline "Generic Lwt close: blocked I/O, socket/accept waits, exception settlement, exact fd reuse and reentrancy passed."
