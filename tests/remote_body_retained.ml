(* Last case: a synthetic typed carrier, no directory/FD ever acquired.
   Logical retained guards intentionally survive until this process exits. *)
exception Body_plugin_uncertain
let () =
 body_zero ();
 let before=RetainedOwnership.count () in
 let owner=DirectoryOwner.prepare () in
 let retained=DirectoryOwner.Uncertain owner in
 let weak=Weak.create 1 in
 with_connection(fun c w->
  send w[R.encodeInt 1;Bytearray.of_string "u",0,1];
  (try Lwt_unix.run(R.start_bounded_request c 8(fun b->
     Weak.set weak 0 (Some b);Lwt.fail retained))
   with DirectoryOwner.Uncertain _->failwith "DESIGNATED body uncertainty escaped");
  R.closeConnection c;
  body_usage R.requestInputLane 1 1 "raw ticket released on typed uncertainty";
  require(!(R.bounded_input_bytes)=1 && !(R.bounded_input_count)=1)"bounded subset released on typed uncertainty";
  require(RetainedOwnership.count ()=before+1)"typed body guard not rooted";
  Gc.full_major();require(Weak.check weak 0)"retained raw payload no longer reachable");
 let stream_owner=DirectoryOwner.prepare () in
 let stream_retained=DirectoryOwner.Uncertain stream_owner in
 let stream_weak=Weak.create 1 in
 R.serverStreams:=Util.StringMap.add "body-retained-stream"
  (fun _ buffer->Weak.set stream_weak 0 (Some buffer);raise stream_retained) !(R.serverStreams);
 with_connection(fun c w->
  send w(R.encodeInt 12204::R.marshalHeader c(R.Stream "body-retained-stream")
   [R.encodeInt 1;Bytearray.of_string "v",0,1]);
  let receiving=R.receive c in Lwt_unix.run(Lwt_unix.yield());
  require(Lwt.poll receiving=None)"stream uncertainty did not retain receive promise";
  body_usage R.requestInputLane 2 2 "DESIGNATED stream uncertainty converted to abort";
  R.closeConnection c;
  body_usage R.requestInputLane 2 2 "stream uncertainty released raw allowance";
  require(RetainedOwnership.count ()=before+2)"stream guard not rooted";
  require(not(Hashtbl.mem R.streamError 12204))"uncertainty entered ordinary stream table";
  Gc.full_major();require(Weak.check stream_weak 0)"retained stream payload lost");
 R.register_body_ownership_classifier(function Body_plugin_uncertain->true | _->false);
 with_connection(fun c w->
  send w[R.encodeInt 1;Bytearray.of_string "p",0,1];
  (try Lwt_unix.run(R.start_body_request c(fun _->Lwt.fail Body_plugin_uncertain))
   with Body_plugin_uncertain->failwith "DESIGNATED registered body uncertainty escaped");
  R.closeConnection c;
  body_usage R.requestInputLane 3 3 "late classifier released raw allowance";
  require(RetainedOwnership.count ()=before+3)"late classifier guard not rooted");
 print_endline "RPC raw bodies: synthetic core/registered uncertainty retains request/stream payloads and raw/subset charges; no directory/FD acquired; fixtures end at process exit PASS"
