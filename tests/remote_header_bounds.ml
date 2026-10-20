(* Appended to remote_bounds.ml in the private participant: use its R/IO helpers. *)
let header_usage bytes count =
 require(!(R.header_input_bytes)=bytes && !(R.header_input_count)=count) "header input ledger mismatch"
let header_exhausted f =
 try ignore(f());failwith "header quota ignored"
 with Util.Fatal s->require(s="RPC header input budget exhausted") "wrong header quota refusal"
let header_failed promise =
 require((try ignore(Lwt.poll promise);false with Util.Fatal _->true)) "closed header borrower did not settle"
let () =
 let old_max=Prefs.read R.headerMaxBytes and old_mib=Prefs.read R.headerInputMiB and old_slots=Prefs.read R.headerInputSlots in
 header_usage 0 0;
 Prefs.set R.headerMaxBytes 64;Prefs.set R.headerInputMiB 1;Prefs.set R.headerInputSlots 2;
 R.header_test_guard:=Some 64;
 with_connection(fun conn fd->
  let chunks=R.marshalHeader conn(R.Request "header-ok")[] in
  let b,p,_=List.hd chunks in let length=R.decodeInt b p in
  Prefs.set R.headerMaxBytes length;
  send fd chunks;require(Lwt_unix.run(R.receiveHeader conn)=R.Request "header-ok") "exact header limit changed wire";
  header_usage 0 0;Prefs.set R.headerMaxBytes 64);
 with_connection(fun conn fd->send fd [R.encodeInt 65];exceeds(fun()->Lwt_unix.run(R.receiveHeader conn)));header_usage 0 0;
 (* The normal receiving loop, not just the helper, must select the cap. Only
    the length is sent; a guarded old participant cannot allocate or hang. *)
 with_connection(fun conn fd->send fd [R.encodeInt 1201;R.encodeInt 65];exceeds(fun()->Lwt_unix.run(R.receive conn)));header_usage 0 0;
 with_connection(fun conn fd->
  send fd [R.encodeInt 3;Bytearray.of_string "bad",0,3];
  (try ignore(Lwt_unix.run(R.receiveHeader conn));failwith "malformed header accepted" with Util.Fatal _->()));header_usage 0 0;
 (* Slot ownership starts before an idle length prefix, not only on sizing. *)
 with_connection(fun first _->let p=R.receiveHeader first in
  with_connection(fun second _->let q=R.receiveHeader second in
   header_usage 0 2;
   with_connection(fun third _->header_exhausted(fun()->R.receiveHeader third));
   R.closeConnection first;R.closeConnection second;header_failed p;header_failed q;header_usage 0 0));
 (* Current policy can narrow an already-started prefix before byte allocation. *)
 with_connection(fun conn fd->
  let pending=R.receiveHeader conn in Prefs.set R.headerMaxBytes 32;
  send fd[R.encodeInt 33];exceeds(fun()->Lwt_unix.run pending);header_usage 0 0;
  Prefs.set R.headerMaxBytes 64);
 (* A failure at the private allocation guard follows the reservation and must
    settle its exact bytes/slot without a body read. *)
 R.header_test_guard:=Some 0;
 with_connection(fun conn fd->send fd[R.encodeInt 1];
  (try ignore(Lwt_unix.run(R.receiveHeader conn));failwith "allocation failure swallowed"
   with Failure s->require(s="DESIGNATED header payload allocation reached") "wrong allocation failure"));
 header_usage 0 0;R.header_test_guard:=Some 64;
 let ticket={R.header_bytes=0;header_active=false;header_sized=false} in
 let limits=R.header_limits() in R.reserve_header_slot limits ticket;R.reserve_header_input limits ticket 0;header_usage 0 1;
 require((try R.reserve_header_input limits ticket 0;false with Invalid_argument _->true)) "header sizing replay accepted";
 R.release_header_input ticket;R.release_header_input ticket;header_usage 0 0;
 (* Holding a full bounded-body allowance cannot consume the header service lane. *)
 let body_mib=Prefs.read R.boundedInputMiB in Prefs.set R.boundedInputMiB 1;
 let body={R.input_bytes=0;input_active=false} in R.reserve_bounded_input body 1048576;
 with_connection(fun conn fd->send fd(R.marshalHeader conn R.NormalResult []);
  require(Lwt_unix.run(R.receiveHeader conn)=R.NormalResult) "body credits blocked header progress");
 R.release_bounded_input body;Prefs.set R.boundedInputMiB body_mib;header_usage 0 0;
 (* Two incomplete headers own two slots. Third refusal precedes allocation. *)
 with_connection(fun first a->
  send a[R.encodeInt 32];let p=R.receiveHeader first in
  with_connection(fun second b->
   send b[R.encodeInt 32];let q=R.receiveHeader second in
   Lwt_unix.run(Lwt_unix.yield());header_usage 64 2;
   with_connection(fun third c->send c[R.encodeInt 1];header_exhausted(fun()->Lwt_unix.run(R.receiveHeader third)));
   header_usage 64 2;R.closeConnection first;R.closeConnection second;
   header_failed p;header_failed q;header_usage 0 0));
 (* Independent byte exhaustion at the exact1MiB boundary. *)
 R.header_test_guard:=Some 524288;Prefs.set R.headerMaxBytes 1048576;Prefs.set R.headerInputSlots 4;
 with_connection(fun first a->
  send a[R.encodeInt 524288];let p=R.receiveHeader first in
  with_connection(fun second b->
   send b[R.encodeInt 524288];let q=R.receiveHeader second in
   Lwt_unix.run(Lwt_unix.yield());header_usage 1048576 2;
   with_connection(fun third c->send c[R.encodeInt 1];header_exhausted(fun()->Lwt_unix.run(R.receiveHeader third)));
   header_usage 1048576 2;R.closeConnection first;R.closeConnection second;
   header_failed p;header_failed q;header_usage 0 0));
 R.header_test_guard:=None;
 List.iter(fun(maximum,mib,slots)->
  Prefs.set R.headerMaxBytes maximum;Prefs.set R.headerInputMiB mib;Prefs.set R.headerInputSlots slots;
  with_connection(fun conn _->
   (try ignore(R.receiveHeader conn);failwith "invalid header budgets accepted"
    with Util.Fatal s->require(s="Invalid RPC header input budgets") "wrong header config refusal"));header_usage 0 0)
  [0,1,2;64,0,2;64,1,0;64,1,65537;1048577,1,2;64,max_int,2];
 Prefs.set R.headerMaxBytes old_max;Prefs.set R.headerInputMiB old_mib;Prefs.set R.headerInputSlots old_slots;
 (* Endpoint-local settings are absent from outgoing prefs and peer bytes are
    skipped before decoding, even with a wrong RPC version. *)
 let codec=Umarshal.(list(prod3 string bool string id id)) in
 let names=["rpcheadermaxbytes";"rpcheaderinputbudget";"rpcheaderinputslots"] in
 let raw=Umarshal.from_string codec(Umarshal.to_string Prefs.mdumpedPrefs(Prefs.dump 1))0 in
 require(not(List.exists(fun(name,_,_)->List.mem name names)raw)) "header budgets transmitted to peer";
 let wire=Umarshal.from_string Prefs.mdumpedPrefs(Umarshal.to_string codec(List.map(fun name->name,false,"bad payload")names))0 in
 Prefs.load wire 999;
 require(Prefs.read R.headerMaxBytes=old_max && Prefs.read R.headerInputMiB=old_mib && Prefs.read R.headerInputSlots=old_slots) "peer changed header budgets";
 header_usage 0 0;print_endline "RPC headers: exact cap, routing, malformed decode, independent byte/slot budgets, disconnect settlement and endpoint policy PASS"
