open Lwt
module R=SemanticRuntime
module W=SemanticWorkers
module H=HelperSupervisor
module I=IoAdmission
module A=SemanticAdmission
module S=SemanticRemote
let assertions=ref 0
let check condition reason=incr assertions;if not condition then failwith reason
let run=Lwt_unix.run
let family=Sys.argv.(1) and phase=Sys.argv.(2) and disposition=Sys.argv.(3)
let requested=int_of_string Sys.argv.(4)
let meaning=Sys.argv.(5)="meaning"
let negative=Array.exists ((=) "negative") Sys.argv
let contents prefix=prefix ^ String.init (8192-String.length prefix) (fun i -> Char.chr ((i*73+19) land 255))
let write path data=let ch=open_out_bin path in
  Fun.protect ~finally:(fun () -> close_out ch) (fun () -> output_string ch data)
let read path=let ch=open_in_bin path in
  Fun.protect ~finally:(fun () -> close_in ch) (fun () -> really_input_string ch (in_channel_length ch))
let outcome work=try match Lwt.poll work with None->`Sleeping|Some _->`Returned with e->`Failed e
let ticks=ref 0
let rec pulse count=if count=0 then return () else
  Lwt_unix.sleep 0.002 >>=fun ()->incr ticks;pulse(count-1)
let rec until_entered index count=
  if Atomic.get Fault.entered.(index) then return ()
  else if count=0 then fail(Failure "actual runtime domain did not enter fixture")
  else Lwt_unix.sleep 0.001 >>=fun ()->until_entered index(count-1)
let primary work=let result=try Ok(run work) with e->Error e in
  check(result=Error Fault.primary) "first observed waiter error was replaced"
let settled runtime baseline=
  ignore(run(Lwt_unix.yield()));
  let a=R.admission_usage() and i=I.usage runtime.R.io and w=W.usage runtime.R.pool in
  check(a.A.transactions=0 && a.pending=0 && a.descriptors=0 && a.payload_bytes=0 &&
        i.I.active_jobs=0 && i.pending=0 && i.devices=[] && w.W.pending=0 && w.running=0 &&
        W.test_slots runtime.pool=0 && H.usage runtime.supervisor=(0,0) && Fault.fd_count()=baseline)
    "runtime/report completion did not settle actual descriptors and every ledger"
let source="source.bin"
let source_bytes=contents "ONE0"
let module_profile="org.firstpair.runtime-settlement/1"
module Probe = struct
  let profile=module_profile
  let inspect file=
    let prefix=SemanticFile.read file 0L 4 in
    Fault.pause(if prefix="TWO0" then 1 else 0);
    Ok {FormatExtension.regions=[{offset=4L;length=8}]}
end
let configure()=
  Unix.mkdir Util.unisonDir 0o700;
  write source source_bytes;
  if family="report" || family="pair" || family="rpc" then begin
    SemanticFormats.register ~max_payload:8 (module Probe);
    Prefs.loadStrings["semanticprofile = "^module_profile;"semanticworkers = "^(if family="pair" then "2" else "1");
      "semanticmaxinflight = "^(if family="pair" then "3" else "2");
      "semanticpayloadbudget = 2";"semanticdescriptorbudget = 32";
      "semanticvolumejobs = "^(if family="pair" then "2" else "1")]
  end else Prefs.loadStrings["semanticworkers = 1";"semanticmaxinflight = 1";
    "semanticpayloadbudget = 1";"semanticdescriptorbudget = 24";"semanticvolumejobs = 2"];
  Fault.configure phase requested
let extension()=match FormatExtension.resolve module_profile with Some e->e|None->failwith "profile registration absent"
let check_fault()=if phase<>"normal" then
  check(!(Fault.failures)=requested && !(Fault.captured)) "actual returned-promise waiter fault did not execute"
let runtime_case runtime=
  let input=Unix.openfile source [Unix.O_RDONLY;Unix.O_CLOEXEC] 0 in
  let base=Fault.fd_count() in
  let cancellation=H.cancellation() and next_cancel=H.cancellation() and device_cancel=H.cancellation() in
  let cleanup()=Fault.release_all();H.cancel cancellation;H.cancel next_cancel;H.cancel device_cancel;
    (try ignore(run(W.shutdown runtime.R.pool)) with _->());Unix.close input in
  Fun.protect ~finally:cleanup(fun()->
    let module Recognizer=struct
      let format="runtime-settlement-identify/1"
      let identify _=Fault.pause 0;FormatRecognition.Not_matched
    end in
    let handle=FormatRecognition.trusted(module Recognizer) in
    let first=R.with_cancellation(fun inherited ->
      R.with_admission inherited ~payload_bytes:1048576 ~descriptors:9(fun()->
        R.with_io_file cancellation source(fun()->
          W.identify runtime.pool cancellation ~recognizers:[handle,false] input))) in
    ignore(run(until_entered 0 3000));ignore(run(pulse 3));check_fault();
    let a=R.admission_usage() in
    check(Fault.fd_count()=base+3 && a.transactions=1 && a.descriptors=9 && a.payload_bytes=1048576 &&
          (W.usage runtime.pool).running=1 && (W.usage runtime.pool).pending=1 &&
          W.test_slots runtime.pool=1 && H.usage runtime.supervisor=(1,0) &&
          (I.usage runtime.io).active_jobs=2 && outcome first=`Sleeping)
      "DESIGNATED runtime grouped descriptor or active worker loan retired before settlement";
    let next_started=ref false and device_started=ref false in
    let next=R.with_admission next_cancel ~payload_bytes:1048576 ~descriptors:9(fun()->
      next_started:=true;W.digest runtime.pool next_cancel input) in
    let device=I.with_devices runtime.io device_cancel ~devices:(I.devices_of_fds[input])
      (fun()->device_started:=true;return()) in
    ignore(run(pulse 3));
    check(not !next_started && not !device_started && (R.admission_usage()).pending=1 &&
          (I.usage runtime.io).pending=1) "runtime waiter started before active worker settled";
    if disposition="cancel" then H.cancel cancellation
    else if disposition="connection" then Remote.test_client_cleanup();
    ignore(run(pulse 3));
    check(Fault.fd_count()=base+3 && (R.admission_usage()).transactions=1 &&
          (I.usage runtime.io).active_jobs=2 && not !next_started && not !device_started &&
          outcome first=`Sleeping) "runtime cancel/connection cleanup retired live worker descriptors";
    Fault.release_all();
    if phase="normal" then ignore(run first) else primary first;
    (match run next with Some value->check(value.W.digest=SemanticHash.string source_bytes) "runtime exact reuse changed digest"
     |None->failwith "runtime next consumer was cancelled");
    check(run device=Some()) "runtime device waiter did not settle";
    settled runtime base;
    check(read source=source_bytes) "runtime probe changed source bytes")
let report_case runtime=
  let base=Fault.fd_count() in
  let cancellation=H.cancellation() and next_cancel=H.cancellation() in
  let next_input=ref None in
  let cleanup()=Fault.release_all();H.cancel cancellation;H.cancel next_cancel;
    S.test_release_reports();(try ignore(run(W.shutdown runtime.R.pool)) with _->());
    (match !next_input with None->()|Some fd->Unix.close fd) in
  Fun.protect ~finally:cleanup(fun()->
    let first=R.with_transaction ~role:A.Source ~max_payload:8(fun inherited ->
      let _=inherited in S.test_inspect_file ~meaning cancellation(extension())(Fspath.canonize(Some source))) in
    ignore(run(until_entered 0 3000));ignore(run(pulse 3));check_fault();
    let live=S.test_report_state() in
    let a=R.admission_usage() in
    check(Fault.fd_count()=base+3 && live=[true;false;false] &&
          a.transactions=1 && a.descriptors=8 && a.payload_bytes=262208 &&
          (W.usage runtime.pool).running=1 && (W.usage runtime.pool).pending=1 &&
          W.test_slots runtime.pool=1 && H.usage runtime.supervisor=(1,0) &&
          (I.usage runtime.io).active_jobs=1 && outcome first=`Sleeping)
      "DESIGNATED report held descriptor or active source loan retired before settlement";
    let next_started=ref false in
    let next=R.with_admission next_cancel ~payload_bytes:1048576 ~descriptors:9(fun()->
      next_started:=true;
      let input=Unix.openfile source [Unix.O_RDONLY;Unix.O_CLOEXEC]0 in next_input:=Some input;
      W.digest runtime.pool next_cancel input) in
    if disposition="cancel" then H.cancel cancellation
    else if disposition="connection" then Remote.test_client_cleanup()
    else if disposition="close" then S.test_release_reports();
    ignore(run(pulse 3));
    let flags=S.test_report_state() in
    let expected_closing=disposition="connection" || disposition="close" in
    check(flags=[true;expected_closing;false] && Fault.fd_count()=base+3 &&
          (R.admission_usage()).transactions=1 && (I.usage runtime.io).active_jobs=1 &&
          not !next_started && outcome first=`Sleeping)
      "report cleanup closed/unborrowed a held file while actual worker remained active";
    Fault.release_all();
    if phase="normal" then ignore(run first) else primary first;
    (match run next with Some value->check(value.W.digest=SemanticHash.string source_bytes) "report exact reuse changed digest"
     |None->failwith "report next consumer was cancelled");
    (match !next_input with None->()|Some fd->Unix.close fd;next_input:=None);
    settled runtime base;
    check(S.test_report_state()=[false;true;true]) "report owner did not settle deferred closing";
    check(read source=source_bytes) "report probe changed source bytes")
let loan_case runtime=
  let input=Unix.openfile source[Unix.O_RDONLY;Unix.O_CLOEXEC]0 in
  let base=Fault.fd_count() in
  let cancellation=H.cancellation() and next_cancel=H.cancellation() in
  let reservation=if disposition="retire" then Some(R.make_publication_reservation()) else None in
  let cleanup()=Fault.release_all();H.cancel cancellation;H.cancel next_cancel;
    (match reservation with None->()|Some owner->(try A.retire owner with _->()));
    (try ignore(run(W.shutdown runtime.R.pool)) with _->());Unix.close input in
  Fun.protect ~finally:cleanup(fun()->
    (match reservation with None->()|Some owner->check(run(A.acquire owner cancellation)) "loan owner not acquired");
    let module Recognizer=struct
      let format="runtime-scalar-loan/1"
      let identify _=Fault.pause 0;FormatRecognition.Not_matched
    end in
    let recognizer=FormatRecognition.trusted(module Recognizer) in
    let first=R.with_admission ?reservation cancellation ~payload_bytes:1048576 ~descriptors:9(fun()->
      W.identify runtime.pool cancellation ~recognizers:[recognizer,false] input) in
    ignore(run(until_entered 0 3000));ignore(run(pulse 3));check_fault();
    let declared=match reservation with None->9|Some _->24 in
    check(Fault.fd_count()=base+2 && (R.admission_usage()).transactions=1 &&
          (R.admission_usage()).descriptors=declared && (W.usage runtime.pool).pending=1 &&
          W.test_slots runtime.pool=1 && H.usage runtime.supervisor=(1,0) &&
          (I.usage runtime.io).active_jobs=1 && outcome first=`Sleeping)
      "DESIGNATED scalar resource loan returned while actual worker descriptors remained active";
    (match reservation with None->H.cancel cancellation|Some owner->A.retire owner);
    let next_started=ref false in
    let next=R.with_admission next_cancel ~payload_bytes:1048576 ~descriptors:9(fun()->
      next_started:=true;W.digest runtime.pool next_cancel input) in
    ignore(run(pulse 3));
    check(Fault.fd_count()=base+2 && (R.admission_usage()).transactions=1 &&
          (R.admission_usage()).descriptors=declared && not !next_started && outcome first=`Sleeping)
      "scalar cancellation/retirement released live loan early";
    Fault.release_all();if phase="normal" then ignore(run first) else primary first;
    (match run next with Some value->check(value.W.digest=SemanticHash.string source_bytes) "scalar exact reuse changed"
     |None->failwith "scalar exact reuse was cancelled");
    (match reservation with None->()|Some owner->A.retire owner);
    settled runtime base;check(read source=source_bytes) "scalar probe changed source bytes")
let pair_case runtime=
  let second="source-right.bin" in
  let second_bytes=contents "TWO0" in write second second_bytes;
  let base=Fault.fd_count() in
  let cancellation=H.cancellation() in
  let calls=Array.make 2 0 in
  let observe index path ()=
    calls.(index)<-calls.(index)+1;
    R.with_transaction ~role:A.Source ~max_payload:8(fun _ ->
      S.test_inspect_file ~meaning cancellation(extension())(Fspath.canonize(Some path))) in
  let first=Fault.watch "pair-first" (observe 0 source) in
  let right()=
    if disposition="launch-error" then (calls.(1)<-calls.(1)+1;raise Fault.secondary)
    else Fault.watch "pair-second" (observe 1 second)() in
  let cleanup()=Fault.release_all();H.cancel cancellation;S.test_release_reports();
    (try ignore(run(W.shutdown runtime.R.pool)) with _->()) in
  Fun.protect ~finally:cleanup(fun()->
    let work=try BorrowedWork.all[first;right] with error->fail error in
    ignore(run(until_entered 0 3000));
    let active=if disposition="launch-error" then 1 else 2 in
    if active=2 then ignore(run(until_entered 1 3000));
    ignore(run(pulse 3));if phase<>"pair-second" then check_fault();
    check(calls=[|1;1|] && Fault.fd_count()=base+3*active &&
          (R.admission_usage()).transactions=active && (R.admission_usage()).descriptors=8*active &&
          (W.usage runtime.pool).running=active && (W.usage runtime.pool).pending=active &&
          W.test_slots runtime.pool=active && H.usage runtime.supervisor=(active,0) &&
          (I.usage runtime.io).active_jobs=active && outcome work=`Sleeping)
      "DESIGNATED report pair lost an actual started participant before settlement";
    Atomic.set Fault.released.(0) true;
    if active=2 then begin
      let rec until_first_settled count=
        if (R.admission_usage()).transactions=1 then return()
        else if count=0 then fail(Failure "first report did not settle independently")
        else Lwt_unix.sleep 0.002 >>=fun()->until_first_settled(count-1) in
      ignore(run(until_first_settled 3000));ignore(run(pulse 3));check_fault();
      check(Atomic.get Fault.entered.(1) && not(Atomic.get Fault.left.(1)) &&
            Fault.fd_count()=base+3 && (R.admission_usage()).descriptors=8 &&
            (W.usage runtime.pool).running=1 && (I.usage runtime.io).active_jobs=1 &&
            outcome work=`Sleeping && calls=[|1;1|])
        "report pair returned/retried after one child settled while its sibling remained active";
      Atomic.set Fault.released.(1) true
    end;
    if disposition="launch-error" then
      check((try ignore(run work);false with e->e=Fault.secondary)) "first launch error was replaced"
    else if phase="normal" then check(List.length(run work)=2) "ordinary concurrent report pair changed"
    else primary work;
    settled runtime base;
    check(read source=source_bytes && read second=second_bytes) "report pair changed source files")
let rpc_case runtime=
  let base=Fault.fd_count() in
  let socket,peer=Unix.socketpair Unix.PF_UNIX Unix.SOCK_STREAM 0 in
  Unix.set_close_on_exec socket;Unix.set_close_on_exec peer;
  Unix.setsockopt_int socket Unix.SO_SNDBUF 4096;
  Unix.set_nonblock peer;
  let cancellation=H.cancellation() in
  let connection=ref None in
  let socket_owned=ref true and peer_owned=ref true in
  let reply=String.init 524288(fun i->Char.chr((i*29+5) land 255)) in
  let calls=ref 0 in
  let handler()=
    incr calls;
    BorrowedWork.bind
      (fun()->S.test_inspect_file ~meaning cancellation(extension())(Fspath.canonize(Some source)))
      (fun _->return reply) in
  let scope dispatch=R.with_transaction ~role:A.Source ~max_payload:8(fun _->dispatch()) in
  let cleanup()=Fault.release_all();H.cancel cancellation;S.test_release_reports();
    (if !socket_owned then begin socket_owned:=false;
      match !connection with None->(try Unix.close socket with _->())
       |Some value->(try Remote.test_rpc_close value with _->()) end);
    (if !peer_owned then begin peer_owned:=false;try Unix.close peer with _->() end);
    (try ignore(run(W.shutdown runtime.R.pool))with _->()) in
  Fun.protect ~finally:cleanup(fun()->
    let conn,work=Remote.test_rpc_start socket scope handler in connection:=Some conn;
    ignore(run(until_entered 0 3000));ignore(run(pulse 3));
    check(!calls=1 && Fault.fd_count()=base+5 && (R.admission_usage()).transactions=1 &&
          (R.admission_usage()).descriptors=8 && W.test_slots runtime.pool=1 &&
          H.usage runtime.supervisor=(1,0) && (I.usage runtime.io).active_jobs=1 &&
          S.test_report_state()=[true;false;false] && outcome work=`Sleeping)
      "DESIGNATED scoped RPC discarded live worker/report/source owner";
    if phase<>"rpc-output-action" && phase<>"normal" then check_fault();
    Fault.release_all();
    let no_output=phase="rpc-server-map" || phase="rpc-dispatch" in
    if no_output then begin
      primary work;
      check(not !(Fault.output_captured) && !calls=1 && (R.admission_usage()).transactions=0)
        "failed RPC handler appended an output packet or retained its settled source";
      let tiny=Bytes.create 1 in
      check((try ignore(Unix.read peer tiny 0 1);false
        with Unix.Unix_error((Unix.EAGAIN|Unix.EWOULDBLOCK),_,_)->true))
        "failed unrecognized RPC observer emitted an exception packet"
    end else begin
      let rec until_output count=
        if !(Fault.output_captured) && (W.usage runtime.pool).running=0 then return()
        else if count=0 then fail(Failure"actual large RPC output did not block after worker completion")
        else Lwt_unix.sleep 0.001 >>=fun()->until_output(count-1) in
      ignore(run(until_output 3000));ignore(run(pulse 3));check_fault();
      check(!(Fault.output_sleeping)() && Fault.fd_count()=base+2 && !calls=1 &&
            (R.admission_usage()).transactions=1 && (R.admission_usage()).descriptors=8 &&
            (R.admission_usage()).payload_bytes=262208 && H.usage runtime.supervisor=(0,0) &&
            W.test_slots runtime.pool=0 && (I.usage runtime.io).active_jobs=0 &&
            S.test_report_state()=[false;true;true] && outcome work=`Sleeping)
        "DESIGNATED scoped RPC released Source admission while actual output action remained sleeping";
      let bytes=Bytes.create 16384 and received=Buffer.create 524400 in
      let rec drain count idle=
        if count=0 then fail(Failure"actual RPC socket drain deadline") else
        let n=try Unix.read peer bytes 0(Bytes.length bytes)
          with Unix.Unix_error((Unix.EAGAIN|Unix.EWOULDBLOCK),_,_)-> -1 in
        if n>0 then begin Buffer.add_subbytes received bytes 0 n;drain(count-1)0 end
        else if n=0 then return()
        else if outcome work<>`Sleeping && idle>=20 then return()
        else Lwt_unix.sleep 0.001 >>=fun()->drain(count-1)(idle+1) in
      ignore(run(drain 6000 0));
      if phase="normal" then ignore(run work)else primary work;
      check(!calls=1 && not(!(Fault.output_sleeping)()))
        "RPC output action or handler remained active/repeated after drain";
      let wire=Buffer.contents received in
      if phase="rpc-output-action" then begin
        let expected=Remote.test_rpc_expected conn reply in
        check(String.length wire>0 && String.length wire<=String.length expected &&
              wire=String.sub expected 0(String.length wire))
          "failed/partial RPC output appended an exception or changed its packet prefix";
        Printf.printf "RPC-PARTIAL returned=%d expected=%d action_terminal=true\n%!"
          (String.length wire)(String.length expected)
      end else
        check(Remote.test_rpc_decode conn wire=reply)
          "actual RPC wire changed reply bytes/id/header or added another packet"
    end;
    socket_owned:=false;Remote.test_rpc_close conn;connection:=None;
    peer_owned:=false;Unix.close peer;
    settled runtime base;check(read source=source_bytes)"RPC report changed source bytes")
let ()=
  configure();let runtime=R.get() in
  (match family with "runtime"->runtime_case runtime|"report"->report_case runtime
   |"loan"->loan_case runtime|"pair"->pair_case runtime|"rpc"->rpc_case runtime
   |_ ->invalid_arg "runtime/report family not implemented");
  check(not negative) "parent hazard unexpectedly passed current invariant";
  check(!(Fault.timer_failures)= !(Fault.timer_requested)) "finite polling timer faults did not execute";
  Printf.printf "PASS family=%s phase=%s disposition=%s meaning=%b faults=%d timers=%d ticker=%d assertions=%d\n%!"
    family phase disposition meaning !(Fault.failures) !(Fault.timer_failures) !ticks !assertions
