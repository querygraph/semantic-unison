let check v reason = if not v then failwith reason
external live : unit -> int (* ox-portable-ffi *) = "unison_evp_hash_test_live"
external methods : unit -> int (* ox-portable-ffi *) = "unison_evp_hash_test_methods"
external inject : int -> unit (* ox-portable-ffi *) = "unison_evp_hash_test_failure"
let read name = let c=open_in_bin name in
  Fun.protect ~finally:(fun () -> close_in c) (fun () -> really_input_string c (in_channel_length c))
let hash text = let context=Evp.create () in
  Evp.feed context (Bytes.of_string text) 0 (String.length text); Evp.finish context
let bounds () =
  let context=Evp.create () and input=Bytes.of_string "abc" in
  Evp.feed context input 0 1;
  List.iter (fun (offset,count) ->
    check (try Evp.feed context input offset count;false with Invalid_argument _ -> true)
      "invalid range accepted")
    [min_int,0;-1,0;0,-1;0,min_int;max_int,0;0,max_int;max_int,max_int;4,0;3,1;1,3];
  Evp.feed context input 3 0; Evp.feed context input 1 2;
  check (SemanticHash.hex(Evp.finish context)=
    "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad") "rejected range changed stream";
  check (try ignore(Evp.finish context);false with Invalid_argument _ -> true) "double finish";
  check (try Evp.feed context input 0 0;false with Invalid_argument _ -> true) "feed after finish"
let () =
  check (SemanticHash.hex(hash "")=
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855") "empty vector";
  bounds ();
  let vectors=List.map (fun n ->
    let data=read(string_of_int n^".bin") and expected=String.trim(read(string_of_int n^".sha256")) in
    check (SemanticHash.hex(hash data)=expected) "EVP vector";
    check (SemanticHash.hex(SemanticHash.string data)=expected) "selected production backend vector";
    check (SemanticHash.hex(SemanticHash.reference_string data)=expected) "reference vector";
    data,expected) [0;1;55;56;63;64;65;119;120;127;128;65535;65536;65537;1048576] in
  let domains=List.init 4 (fun _ -> Domain.Safe.spawn (fun () ->
    bounds ();
    List.iter (fun (data,expected) ->
      let context=Evp.create () in
      let input=Bytes.of_string data in
      let rec feed offset =
        if offset<Bytes.length input then begin
          let n=min 12347 (Bytes.length input-offset) in
          Evp.feed context input offset n; feed(offset+n)
        end in
      feed 0; check (SemanticHash.hex(Evp.finish context)=expected) "domain stream vector";
      check (SemanticHash.hex(SemanticHash.string data)=expected) "production domain stream vector") vectors)) in
  List.iter Domain.join domains;
  Gc.full_major (); Gc.full_major ();
  check (live ()=0 && methods ()=0) "finished contexts or methods leaked";
  for _=1 to 128 do ignore(Evp.create ()) done;
  Gc.full_major (); Gc.full_major ();
  check (live ()=0 && methods ()=0) "abandoned context finalizers leaked";
  inject 1;
  check (try ignore(Evp.create ());false with Failure _ -> true) "missing digest initialization accepted";
  check (live ()=0 && methods ()=0) "failed initialization leaked";
  let updating=Evp.create () in
  inject 2;
  check (try Evp.feed updating (Bytes.of_string "x") 0 1;false with Failure _ -> true) "failed update accepted";
  check (try ignore(Evp.finish updating);false with Invalid_argument _ -> true) "failed update context usable";
  check (live ()=0 && methods ()=0) "failed update leaked";
  let finishing=Evp.create () in
  inject 3;
  check (try ignore(Evp.finish finishing);false with Failure _ -> true) "failed finalization accepted";
  check (try ignore(Evp.finish finishing);false with Invalid_argument _ -> true) "failed finalization repeat accepted";
  check (live ()=0 && methods ()=0) "failed finalization leaked";
  Printf.printf "PASS %s:15vectors,4private domains,bounds/state,context+method cleanup,3failure stages\n" (Evp.version ())
