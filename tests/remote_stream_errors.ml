(* Known diagnostic bytes/count persist through actual ping output settlement. *)
exception Stream_unknown of int ref
let stream_error_usage bytes count message =
 require(!(R.stream_error_bytes)=bytes && !(R.stream_error_count)=count)message
let () =
 R.resetStreamErroState();stream_error_usage 0 0 "stream error baseline";
 let slots=Prefs.read R.streamErrorSlots and mib=Prefs.read R.streamErrorMiB in
 Prefs.set R.streamErrorSlots 1;Prefs.set R.streamErrorMiB 1;
 let calls=ref 0 and name="stream-error-fixture"in
 let _client=R.registerStreamCmd name (R.defaultMarshalingFunctions Umarshal.unit)(fun _ ()->incr calls;raise(Util.Transient"abc"))in
 with_connection(fun c _->
  let body=Bytearray.of_string(name ^ "-str" ^ Umarshal.to_string Umarshal.unit())in
  Lwt_unix.run(R.processStream c(request_id 12600)name body);
  stream_error_usage 3 1 "DESIGNATED stream error not admitted";
  (match (Hashtbl.find R.streamError 12600).R.stream_cause with
   Util.Transient message->require(message="abc")"stream error changed"|_->failwith"wrong stream exception");
  (* Already aborted chunks for the same ID don't acquire another slot. *)
  Lwt_unix.run(R.processStream c(request_id 12600)name body);
  require(!calls=1)"aborted stream reran handler";
  (try ignore(R.processStream c(request_id 12601)name body);failwith"DESIGNATED full stream table ignored"
   with Util.Fatal why->require(why="RPC stream error budget exhausted")"wrong stream capacity error");
  require(!calls=1)"DESIGNATED full error registry ran another handler";
  pause_output c;
  let ping=R.processRequest c(request_id 12602)(name ^ "Ping")
    (request_body(name ^ "Ping")Umarshal.int 12600)in
  require(not(Hashtbl.mem R.streamError 12600))"ping didn't take stored error";
  require(Lwt.poll ping=None)"queued ping unexpectedly settled";
  stream_error_usage 3 1 "DESIGNATED ping released stream error before output";
  R.allowWrites c.R.outputQueue;Lwt_unix.run ping;
  stream_error_usage 0 0 "settled ping retained error credit");
 (* Reset releases table entries once, not borrowed replies; exact byte boundary. *)
 Prefs.set R.streamErrorSlots 3;
 let text=String.make 1048576 'x'in
 R.record_stream_error 12610(Util.Fatal text);
 R.record_stream_error 12611(Util.Transient"");
 stream_error_usage 1048576 2 "exact stream diagnostic budget refused";
 (try R.record_stream_error 12612(Util.Transient"x");failwith"DESIGNATED stream diagnostic byte limit ignored"
  with Util.Fatal why->require(why="RPC stream error budget exhausted")"wrong stream byte error");
 stream_error_usage 1048576 2 "refused stream error mutated prior entries";
 (try R.record_stream_error 12610(Util.Transient"");failwith"duplicate stream error stored"
  with Invalid_argument _->());
 R.resetStreamErroState();R.resetStreamErroState();stream_error_usage 0 0 "reset released wrong count";
 List.iter(fun(error,bytes)->
  R.record_stream_error 12616 error;
  require((Hashtbl.find R.streamError 12616).R.stream_cause==error)"standard exception identity changed";
  stream_error_usage bytes 1 "standard diagnostic fields charged incorrectly";
  R.resetStreamErroState();stream_error_usage 0 0 "standard error reset leaked")
  [Failure"fault",5;Invalid_argument"bad",3;Sys_error"disk",4;
   Unix.Unix_error(Unix.EIO,"write","path"),9;Match_failure("file",1,2),4;
   Assert_failure("file",1,2),4;End_of_file,0;Not_found,0;Exit,0;
   Division_by_zero,0;Out_of_memory,0;Stack_overflow,0;Sys.Break,0];
 let token=ref 0 in
 (try R.record_stream_error 12613(Stream_unknown token);failwith"DESIGNATED unknown exception stored"
  with Stream_unknown actual->require(actual==token)"unknown stream cause changed");
 stream_error_usage 0 0 "unknown exception was charged/stored";
 require(not(Hashtbl.mem R.streamError 12613))"unknown stream exception retained";
 R.record_stream_error 12614(Util.Transient"abc");
 let gate=Lwt.wait()in
 let borrowing=R.with_stream_error_scope 12614(fun()->gate)in
 (try Lwt_unix.run(R.with_stream_error_scope 12614(fun()->failwith"DESIGNATED duplicate borrower invoked"));
      failwith"duplicate stream borrower accepted"with Util.Fatal _->());
 R.resetStreamErroState();stream_error_usage 3 1 "DESIGNATED reset revoked borrowed stream error";
 Lwt.wakeup gate();Lwt_unix.run borrowing;stream_error_usage 0 0 "borrowed stream error didn't settle";
 List.iter(fun invalid->Prefs.set R.streamErrorSlots invalid;
  (try R.check_stream_error_capacity();failwith"invalid stream error policy accepted"with Util.Fatal _->());
  stream_error_usage 0 0 "invalid policy changed stream counters")[0;-1;65537];
 Prefs.set R.streamErrorSlots slots;Prefs.set R.streamErrorMiB mib;
 let dumped=Umarshal.from_string Umarshal.(list(prod3 string bool string id id))
   (Umarshal.to_string Prefs.mdumpedPrefs(Prefs.dump 1))0 in
 List.iter(fun name->require(not(List.exists(fun(key,_,_)->key=name)dumped))"stream policy exported")
   ["rpcstreamerrorslots";"rpcstreamerrorbudget"];
 (* Synthetic typed ownership uncertainty keeps the exact diagnostic and charge.
    No directory/native FD is acquired. Actual OS group exit settles this fixture. *)
 R.record_stream_error 12615(Util.Transient"u");
 let owner=DirectoryOwner.prepare()in
 let retained=R.with_stream_error_scope 12615(fun()->Lwt.fail(DirectoryOwner.Uncertain owner))in
 require((try Lwt.poll retained=None with DirectoryOwner.Uncertain _->false))
   "DESIGNATED stream error uncertainty escaped";
 R.resetStreamErroState();stream_error_usage 1 1 "uncertain stream error credit released";
 require(!(R.retained_stream_errors)<>None)"uncertain stream error root missing";
 print_endline"RPC stream errors: known byte/count admission, exact errors, ping/reset settlement, unknown cause propagation and uncertainty retention PASS"
