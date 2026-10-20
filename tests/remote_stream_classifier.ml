(* Throwing pure stream classifiers preserve both causes and raw ownership. *)
exception Stream_classifier_original
exception Stream_classifier_failure
exception Stream_classifier_unregistered
let stream_classifier_known=Util.Transient "classified stream diagnostic"
let ()=
 let initial_bytes= !(R.requestInputLane.R.body_bytes)
 and initial_count= !(R.requestInputLane.R.body_count)in
 let before=RetainedOwnership.count()in
 R.register_body_ownership_classifier(function
   |Stream_classifier_original->raise Stream_classifier_failure
   |e when e==stream_classifier_known->raise Stream_classifier_failure
   |_->false);
 let check id name error payload held_bytes held_count =
   let weak=Weak.create 1 in
   R.serverStreams:=Util.StringMap.add name
     (fun _ body->Weak.set weak 0(Some body);raise error) !(R.serverStreams);
   with_connection(fun c w->
     let length=String.length payload in
     send w(R.encodeInt id::R.marshalHeader c(R.Stream name)
       [R.encodeInt length;Bytearray.of_string payload,0,length]);
     let receiving=R.receive c in Lwt_unix.run(Lwt_unix.yield());
     let pending=try Lwt.poll receiving=None with _->false in
     Printf.printf "stream-classifier id=%d pending=%b raw=%d/%d retained-delta=%d cached=%b\n%!"
       id pending !(R.requestInputLane.R.body_bytes) !(R.requestInputLane.R.body_count)
       (RetainedOwnership.count()-before)(Hashtbl.mem R.streamError id);
     require pending "DESIGNATED classifier failure escaped stream owner";
     require(not(Hashtbl.mem R.streamError id))
       "DESIGNATED uncertain stream entered ordinary error table";
     body_usage R.requestInputLane(initial_bytes+held_bytes)(initial_count+held_count)
       "stream classifier failure released raw allowance";
     let paired=ref false in
     RetainedOwnership.iter(fun entry->
       if RetainedOwnership.cause entry==error then
         match RetainedOwnership.classification_error entry with
         |Some Stream_classifier_failure->paired:=true|_->());
     require !paired "stream classifier lost original/cause pair";
     R.closeConnection c;Gc.full_major();
     require(Weak.check weak 0)"stream classifier lost exact payload root")in
 check 15110 "stream-classifier-original" Stream_classifier_original "fault" 5 1;
 check 15112 "stream-classifier-known" stream_classifier_known "k" 6 2;
 require(RetainedOwnership.count()=before+2)"stream classifier double/missing retention";
 (* An ordinary unregistered custom exception still propagates unchanged,
    without a diagnostic-cache entry, and its raw allowance settles. *)
 let name="stream-classifier-unregistered"in
 R.serverStreams:=Util.StringMap.add name(fun _ _->raise Stream_classifier_unregistered)
   !(R.serverStreams);
 with_connection(fun c w->
   send w(R.encodeInt 15113::R.marshalHeader c(R.Stream name)
     [R.encodeInt 1;Bytearray.of_string "u",0,1]);
   (try Lwt_unix.run(R.receive c);failwith"unregistered stream error swallowed"
    with Stream_classifier_unregistered->());
   require(not(Hashtbl.mem R.streamError 15113))"unregistered error cached";
   body_usage R.requestInputLane(initial_bytes+6)(initial_count+2)
     "known custom failure leaked raw allowance");
 print_endline"RPC stream classifier original/cause/raw-root retention PASS"
