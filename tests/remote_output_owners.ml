(* Selected logical output ownership; private queues/gates, no SDK/native FD. *)
let output_usage lane bytes parts count message =
 require(!(lane.R.out_bytes)=bytes && !(lane.R.out_parts)=parts && !(lane.R.out_count)=count)message
let output_zero ()=
 output_usage R.normalOutputLane 0 0 0 "DESIGNATED normal output owner leaked";
 output_usage R.urgentOutputLane 0 0 0 "DESIGNATED urgent output owner leaked"
let output_refused witness f =
 try ignore(Lwt.poll(f()));failwith witness with
 Util.Transient why->require(why="RPC output budget exhausted")"wrong output quota error"
let output_failed work text =
 try ignore(Lwt.poll work);failwith"output failure not delivered"with
 Util.Transient why->require(why=text)"output cause changed"
(* Do not let the caller's optimizer keep the fixture's dead local array in
   its initializer stack frame. The factory returns before the action settles;
   only actual queued/active ownership may retain its freshly allocated array. *)
let[@inline never] make_output_liveness_case q weak gate =
 let b=Bytearray.of_string "old" in
 Weak.set weak 0(Some b);
 R.perform_owned_output q R.Normal[b,0,3](fun parts->
   require(List.length parts=1)"own output payload changed";gate)
