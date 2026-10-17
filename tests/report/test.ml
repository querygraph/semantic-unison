module Report = SemanticReport
module Multiple = struct
  let profile = "test.multiple-report/0"
  let inspect _ = Ok {FormatExtension.regions=[{offset=4L;length=4000};
    {offset=4096L;length=4000};{offset=8192L;length=4000}]}
end
let test name f = f (); Printf.printf "PASS %s\n%!" name
let inspect extension path = with_file path (fun file ->
  Report.from_proof (ok (SemanticDelta.inspect extension file)))
let nonce=String.make 32 'n'
let contains value fragment =
  let rec scan i = if i+String.length fragment>String.length value then false
    else if String.sub value i (String.length fragment)=fragment then true else scan (i+1) in
  scan 0
let roundtrip observation =
  let encoded=Report.encode ~nonce observation in
  let decoded=ok (Report.decode ~nonce ~profile:(Report.profile observation)
    ~max_payload:FormatExtension.max_payload encoded) in
  require (Report.encode ~nonce decoded=encoded) "report is not canonical";
  decoded
let () =
  let p = {ComponentHash.sha256=String.make 32 'p';components=1;bytes=1024L} in
  let c = {Report.schema="dng-components/0";full_sha256=String.make 32 'f';
    layout_sha256=String.make 32 'l';projections=[ComponentHash.Encoded_pixels,Some p]} in
  let encode value=Report.encode_components ~nonce ~schema:c.schema value in
  let decode value=Report.decode_components ~nonce ~schema:c.schema value in
  test "SIC0 matches independent fixed-role byte vector" (fun () ->
    let expected="SIC\000\000\000\000\000" ^ nonce ^ String.make 7 '\000' ^ "\016" ^
      "dng-components/0" ^ "\000" ^ String.make 32 'f' ^ String.make 32 'l' ^
      "\001" ^ String.make 32 'p' ^ String.make 7 '\000' ^ "\001" ^
      String.make 6 '\000' ^ "\004\000" ^ String.make 4 '\000' in
    require (encode (Ok c)=expected) "SIC0 wire vector drift");
  test "SIC0 canonical fixed slots preserve missing versus present lanes" (fun () ->
    List.iter (fun value -> let bytes=encode value in
      let decoded=ok (decode bytes) in require (encode decoded=bytes) "noncanonical component report")
      [Ok c;Ok {c with projections=[]};Error "unsupported"]);
  test "SIC0 rejects every truncation and substituted request" (fun () ->
    let bytes=encode (Ok c) in
    for length=0 to String.length bytes-1 do error (decode (String.sub bytes 0 length)) done;
    error (Report.decode_components ~nonce:(String.make 32 'x') ~schema:c.schema bytes);
    error (Report.decode_components ~nonce ~schema:"other-contract" bytes);
    error (decode (bytes ^ "x"));error (decode (String.make 2049 'x')));
  test "SIC0 rejects bad version status presence counts and integer overflow" (fun () ->
    let bytes=encode (Ok c) in
    let status=8+32+8+String.length c.schema in
    let flag=status+1+64 in
    let mutate at value=let b=Bytes.of_string bytes in Bytes.set b at value;Bytes.to_string b in
    error (decode (mutate 0 'X'));error (decode (mutate status '\002'));
    error (decode (mutate flag '\002'));error (decode (mutate (flag+33) '\255'));
    let b=Bytes.of_string bytes in Bytes.fill b (flag+33) 8 '\000';error (decode (Bytes.to_string b));
    let b=Bytes.of_string bytes in Bytes.fill b (flag+41) 8 '\000';error (decode (Bytes.to_string b)));
  test "SIC0 enforces encoder binding and diagnostic limits" (fun () ->
    let refuses f= require (try ignore(f());false with Invalid_argument _ -> true) "invalid encoding accepted" in
    refuses (fun () -> encode (Error (String.make 1025 'x')));
    refuses (fun () -> encode (Ok {c with schema="different"}));
    refuses (fun () -> Report.encode_components ~nonce:"short" ~schema:c.schema (Ok c)));
  test "component equality preserves unknown lanes and advisory scope" (fun () ->
    let text=ok (Report.render_components ~left:c ~right:c) in
    require (contains text "Encoded pixels: equal" && contains text "Private metadata: unknown" &&
      contains text "do not prove equal rendering") "missing lane equated or authority broadened");
  test "different full bytes can preserve pixel identity" (fun () ->
    let text=ok (Report.render_components ~left:c ~right:{c with full_sha256=String.make 32 'x'}) in
    require (contains text "full-file bytes: different" && contains text "Encoded pixels: equal")
      "full bytes and pixel identity conflated");
  test "schema mismatch suppresses component equality" (fun () ->
    let text=ok (Report.render_components ~left:c ~right:{c with schema="dng-components/1"}) in
    require (contains text "incomparable" && not (contains text "Encoded pixels: equal")) "schema mismatch compared");
  test "component report rejects malformed and duplicate claims" (fun () ->
    List.iter (fun bad -> require (match Report.render_components ~left:bad ~right:c with
      Error _ -> true | _ -> false) "invalid component claim accepted")
      [{c with full_sha256="short"};{c with projections=c.projections@c.projections};
       {c with projections=[ComponentHash.Encoded_pixels,Some {p with bytes=0L}]}]);
  test "component schema cannot inject terminal controls" (fun () ->
    let value={c with schema="schema\027[2J"} in
    require (not (String.contains (ok (Report.render_components ~left:value ~right:value)) '\027'))
      "schema leaked escape");
  write "base" (fixture ());
  write "metadata" (fixture ~xmp:"<x>two</x>      " ());
  write "opaque" (fixture ~opaque:'Z' ());
  write "layout" (fixture ~xmp:"<x>a longer packet</x>   " ());
  let base=inspect (module DngSemantic) "base"
  and metadata=inspect (module DngSemantic) "metadata"
  and opaque=inspect (module DngSemantic) "opaque"
  and layout=inspect (module DngSemantic) "layout" in
  test "current-pair classifications preserve metadata/complement/layout distinctions" (fun () ->
    require (Report.classification base base=Report.Exact_bytes) "exact classification";
    require (Report.classification base metadata=Report.Metadata_only) "metadata classification";
    require (Report.classification base opaque=Report.Other_bytes) "opaque bytes mislabeled metadata";
    require (Report.classification base layout=Report.Other_bytes) "layout change mislabeled metadata";
    require (Report.classification base (Report.Unsupported (DngSemantic.profile,"unsupported graph"))=Report.Unknown)
      "unsupported report implied equality");
  test "supported, unsupported and old-peer observations round-trip with request binding" (fun () ->
    List.iter (fun observation -> ignore (roundtrip observation))
      [base;metadata;opaque;layout;Report.Unsupported (DngSemantic.profile,"unknown tag");
       Report.Unavailable (DngSemantic.profile,"old peer")];
    let encoded=Report.encode ~nonce base in
    error (Report.decode ~nonce:(String.make 32 'x') ~profile:DngSemantic.profile ~max_payload:1048576 encoded);
    error (Report.decode ~nonce ~profile:"another-profile/0" ~max_payload:1048576 encoded);
    error (Report.decode ~nonce ~profile:DngSemantic.profile ~max_payload:8 encoded));
  test "bounded prefixes retain full packet digests and escape control bytes" (fun () ->
    write "multiple" ("HEAD" ^ String.make 16380 '\027');
    let observation=inspect (module Multiple) "multiple" in
    let checked=roundtrip observation in
    begin match checked with
    | Report.Supported value ->
        require (List.length value.samples=3) "sample count";
        require (List.fold_left (fun total (s:SemanticDelta.sample) -> total+String.length s.prefix) 0 value.samples=8192)
          "aggregate prefix limit";
        require (List.map (fun (s:SemanticDelta.sample) -> String.length s.prefix) value.samples=[4000;4000;192])
          "per-region or aggregate prefix limit";
        require ((List.nth value.samples 2).truncated) "truncated prefix claimed complete"
    | _ -> failwith "multiple format unsupported" end;
    let text=Report.render ~left_label:"left\027[2J" ~right_label:"right" observation observation in
    require (not (String.contains text '\027') && not (String.contains text '\000')) "terminal control escaped incorrectly";
    require (String.length text<=65536 && contains text "\\x1b") "bounded byte preview missing");
  test "operational diagnostics are clipped and terminal-safe" (fun () ->
    let text=Report.display_reason (String.make 3000 '\027' ^ "\000") in
    require (not (String.contains text '\027') && not (String.contains text '\000') && String.length text<=4096)
      "diagnostic leaked terminal controls or exceeded its escaped limit");
  test "malformed reports reject extents, digests, flags and unchecked lengths" (fun () ->
    let encoded=Report.encode ~nonce base in
    let decode value=Report.decode ~nonce ~profile:DngSemantic.profile ~max_payload:1048576 value in
    for n=0 to String.length encoded-1 do error (decode (String.sub encoded 0 n)) done;
    error (decode (encoded ^ "trailing"));
    error (decode (String.make (Report.max_size+1) 'x'));
    let region=8+8+String.length DngSemantic.profile+32+1+8+32+32+8 in
    let mutate at length value = let bytes=Bytes.of_string encoded in
      Bytes.fill bytes at length value; error (decode (Bytes.to_string bytes)) in
    mutate region 8 '\255';
    mutate (region+8) 8 '\255';
    mutate (region+16) 32 '\000';
    mutate (region+48) 8 '\255';
    mutate (String.length encoded-1) 1 '\255');
  test "random malformed observations stay bounded" (fun () ->
    let state=Random.State.make [|871;19|] in
    for _=1 to 2000 do
      let value=String.init (Random.State.int state 1024) (fun _ -> Char.chr (Random.State.int state 256)) in
      error (Report.decode ~nonce ~profile:DngSemantic.profile ~max_payload:1048576 value)
    done);
  test "advisory text identifies current files without archive/rendering authority" (fun () ->
    let text=Report.render ~left_label:"left" ~right_label:"right" base metadata in
    require (contains text "without an archived base" && contains text "no rendering equivalence") "observation scope missing";
    require (Report.classification base (roundtrip metadata)=Report.Metadata_only) "wire classification differs");
  print_endline "All bounded semantic report tests passed."

