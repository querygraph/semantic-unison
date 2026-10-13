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
