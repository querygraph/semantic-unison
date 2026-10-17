(* Original serialized-metadata controls; no archive trust or IO grant. *)
module C=ComponentHash
module T=Component_hash
let checks=ref 0
let check yes why=incr checks;if not yes then failwith why
let invalid f=try ignore(f());false with C.Invalid _ -> true
let capture layout=T.with_input T.data (fun _ fd -> SemanticFile.with_fd fd (fun file ->
  C.with_snapshot ~max_read_bytes:8192L file layout (fun session snapshot ->
    let checkpoint=C.checkpoint session snapshot in
    C.checkpoint_bytes checkpoint,C.checkpoint_sha256 checkpoint,C.layout_sha256 snapshot,
    C.projection snapshot C.Encoded_pixels)))
let encoded,seal,layout_hash,pixels=capture T.layout
let restore ?(budget=8192L) ?(schema="synthetic-layout/0") bytes digest file callback =
  C.with_checkpoint ~expected_checkpoint_sha256:digest ~expected_root_schema:schema
    ~max_read_bytes:budget file bytes callback
let mutate offset value bytes=let b=Bytes.of_string bytes in Bytes.set b offset value;Bytes.to_string b
let put_number offset number bytes=let b=Bytes.of_string bytes in
  for i=0 to 7 do Bytes.set b (offset+i) (Char.chr(Int64.to_int(Int64.logand 255L
    (Int64.shift_right_logical number (56-8*i))))) done;Bytes.to_string b
let frames bytes =
  let at=ref 16 in
  let number ()=let value=ref 0 in for _=0 to 7 do value:=(!value lsl 8)+Char.code bytes.[!at];incr at done;!value in
  let string ()=let count=number () in let start= !at in at:= !at+count;start in
  let rec node ()=
    let id=string () in ignore(string ());let role= !at in incr at;
    let offset= !at in ignore(number ());let length= !at in ignore(number ());
    let hash= !at in at:= !at+32;let children= !at in let count=number () in
    (id,role,offset,length,hash,children)::List.concat(List.init count(fun _ -> node ())) in node ()
