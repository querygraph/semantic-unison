type native
type t = { native:native; mutable finalized:bool; mutable length:int64 }
external initialize : unit -> native (* ox-portable-ffi *) = "unison_evp_hash_create"
external chunk : native -> bytes -> int -> int -> unit (* ox-portable-ffi *) = "unison_evp_hash_feed"
external finalize : native -> string (* ox-portable-ffi *) = "unison_evp_hash_finish"
external version : unit -> string (* ox-portable-ffi *) = "unison_evp_hash_version"
let create () = {native=initialize ();finalized=false;length=0L}
let feed t input offset length =
  if t.finalized || offset < 0 || length < 0 || offset > Bytes.length input - length
     || t.length > Int64.sub 0x1fffffffffffffffL (Int64.of_int length) then
    invalid_arg "EVP SHA256 range";
  t.length <- Int64.add t.length (Int64.of_int length);
  let rec consume offset length =
    if length = 0 then chunk t.native input offset 0 else
    let count=min 65536 length in
    chunk t.native input offset count;
    if count < length then consume (offset+count) (length-count)
  in consume offset length
let finish t =
  if t.finalized then invalid_arg "EVP SHA256 finalized";
  t.finalized <- true; finalize t.native