let () =
  let extension = FormatExtension.trusted ~max_payload:1048576 ~observer:DngSemantic.observer (module DngSemantic) in
  let packet rating exposure =
    "<rdf:RDF xmlns:rdf=\"http://www.w3.org/1999/02/22-rdf-syntax-ns#\" " ^
    "xmlns:xmp=\"http://ns.adobe.com/xap/1.0/\" xmlns:crs=\"http://ns.adobe.com/camera-raw-settings/1.0/\">" ^
    "<rdf:Description rdf:about=\"\" xmp:Rating=\"" ^ rating ^ "\" crs:Exposure2012=\"" ^ exposure ^ "\"/></rdf:RDF>" in
  let observed path bytes =
    write path (fixture ~xmp:bytes ());
    with_file path (fun file ->
      let proof=ok (SemanticDelta.inspect (module DngSemantic) file) in
      let meaning=SemanticDelta.observe ~extension proof in
      Report.from_proof ?meaning proof) in
  let a=observed "meaning-a" (packet "1" "0")
  and b=observed "meaning-b" (packet "2" "1") in
  let decode encoded = Report.decode_observation ~nonce ~profile:DngSemantic.profile ~max_payload:1048576 encoded in
  test "extension-defined XMP meaning survives SIR1 but SIR0 omits it" (fun () ->
    let encoded=Report.encode_observation ~nonce a in
    let restored=ok (decode encoded) in
    require (restored=a && Report.encode_observation ~nonce restored=encoded) "SIR1 canonical roundtrip";
    (match roundtrip a with Report.Supported {meaning=None;_} -> () | _ -> failwith "SIR0 leaked new properties");
    require (Report.classification a b=Report.Metadata_only) "meaning changed byte classification";
    let text=Report.render ~left_label:"left" ~right_label:"right" a b in
    require (contains text "descriptive metadata:" && contains text "Rating encoding/context changed") "rating meaning missing";
    require (contains text "rendering metadata:" && contains text "Exposure2012 encoding/context changed") "rendering meaning missing";
    require (contains text "not XML/RDF value equality or rendering equivalence") "meaning implied rendering equality");
  test "SIR1 rejects truncation, request substitution, over-limit and trailing encodings" (fun () ->
    let encoded=Report.encode_observation ~nonce a in
    for n=0 to String.length encoded-1 do error (decode (String.sub encoded 0 n)) done;
    error (decode (encoded^"trailing"));error (decode (String.make (Report.max_observation_size+1) 'x'));
    error (Report.decode_observation ~nonce:(String.make 32 'x') ~profile:DngSemantic.profile ~max_payload:1048576 encoded);
    error (Report.decode_observation ~nonce ~profile:"wrong-profile" ~max_payload:1048576 encoded));
  test "generic observer validates bounds and unique names before reporting" (fun () ->
    let property={FormatExtension.name="field";category=FormatExtension.Workflow;digest=String.make 32 'd'} in
    let invalid props =
      let observer={FormatExtension.schema="generic-v0";observe=(fun _ -> Ok props)} in
      let handle=FormatExtension.trusted ~observer (module DngSemantic) in
      match FormatExtension.observe handle ["packet"] with Some (Error _) -> () | _ -> failwith "invalid observer output accepted" in
    invalid [property;property]; invalid [{property with name=String.make 513 'x'}];
    invalid [{property with digest="bad"}];invalid (List.init 129 (fun i -> {property with name=string_of_int i}));
    (try ignore (FormatExtension.trusted ~observer:{schema="";observe=(fun _ -> Ok [])} (module DngSemantic));
      failwith "empty schema accepted" with Invalid_argument _ -> ()));
  test "unsupported XMP interpretation preserves exact-transfer proof and SIR1 reason" (fun () ->
    let bad=observed "meaning-bad" "<x>unqualified</x>" in
    (match bad with Report.Supported {meaning=Some (Error _);_} -> () | _ -> failwith "bad XMP meaning reported");
    ignore (ok (decode (Report.encode_observation ~nonce bad)));
    let base=proof "meaning-bad" in
    ignore (ok (SemanticDelta.plan ~nonce ~base ~target:base)));
  test "SDR peer claims cannot feed the full-packet observation hook" (fun () ->
    let base=proof "meaning-a" in
    let _,peer=ok (SemanticDelta.decode_request (SemanticDelta.encode_request ~nonce base)) in
    match SemanticDelta.observe ~extension peer with Some (Error _) -> () | _ -> failwith "peer hash claims interpreted as packet bytes");
  test "SIR1 rejects invalid property tags and canonical-name mutations" (fun () ->
    let encoded=Report.encode_observation ~nonce a in
    let base_length=String.length (Report.encode ~nonce a) in
    let header=16+base_length+1 in
    let schema_length=String.length "dng-xmp-property-encoding-v0" in
    let name_start=header+8+schema_length+8+8 in
    let name_length=match a with Report.Supported {meaning=Some (Ok value);_} ->
      String.length (List.hd value.properties).FormatExtension.name | _ -> assert false in
    let bytes=Bytes.of_string encoded in
    Bytes.set bytes (name_start+name_length) '\255';error (decode (Bytes.to_string bytes));
    let bytes=Bytes.of_string encoded in Bytes.set bytes name_start '\000';error (decode (Bytes.to_string bytes));
    let bytes=Bytes.of_string encoded in Bytes.fill bytes (header+8+schema_length) 8 '\255';error (decode (Bytes.to_string bytes));
    let bytes=Bytes.of_string encoded in Bytes.set bytes (16+base_length) '\255';error (decode (Bytes.to_string bytes));
    let bytes=Bytes.of_string encoded in Bytes.set bytes 7 '\002';error (decode (Bytes.to_string bytes)));
  test "bounded interpretation escapes names and compares schema versions conservatively" (fun () ->
    let with_meaning observation schema props=match observation with Report.Supported value ->
      Report.Supported {value with meaning=Some (Ok {FormatExtension.schema;properties=props})} | _ -> assert false in
    let property={FormatExtension.name="field\027[2J";category=FormatExtension.Opaque;digest=String.make 32 'a'} in
    let left=with_meaning a "custom-v0" [property] and right=with_meaning b "custom-v0" [{property with digest=String.make 32 'b'}] in
    let text=Report.render ~left_label:"left" ~right_label:"right" left right in
    require (not (String.contains text '\027') && contains text "unclassified metadata") "observer name leaked control";
    let right=with_meaning b "custom-v1" [property] in
    require (contains (Report.render ~left_label:"left" ~right_label:"right" left right) "schema versions differ") "schema mismatch equated");
  test "complete SIR1 metadata is bounded even with maximum field declarations" (fun () ->
    let properties=List.init 128 (fun i -> {FormatExtension.name=Printf.sprintf "%03d" i ^ String.make 509 'x';
      category=FormatExtension.Opaque;digest=String.make 32 'd'}) in
    let observation=match a with Report.Supported value -> Report.Supported {value with
      meaning=Some (Ok {FormatExtension.schema="boundary-v0";properties})} | _ -> assert false in
    let encoded=Report.encode_observation ~nonce observation in
    require (String.length encoded<=Report.max_observation_size) "valid maximum fields exceed wire cap";
    ignore (ok (decode encoded));
    let dangerous=List.map (fun (p:FormatExtension.property) ->
      {p with name=String.sub p.name 0 3 ^ String.make 509 '\200'}) properties in
    let left=match a with Report.Supported value -> Report.Supported {value with
      meaning=Some (Ok {FormatExtension.schema="boundary-v0";properties=dangerous})} | _ -> assert false in
    let right=match b with Report.Supported value -> Report.Supported {value with
      meaning=Some (Ok {FormatExtension.schema="boundary-v0";properties=List.map (fun (p:FormatExtension.property) ->
        {p with digest=String.make 32 'e'}) dangerous})} | _ -> assert false in
    let text=Report.render ~left_label:"left" ~right_label:"right" left right in
    require (String.length text<=65536 && contains text "Property categories are advisory" &&
      contains text "without an archived base" && contains text "no rendering equivalence")
      "truncation removed the advisory boundary")
