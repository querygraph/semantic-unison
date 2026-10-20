module U=Umarshal
exception Owner_refusal
let checks=ref 0
let check b message=incr checks;if not b then failwith message
let bytes s=let a=Bigarray.(Array1.create char c_layout(String.length s))in
 String.iteri(fun i c->a.{i}<-c)s;a
type reader={run:'a. max_alloc_bytes:int -> max_elements:int ->
 reserve:(bytes:int -> elements:int -> unit) -> 'a U.t -> string -> 'a}
let readers=[
 "bytes",{run=(fun ~max_alloc_bytes ~max_elements ~reserve m s->
  U.from_bytes_accounted ~max_alloc_bytes ~max_elements ~reserve m(Bytes.of_string s)0)};
 "bigarray",{run=(fun ~max_alloc_bytes ~max_elements ~reserve m s->
  U.unmarshal_from_bytearray_accounted ~max_alloc_bytes ~max_elements ~reserve m(bytes s)0)};
 "channel",{run=(fun ~max_alloc_bytes ~max_elements ~reserve m s->
  let oc=open_out_bin "accounted-stream" in
  Fun.protect ~finally:(fun()->close_out oc)(fun()->output_string oc s);
  let ic=open_in_bin "accounted-stream" in
  Fun.protect ~finally:(fun()->close_in ic)(fun()->
   U.from_channel_accounted ~max_alloc_bytes ~max_elements ~reserve m ic))}]
let ()=
 let oc=open_out_bin "policy-stream" in
 Fun.protect ~finally:(fun()->close_out oc)(fun()->output_string oc(U.to_string U.unit()));
 List.iter(fun(label,r)->
 let run ?(allocation=65536) ?(elements=1024) reserve m encoded =
  r.run ~max_alloc_bytes:allocation ~max_elements:elements ~reserve m encoded in
 let total=ref 0 and count=ref 0 in
 let reserve ~bytes ~elements=total:= !total+bytes;count:= !count+elements in
 let encoded=U.to_string U.string "abc" in
 check(run reserve U.string encoded="abc")"accounted string changed value";
 check(!total=8 && !count=0)"DESIGNATED external decode reservation missing";
 Gc.full_major();check(!total=8)"decoder guessed release after GC";
 check(run reserve U.string encoded="abc" && !total=16)"new decode reset caller accounting";
 let debited=ref 0 in
 let limited ~bytes ~elements:_=if bytes>15- !debited then raise Owner_refusal else debited:= !debited+bytes in
 ignore(run limited U.string encoded);
 check((try ignore(run limited U.string encoded);false with Owner_refusal->true))"aggregate owner refusal ignored";
 check(!debited=10)"partial external debit hidden/refunded/retried";
 let local_debits=ref 0 in
 check((try ignore(run ~allocation:7 (fun ~bytes ~elements:_->local_debits:= !local_debits+bytes) U.string encoded);false with U.Error _->true))"local allocation limit ignored";
 check(!local_debits=2)"owner charged before local allocation validation";
 let reached=ref false in
 let mapped=U.prod2 U.string U.unit (fun s->s,())(fun(s,())->reached:=true;s) in
 check((try ignore(run (fun ~bytes ~elements:_->if bytes>=6 then raise Owner_refusal) mapped(U.to_string mapped "abc"));false with Owner_refusal->true))"owner refusal wrapped or ignored";
 check(not !reached)"conversion ran after reservation refusal";
 let elements=ref 0 in
 let element_gate ~bytes:_ ~elements:n=if n>3- !elements then raise Owner_refusal else elements:= !elements+n in
 let units=U.list U.unit and wire=U.to_string(U.list U.unit)[();()] in
 check(List.length(run element_gate units wire)=2)"accounted list changed";
 check((try ignore(run element_gate units wire);false with Owner_refusal->true))"cross-decode element quota reset";
 check(!elements=2)"element refusal partially changed owner";
 let seen=ref 0 in
 check((try ignore(run ~elements:1 (fun ~bytes:_ ~elements:n->seen:= !seen+n) units wire);false with U.Error _->true))"local element bound ignored";
 check(!seen=0)"owner charged before local element validation";
 let b=ref 0 and e=ref 0 in
 let account ~bytes ~elements=b:= !b+bytes;e:= !e+elements in
 let nested=U.list(U.list U.unit)in
 check(run account nested(U.to_string nested[[();()];[];[()]])=[[();()];[];[()]])"nested accounted value changed";
 check(!e=6 && !b>=6*6*(Sys.word_size/8))"nested accounting context reset";
 let b=ref 0 and e=ref 0 in
 let a=run(fun ~bytes ~elements->b:= !b+bytes;e:= !e+elements)U.bytearray(U.to_string U.bytearray(bytes "abc"))in
 check(Bigarray.Array1.dim a=3 && !b=8 && !e=3)"bytearray selected charge changed";
 let hits=ref 0 in
 check(run ~allocation:0 ~elements:0 (fun ~bytes:_ ~elements:_->incr hits)U.unit(U.to_string U.unit())=())"zero-charge unit refused";
 check(!hits=0)"unit invented selected allocation";
 let ordering codec text =
  Allocation_witness.arm ();
  ignore(run (fun ~bytes ~elements:_->Allocation_witness.reserved ~bytes)codec text);
  Allocation_witness.stop ();
  check(not !(Allocation_witness.owed) && !(Allocation_witness.payloads)=1)"preallocation reservation witness missed";
  Allocation_witness.arm ();
  let refused=try ignore(run(fun ~bytes ~elements:_->if bytes=6 then raise Owner_refusal)codec text);false with Owner_refusal->true in
  Allocation_witness.stop ();
  check(refused && !(Allocation_witness.payloads)=0)"reservation refusal reached payload allocation" in
 ordering U.string encoded;
 ordering U.bytearray(U.to_string U.bytearray(bytes "abc"));
 let ic=open_in_bin "policy-stream" in
 check((try ignore(U.from_channel_accounted ~max_alloc_bytes:(-1) ~max_elements:0 ~reserve:(fun ~bytes:_ ~elements:_->failwith "invalid policy called owner")U.unit ic);false with Invalid_argument _->true))"invalid accounted channel policy accepted";
 check(pos_in ic=0)"invalid accounted channel consumed header";close_in ic;
 Printf.printf "PASS accounted reader %s; caller retains partial/success charges, never implicit release\n%!"label)readers;
 Printf.printf "PASS %d accounted decode checks; selected builtin costs only, no heap/RSS/liveness claim\n%!" !checks
