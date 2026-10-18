(* Appended to the private RPC participant; original pipe data only. *)
let startup_refused f =
 try ignore(f());failwith "startup limit ignored"
 with Util.Fatal s->require(s="RPC startup input limit exceeded") "wrong startup refusal"
let () =
 let old=Prefs.read R.startupMaxBytes and slots=Prefs.read R.headerInputSlots in
 Prefs.set R.startupMaxBytes 8;
 with_connection(fun c w->send w[Bytearray.of_string "1234567\n",0,8];
  require(Lwt_unix.run(R.receiveUntilNewline c)="1234567") "exact startup line changed");
 with_connection(fun c w->send w[Bytearray.of_string "1234567 ",0,8];
  require(Lwt_unix.run(R.receiveUntilSpaceOrNl c)="1234567 ") "startup separator changed");
 with_connection(fun c w->send w[Bytearray.of_string "a\rb\r\n",0,5];
  require(Lwt_unix.run(R.receiveUntilNewline c)="ab") "CR compatibility changed");
 List.iter(fun data->with_connection(fun c w->
  send w[Bytearray.of_string data,0,9];
  startup_refused(fun()->Lwt_unix.run(R.receiveUntilNewline c)));header_usage 0 0)
  ["12345678\n";String.make 8 '\r'^"\n"];
 with_connection(fun c w->send w[Bytearray.of_string "12345678",0,8];
  require(Lwt_unix.run(R.receiveString c 8)="12345678") "fixed startup bytes changed");
 with_connection(fun c _->startup_refused(fun()->R.receiveString c 9));header_usage 0 0;
 with_connection(fun c _->require(Lwt_unix.run(R.receiveString c 0)="") "empty startup field failed");header_usage 0 0;
 with_connection(fun c _->require(Lwt_unix.run(R.receiveUntilNewlineNb c)="") "empty buffered diagnostic failed");header_usage 0 0;
 R.startup_test_fail_allocation:=true;
 with_connection(fun c _->
  try ignore(Lwt_unix.run(R.receiveUntilNewline c));failwith "startup allocation injection missed"
  with Failure s->require(s="DESIGNATED startup allocation failure") "wrong startup allocation failure");
 R.startup_test_fail_allocation:=false;header_usage 0 0;
 with_connection(fun c w->send w[Bytearray.of_string "OK\n",0,3];
  require(Lwt_unix.run(R.receiveHandshakeMsg c)=R.Ok) "OK handshake changed");
 with_connection(fun c w->send w[Bytearray.of_string "K 1 2\n",0,6];
  require(Lwt_unix.run(R.receiveHandshakeData c "K ")=R.Data "1 2") "version handshake changed");
 with_connection(fun c w->send w[Bytearray.of_string "NOK bad\n",0,8];
  require(Lwt_unix.run(R.receiveHandshakeMsg c)=R.Error "bad") "NOK handshake changed");
 (* Slot/byte reservations precede any peer input, and survive until closure. *)
 Prefs.set R.headerInputSlots 1;
 with_connection(fun c _->let p=R.receiveUntilNewline c in
  header_usage 16 1;
  with_connection(fun other _->header_exhausted(fun()->R.receiveUntilNewline other));
  R.closeConnection c;header_failed p;header_usage 0 0);
 Prefs.set R.headerInputSlots slots;
 Prefs.set R.startupMaxBytes 524289;
 with_connection(fun c _->
  let mib=Prefs.read R.headerInputMiB and maximum=Prefs.read R.headerMaxBytes in
  Prefs.set R.headerMaxBytes 64;Prefs.set R.headerInputMiB 1;
  (try header_exhausted(fun()->R.receiveUntilNewline c)
   with e->Prefs.set R.headerInputMiB mib;Prefs.set R.headerMaxBytes maximum;raise e);
  Prefs.set R.headerInputMiB mib;Prefs.set R.headerMaxBytes maximum);header_usage 0 0;
 List.iter(fun n->Prefs.set R.startupMaxBytes n;
  with_connection(fun c _->
   try ignore(R.receiveUntilNewline c);failwith "invalid startup policy accepted"
   with Util.Fatal s->require(s="Invalid RPC startup input limit") "wrong startup policy refusal")) [0;-1;max_int];
 Prefs.set R.startupMaxBytes (String.length R.magicPacket);
 with_connection(fun c w->send w R.magic;
  require(Lwt_unix.run(R.checkForMagicString c)) "legacy upgrade packet changed");
 with_connection(fun c w->send w[R.encodeInt R.magicId;R.encodeInt(String.length R.magicPacket+1)];
  exceeds(fun()->Lwt_unix.run(R.checkForMagicString c)));header_usage 0 0;
 Prefs.set R.startupMaxBytes old;
 let codec=Umarshal.(list(prod3 string bool string id id)) in
 let raw=Umarshal.from_string codec(Umarshal.to_string Prefs.mdumpedPrefs(Prefs.dump 1))0 in
 require(not(List.exists(fun(n,_,_)->n="rpcstartupmaxbytes")raw)) "startup pref exported";
 let wire=Umarshal.from_string Prefs.mdumpedPrefs
  (Umarshal.to_string codec["rpcstartupmaxbytes",false,"bad payload"])0 in
 Prefs.load wire 999;
 require(Prefs.read R.startupMaxBytes=old) "startup pref peer poisoned";
 header_usage 0 0;
 print_endline "RPC startup: exact wire limit, CR accounting, handshakes, legacy upgrade, slot/byte admission and disconnect settlement PASS"
