(* Exact role-tag/body caps on original unit payloads; no transport process. *)
let () =
 let name="stream-cap-exact"and calls=ref 0 in
 let codec=R.defaultMarshalingFunctions Umarshal.string in
 let payload=String.length(Umarshal.to_string Umarshal.string "abc")in
 let _stream=R.registerStreamCmd ~maxPayload:payload name codec(fun _ value->
   require(value="abc")"custom stream payload changed";incr calls)in
 let stream_cap=String.length(name^"-str")+payload
 and request_cap=String.length(name^"-args")+payload in
 require(Util.StringMap.find name !(R.serverStreamLimits)=stream_cap)
   "stream payload/tag cap incorrect";
 require(Util.StringMap.find name !(R.serverArgLimits)=request_cap)
   "nonstream fallback payload/tag cap incorrect";
 List.iter(fun is_stream->
  with_connection(fun c w->
   let body=if is_stream then Bytearray.of_string(name^"-str"^Umarshal.to_string Umarshal.string "abc")
            else request_body name Umarshal.string "abc"in
   let header=if is_stream then R.Stream name else R.Request name in
   send w(R.encodeInt 12400::R.marshalHeader c header
     [R.encodeInt(Bytearray.length body);body,0,Bytearray.length body]);
   let receiving=R.receive c in Lwt_unix.run(Lwt_unix.yield());
   require(!calls=(if is_stream then 1 else 2))"exact stream/fallback cap refused";
   R.closeConnection c;disconnected receiving;
   require(!(R.requestInputLane.R.body_count)=0&& !(R.bounded_input_count)=0)
     "exact custom stream body leaked raw ownership")) [true;false];
 let previous=Prefs.read R.packetMaxBytes in
 Prefs.set R.packetMaxBytes 1024;
 List.iter(fun is_stream->with_connection(fun c w->
   let cap=if is_stream then stream_cap else request_cap in
   (* Guard the old path before allocation/read if its command limit is lost. *)
   R.header_test_guard:=Some cap;
   let header=if is_stream then R.Stream name else R.Request name in
   send w(R.encodeInt 12401::R.marshalHeader c header[R.encodeInt(cap+1)]);
   exceeds(fun()->Lwt_unix.run(R.receive c));
   require(!calls=2)"oversized custom packet reached handler";
   require(!(R.requestInputLane.R.body_count)=0&& !(R.bounded_input_count)=0)
     "oversized custom packet retained a known closed input")) [true;false];
 R.header_test_guard:=None;Prefs.set R.packetMaxBytes previous;
 List.iter(fun invalid->
  let before=Util.StringMap.cardinal !(R.serverCmds)in
  (try let _client=R.registerStreamCmd ~maxPayload:invalid "invalid-stream-cap" codec(fun _ _->())in
    failwith "invalid stream cap accepted"
   with Invalid_argument _->());
  require(Util.StringMap.cardinal !(R.serverCmds)=before)
    "invalid cap mutated command registry") [-1;max_int];
 let _empty=R.registerStreamCmd ~maxPayload:0 "zero-stream-cap" codec(fun _ _->())in
 require(Util.StringMap.find "zero-stream-cap" !(R.serverStreamLimits)=String.length"zero-stream-cap-str")
   "zero custom payload policy changed tag size";
 print_endline "RPC custom stream limits: exact cap, stream/fallback oversize before allocation, raw settlement and invalid registration PASS"
