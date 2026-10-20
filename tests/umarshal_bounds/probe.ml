module U=Umarshal
module R=UmarshalReference
let checks=ref 0
let check b s=incr checks;if not b then failwith s
let rejection f label=check((try ignore(f());false with U.Error _->true))label
let bytes s=let b=Bigarray.(Array1.create char c_layout(String.length s)) in String.iteri(fun i c->b.{i}<-c)s;b
let wire m reference value =
 let encoded=U.to_string m value in
 check(encoded=R.to_string reference value) "wire bytes changed";
 check(U.to_string m(U.from_string m encoded 0)=encoded) "byte roundtrip changed value";
 check(U.to_string m(U.unmarshal_from_bytearray m(bytes encoded)0)=encoded) "bigarray roundtrip changed value";
 check(U.to_string m(U.unmarshal_from_bytearray_bounded ~max_alloc_bytes:1048576 ~max_elements:65536 m(bytes encoded)0)=encoded) "bounded roundtrip changed value";
 let c=open_out_bin "valid-stream" in output_string c encoded;output_string c(U.to_string U.int 42);close_out c;
 let ic=open_in_bin "valid-stream" in
 check(U.to_string m(U.from_channel m ic)=encoded) "channel roundtrip changed value";
 check(U.from_channel U.int ic=42) "decoder crossed stream frame";close_in ic
let ()=
 List.iter(fun s->wire U.string R.string s)["";"abc";String.make 4096 'x';"\000\255\128"];
 List.iter(fun n->wire U.int R.int n)[min_int;-128;-1;0;1;127;128;max_int];
 List.iter(fun n->wire U.int64 R.int64 n)[Int64.min_int;-1L;0L;1L;Int64.max_int];
 List.iter(fun f->wire U.float R.float f)[neg_infinity;-0.;0.;1.5;infinity];
 wire U.bool R.bool false;wire U.bool R.bool true;
 wire(U.list U.string)(R.list R.string)["";"abc";"def"];
 wire(U.list(U.list U.unit))(R.list(R.list R.unit))[[();()];[];[()]];
 wire(U.prod2 U.string U.int U.id U.id)(R.prod2 R.string R.int R.id R.id)("abc",42);
 let a=Bigarray.(Array1.create int32 c_layout 3) in a.{0}<-Int32.min_int;a.{1}<-0l;a.{2}<-Int32.max_int;
 wire U.int32bigarray R.int32bigarray a;
 wire U.bytearray R.bytearray(bytes "abc");
 let huge=U.to_string U.int (1 lsl 30) in
 List.iter(fun codec->
  rejection(fun()->U.from_string codec huge 0) "inner string/array exceeded actual frame";
  rejection(fun()->U.unmarshal_from_bytearray codec(bytes huge)0) "bigarray framed preflight missing")
  [U.cond(fun()->true)() (U.prod2 U.string U.unit (fun()->"",()) (fun _->()));
   U.cond(fun()->true)() (U.prod2 U.bytearray U.unit (fun()->bytes "",()) (fun _->()));
   U.cond(fun()->true)() (U.prod2 U.int32bigarray U.unit (fun()->a,()) (fun _->()))];
 List.iter(fun offset->
  rejection(fun()->U.from_string U.string(U.to_string U.string "abc")offset) "invalid byte offset accepted";
  rejection(fun()->U.unmarshal_from_bytearray U.string(bytes(U.to_string U.string "abc"))offset) "unsafe bigarray offset accepted")
  [-1;min_int;max_int;100];
 let text=U.to_string U.string "abc" in
 for n=0 to String.length text-1 do
  rejection(fun()->U.from_string U.string(String.sub text 0 n)0) "truncated byte frame accepted";
  rejection(fun()->U.unmarshal_from_bytearray U.string(bytes(String.sub text 0 n))0) "truncated bigarray frame accepted"
 done;
 let bound n e m encoded=U.unmarshal_from_bytearray_bounded ~max_alloc_bytes:n ~max_elements:e m(bytes encoded)0 in
 check(bound 8 0 U.string text="abc") "exact string charge boundary rejected";
 rejection(fun()->bound 7 0 U.string text) "string charge below boundary accepted";
 check(bound 8 3 U.bytearray(U.to_string U.bytearray(bytes "abc")) |> Bigarray.Array1.dim=3) "bytearray boundary rejected";
 rejection(fun()->bound 8 2 U.bytearray(U.to_string U.bytearray(bytes "abc"))) "bytearray element limit ignored";
 let units=U.to_string(U.list U.unit)(List.init 100(fun _->())) in
 check(List.length(bound 65536 100 (U.list U.unit)units)=100) "unit list exact element boundary rejected";
 rejection(fun()->bound 65536 99 (U.list U.unit)units) "zero-byte list element budget ignored";
 rejection(fun()->bound 4096 1000 (U.list U.unit)units) "unit list spine budget ignored";
 let nested=U.to_string(U.list(U.list U.unit))[[();()];[();()]] in
 rejection(fun()->bound 65536 5 (U.list(U.list U.unit))nested) "nested collection budget reset";
 let negative=U.to_string U.int (-1) in rejection(fun()->U.from_string(U.list U.unit)negative 0) "negative list count accepted";
 (* A stream with a small advertised frame must refuse the oversized inner
    length before allocation. Bound the decoder too when the outer header lies. *)
 let name="stream" in
 let c=open_out_bin name in output_string c huge;close_out c;
 let ic=open_in_bin name in rejection(fun()->U.from_channel U.string ic) "stream framing ignored";close_in ic;
 let lie=Bytes.of_string huge in Bytes.set_int64_be lie 0 (Int64.of_int(1 lsl 30));
 let c=open_out_bin name in output_bytes c lie;close_out c;
 let ic=open_in_bin name in rejection(fun()->U.from_channel_bounded ~max_alloc_bytes:1024 ~max_elements:1024 U.string ic) "bounded stream allocation ignored";close_in ic;
 (* Policy errors refuse before consuming even a channel header. *)
 let ic=open_in_bin name in
 check((try ignore(U.from_channel_bounded ~max_alloc_bytes:(-1) ~max_elements:0 U.unit ic);false with Invalid_argument _->true)) "negative allocation budget accepted";
 check(pos_in ic=0) "invalid budget consumed stream input";close_in ic;
 check((try ignore(bound 100 (-1) U.unit(U.to_string U.unit()));false with Invalid_argument _->true)) "negative element budget accepted";
 let prefixed="tag"^text in check(U.from_string U.string prefixed 3="abc") "positive byte offset changed";
 check(U.unmarshal_from_bytearray U.string(bytes prefixed)3="abc") "positive bigarray offset changed";
 let array_text=U.to_string U.int32bigarray a in
 rejection(fun()->bound 65536 2 U.int32bigarray array_text) "int32 collection limit ignored";
 rejection(fun()->bound 12 3 U.int32bigarray array_text) "int32 allocation budget ignored";
 (* Only the historical allocation site is guarded; never allocate 1GiB. *)
 let caught=try ignore(R.from_string R.string huge 0);false with Failure s->s="DESIGNATED oversized allocation reached" in
 check caught "historical allocation order not reproduced";
 Printf.printf "PASS %d Umarshal framing/allocation/count/wire checks; historical oversized allocation reached guarded site\n%!" !checks
