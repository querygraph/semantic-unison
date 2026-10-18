(* Original tiny producer ownership controls, no SDK/Photo payload. *)
exception Encoder_original
exception Encoder_classifier
let encoder_snapshot lane=(!(lane.R.out_bytes),!(lane.R.out_count),!(lane.R.out_parts))
let encoder_delta lane (bytes,count,parts) db dc dp message=
 require(encoder_snapshot lane=(bytes+db,count+dc,parts+dp))message
let encoder_failure work message=
 try ignore(Lwt.poll work);failwith message with Util.Transient _->()
let encoder_unit ()=fst(R.marshalV1 Umarshal.unit()[])
let encoder_produce kind gate=
 R.with_produced_output kind encoder_unit(fun _ settle->settle(fun()->gate))
let ()=
 let lane=R.encoderLane and urgent=R.urgentEncoderLane in
 let baseline=encoder_snapshot lane and urgent_base=encoder_snapshot urgent in
 let prefs=[R.encoderMiB;R.encoderSlots;R.encoderBuffers;R.urgentEncoderBytes;
            R.urgentEncoderSlots;R.urgentEncoderBuffers]in
 let old=List.map Prefs.read prefs in
 let _,base_slots,base_buffers=baseline in
 Prefs.set R.encoderSlots(base_slots+1);Prefs.set R.encoderBuffers(base_buffers+8);
 let gate=Lwt.wait()in
 let work=encoder_produce R.Normal gate in
 require(!(R.encoder_context)=None)"DESIGNATED encoder context escaped builder";
 encoder_delta lane baseline 16 1 1 "DESIGNATED encoder allocation uncharged";
 let entered=ref false in
 let refused=R.with_produced_output R.Idle(fun()->entered:=true;encoder_unit())
   (fun _ settle->settle(fun()->Lwt.return()))in
 encoder_failure refused "full producer slot accepted";
 require(not !entered)"full producer entered serializer";
 let urgent_gate=Lwt.wait()in let u=encoder_produce R.Urgent urgent_gate in
 encoder_delta urgent urgent_base 16 1 1 "urgent encoder shares bulk lane";
 Lwt.wakeup gate();Lwt_unix.run work;
 encoder_delta lane baseline 0 0 0 "settled producer leaked";
 Lwt.wakeup urgent_gate();Lwt_unix.run u;
 encoder_delta urgent urgent_base 0 0 0 "urgent producer leaked";
 Prefs.set R.encoderSlots(base_slots+4);
 (* Buffer admission occurs before each codec invocation and partial roots
    release on known failure; no borrower has seen a failed builder. *)
 Prefs.set R.encoderBuffers(base_buffers+1);
 let refused=R.with_produced_output R.Normal(fun()->
    ignore(encoder_unit());encoder_unit())(fun _ _->failwith"builder entered consumer")in
 encoder_failure refused "buffer quota accepted";
 encoder_delta lane baseline 0 0 0 "partial buffer quota leaked";
 require(!(R.encoder_context)=None)"failed builder context escaped";
 Prefs.set R.encoderBuffers(base_buffers+8);
 let marker=Failure"encoder conversion original"in
 let bad=Umarshal.prod2 Umarshal.unit Umarshal.unit
   (fun ()->raise marker)(fun _->())in
 let refused=R.with_produced_output R.Normal(fun()->fst(R.marshalV1 bad()[]))
   (fun _ _->failwith"failed conversion consumed")in
 (try ignore(Lwt.poll refused);failwith"conversion accepted"with e when e==marker->());
 encoder_delta lane baseline 0 0 0 "conversion refusal leaked";
 require(!(R.encoder_context)=None)"conversion context escaped";
 (* Same-owner nested builders restore the outer synchronous context. *)
 Lwt_unix.run(R.with_produced_output R.Normal(fun()->
   let outer= !(R.encoder_context)in
   Lwt_unix.run(encoder_produce R.Idle(Lwt.return()));
   require(!(R.encoder_context)==outer)"nested encoder lost outer owner";
   encoder_unit())(fun _ settle->settle(fun()->Lwt.return())));
 encoder_delta lane baseline 0 0 0 "nested producer leaked";
 (* Independent byte budget, refusal must preserve the existing owner. *)
 let ub,_,_=urgent_base in Prefs.set R.urgentEncoderBytes(ub+31);
 let gate=Lwt.wait()in let held=encoder_produce R.Urgent gate in
 encoder_failure(encoder_produce R.Urgent(Lwt.return()))"byte quota accepted";
 encoder_delta urgent urgent_base 16 1 1 "refusal debited existing producer";
 Lwt.wakeup gate();Lwt_unix.run held;
 encoder_delta urgent urgent_base 0 0 0 "byte quota settlement leaked";
 (* The queued producer has no live writer; actual known cancellation clears it. *)
 let q=R.makeOutputQueue false(fun _->Lwt.return())in q.R.canWrite<-false;
 let queued=R.with_produced_output R.Normal encoder_unit(fun parts settle->
   R.perform_owned_output q R.Normal parts(fun _->settle(fun()->Lwt.return())))in
 encoder_delta lane baseline 16 1 1 "queued producer not charged";
 R.failOutputQueue q(Util.Transient"producer queued cancellation");
 encoder_failure queued "queued producer did not fail";
 encoder_delta lane baseline 0 0 0 "queued producer cancellation leaked";
 (* Immediate action settlement precedes an unrelated later queued drain. *)
 let q=R.makeOutputQueue false(fun _->Lwt.return())in
 let own=Lwt.wait()and later=Lwt.wait()in
 let first=R.with_produced_output R.Normal encoder_unit(fun parts settle->
   R.perform_owned_output q R.Normal parts(fun _->settle(fun()->own)))in
 let second=R.performOutput q R.Normal(fun()->later)in
 Lwt.wakeup own();
 require(Lwt.poll first=None)"later action did not hold outer drain";
 encoder_delta lane baseline 0 0 0 "DESIGNATED producer retained after own consumer";
 Lwt.wakeup later();Lwt_unix.run first;Lwt_unix.run second;
 List.iter2 Prefs.set prefs old;
 let dumped=Umarshal.from_string Umarshal.(list(prod3 string bool string id id))
   (Umarshal.to_string Prefs.mdumpedPrefs(Prefs.dump 1))0 in
 List.iter(fun name->require(not(List.exists(fun(key,_,_)->key=name)dumped))
   "encoder preference exported")
   ["rpcencodebudget";"rpcencodeslots";"rpcencodebuffers";"rpcurgentencodebytes";
    "rpcurgentencodeslots";"rpcurgentencodebuffers"];
 (* Known body/handler paths must use the same producer scope. *)
 with_connection(fun c _->
   pause_output c;
   let command=R.registerServerCmd "encoder-client-fixture" Umarshal.unit Umarshal.unit
     (fun _ ()->Lwt.return())in
   let request=command c()in
   let bytes,owners,buffers=encoder_snapshot lane in
   let b,n,p=baseline in
   require(bytes>b && owners=n+1 && buffers=p+2)"client bypassed encoder owner";
   R.stopConnectionOutput c;
   (try ignore(Lwt.poll request)with Util.Fatal _->());
   encoder_delta lane baseline 0 0 0 "failed client producer leaked");
 (* Typed and classifier uncertainty preserve partial result roots and charges.
    No descriptor is acquired by the prepared synthetic DirectoryOwner. *)
 let retained_case error=
   let weak=Weak.create 1 in
   let work=R.with_produced_output R.Normal encoder_unit(fun parts settle->
     let b,_,_=List.hd parts in Weak.set weak 0(Some b);
     settle(fun()->Lwt.fail error))in
   require((try Lwt.poll work=None with _->false))"uncertain encoder escaped";
   Gc.full_major();
   require(Weak.check weak 0)"DESIGNATED uncertain encoder lost published root";
   let rooted=match !(R.retained_encoder_owners),Weak.get weak 0 with
     |Some owner,Some b->(match owner.R.enc_roots with
       |Some node->node.R.enc_buffer==b|None->false)|_->false in
   require rooted "DESIGNATED uncertain encoder lost published root"in
 let directory=DirectoryOwner.prepare()in retained_case(DirectoryOwner.Uncertain directory);
 encoder_delta lane baseline 16 1 1 "uncertain producer retired charges";
 R.register_body_ownership_classifier(function Encoder_original->raise Encoder_classifier|_->false);
 retained_case Encoder_original;
 encoder_delta lane baseline 32 2 2 "classifier producer retired charges";
 let paired=ref false in
 RetainedOwnership.iter(fun entry->match RetainedOwnership.cause entry,
    RetainedOwnership.classification_error entry with
   |Encoder_original,Some Encoder_classifier->paired:=true|_->());
 require !paired "encoder classifier lost original cause";
 (* Admission refusal has no producer resources. A throwing classifier must
    not turn that refusal into an uncharged retained pending operation. *)
 let _,held_slots,_=encoder_snapshot lane in
 Prefs.set R.encoderSlots held_slots;
 let before=RetainedOwnership.count()in
 R.register_body_ownership_classifier(function
   |Util.Transient "RPC encoder budget exhausted"->raise Encoder_classifier
   |_->false);
 let blocked=encoder_produce R.Normal(Lwt.return())in
 let known=try match Lwt.poll blocked with None->false|Some _->false with
   Util.Transient "RPC encoder budget exhausted"->true in
 require known "DESIGNATED inactive encoder refusal became retained";
 require(RetainedOwnership.count()=before)"inactive encoder allocated retained entry";
 Prefs.set R.encoderSlots(List.nth old 1);
 print_endline"RPC producer selected allocation/root lifetimes PASS"
