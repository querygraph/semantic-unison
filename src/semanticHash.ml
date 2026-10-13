(* SHA-256, FIPS 180-4. Portable reference implementation; each worker owns
   its context. This deliberately does not change Unison archive digests. *)
let constants = [|
  0x428a2f98l;0x71374491l;0xb5c0fbcfl;0xe9b5dba5l;0x3956c25bl;0x59f111f1l;0x923f82a4l;0xab1c5ed5l;
  0xd807aa98l;0x12835b01l;0x243185bel;0x550c7dc3l;0x72be5d74l;0x80deb1fel;0x9bdc06a7l;0xc19bf174l;
  0xe49b69c1l;0xefbe4786l;0x0fc19dc6l;0x240ca1ccl;0x2de92c6fl;0x4a7484aal;0x5cb0a9dcl;0x76f988dal;
  0x983e5152l;0xa831c66dl;0xb00327c8l;0xbf597fc7l;0xc6e00bf3l;0xd5a79147l;0x06ca6351l;0x14292967l;
  0x27b70a85l;0x2e1b2138l;0x4d2c6dfcl;0x53380d13l;0x650a7354l;0x766a0abbl;0x81c2c92el;0x92722c85l;
  0xa2bfe8a1l;0xa81a664bl;0xc24b8b70l;0xc76c51a3l;0xd192e819l;0xd6990624l;0xf40e3585l;0x106aa070l;
  0x19a4c116l;0x1e376c08l;0x2748774cl;0x34b0bcb5l;0x391c0cb3l;0x4ed8aa4al;0x5b9cca4fl;0x682e6ff3l;
  0x748f82eel;0x78a5636fl;0x84c87814l;0x8cc70208l;0x90befffal;0xa4506cebl;0xbef9a3f7l;0xc67178f2l |]

type reference = { h : int32 array; block : bytes; w : int32 array;
           mutable used : int; mutable length : int64; mutable done_ : bool }
let create () = { h = [|0x6a09e667l;0xbb67ae85l;0x3c6ef372l;0xa54ff53al;
                         0x510e527fl;0x9b05688cl;0x1f83d9abl;0x5be0cd19l|];
                  block = Bytes.create 64; w = Array.make 64 0l;
                  used = 0; length = 0L; done_ = false }
let ( ++ ) = Int32.add
let ( ^^ ) = Int32.logxor
let rotr x n = Int32.logor (Int32.shift_right_logical x n) (Int32.shift_left x (32-n))
let small0 x = rotr x 7 ^^ rotr x 18 ^^ Int32.shift_right_logical x 3
let small1 x = rotr x 17 ^^ rotr x 19 ^^ Int32.shift_right_logical x 10
let big0 x = rotr x 2 ^^ rotr x 13 ^^ rotr x 22
let big1 x = rotr x 6 ^^ rotr x 11 ^^ rotr x 25
let compress t =
  let w = t.w in
  for i = 0 to 15 do
    let v = ref 0l in
    for j = 0 to 3 do
      v := Int32.logor (Int32.shift_left !v 8)
          (Int32.of_int (Char.code (Bytes.get t.block (4*i+j))))
    done; w.(i) <- !v
  done;
  for i = 16 to 63 do
    w.(i) <- small1 w.(i-2) ++ w.(i-7) ++ small0 w.(i-15) ++ w.(i-16)
  done;
  let a = ref t.h.(0) and b = ref t.h.(1) and c = ref t.h.(2)
  and d = ref t.h.(3) and e = ref t.h.(4) and f = ref t.h.(5)
  and g = ref t.h.(6) and h = ref t.h.(7) in
  for i = 0 to 63 do
    let ch = Int32.logand !e !f ^^ Int32.logand (Int32.lognot !e) !g in
    let maj = Int32.logand !a !b ^^ Int32.logand !a !c ^^ Int32.logand !b !c in
    let x = !h ++ big1 !e ++ ch ++ constants.(i) ++ w.(i) in
    let y = big0 !a ++ maj in
    h := !g; g := !f; f := !e; e := !d ++ x;
    d := !c; c := !b; b := !a; a := x ++ y
  done;
  Array.iteri (fun i x -> t.h.(i) <- t.h.(i) ++ x)
    [|!a;!b;!c;!d;!e;!f;!g;!h|]

let feed t b off len =
  if t.done_ || off < 0 || len < 0 || off > Bytes.length b - len then
    invalid_arg "SemanticHash.feed";
  if Int64.compare t.length (Int64.sub 0x1fffffffffffffffL (Int64.of_int len)) > 0 then
    invalid_arg "SHA-256 input too long";
  t.length <- Int64.add t.length (Int64.of_int len);
  let rec loop off len = if len > 0 then begin
    let n = min len (64-t.used) in
    Bytes.blit b off t.block t.used n; t.used <- t.used+n;
    if t.used = 64 then (compress t; t.used <- 0);
    loop (off+n) (len-n)
  end in loop off len

let finish t =
  if t.done_ then invalid_arg "SemanticHash.finish";
  let bit_length = Int64.shift_left t.length 3 in
  let n = if t.used < 56 then 64-t.used else 128-t.used in
  let padding = Bytes.make n '\000' in
  Bytes.set padding 0 '\128';
  for i = 0 to 7 do
    Bytes.set padding (n-1-i)
      (Char.chr (Int64.to_int (Int64.logand 255L
        (Int64.shift_right_logical bit_length (8*i)))))
  done;
  feed t padding 0 n; t.done_ <- true;
  let out = Bytes.create 32 in
  Array.iteri (fun i v -> for j = 0 to 3 do
    Bytes.set out (4*i+j) (Char.chr (Int32.to_int
      (Int32.logand 255l (Int32.shift_right_logical v (24-8*j)))))
  done) t.h;
  Bytes.to_string out
let string s = let t = create () in feed t (Bytes.of_string s) 0 (String.length s); finish t
(* The reference implementation above remains independently testable. *)
let reference_string = string
external native_init : unit -> bytes option = "unison_semantic_sha256_init"
external native_feed : bytes -> bytes -> int -> int -> unit = "unison_semantic_sha256_feed"
external native_finish : bytes -> string = "unison_semantic_sha256_finish"
type t = Reference of reference | Native of { state:bytes; mutable finalized:bool; mutable length:int64 }
let create () = match native_init () with
  | None -> Reference (create ())
  | Some state -> Native {state;finalized=false;length=0L}
let feed context b off len = match context with
  | Reference r -> feed r b off len
  | Native n ->
    if n.finalized || off < 0 || len < 0 || off > Bytes.length b - len ||
       n.length > Int64.sub 0x1fffffffffffffffL (Int64.of_int len) then
      invalid_arg "SemanticHash.feed";
    n.length <- Int64.add n.length (Int64.of_int len);
    let rec loop off len = if len > 0 then begin
      let chunk = min len 65536 in native_feed n.state b off chunk;
      loop (off+chunk) (len-chunk)
    end in loop off len
let finish = function
  | Reference r -> finish r
  | Native n -> if n.finalized then invalid_arg "SemanticHash.finish";
    n.finalized <- true; native_finish n.state
let string s = let t = create () in feed t (Bytes.of_string s) 0 (String.length s); finish t
let hex s =
  let alphabet = "0123456789abcdef" in
  let b = Bytes.create (2*String.length s) in
  String.iteri (fun i c -> let n = Char.code c in
    Bytes.set b (2*i) alphabet.[n lsr 4]; Bytes.set b (2*i+1) alphabet.[n land 15]) s;
  Bytes.to_string b