let () =
  check(String.length seal=32 && seal=SemanticHash.string encoded &&
    String.length encoded<=C.max_checkpoint_size) "checkpoint envelope digest/bound differs";
  T.with_input T.data (fun _ fd ->
    let (session,snapshot),stats=SemanticFile.with_read_stats fd (fun file ->
      restore ~budget:11266L encoded seal file (fun session snapshot ->
        check(C.full_sha256 snapshot=SemanticHash.string T.data) "restored full identity differs";
        check(C.layout_sha256 snapshot=layout_hash && C.projection snapshot C.Encoded_pixels=pixels)
          "restored view/pixel identity differs";
        check(C.bytes_requested session=8192L) "restore did not charge full input verification";
        let checkpoint=C.checkpoint session snapshot in
        check(C.checkpoint_bytes checkpoint=encoded && C.checkpoint_sha256 checkpoint=seal)
          "checkpoint roundtrip not canonical";
        let binding=SemanticHash.string "original-root/path/generation/decoder-contract" in
        let record=C.checkpoint_record ~binding checkpoint in
        let record_digest=SemanticHash.string record in
        let unpack bytes digest=C.checkpoint_from_record ~expected_binding:binding
          ~expected_record_sha256:digest bytes in
        let restored=unpack record record_digest in
        check(C.checkpoint_bytes restored=encoded && C.checkpoint_sha256 restored=seal)
          "owner record changed checkpoint";
        T.with_input "" (fun path _ ->
          let output=Unix.openfile path [Unix.O_RDWR] 0 in
          Fun.protect ~finally:(fun () -> Unix.close output) (fun () ->
            let actual=C.write_checkpoint_record ~binding checkpoint output in
            check(actual=record_digest) "disk record digest differs";
            check((Unix.fstat output).Unix.st_size=String.length record)
              "record output size differs";
            let loaded=SemanticFile.with_fd output (fun file ->
              C.read_checkpoint_record ~expected_binding:binding
                ~expected_record_sha256:record_digest file) in
            check(C.checkpoint_bytes loaded=encoded && C.checkpoint_sha256 loaded=seal)
              "disk record roundtrip differs";
            check(invalid(fun () -> C.write_checkpoint_record ~binding checkpoint output))
              "nonempty record stage overwritten";
            check((Unix.fstat output).Unix.st_kind=Unix.S_REG)
              "borrowed record descriptor closed"));
        T.with_input "" (fun path _ ->
          let output=Unix.openfile path [Unix.O_RDWR] 0 in
          Fun.protect ~finally:(fun () -> Unix.close output) (fun () ->
            Unix.fchmod output 0o644;
            check(invalid(fun () -> C.write_checkpoint_record ~binding checkpoint output))
              "nonprivate record stage accepted";
            check((Unix.fstat output).Unix.st_size=0) "refused record stage was written"));
        T.with_input record (fun _ input -> SemanticFile.with_fd input (fun file ->
          check(invalid(fun () -> C.read_checkpoint_record ~expected_binding:binding
            ~expected_record_sha256:(String.make 32 'X') file))
            "disk record bypassed trusted digest"));
        check(String.sub record 0 8="UCR\000\000\000\000\000" &&
          String.sub record 8 32=binding && String.sub record 40 32=seal &&
          String.sub record 72 8=put_number 0 (Int64.of_int(String.length encoded)) (String.make 8 '\000') &&
          String.sub record 80 (String.length encoded)=encoded)
          "owner record independent framing differs";
        check(invalid(fun () -> C.checkpoint_from_record
          ~expected_binding:(SemanticHash.string "different-generation")
          ~expected_record_sha256:record_digest record)) "wrong owner generation accepted";
        check(invalid(fun () -> unpack (mutate 90 'X' record) record_digest))
          "tampered record accepted under trusted index digest";
        List.iter(fun bytes -> check(invalid(fun () -> unpack bytes (SemanticHash.string bytes)))
          "malformed authenticated record accepted")
          [record^"x";mutate 0 'X' record;put_number 72 0L record;
           mutate 40 'X' record;put_number 72 Int64.min_int record];
        for count=0 to String.length record-1 do
          let bytes=String.sub record 0 count in
          check(invalid(fun () -> unpack bytes (SemanticHash.string bytes)))
            "truncated owner record accepted"
        done;
        let pixel=T.find snapshot "file/pixels" in
        C.validate_base session snapshot T.layout;
        check(C.bytes_requested session=8192L) "base validation read payload";
        check(invalid(fun () -> C.validate_base session snapshot
          {T.layout with schema="changed-base/1"})) "changed base schema accepted";
        check(invalid(fun () -> C.validate_base session snapshot
          {T.layout with length=8191L})) "changed base extent accepted";
        check(invalid(fun () -> C.validate_base session snapshot
          {T.layout with children=List.map(fun (s:C.spec) ->
            if s.id="file/pixels" then {s with role=C.Opaque} else s) T.layout.children}))
          "changed pixel role accepted";
        let refined=match C.apply_plugin session snapshot ~component:"file/private" T.model_plugin with
          Ok value -> value | Error why -> failwith why in
        check(T.find refined "file/pixels"==pixel && C.projection refined C.Encoded_pixels=pixels)
          "restored refinement did not reuse unaffected pixel node/hash";
        C.validate_base session refined T.layout;
        check(C.bytes_requested session=11266L) "refined base validation read payload";
        check(C.bytes_requested session=11266L && C.full_sha256 refined=C.full_sha256 snapshot)
          "localized refinement read budget/full identity differs";
        session,snapshot)) in
    check(stats.logical_bytes=11266L && not stats.saturated) "restore/refine delivered-byte count differs";
    check(invalid(fun () -> C.checkpoint session snapshot)) "expired restored session exported authority");
  T.with_input T.data (fun _ fd ->
    let (),stats=SemanticFile.with_read_stats fd (fun file ->
      for count=0 to String.length encoded-1 do
        let truncated=String.sub encoded 0 count in
        check(invalid(fun () -> restore truncated (SemanticHash.string truncated) file (fun _ _ -> ())))
          "authenticated malformed truncated checkpoint accepted"
      done;
      let root=List.hd(frames encoded) and child=List.nth(frames encoded) 1 in
      let _,root_role,_,root_length,_,root_children=root in
      let _,_,child_offset,_,child_hash,_=child in
      List.iter(fun bytes -> check(invalid(fun () -> restore bytes (SemanticHash.string bytes) file
        (fun _ _ -> ()))) "malformed checkpoint accepted") [
        encoded^"x";mutate 0 'X' encoded;put_number 8 1025L encoded;
        mutate root_role '\009' encoded;put_number root_length 8191L encoded;
        put_number root_children 1024L encoded;put_number child_offset 1L encoded];
      check(invalid(fun () -> restore (mutate child_hash 'X' encoded) seal file (fun _ _ -> ())))
        "tampered cached pixel hash accepted under prior trusted digest";
      check(invalid(fun () -> restore ~schema:"wrong/0" encoded seal file (fun _ _ -> ())))
        "wrong root contract accepted";
      check(invalid(fun () -> restore ~budget:8191L encoded seal file (fun _ _ -> ())))
        "under-budget full verification accepted";
      check(invalid(fun () -> restore (String.make(C.max_checkpoint_size+1) 'x') seal file (fun _ _ -> ())))
        "oversized cache accepted") in
    check(stats.logical_bytes=0L) "metadata/budget refusals read input payload");
  T.with_input (mutate 8191 'Z' T.data) (fun _ fd -> SemanticFile.with_fd fd (fun file ->
    let called=ref false in
    check(invalid(fun () -> restore encoded seal file (fun _ _ -> called:=true))) "changed input reused cached hashes";
    check(not !called) "changed input reached reuse callback"));
  T.with_input T.data (fun _ fd -> SemanticFile.with_fd fd (fun file ->
    restore ~budget:17414L encoded seal file (fun session initial ->
      let apply snapshot plugin=match C.apply_plugin session snapshot ~component:"file/private" plugin with
        Ok value -> value | Error why -> failwith why in
      let first=apply initial T.model_plugin in
      let pending=C.reset_private_view session first ~component:"file/private" ~schema:"opaque-private/0" in
      check(C.projection pending C.Private_metadata=None && C.layout_sha256 pending=layout_hash)
        "private invalidation failed to retain exact opaque fallback";
      check(C.projection first C.Private_metadata<>None) "invalidation mutated historical snapshot";
      let next=apply pending {T.model_plugin with implementation_sha256=String.make 32 'V'} in
      check(T.find next "file/pixels"==T.find initial "file/pixels" &&
        C.projection next C.Encoded_pixels=pixels) "decoder upgrade invalidated unaffected pixels";
      check(C.layout_sha256 first<>C.layout_sha256 next &&
        C.projection first C.Private_metadata=C.projection next C.Private_metadata)
        "implementation provenance and unchanged leaf semantics conflated";
      check(C.bytes_requested session=14340L) "private reset reread unrelated data";
      let pending=C.reset_private_view session next ~component:"file/private" ~schema:"opaque-private/0" in
      let updated : C.plugin = {T.model_plugin with id="community.test.model/2";
        implementation_sha256=String.make 32 'W';decode=(fun reader ->
          match T.model_plugin.decode reader with
          | Ok ((field:C.spec)::rest) -> Ok ({field with schema="model-field/2"}::rest)
          | value -> value)} in
      let updated=apply pending updated in
      check(C.projection updated C.Private_metadata<>C.projection first C.Private_metadata &&
        C.projection updated C.Encoded_pixels=pixels && C.bytes_requested session=17414L)
        "meaning-schema refinement failed to update only its private view";
      check(invalid(fun () -> C.reset_private_view session next ~component:"file" ~schema:"wrong/0"))
        "private invalidation discarded structural/pixel claims";
      check(invalid(fun () -> C.reset_private_view session next ~component:"file/pixels" ~schema:"wrong/0"))
        "private invalidation accepted pixel leaf")));
  List.iter(fun role -> T.with_input T.data (fun _ fd -> SemanticFile.with_fd fd (fun file ->
    restore ~budget:11264L encoded seal file (fun session initial ->
      let unsafe=C.refine session initial ~component:"file/private" ~schema:"mixed/0"
        [T.spec "file/private/claimed" "claimed/0" role 0 3072] in
      check(invalid(fun () -> C.validate_base session unsafe T.layout))
        "base validation accepted private pixel/standard escalation";
      check(invalid(fun () -> C.reset_private_view session unsafe ~component:"file/private" ~schema:"opaque-private/0"))
        "private reset discarded an embedded pixel/standard claim")))) [C.Encoded_pixels;C.Standard_metadata];
  Printf.printf "PASS %d checkpoint controls; authenticated metadata, full input verification, localized refinement, malformed/tampered/stale refusals\n%!" !checks
