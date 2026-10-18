(* Appended to the private RPC participant; tiny generated pipe data only. *)
let () =
 let old=Prefs.read R.packetMaxBytes in
 Prefs.set R.packetMaxBytes 8;R.header_test_guard:=Some 8;
 with_connection(fun c w->send w[R.encodeInt 8;Bytearray.of_string "12345678",0,8];
  require(Bytearray.to_string(Lwt_unix.run(R.receivePacket c))="12345678") "global exact frame changed");
 with_connection(fun c w->send w[R.encodeInt 0];
  require(Bytearray.length(Lwt_unix.run(R.receivePacket c))=0) "empty frame changed");
 List.iter(fun specific->with_connection(fun c w->send w[R.encodeInt 9];
  exceeds(fun()->Lwt_unix.run(R.receivePacket ?maxBytes:specific c))))[None;Some 100];
 with_connection(fun c w->send w[R.encodeInt 4];
  exceeds(fun()->Lwt_unix.run(R.receivePacket ~maxBytes:3 c)));
 (* Finite endpoint refusal must precede reserve and any payload allocation. *)
 with_connection(fun c w->send w[R.encodeInt 9];
  exceeds(fun()->Lwt_unix.run(R.receivePacket ~reserve:(fun _->failwith "reserve preceded outer cap") c)));
 Prefs.set R.packetMaxBytes 128;R.header_test_guard:=Some 128;
 (* Small legacy traffic still reaches its actual reader/dispatcher. *)
 with_connection(fun c w->
  let response=R.wait_for_reply 12100 in
  send w(R.encodeInt 12100::R.marshalHeader c R.NormalResult
   [R.encodeInt 3;Bytearray.of_string "abc",0,3]);
  let receiving=R.receive c in
  let packet=Lwt_unix.run response in
  require(Lwt_unix.run(R.with_body_packet packet(fun buf->Lwt.return(Bytearray.to_string buf)))="abc") "legacy reply payload changed";
  R.closeConnection c;disconnected receiving);
 let accepted=Lwt.wait () in
 let _client=R.registerServerCmd "packet-valid-request" Umarshal.unit Umarshal.unit
  (fun _ ()->Lwt.wakeup accepted ();Lwt.return ()) in
 with_connection(fun c w->
  let body=request_body "packet-valid-request" Umarshal.unit () in
  send w(R.encodeInt 12101::R.marshalHeader c(R.Request "packet-valid-request")
   [R.encodeInt(Bytearray.length body);body,0,Bytearray.length body]);
  let receiving=R.receive c in Lwt_unix.run accepted;
  Lwt_unix.run(Lwt_unix.yield());R.closeConnection c;disconnected receiving);
 let streamed=Lwt.wait () in
 let _stream=R.registerStreamCmd "packet-valid-stream"
  (R.defaultMarshalingFunctions Umarshal.unit) (fun _ ()->Lwt.wakeup streamed ()) in
 with_connection(fun c w->
  let body=Bytearray.of_string("packet-valid-stream-str"^Umarshal.to_string Umarshal.unit ()) in
  send w(R.encodeInt 12102::R.marshalHeader c(R.Stream "packet-valid-stream")
   [R.encodeInt(Bytearray.length body);body,0,Bytearray.length body]);
  let receiving=R.receive c in Lwt_unix.run streamed;
  R.closeConnection c;disconnected receiving);
 (* None of the three previously unbounded receive branches can bypass it. *)
 with_connection(fun c w->send w(R.encodeInt 12001::R.marshalHeader c(R.Request "legacy_header_only")[R.encodeInt 129]);
  exceeds(fun()->Lwt_unix.run(R.receive c)));
 with_connection(fun c w->ignore(R.wait_for_reply 12002);
  send w(R.encodeInt 12002::R.marshalHeader c R.NormalResult[R.encodeInt 129]);
  exceeds(fun()->Lwt_unix.run(R.receive c)));
 with_connection(fun c w->send w(R.encodeInt 12003::R.marshalHeader c(R.Stream "legacy_stream_only")[R.encodeInt 129]);
  exceeds(fun()->Lwt_unix.run(R.receive c)));
 header_usage 0 0;
 List.iter(fun n->Prefs.set R.packetMaxBytes n;
  with_connection(fun c _->
   try ignore(R.receivePacket c);failwith "invalid global frame policy accepted"
   with Util.Fatal s->require(s="Invalid RPC packet input limit") "wrong packet policy refusal")) [0;-1];
 (* A representable positive bigarray policy is not an OCaml-string limit.
    Only an empty packet is read; never allocate a max_int payload. *)
 Prefs.set R.packetMaxBytes max_int;
 with_connection(fun c w->send w[R.encodeInt 0];
  require(Bytearray.length(Lwt_unix.run(R.receivePacket c))=0) "large finite packet policy rejected");
 Prefs.set R.packetMaxBytes old;R.header_test_guard:=None;
 let codec=Umarshal.(list(prod3 string bool string id id)) in
 let raw=Umarshal.from_string codec(Umarshal.to_string Prefs.mdumpedPrefs(Prefs.dump 1))0 in
 require(not(List.exists(fun(n,_,_)->n="rpcpacketmaxbytes")raw)) "packet pref exported";
 let wire=Umarshal.from_string Prefs.mdumpedPrefs
  (Umarshal.to_string codec["rpcpacketmaxbytes",false,"bad payload"])0 in
 Prefs.load wire 999;
 require(Prefs.read R.packetMaxBytes=old) "packet pref peer poisoned";
 print_endline "RPC packets: global outer limit, stricter explicit limits, legacy request/reply/stream routes and endpoint isolation PASS"
