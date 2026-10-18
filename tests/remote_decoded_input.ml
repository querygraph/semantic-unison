(* Original bounded arguments and private pipes; logical selected charges only. *)
let decoded_usage bytes elements count message =
 require(!(R.decoded_request_bytes)=bytes && !(R.decoded_request_elements)=elements &&
         !(R.decoded_request_count)=count) message
let decoded_zero ()=decoded_usage 0 0 0 "decoded argument owner leaked"
exception Decoded_classifier_uncertain
let decoded_ticket ()={R.decoded_bytes=0;decoded_elements=0;decoded_active=false}
let () =
 decoded_zero ();
 let mib=Prefs.read R.decodedRequestMiB and elements=Prefs.read R.decodedRequestElements
 and slots=Prefs.read R.decodedRequestSlots in
 Prefs.set R.decodedRequestMiB 1;Prefs.set R.decodedRequestElements 2;
 Prefs.set R.decodedRequestSlots 2;
 let calls=ref 0 and fail=ref false in
 let _client=R.registerBoundedServerCmd "decoded-string" ~maxArgs:64 ~maxResult:64
   Umarshal.string Umarshal.unit (fun _ value->
     incr calls;require(value="abc")"decoded string changed";
     if !fail then Lwt.fail(Util.Transient "decoded handler failure")else Lwt.return()) in
 let dispatch conn id=R.processRequest conn(request_id id)"decoded-string"
   (request_body "decoded-string" Umarshal.string "abc") in
 List.iter(fun failure->fail:=failure;calls:=0;
  with_connection(fun c _->
   pause_output c;let first=dispatch c 12301 in
   decoded_usage 8 0 1 "DESIGNATED decoded arguments released before output";
   let second=dispatch c 12302 in decoded_usage 16 0 2 "aggregate decoded ownership missing";
   let refused=dispatch c 12303 in
   require(!calls=2)"decoded slot exhaustion reached handler";
   decoded_usage 16 0 2 "slot refusal changed live owners";
   R.allowWrites c.R.outputQueue;Lwt_unix.run first;Lwt_unix.run second;
   Lwt_unix.run refused;decoded_zero()))[false;true];
 fail:=false;
 (* Partial selected debit is released on a known decode refusal, while the
    pre-existing reservation remains. No payload allocation follows refusal. *)
 let occupied=decoded_ticket()in R.reserve_decoded_slot occupied;
 R.reserve_decoded_input occupied ~bytes:(1048576-2)~elements:0;
 with_connection(fun c _->calls:=0;
   Lwt_unix.run(dispatch c 12304);require(!calls=0)"byte refusal reached handler";
   decoded_usage (1048576-2) 0 1 "partial decode refusal lost another debit");
 R.release_decoded_input occupied;R.release_decoded_input occupied;decoded_zero();
 let checked=decoded_ticket()in
 (try R.reserve_decoded_input checked ~bytes:0 ~elements:0;
      failwith "inactive decoded owner accepted debit"with Invalid_argument _->());
 R.reserve_decoded_slot checked;
 (try R.reserve_decoded_slot checked;failwith "duplicate decoded owner admitted"
  with Invalid_argument _->());
 List.iter(fun (bytes,elements)->
   (try R.reserve_decoded_input checked ~bytes ~elements;
     failwith "oversized decoded debit accepted"with Util.Fatal _->());
   decoded_usage 0 0 1 "refused compound debit changed counters")
   [max_int,0;1,3];
 (try R.reserve_decoded_input checked ~bytes:(-1)~elements:0;
   failwith "negative decoded debit accepted"with Invalid_argument _->());
 R.release_decoded_input checked;decoded_zero();
 let list_calls=ref 0 in
 let _list=R.registerBoundedServerCmd "decoded-list" ~maxArgs:64 ~maxResult:64
   Umarshal.(list unit) Umarshal.unit (fun _ _->incr list_calls;Lwt.return()) in
 with_connection(fun c _->
   pause_output c;
   let run id=R.processRequest c(request_id id)"decoded-list"
     (request_body "decoded-list" Umarshal.(list unit)[();()]) in
   let first=run 12305 in
   require(!(R.decoded_request_elements)=2)"collection count not reserved";
   let refused=run 12306 in
   require(!list_calls=1 && !(R.decoded_request_count)=1)
     "element refusal reached handler or retained a known failed owner";
   R.allowWrites c.R.outputQueue;Lwt_unix.run first;Lwt_unix.run refused;decoded_zero());
 (* The request's explicit value root must survive even when the handler's
    promise contains no reference to the decoded argument. Disconnect cannot
    release an actually sleeping handler. *)
 let waiting=Lwt.wait()and weak=Weak.create 1 in
 let _wait=R.registerBoundedServerCmd "decoded-sleep" ~maxArgs:64 ~maxResult:64
   Umarshal.string Umarshal.unit(fun _ value->Weak.set weak 0(Some value);waiting)in
 with_connection(fun c _->
   let pending=R.processRequest c(request_id 12307)"decoded-sleep"
     (request_body "decoded-sleep" Umarshal.string "abc")in
   decoded_usage 8 0 1 "sleeping handler not charged";
   R.closeConnection c;Gc.full_major();
   require(Weak.check weak 0)"sleeping handler lost explicit decoded value root";
   decoded_usage 8 0 1 "disconnect released sleeping decoded owner";
   Lwt.wakeup waiting();disconnected pending;decoded_zero());
 (* Dynamic reductions refuse new owners without shrinking live reservations. *)
 let occupied=decoded_ticket()in R.reserve_decoded_slot occupied;
 R.reserve_decoded_input occupied ~bytes:5 ~elements:2;
 Prefs.set R.decodedRequestElements 1;
 (try R.reserve_decoded_input occupied ~bytes:0 ~elements:0;
      failwith "lowered element policy accepted live overage"
  with Util.Fatal _->());
 decoded_usage 5 2 1 "policy change mutated retained debit";
 R.release_decoded_input occupied;decoded_zero();
 Prefs.set R.decodedRequestElements 2;
 List.iter(fun invalid->Prefs.set R.decodedRequestSlots invalid;
   with_connection(fun c _->calls:=0;Lwt_unix.run(dispatch c 12308);
     require(!calls=0)"invalid decoded policy reached handler";decoded_zero()))[0;-1;65537];
 Prefs.set R.decodedRequestSlots 2;
 List.iter(fun invalid->Prefs.set R.decodedRequestMiB invalid;
   with_connection(fun c _->calls:=0;Lwt_unix.run(dispatch c 12310);
     require(!calls=0)"invalid decoded byte policy reached handler";decoded_zero()))[0;-1;max_int];
 Prefs.set R.decodedRequestMiB 1;
 List.iter(fun invalid->Prefs.set R.decodedRequestElements invalid;
   with_connection(fun c _->calls:=0;Lwt_unix.run(dispatch c 12311);
     require(!calls=0)"invalid decoded element policy reached handler";decoded_zero()))[0;-1];
 Prefs.set R.decodedRequestMiB mib;Prefs.set R.decodedRequestElements elements;
 Prefs.set R.decodedRequestSlots slots;
 print_endline "RPC decoded arguments: preallocation slot/byte/element admission, partial refusal, queued reply and disconnect lifetimes PASS";
 (* Synthetic typed uncertainty: no directory/FD acquired. Keep the selected
    decoded value, not just its numeric debit, rooted until process exit. *)
 let weak=Weak.create 1 and before=RetainedOwnership.count() in
 let uncertain=DirectoryOwner.Uncertain(DirectoryOwner.prepare())in
 let _retained=R.registerBoundedServerCmd "decoded-retained" ~maxArgs:64 ~maxResult:64
   Umarshal.string Umarshal.unit(fun _ value->Weak.set weak 0(Some value);Lwt.fail uncertain)in
 with_connection(fun c _->
   let pending=R.processRequest c(request_id 12309)"decoded-retained"
     (request_body "decoded-retained" Umarshal.string "abc")in
   require((try Lwt.poll pending=None with DirectoryOwner.Uncertain _->false))
     "DESIGNATED decoded uncertainty escaped its owner";
   R.closeConnection c;Gc.full_major();
   decoded_usage 8 0 1 "DESIGNATED uncertain decoded argument released";
   require(Weak.check weak 0 && RetainedOwnership.count()=before+1)
     "DESIGNATED uncertain decoded value root lost";
   require(!(R.decoded_retained_roots)<>None)"decoded retention link absent");
 let other=Weak.create 1 in
 R.register_body_ownership_classifier(function
   | Decoded_classifier_uncertain->failwith "original classifier refusal"
   | _->false);
 let _classified=R.registerBoundedServerCmd "decoded-classifier" ~maxArgs:64 ~maxResult:64
   Umarshal.string Umarshal.unit(fun _ value->Weak.set other 0(Some value);
     Lwt.fail Decoded_classifier_uncertain)in
 with_connection(fun c _->
   let pending=R.processRequest c(request_id 12312)"decoded-classifier"
     (request_body "decoded-classifier" Umarshal.string "abc")in
   require(Lwt.poll pending=None)"classifier failure escaped decoded owner";
   R.closeConnection c;Gc.full_major();
   decoded_usage 16 0 2 "classifier uncertainty released decoded charges";
   require(Weak.check weak 0 && Weak.check other 0 && RetainedOwnership.count()=before+2)
     "multiple retained decoded value roots not preserved";
   let found=ref false in RetainedOwnership.iter(fun entry->
     match RetainedOwnership.classification_error entry with
     | Some(Failure why) when why="original classifier refusal"->found:=true
     | _->());require !found "classifier failure provenance lost");
 print_endline "RPC decoded arguments: typed/classifier uncertainty roots multiple values and charges; no directory/FD; retained until process exit PASS"
