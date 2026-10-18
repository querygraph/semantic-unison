(* Current RPC decoded owner: real returned promises/socket output, no SDK. *)
let check value why=if not value then failwith why
let phase=Sys.argv.(2)
let faults=int_of_string Sys.argv.(4)
let rec pulse count=if count=0 then Lwt.return()else
 Lwt.bind(Lwt_unix.sleep 0.001)(fun()->pulse(count-1))
let run=Lwt_unix.run
let sleeping promise=try Lwt.poll promise=None with _->false
let primary promise=match Lwt.poll promise with
 | _->failwith "RPC setup fault did not survive actual settlement"
 | exception error->check(error=Fault.primary)"RPC setup fault provenance changed"
let ()=
 Sys.set_signal Sys.sigpipe Sys.Signal_ignore;
 Fault.configure phase faults;
 let base=Fault.fd_count()in
 let socket,peer=Unix.socketpair Unix.PF_UNIX Unix.SOCK_STREAM 0 in
 Unix.set_close_on_exec socket;Unix.set_close_on_exec peer;
 Unix.setsockopt_int socket Unix.SO_SNDBUF 4096;Unix.set_nonblock peer;
 let connection=ref None and socket_owned=ref true and peer_owned=ref true in
 let gate=Lwt.wait()and entered=ref false and calls=ref 0 in
 let weak=Weak.create 1 in
 let reply=String.init 524288(fun i->Char.chr((i*29+5)land 255))in
 let decoded expected=match Remote.test_decoded_usage()with
  | Some(bytes,elements,slots)->check(bytes=8 && elements=0 && slots=expected)
     "DESIGNATED decoded owner retired before actual RPC settlement"
  | None->failwith "current RPC decoded owner diagnostic unavailable"in
 let decoded_zero()=check(Remote.test_decoded_usage()=Some(0,0,0))
   "decoded owner remained after actual RPC settlement"in
 let cleanup()=
  (if !socket_owned then begin socket_owned:=false;
    match !connection with None->(try Unix.close socket with _->())
      |Some c->(try Remote.test_rpc_close c with _->())end);
  if !peer_owned then begin peer_owned:=false;try Unix.close peer with _->()end in
 Fun.protect ~finally:cleanup(fun()->
  let handler args=check(args="abc")"decoded RPC arguments changed";
   incr calls;Weak.set weak 0(Some args);entered:=true;gate in
  let conn,work=Remote.test_rpc_start socket(fun dispatch->dispatch())handler in
  connection:=Some conn;
  run(pulse 3);check(!entered && !calls=1 && sleeping work)
    "RPC did not retain its real pending handler";
  decoded 1;Gc.full_major();check(Weak.check weak 0)"RPC lost live decoded argument";
  check(Fault.fd_count()=base+2)"unexpected RPC fixture descriptors";
  if phase<>"rpc-output-action" && phase<>"normal"then
    check(!(Fault.failures)=faults)"returned handler/scope waiter faults not exercised";
  Lwt.wakeup gate reply;
  let no_output=phase="rpc-server-map"||phase="rpc-dispatch"in
  if no_output then begin
   let rec until_settled n=if not(sleeping work)then Lwt.return()else
    if n=0 then Lwt.fail(Failure"RPC borrower did not settle after gate release")else
    Lwt.bind(Lwt_unix.sleep 0.001)(fun()->until_settled(n-1))in
   run(until_settled 3000);primary work;decoded_zero();
   check(not !(Fault.output_captured))"failed handler observer emitted output";
   let b=Bytes.create 1 in
   check((try ignore(Unix.read peer b 0 1);false with
     Unix.Unix_error((Unix.EAGAIN|Unix.EWOULDBLOCK),_,_)->true))
     "failed RPC observer appended a packet"
  end else begin
   let rec until_output n=
    if !(Fault.output_captured) then Lwt.return()else
    if n=0 then Lwt.fail(Failure"RPC output did not start")else
    Lwt.bind(Lwt_unix.sleep 0.001)(fun()->until_output(n-1))in
   run(until_output 3000);run(pulse 3);
   check(!(Fault.output_sleeping)() && sleeping work)
     "actual large RPC output did not remain pending";
   decoded 1;Gc.full_major();check(Weak.check weak 0)"queued RPC lost argument owner";
   check(!(Fault.failures)=faults)"RPC output/scope waiter faults not exercised";
   let bytes=Bytes.create 16384 and received=Buffer.create 524400 in
   let rec drain count idle=
    if count=0 then Lwt.fail(Failure"actual RPC socket drain deadline")else
    let n=try Unix.read peer bytes 0(Bytes.length bytes)with
     Unix.Unix_error((Unix.EAGAIN|Unix.EWOULDBLOCK),_,_)-> -1 in
    if n>0 then begin Buffer.add_subbytes received bytes 0 n;drain(count-1)0 end
    else if n=0 then Lwt.return()
    else if not(sleeping work)&&idle>=20 then Lwt.return()
    else Lwt.bind(Lwt_unix.sleep 0.001)(fun()->drain(count-1)(idle+1))in
   run(drain 6000 0);
   if phase="normal"then ignore(run work)else primary work;
   decoded_zero();check(not(!(Fault.output_sleeping)()))"output action remained active";
   let wire=Buffer.contents received in
   if phase="rpc-output-action"then begin
    let expected=Remote.test_rpc_expected conn reply in
    check(String.length wire>0 && String.length wire<=String.length expected &&
      wire=String.sub expected 0(String.length wire))
      "failed output changed packet prefix or appended exception"
   end else check(Remote.test_rpc_decode conn wire=reply)"actual RPC output bytes changed"
  end;
  check(!calls=1)"RPC handler retried";
  socket_owned:=false;Remote.test_rpc_close conn;connection:=None;
  peer_owned:=false;Unix.close peer;
  check(Fault.fd_count()=base)"RPC fixture descriptor leak";
  Printf.printf "RPC-DECODED %s faults=%d timers=%d owner_closed=true fds_closed=true PASS\n%!"
    phase !(Fault.failures) !(Fault.timer_failures))
