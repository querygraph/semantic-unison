(* Original pipe data and real Lwt borrower settlement; no network or SDK. *)
let body_usage lane bytes count message =
 require(!(lane.R.body_bytes)=bytes && !(lane.R.body_count)=count)message
let body_zero () =
 body_usage R.requestInputLane 0 0 "DESIGNATED raw body input retained";
 body_usage R.replyInputLane 0 0 "DESIGNATED raw body input retained"
let body_exhausted f =
 try ignore(f());failwith "body budget ignored"
 with Util.Fatal s->require(s="RPC body input budget exhausted")"wrong body quota refusal"
let () =
 body_zero ();
 let request_mib=Prefs.read R.requestInputMiB and reply_mib=Prefs.read R.replyInputMiB
 and slots=Prefs.read R.bodyInputSlots in
 Prefs.set R.requestInputMiB 1;Prefs.set R.replyInputMiB 1;Prefs.set R.bodyInputSlots 2;
 (* A detached request owns the buffer until its actual processing settles. *)
 with_connection(fun c w->
  let finish=Lwt.wait () in
  send w[R.encodeInt 4;Bytearray.of_string "data",0,4];
  Lwt_unix.run(R.start_body_request c(fun b->
   require(Bytearray.to_string b="data")"request bytes changed";finish));
  body_usage R.requestInputLane 4 1 "DESIGNATED raw request released before borrower";
  R.closeConnection c;
  body_usage R.requestInputLane 4 1 "disconnect released active request borrower";
  Lwt.wakeup finish ();body_zero ());
 (* Legacy requests retain raw input through queued response consumption. *)
 let accepted=ref(Lwt.wait ()) in
 let _queued=R.registerServerCmd "body-queued-request" Umarshal.unit Umarshal.unit
  (fun _ ()->Lwt.wakeup !accepted ();Lwt.return ()) in
 List.iter(fun close_output->with_connection(fun c w->
  accepted:=Lwt.wait ();pause_output c;
  let body=request_body "body-queued-request" Umarshal.unit () in
  send w(R.encodeInt 12202::R.marshalHeader c(R.Request "body-queued-request")
   [R.encodeInt(Bytearray.length body);body,0,Bytearray.length body]);
  let receiving=R.receive c in Lwt_unix.run !accepted;Lwt_unix.run(Lwt_unix.yield());
  body_usage R.requestInputLane (Bytearray.length body) 1 "DESIGNATED queued request input released";
  require(Queue.length c.R.outputQueue.R.writes=1)"queued reply fixture not active";
  if close_output then R.closeConnection c
  else begin R.allowWrites c.R.outputQueue;Lwt_unix.run(Lwt_unix.yield());R.closeConnection c end;
  disconnected receiving;body_zero ())) [false;true];
 (* A reply can arrive before the outgoing request queue fails. No decoder
    starts on the failed send path; its arrived packet must be abandoned. *)
 let queued_client=R.registerServerCmd "body-failed-send" Umarshal.unit Umarshal.unit
  (fun _ ()->Lwt.return ()) in
 with_connection(fun c w->
  pause_output c;let reply=queued_client c () in let id= !(R.ids) in
  let body=Bytearray.of_string("body-failed-send-res"^Umarshal.to_string Umarshal.unit ()) in
  send w(R.encodeInt id::R.marshalHeader c R.NormalResult
   [R.encodeInt(Bytearray.length body);body,0,Bytearray.length body]);
  let receiving=R.receive c in Lwt_unix.run(Lwt_unix.yield());Lwt_unix.run(Lwt_unix.yield());
  body_usage R.replyInputLane (Bytearray.length body) 1 "arrived pre-send reply not retained";
  R.closeConnection c;Lwt_unix.run(Lwt_unix.yield());
  disconnected reply;disconnected receiving;body_zero ());
 (* Two unfinished prefixes consume slots, not reply/header service credits. *)
 with_connection(fun c _->let p=R.receive_body_packet R.requestInputLane c in
  with_connection(fun d _->let q=R.receive_body_packet R.requestInputLane d in
   body_usage R.requestInputLane 0 2 "idle body prefixes uncharged";
   with_connection(fun e _->body_exhausted(fun()->R.receive_body_packet R.requestInputLane e));
   with_connection(fun e w->send w(R.marshalHeader e R.NormalResult []);
    require(Lwt_unix.run(R.receiveHeader e)=R.NormalResult)"full requests blocked header");
   with_connection(fun e w->
    let response=R.wait_for_reply 12200 in
    send w(R.encodeInt 12200::R.marshalHeader e R.NormalResult[R.encodeInt 1;Bytearray.of_string "r",0,1]);
    let receiving=R.receive e in
    let packet=Lwt_unix.run response in
    body_usage R.replyInputLane 1 1 "arrived reply released before consumer";
    require(Lwt_unix.run(R.with_body_packet packet(fun b->Lwt.return(Bytearray.to_string b)))="r")"reply lane changed bytes";
    R.release_body_packet packet; (* idempotent after actual consumer settlement *)
    R.closeConnection e;disconnected receiving);
   R.closeConnection c;R.closeConnection d;header_failed p;header_failed q));
 body_zero ();
 Prefs.set R.bodyInputSlots 3;
 with_connection(fun c w->send w[R.encodeInt 524288];let p=R.receive_body_packet R.requestInputLane c in
  with_connection(fun d x->send x[R.encodeInt 524288];let q=R.receive_body_packet R.requestInputLane d in
   Lwt_unix.run(Lwt_unix.yield());body_usage R.requestInputLane 1048576 2 "exact raw byte allowance not held";
   with_connection(fun e y->send y[R.encodeInt 1];body_exhausted(fun()->Lwt_unix.run(R.receive_body_packet R.requestInputLane e)));
   R.closeConnection c;R.closeConnection d;header_failed p;header_failed q));body_zero ();
 with_connection(fun c w->send w[R.encodeInt 0];
  let packet=Lwt_unix.run(R.receive_body_packet R.requestInputLane c) in
  body_usage R.requestInputLane 0 1 "empty packet slot absent";
  let _,ticket=packet in
  require((try R.reserve_body_bytes ticket 0;false with Invalid_argument _->true))"packet sizing replay accepted";
  Lwt_unix.run(R.with_body_packet packet(fun b->require(Bytearray.length b=0)"empty payload changed";Lwt.return ()));body_zero ());
 with_connection(fun c w->send w[R.encodeInt 1];R.header_test_guard:=Some 0;
  (try ignore(Lwt_unix.run(R.receive_body_packet R.requestInputLane c));failwith "body allocation injection missed"
   with Failure s->require(s="DESIGNATED header payload allocation reached")"wrong body allocation failure");
  R.header_test_guard:=None);body_zero ();
 with_connection(fun c w->send w[R.encodeInt 1];
  (try ignore(Lwt_unix.run(R.receive_body_packet ~reserve:(fun _->failwith "original reserve failure") R.requestInputLane c));failwith "reserve callback ignored"
   with Failure s->require(s="original reserve failure")"reserve cause replaced"));body_zero ();
 (* A real result consumer is already borrowing when another observer throws.
    Handoff failure must not free its live buffer, even after connection close. *)
 with_connection(fun c w->
  let pending=Lwt.wait () and finish=Lwt.wait () in
  R.receivers:=R.MsgIdMap.add 12201 pending !(R.receivers);
  let throwing=Lwt.bind pending(fun _->Lwt.fail(Failure "original reply observer")) in
  Lwt.ignore_result throwing;
  let consumer=BorrowedWork.bind(fun()->pending)(fun packet->
   R.with_body_packet packet(fun b->require(Bytearray.to_string b="z")"handoff bytes changed";finish)) in
  send w(R.encodeInt 12201::R.marshalHeader c R.NormalResult[R.encodeInt 1;Bytearray.of_string "z",0,1]);
  (try ignore(Lwt_unix.run(R.receive c));failwith "reply observer did not fail"
   with Failure s->require(s="original reply observer")"observer cause replaced");
  body_usage R.replyInputLane 1 1 "DESIGNATED handed-off reply released";
  R.closeConnection c;body_usage R.replyInputLane 1 1 "closed connection released live result consumer";
  Lwt.wakeup finish ();require(Lwt.poll consumer=Some ())"reply borrower did not settle";body_zero ());
 (* Ordinary stream errors still abort normally; charge lasts through the
    queued abort write and releases only when that actual output settles. *)
 with_connection(fun c w->
  let called=Lwt.wait () in
  R.serverStreams:=Util.StringMap.add "body-stream-abort"
   (fun _ _->Lwt.wakeup called ();raise(Failure "ordinary stream failure")) !(R.serverStreams);
  let output_finish=Lwt.wait () in
  let active_output=R.performOutput c.R.outputQueue R.Normal(fun()->output_finish) in
  pause_output c;
  send w(R.encodeInt 12203::R.marshalHeader c(R.Stream "body-stream-abort")
   [R.encodeInt 1;Bytearray.of_string "s",0,1]);
  let receiving=R.receive c in Lwt_unix.run called;Lwt_unix.run(Lwt_unix.yield());
  body_usage R.requestInputLane 1 1 "stream released before abort output";
  require(Queue.length c.R.outputQueue.R.urgentWrites=1)"abort output not queued";
  R.closeConnection c;disconnected receiving;body_zero ();
  Lwt.wakeup output_finish ();disconnected active_output);
 R.resetStreamErroState ();
 List.iter(fun(mib,slot)->Prefs.set R.requestInputMiB mib;Prefs.set R.bodyInputSlots slot;
  with_connection(fun c _->
   try ignore(R.receive_body_packet R.requestInputLane c);failwith "invalid raw body budget accepted"
   with Util.Fatal s->require(s="Invalid RPC body input budget")"wrong raw budget refusal"))
  [0,2;max_int,2;1,0;1,65537];
 Prefs.set R.requestInputMiB request_mib;Prefs.set R.replyInputMiB reply_mib;Prefs.set R.bodyInputSlots slots;
 body_zero ();
 let codec=Umarshal.(list(prod3 string bool string id id)) in
 let names=["rpcrequestinputbudget";"rpcreplyinputbudget";"rpcbodyinputslots"] in
 let raw=Umarshal.from_string codec(Umarshal.to_string Prefs.mdumpedPrefs(Prefs.dump 1))0 in
 require(not(List.exists(fun(n,_,_)->List.mem n names)raw))"raw budgets exported";
 let wire=Umarshal.from_string Prefs.mdumpedPrefs(Umarshal.to_string codec(List.map(fun n->n,false,"bad payload")names))0 in
 Prefs.load wire 999;
 require(Prefs.read R.requestInputMiB=request_mib && Prefs.read R.replyInputMiB=reply_mib && Prefs.read R.bodyInputSlots=slots)"peer changed raw budgets";
 print_endline "RPC raw bodies: independent request/reply lanes, detached borrowers, prefix/byte/empty admission, allocation rollback and observer handoff PASS"
