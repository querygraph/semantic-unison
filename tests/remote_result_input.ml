(* Scoped client result ownership, original tiny values and real pipe replies. *)
let result_usage bytes elements count message =
 require(!(R.decoded_result_bytes)=bytes && !(R.decoded_result_elements)=elements &&
         !(R.decoded_result_count)=count)message
let result_zero ()=result_usage 0 0 0 "decoded result owner leaked"
let result_body name codec value=Bytearray.of_string(name ^ "-res" ^ Umarshal.to_string codec value)
exception Result_uncertain
let () =
 result_zero();
 let mib=Prefs.read R.decodedResultMiB and elements=Prefs.read R.decodedResultElements
 and slots=Prefs.read R.decodedResultSlots in
 Prefs.set R.decodedResultMiB 1;Prefs.set R.decodedResultElements 2;
 Prefs.set R.decodedResultSlots 1;
 let client=R.registerBoundedServerCmdWithResultScope "scoped-result-fixture"
   ~maxArgs:64 ~maxResult:64 Umarshal.unit Umarshal.string
   (fun _ ()->Lwt.return"abc")in
 with_connection(fun c writer->
  let gate=Lwt.wait()and observed=ref false in
  let pending=client c () (fun value->
   observed:=true;require(value="abc")"scoped result changed";
   result_usage 8 0 1 "DESIGNATED decoded result missing during consumer";
   BorrowedWork.bind(fun()->gate)(fun()->require(value="abc")"borrowed result changed";Lwt.return()))in
  let id= !(R.ids)in
  let packet=result_body "scoped-result-fixture" Umarshal.string "abc"in
  send writer(R.encodeInt id::R.marshalHeader c R.NormalResult
   [R.encodeInt(Bytearray.length packet);packet,0,Bytearray.length packet]);
  let receiving=R.receive c in
  Lwt_unix.run(Lwt_unix.yield());
  require !observed "scoped consumer not invoked";
  require(Lwt.poll pending=None)"consumer gate not retained";
  result_usage 8 0 1 "DESIGNATED decoded result released before consumer";
  let refused=R.with_decoded_result (Some 64) Umarshal.string
    (Bytearray.of_string"other-res") c (result_body "other" Umarshal.string "abc")
    (fun _->failwith "result quota reached second consumer")in
  (try Lwt_unix.run refused;failwith "result slot quota ignored"with
   Util.Fatal why->require(why="RPC decoded result budget exhausted")"wrong result quota error");
  result_usage 8 0 1 "result refusal lost existing owner";
  R.closeConnection c;disconnected receiving;
  result_usage 8 0 1 "disconnect revoked consumer result";
  Lwt.wakeup gate();Lwt_unix.run pending;result_zero());
 (* Known failures release all partial selected charges. *)
 with_connection(fun c _->
  let decode codec value use=R.with_decoded_result (Some 64)codec
    (Bytearray.of_string"known-res")c(result_body"known"codec value)use in
  (try Lwt_unix.run(decode Umarshal.string "abc"(fun _->Lwt.fail(Util.Transient"known")));
       failwith"consumer failure lost"with Util.Transient"known"->()|e->raise e);
  result_zero();
  (try Lwt_unix.run(decode Umarshal.(list unit)[();();()](fun _->failwith"element refusal reached consumer"));
       failwith"element quota ignored"with Util.Fatal _->());result_zero();
  let held={R.result_bytes=0;result_elements=0;result_active=false}in
  R.reserve_result_slot held;R.reserve_result_input held ~bytes:(1048576-2)~elements:0;
  Prefs.set R.decodedResultSlots 2;
  (try Lwt_unix.run(decode Umarshal.string "abc"(fun _->failwith"DESIGNATED result byte quota bypass"));
       failwith"result bytes ignored"with Util.Fatal _->());
  result_usage(1048576-2)0 1 "partial result refusal changed prior debit";
  R.release_result_input held;R.release_result_input held;result_zero());
 List.iter(fun invalid->Prefs.set R.decodedResultSlots invalid;
  with_connection(fun c _->
   (try Lwt_unix.run(R.with_decoded_result(Some 64)Umarshal.unit
     (Bytearray.of_string"bad-res")c(result_body"bad"Umarshal.unit())(fun()->Lwt.return()));
     failwith"invalid result policy accepted"with Util.Fatal _->());result_zero()))[0;-1;65537];
 Prefs.set R.decodedResultMiB mib;Prefs.set R.decodedResultElements elements;
 Prefs.set R.decodedResultSlots slots;
 let dumped=Umarshal.from_string Umarshal.(list(prod3 string bool string id id))
   (Umarshal.to_string Prefs.mdumpedPrefs(Prefs.dump 1))0 in
 List.iter(fun name->require(not(List.exists(fun(key,_,_)->key=name)dumped))"result preference exported")
  ["rpcdecodedresultbudget";"rpcdecodedresultelements";"rpcdecodedresultslots"];
 (* A recognized uncertain consumer remains rooted, with debit, after failure.
    No OS/native resources are acquired by this original synthetic exception. *)
 R.register_body_ownership_classifier(function Result_uncertain->true|_->false);
 let weak=Weak.create 1 in
 with_connection(fun c _->
  let pending=R.with_decoded_result(Some 64)Umarshal.string
   (Bytearray.of_string"retained-res")c(result_body"retained"Umarshal.string"abc")
   (fun value->Weak.set weak 0(Some value);Lwt.fail Result_uncertain)in
  require((try Lwt.poll pending=None with Result_uncertain->false))"DESIGNATED uncertain result escaped";
  result_usage 8 0 1 "uncertain result debit released");
 Gc.full_major();require(Weak.check weak 0)"DESIGNATED uncertain result lost value root";
 require(!(R.result_retained_roots)<>None)"uncertain result owner not linked";
 print_endline"RPC scoped results: admission, actual consumer/disconnect lifetime, partial failure, endpoint policy and retained roots PASS"
