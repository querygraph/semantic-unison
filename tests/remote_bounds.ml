module R = RemoteForTest
type mutable_resource = { mutable value : int; closed : int ref }
let require value message = if not value then failwith message
let send fd chunks = List.iter (fun (b,p,n) ->
  let s = Bytearray.sub b p n in
  require (Unix.write_substring fd s 0 n = n) "short test write") chunks
let with_connection ?(blocked_output=false) f =
  let input,writer = Lwt_unix.pipe_in () in
  let reader,output = if blocked_output then
    let reader,output = Lwt_unix.pipe_out () in Some reader,output
  else None,Lwt_unix.of_unix_file_descr (Unix.openfile "/dev/null" [Unix.O_WRONLY] 0) in
  let conn = R.makeConnection false input output in
  conn.R.version <- 1;
  let cleanup () = Unix.close writer; R.closeConnection conn;
    match reader with None -> () | Some fd -> Unix.close fd in
  match f conn writer with
  | x -> cleanup (); x
  | exception e -> cleanup (); raise e
let disconnected thread =
  try ignore (Lwt.poll thread); failwith "disconnected operation did not fail"
  with Util.Fatal message ->
    require (message = "Lost connection with the server") "wrong disconnect error"
let exceeds f =
  match f () with
  | _ -> failwith "oversized frame accepted"
  | exception Util.Fatal message ->
    require (message = "RPC packet length exceeds command limit") "wrong rejection"
let request_body name codec value =
  Bytearray.of_string (name ^ "-args" ^ Umarshal.to_string codec value)
let request_id n = let b,_,_ = R.encodeInt n in b
let pause_output conn = conn.R.outputQueue.R.canWrite <- false

