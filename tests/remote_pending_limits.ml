(* Pending metadata admission; original paused outputs and pipe replies only. *)
let () =
 R.resetReceivers();
 let previous=Prefs.read R.pendingReplySlots in Prefs.set R.pendingReplySlots 2;
 let marshals=ref 0 in
 let codec=Umarshal.prod2 Umarshal.unit Umarshal.unit
   (fun ()->incr marshals;((),()))(fun((),())->())in
 let command=R.registerServerCmd "pending-limit-fixture" codec Umarshal.unit
   (fun _ ()->Lwt.return())in
 with_connection(fun c _->
  pause_output c;
  let first=command c()and second=command c()in
  let id= !(R.ids)and writes=Queue.length c.R.outputQueue.R.writes in
  require(R.MsgIdMap.cardinal !(R.receivers)=2 && !marshals>0)"pending fixture not full";
  let before_marshals= !marshals in
  let refused=try ignore(command c());false with
   Util.Transient why->require(why="RPC pending reply budget exhausted")"wrong pending refusal";true in
  require refused "DESIGNATED pending reply cap ignored";
  require(!marshals=before_marshals)"DESIGNATED full registry marshaled new request";
  require(!(R.ids)=id && Queue.length c.R.outputQueue.R.writes=writes)
    "full registry changed request id/output queue";
  require(R.MsgIdMap.cardinal !(R.receivers)=2)"full registry changed prior waiters";
  R.clientConnClose c;Lwt_unix.run(Lwt_unix.yield());
  disconnected first;disconnected second;
  require(R.MsgIdMap.is_empty !(R.receivers)&&R.MsgIdMap.is_empty !(R.receiverLimits))
    "disconnect stranded pending metadata");
 let original=R.wait_for_reply ~maxBytes:17 12500 in
 let stored=R.MsgIdMap.find 12500 !(R.receivers)in
 let refused=try ignore(R.wait_for_reply ~maxBytes:18 12500);false with
   Util.Fatal why->require(why="RPC reply id already pending")"wrong duplicate refusal";true in
 require refused "DESIGNATED duplicate pending id replaced";
 require(R.MsgIdMap.find 12500 !(R.receivers)==stored &&
         R.MsgIdMap.find 12500 !(R.receiverLimits)=17 && Lwt.poll stored=None)
   "duplicate refusal mutated original waiter/limit";
 let delivered=R.find_receiver 12500 in
 require(R.MsgIdMap.is_empty !(R.receivers)&&R.MsgIdMap.is_empty !(R.receiverLimits))
   "response handoff retained registry entries";
 Lwt.wakeup_exn delivered(Util.Transient"original waiter delivery");
 (try ignore(Lwt_unix.run original);failwith "original waiter not delivered"
  with Util.Transient why->require(why="original waiter delivery")"original delivery changed");
 (* Actual normal reply handoff frees metadata, while raw bytes stay with their
    independently owned body ticket until its consumer releases them. *)
 with_connection(fun c w->
  let reply=R.wait_for_reply ~maxBytes:1 12501 in
  send w(R.encodeInt 12501::R.marshalHeader c R.NormalResult
    [R.encodeInt 1;Bytearray.of_string"x",0,1]);
  let receiving=R.receive c in let packet=Lwt_unix.run reply in
  require(R.MsgIdMap.is_empty !(R.receivers))"normal reply retained pending slot";
  require(!(R.replyInputLane.R.body_count)=1)"slot release prematurely released raw reply";
  let probe=R.wait_for_reply 12502 in
  let pending=R.find_receiver 12502 in Lwt.wakeup_exn pending(Util.Transient"probe closed");
  (try ignore(Lwt_unix.run probe)with Util.Transient _->());
  R.release_body_packet packet;
  R.closeConnection c;disconnected receiving);
 List.iter(fun invalid->Prefs.set R.pendingReplySlots invalid;
  (try ignore(R.wait_for_reply 12503);failwith "invalid pending policy accepted"
   with Util.Fatal why->require(why="Invalid RPC pending reply budget")"wrong invalid policy error");
  require(R.MsgIdMap.is_empty !(R.receivers))"invalid policy created waiter") [0;-1;65537];
 Prefs.set R.pendingReplySlots 2;
 (try ignore(R.wait_for_reply ~maxBytes:(-1)12504);failwith "negative reply limit accepted"
  with Invalid_argument _->());
 require(R.MsgIdMap.is_empty !(R.receivers))"bad reply limit created waiter";
 Prefs.set R.pendingReplySlots previous;
 let codec=Umarshal.(list(prod3 string bool string id id))in
 let raw=Umarshal.from_string codec
   (Umarshal.to_string Prefs.mdumpedPrefs(Prefs.dump 1))0 in
 require(not(List.exists(fun(name,_,_)->name="rpcpendingreplyslots")raw))"pending policy exported";
 let poisoned=Umarshal.from_string Prefs.mdumpedPrefs
   (Umarshal.to_string codec["rpcpendingreplyslots",false,"bad"])0 in
 Prefs.load poisoned 999;
 require(Prefs.read R.pendingReplySlots=previous)"peer changed pending policy";
 print_endline "RPC pending metadata: finite admission before marshaling, duplicate preservation, response/disconnect settlement and endpoint policy PASS"