exception Output_classifier_original
exception Output_classifier_failure
let () =
 output_zero();
 let old=List.map Prefs.read[R.outputMiB;R.outputSlots;R.outputParts;R.urgentOutputBytes;
                            R.urgentOutputSlots;R.urgentOutputParts]in
 Prefs.set R.outputMiB 1;Prefs.set R.outputSlots 2;Prefs.set R.outputParts 3;
 Prefs.set R.urgentOutputBytes 8;Prefs.set R.urgentOutputSlots 1;Prefs.set R.urgentOutputParts 2;
 let q=R.makeOutputQueue false(fun _->Lwt.return())in q.R.canWrite<-false;
 let first=R.perform_owned_output q R.Normal[Bytearray.of_string"abc",0,3](fun _->Lwt.return())in
 let second=R.perform_owned_output q R.Idle[Bytearray.of_string"xy",0,2](fun _->Lwt.return())in
 output_usage R.normalOutputLane 5 2 2 "DESIGNATED queued output owner missing";
 output_refused "DESIGNATED output slot quota ignored"(fun()->R.perform_owned_output q R.Normal[](fun _->failwith"quota entered consumer"));
 let gate=Lwt.wait()in
 let urgent=try R.perform_owned_output q R.Urgent[Bytearray.of_string"u!",0,2](fun _->gate)
   with Util.Transient _->failwith"DESIGNATED urgent output not independent"in
 output_usage R.urgentOutputLane 2 1 1 "DESIGNATED urgent output not independent";
 output_refused "DESIGNATED urgent slot quota ignored"(fun()->R.perform_owned_output q R.Urgent[](fun _->failwith"urgent quota entered consumer"));
 R.failOutputQueue q(Util.Transient"cancel queued");
 output_failed first"cancel queued";output_failed second"cancel queued";
 output_usage R.normalOutputLane 0 0 0 "dropped queued output still charged";
 require(Lwt.poll urgent=None)"active urgent borrower settled early";
 output_usage R.urgentOutputLane 2 1 1 "DESIGNATED queue failure revoked live output";
 Lwt.wakeup gate();output_failed urgent"cancel queued";output_zero();
 (* A real nested owner consumes capacity after measurement, before the final
    reservation. The controlled-source hook is absent from production. *)
 Prefs.set R.outputSlots 1;
 let q=R.makeOutputQueue false(fun _->Lwt.return())in q.R.canWrite<-false;
 let held=ref None and b=Bytearray.of_string"xy"in
 R.output_test_before_admit:=Some(fun()->held:=Some(R.perform_owned_output q R.Normal[b,0,1](fun _->Lwt.return())));
 let refused=R.perform_owned_output q R.Normal[b,1,1](fun _->failwith"stale admission consumer entered")in
 (try ignore(Lwt.poll refused);failwith"DESIGNATED stale output admission accepted"with
  Util.Transient why->require(why="RPC output budget exhausted")"wrong recheck refusal");
 require(q.R.failure=None && Queue.length q.R.writes=1)"recheck refusal poisoned prior queued work";
 output_usage R.normalOutputLane 1 1 1 "recheck refusal changed nested owner";
 R.failOutputQueue q(Util.Transient"recheck done");
 (match !held with None->failwith"nested owner missing"|Some work->output_failed work"recheck done");
 output_zero();Prefs.set R.outputSlots 2;
 (* Complete bytes/part admission, including zero-length slices. *)
 let q=R.makeOutputQueue false(fun _->Lwt.return())in q.R.canWrite<-false;
 let large=Bytearray.of_string(String.make 1048576 'x')in
 let held=R.perform_owned_output q R.Normal[large,0,1048576](fun _->Lwt.return())in
 output_usage R.normalOutputLane 1048576 1 1 "exact output byte quota refused";
 output_refused "DESIGNATED output byte quota ignored"(fun()->R.perform_owned_output q R.Normal[large,0,1](fun _->Lwt.return()));
 R.failOutputQueue q(Util.Transient"bytes done");output_failed held"bytes done";output_zero();
 let q=R.makeOutputQueue false(fun _->Lwt.return())in q.R.canWrite<-false;
 let held=R.perform_owned_output q R.Normal[large,0,0;large,1,0;large,2,0](fun _->Lwt.return())in
 output_usage R.normalOutputLane 0 3 1 "empty slices not counted";
 output_refused "DESIGNATED output part quota ignored"(fun()->R.perform_owned_output q R.Idle[large,3,0](fun _->Lwt.return()));
 R.failOutputQueue q(Util.Transient"parts done");output_failed held"parts done";output_zero();
 (* Its own action is done while the immediate performOutput promise still
    drains an unrelated action. No payload closure may keep the old array. *)
 let q=R.makeOutputQueue false(fun _->Lwt.return())in
 let first_gate=Lwt.wait()and second_gate=Lwt.wait()and second_started=Lwt.wait()in
 let weak=Weak.create 1 in
 let first=make_output_liveness_case q weak first_gate in
 let second=R.performOutput q R.Normal(fun()->Lwt.wakeup second_started();second_gate)in
 output_usage R.normalOutputLane 3 1 1 "live immediate owner missing";
 Lwt.wakeup first_gate();Lwt_unix.run second_started;
 require(Lwt.poll first=None)"unrelated drain fixture unexpectedly complete";
 output_usage R.normalOutputLane 0 0 0 "DESIGNATED own write credit held through unrelated drain";
 Gc.full_major();require(not(Weak.check weak 0))"DESIGNATED settled output payload retained by queued closure";
 Lwt.wakeup second_gate();Lwt_unix.run first;Lwt_unix.run second;output_zero();
 (* Policy checks precede admission; peer preferences cannot set this lane. *)
 List.iter(fun invalid->Prefs.set R.outputSlots invalid;
  (try ignore(R.measure_output R.normalOutputLane[]);failwith"bad output slots accepted"with Util.Fatal _->());
  output_zero())[0;-1;65537];
 List.iter2 Prefs.set[R.outputMiB;R.outputSlots;R.outputParts;R.urgentOutputBytes;
                     R.urgentOutputSlots;R.urgentOutputParts]old;
 let dumped=Umarshal.from_string Umarshal.(list(prod3 string bool string id id))
   (Umarshal.to_string Prefs.mdumpedPrefs(Prefs.dump 1))0 in
 List.iter(fun name->require(not(List.exists(fun(key,_,_)->key=name)dumped))"output preference exported")
  ["rpcoutputbudget";"rpcoutputslots";"rpcoutputparts";"rpcurgentoutputbytes";
   "rpcurgentoutputslots";"rpcurgentoutputparts"];
 (* Both typed and classifier failure retain the exact payload. No OS/native
    resources are acquired; these two original fixtures end at process exit. *)
 let retain_case error =
  let q=R.makeOutputQueue false(fun _->Lwt.return())and weak=Weak.create 1 in
  let work=
   let b=Bytearray.of_string"held"in Weak.set weak 0(Some b);
   R.perform_owned_output q R.Normal[b,0,4](fun _->Lwt.fail error)in
  require((try Lwt.poll work=None with _->false))"DESIGNATED uncertain output escaped";
  Gc.full_major();require(Weak.check weak 0)"DESIGNATED uncertain output lost payload root";
  require(!(R.retained_output_owners)<>None)"uncertain output owner not linked"in
 let directory=DirectoryOwner.prepare()in retain_case(DirectoryOwner.Uncertain directory);
 output_usage R.normalOutputLane 4 1 1 "typed output uncertainty retired credit";
 R.register_body_ownership_classifier(function Output_classifier_original->raise Output_classifier_failure|_->false);
 retain_case Output_classifier_original;
 output_usage R.normalOutputLane 8 2 2 "classifier output uncertainty retired credit";
 let original=ref false in
 RetainedOwnership.iter(fun entry->match RetainedOwnership.cause entry,RetainedOwnership.classification_error entry with
  | Output_classifier_original,Some Output_classifier_failure->original:=true|_->());
 require !original "output classifier lost original/cause pair";
 print_endline"RPC output owners: separate lane byte/part/slot admission, queued/active settlement, own-action release and uncertainty roots PASS"
