let check x why=if not x then failwith why
let read path=let c=open_in_bin path in let s=really_input_string c (in_channel_length c) in close_in c;s
let bounds_and_state () =
  let input=Bytes.of_string "abc" in
  let ctx=SemanticHash.create () in
  SemanticHash.feed ctx input 0 1;
  List.iter (fun (offset,count) ->
    check (try SemanticHash.feed ctx input offset count;false
           with Invalid_argument _ -> true) "invalid hash range accepted")
    [min_int,0; -1,0; 0,-1; 0,min_int; max_int,0; 0,max_int;
     max_int,max_int; 4,0; 3,1; 1,3];
  (* Rejected ranges must not poison the context or advance its byte count. *)
  SemanticHash.feed ctx input 0 0;
  SemanticHash.feed ctx input 3 0;
  SemanticHash.feed ctx input 1 2;
  check (SemanticHash.hex(SemanticHash.finish ctx)=
    "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad")
    "invalid range changed accepted stream";
  let empty=SemanticHash.create () and other=SemanticHash.create () in
  SemanticHash.feed other input 0 3;
  check (SemanticHash.hex(SemanticHash.finish empty)=
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855")
    "another context changed empty digest";
  check (SemanticHash.hex(SemanticHash.finish other)=
    "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad")
    "finalizing another context changed digest"
let () =
  let vectors=List.map (fun length ->
    let input=read(string_of_int length^".bin") in
    let expected=String.trim(read(string_of_int length^".sha256")) in
    check(SemanticHash.hex(SemanticHash.string input)=expected) "native digest differs from hashlib";
    check(SemanticHash.hex(SemanticHash.reference_string input)=expected) "reference digest differs from hashlib";
    length,input,expected) [0;1;55;56;63;64;65;119;120;127;128;65535;65536;65537;1048576] in
  let domains=List.init 4 (fun _ -> Domain.Safe.spawn (fun () ->
    bounds_and_state ();
    List.iter (fun (_,input,expected) ->
      let ctx=SemanticHash.create () in
      let b=Bytes.of_string input in
      let offset=ref 0 in
      while !offset < Bytes.length b do
        let count=min 12347 (Bytes.length b- !offset) in
        SemanticHash.feed ctx b !offset count;offset:= !offset+count
      done;
      check(SemanticHash.hex(SemanticHash.finish ctx)=expected) "private streamed context differs";
      check (try ignore(SemanticHash.finish ctx);false with Invalid_argument _ -> true) "double finish accepted";
      check (try SemanticHash.feed ctx b 0 0;false with Invalid_argument _ -> true) "feed after finish accepted";
      check(SemanticHash.hex(SemanticHash.reference_string input)=expected) "portable reference closure differs") vectors)) in
  List.iter Domain.join domains;
  print_endline "PASS portable native/reference hashing:15 hashlib vectors,4 actual domains,10 invalid ranges/domain, unchanged rejected streams, independent contexts, streaming and finalization"