let test_reply_scopes () =
  let active = ref 0 and calls = ref 0 and mode = ref `Success in
  let delayed = ref (Lwt.wait ()) in
  let scope _ value f =
    require (value = 7) "scope received wrong decoded arguments";
    if !mode = `Before then Lwt.fail (Util.Transient "scope admission failed") else begin
      incr active;
      Lwt.try_bind f
        (fun () -> decr active; Lwt.return ())
        (fun e -> decr active; Lwt.fail e)
    end in
  let _command = R.registerBoundedServerCmd ~withScope:scope "scope-test"
    ~maxArgs:64 ~maxResult:1100000 Umarshal.int Umarshal.string
    (fun _ _ -> incr calls;
      if !mode = `Command then Lwt.fail (Util.Transient "command failed")
      else if !mode = `Delayed then !delayed
      else Lwt.return (if !mode = `Large then String.make 1048576 'x' else "result")) in
  let dispatch conn =
    R.processRequest conn (request_id 991) "scope-test"
      (request_body "scope-test" Umarshal.int 7) in
  let detached conn =
    R.processDetachedRequest conn (request_id 992) "scope-test"
      (request_body "scope-test" Umarshal.int 7) in
  List.iter (fun selected ->
    mode := selected; calls := 0;
    with_connection (fun conn _ ->
      pause_output conn;
      let finished = dispatch conn in
      require (Lwt.poll finished = None) "scope did not await queued reply";
      require (!active = (if selected = `Before then 0 else 1))
        "scope released before output consumed";
      require (!calls = (if selected = `Before then 0 else 1))
        "scope admission did not control server dispatch";
      require (Queue.length conn.R.outputQueue.R.writes = 1) "expected exactly one reply";
      R.allowWrites conn.R.outputQueue;
      Lwt_unix.run finished;
      require (!active = 0) "scope leaked after reply completion"))
    [`Success; `Command; `Before];
  mode := `Success;
  with_connection (fun conn _ ->
    pause_output conn;
    let first = dispatch conn and second = dispatch conn in
    R.closeConnection conn;
    disconnected first; disconnected second;
    require (!active = 0) "scope leaked on output failure";
    require (Queue.is_empty conn.R.outputQueue.R.writes)
      "closed output retained replies or appended an exception reply");
  mode := `Large;
  with_connection ~blocked_output:true (fun conn _ ->
    let first = dispatch conn and second = dispatch conn in
    require (Lwt.poll first = None && Lwt.poll second = None && !active = 2)
      "test did not retain active and queued replies";
    let closes = ref 0 in
    R.registerIOClose (R.connectionIO conn) (fun () -> incr closes; R.clientConnClose conn);
    R.lostConnectionHandler conn.R.outputBuffer.R.channel;
    disconnected first; disconnected second;
    require (!closes = 1 && !active = 0) "connection cleanup re-entered or stranded a scope";
    require (Queue.is_empty conn.R.outputQueue.R.writes) "active write failure did not drain queue";
    let before = !calls in
    disconnected (dispatch conn);
    require (!calls = before) "closed connection started another command";
    disconnected (R.performOutput conn.R.outputQueue R.Normal
      (fun () -> failwith "closed queue ran another output action")));
  with_connection (fun old _ ->
    mode := `Delayed; delayed := Lwt.wait ();
    let finished = detached old in
    Lwt.ignore_result finished;
    R.closeConnection old;
    require (!active=1) "closed connection released a still-active borrower";
    with_connection (fun current _ ->
      mode := `Success; Lwt_unix.run (detached current);
      Lwt.wakeup !delayed "late old result";
      require (Lwt.poll finished=Some () && !active=0)
        "late old-session result escaped into the new owner loop"));
  with_connection (fun old _ ->
    mode := `Delayed; delayed := Lwt.wait ();
    let finished = detached old in
    R.closeConnection old;
    Lwt.wakeup_exn !delayed (Failure "unrelated old-session failure");
    (try ignore (Lwt.poll finished); failwith "unrelated error swallowed"
     with Failure why -> require (why="unrelated old-session failure") "wrong unrelated error");
    require (!active=0) "failed late borrower retained scope")

let test_dynamic_reply_bounds () =
  let command = R.registerBoundedServerCmd "dynamic-bound-test"
    ~maxResultForArgs:(fun n -> n) ~maxArgs:64 ~maxResult:96
    Umarshal.int Umarshal.unit (fun _ _ -> Lwt.return ()) in
  List.iter (fun (requested,limit) ->
    with_connection (fun conn fd ->
      ignore (command conn requested);
      let id = !(R.ids) in
      require (R.MsgIdMap.find id !(R.receiverLimits) = limit)
        "argument-specific reply limit missing or above command cap";
      send fd (R.encodeInt id :: R.marshalHeader conn R.NormalResult [R.encodeInt (limit+1)]);
      exceeds (fun () -> Lwt_unix.run (R.receive conn)));
    R.resetReceivers ()) [32,32; 999,96];
  with_connection (fun conn _ ->
    let before = !(R.ids) in
    (try ignore (command conn (-1)); failwith "negative dynamic limit accepted"
     with Invalid_argument _ -> ());
    require (!(R.ids) = before && R.MsgIdMap.is_empty !(R.receivers))
      "invalid bound registered an outstanding request");
  with_connection (fun conn _ ->
    let reply = command conn 32 in
    require (Lwt.poll reply = None) "test reply did not wait for peer";
    R.clientConnClose conn;
    let failed = Lwt.catch (fun () -> Lwt.bind reply (fun _ -> Lwt.return false))
      (function Util.Fatal _ -> Lwt.return true | e -> Lwt.fail e) in
    require (Lwt_unix.run failed) "disconnect stranded pending RPC consumer";
    require (R.MsgIdMap.is_empty !(R.receivers) && R.MsgIdMap.is_empty !(R.receiverLimits))
      "disconnect retained reply registrations")

let test_output_failure () =
  let q = R.makeOutputQueue false (fun _ -> Lwt.return ()) in
  q.R.canWrite <- false;
  let ran = ref false in
  let first = R.performOutput q R.Normal (fun () -> Lwt.fail Sys.Break) in
  let second = R.performOutput q R.Normal (fun () -> ran := true; Lwt.return ()) in
  q.R.canWrite <- true;
  (try Lwt_unix.run (R.popOutputQueues q); failwith "output failure swallowed"
   with Sys.Break -> ());
  List.iter (fun promise ->
    try ignore (Lwt.poll promise); failwith "failed output left a sleeping waiter"
    with Sys.Break -> ()) [first;second];
  require (not !ran && Queue.is_empty q.R.writes) "failed queue ran or retained later output"
let () =
  let close resource = incr resource.closed in
  let resources = R.resourceWithConnCleanup close close in
  let a = resources.register {value=0;closed=ref 0}
  and b = resources.register {value=0;closed=ref 0} in
  a.value <- 99;
  resources.release a;
  R.clientCloseRootConnection (Common.Local,Fspath.canonize (Some (Sys.getcwd ())));
  require (!(a.closed) = 1 && !(b.closed) = 1) "mutable/equal resources confused during cleanup";
  List.iter (fun s ->
    let ordinary = Umarshal.to_string Umarshal.string s in
    require (ordinary = Umarshal.to_string (Umarshal.bounded_string 1000) s)
      "legacy string encoding changed";
    require (Umarshal.from_string (Umarshal.bounded_string 1000) ordinary 0 = s)
      "bounded string decode") ["";"abc";String.make 1000 'x'];
  let oversized = Umarshal.to_string Umarshal.int (1 lsl 30) in
  (try ignore (Umarshal.from_string (Umarshal.bounded_string 64) oversized 0);
       failwith "field allocation limit ignored"
   with Umarshal.Error message -> require (message = "bounded_string: length exceeds limit")
       "field did not reject before reading absent contents");
  with_connection (fun conn fd ->
    send fd [R.encodeInt 3;Bytearray.of_string "abc",0,3];
    require (Bytearray.to_string (Lwt_unix.run (R.receivePacket ~maxBytes:3 conn)) = "abc")
      "valid bounded frame changed");
  let _command = R.registerBoundedServerCmd "bound-test" ~maxArgs:64 ~maxResult:96
    Umarshal.unit Umarshal.unit (fun _ () -> Lwt.return ()) in
  with_connection (fun conn fd ->
    send fd (R.encodeInt 777 :: R.marshalHeader conn (R.Request "bound-test") [R.encodeInt (1 lsl 30)]);
    exceeds (fun () -> Lwt_unix.run (R.receive conn)));
  with_connection (fun conn fd ->
    ignore (R.wait_for_reply ~maxBytes:96 888);
    send fd (R.encodeInt 888 :: R.marshalHeader conn R.NormalResult [R.encodeInt (1 lsl 30)]);
    exceeds (fun () -> Lwt_unix.run (R.receive conn)));
  R.resetReceivers ();
  test_reply_scopes ();
  test_dynamic_reply_bounds ();
  test_output_failure ();
  print_endline "RPC bounds/scopes: bounded allocation, per-profile reply limits, queued output lifetime and error cleanup"
