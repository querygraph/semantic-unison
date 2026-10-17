let checks=ref 0
let check test reason = incr checks;if not test then failwith reason
let describe file = match DngComponents.describe file with
  | Ok spec -> spec | Error reason -> failwith reason
let digest bytes = Layout_only.with_input bytes (fun file ->
  ComponentHash.with_snapshot ~max_read_bytes:8192L file (describe file)
    (fun session snapshot ->
      check (ComponentHash.bytes_requested session=8192L) "DNG hash budget";
      snapshot))
let projection snapshot role = match ComponentHash.projection snapshot role with
  | Some value -> value | None -> failwith "missing expected DNG projection"
let () =
 List.iter (fun little -> List.iter (fun big ->
  let bytes=Layout_only.fixture little big (String.make 64 'A') in
  let snapshot=digest bytes in
  check (ComponentHash.full_sha256 snapshot=SemanticHash.string bytes) "full DNG SHA";
  let pixel=projection snapshot ComponentHash.Encoded_pixels in
  check (pixel.bytes=512L && pixel.components=1) "encoded strip coverage";
  check ((projection snapshot ComponentHash.Private_metadata).bytes=132L) "private value coverage";
  check ((projection snapshot ComponentHash.Standard_metadata).bytes=76L) "XMP value coverage";
  let changed=Bytes.of_string bytes in Bytes.set changed 3076 'Z';
  let private_change=digest (Bytes.to_string changed) in
  check ((projection private_change ComponentHash.Encoded_pixels).sha256=pixel.sha256)
    "private change invalidated pixel projection";
  check ((projection private_change ComponentHash.Private_metadata).sha256<>
    (projection snapshot ComponentHash.Private_metadata).sha256) "private bytes ignored";
  let changed=Bytes.of_string bytes in Bytes.set changed 2050 'P';
  check ((projection (digest (Bytes.to_string changed)) ComponentHash.Encoded_pixels).sha256<>
    pixel.sha256) "pixel change ignored";
  let primary,cw,ew,va,iw = if big then 16,8,20,12,8 else 8,2,12,8,4 in
  let no_xmp=Bytes.of_string bytes in
  Layout_only.put no_xmp little (primary+cw+ew) 2 65001;
  Layout_only.with_input (Bytes.to_string no_xmp) (fun file ->
    check (match DngLayout.inspect file with Error _ -> true | _ -> false)
      "transfer profile lost XMP prerequisite";
    let spec=describe file in
    ComponentHash.with_snapshot ~max_read_bytes:8192L file spec (fun _ snapshot ->
      check ((projection snapshot ComponentHash.Standard_metadata).bytes=12L)
        "unknown tag gained standard authority";
      check ((projection snapshot ComponentHash.Private_metadata).bytes=196L)
        "XMP-free private coverage"));
  let alias=Bytes.of_string bytes in
  Layout_only.put alias little (primary+cw+ew*2+va) iw 3072;
  Layout_only.with_input (Bytes.to_string alias) (fun file ->
    check (DngComponents.describe file=Error "DNG component physical aliases unsupported")
      "private/pixel alias claimed independent");
  let gap=Bytes.of_string bytes in Bytes.set gap 7000 'G';
  let gap_change=digest (Bytes.to_string gap) in
  check ((projection gap_change ComponentHash.Encoded_pixels).sha256=pixel.sha256)
    "residual change invalidated pixel bytes";
  check ((projection gap_change ComponentHash.Opaque).sha256<>
    (projection snapshot ComponentHash.Opaque).sha256) "gap disappeared"
 ) [false;true]) [false;true];
 let private_id="dng/ifd/0/tag/50740/value" in
 let fragment id role offset length : ComponentHash.spec =
   {id;schema="original-test-field/1";role;offset;length;children=[]} in
 let plugin name decode : ComponentHash.plugin =
   {id=name;implementation_sha256=SemanticHash.string name;decode} in
 let parent=plugin "original.parent/1" (fun reader ->
   ignore(ComponentHash.read reader 0L 2);
   Ok [fragment (private_id^"/known") ComponentHash.Private_metadata 0L 16L;
       fragment (private_id^"/nested") ComponentHash.Opaque 16L 112L]) in
 let child=plugin "original.child/1" (fun reader ->
   ignore(ComponentHash.read reader 0L 1);
   Ok [fragment (private_id^"/nested/code") ComponentHash.Private_metadata 0L 1L]) in
 let unsupported=plugin "original.unsupported/1" (fun _ -> Error "not learned yet") in
 let forbidden=plugin "original.invalid-role/1" (fun _ ->
   Ok [fragment (private_id^"/known/pixels") ComponentHash.Encoded_pixels 0L 1L]) in
 let never=plugin "original.never/1" (fun _ -> failwith "standard target invoked private decoder") in
 let bind component_id decoder : DngComponents.binding = {component_id;decoder} in
 let bindings=[bind private_id parent;bind (private_id^"/nested") child;
   bind "dng/absent" unsupported;bind "dng/ifd/0/tag/50706/value" never;
   bind "dng/ifd/0/tag/65000/value" unsupported;bind (private_id^"/known") forbidden] in
 let frozen=match DngComponents.freeze_decoders bindings with
   | Ok value -> value | Error reason -> failwith reason in
 check (match DngComponents.freeze_decoders [bind private_id parent;bind private_id child] with
   Error _ -> true | _ -> false) "duplicate decoder target";
 check (match DngComponents.freeze_decoders [bind "outside/target" parent] with
   Error _ -> true | _ -> false) "decoder target namespace";
 check (match DngComponents.freeze_decoders [bind private_id {parent with implementation_sha256="bad"}] with
   Error _ -> true | _ -> false) "decoder provenance binding";
 check (match DngComponents.freeze_decoders (List.init 65 (fun n -> bind ("dng/"^string_of_int n) parent)) with
   Error _ -> true | _ -> false) "decoder binding bound";
 Layout_only.with_input (Layout_only.fixture true false (String.make 64 'A')) (fun file ->
   match DngComponents.with_snapshot ~decoders:frozen ~max_read_bytes:8435L file
     (fun session ~initial ~refined outcomes ->
       check (List.map (fun (o:DngComponents.outcome) -> o.status) outcomes=
         [DngComponents.Refined;Refined;Unmatched;Unsupported "target is not private or opaque";
          Unsupported "not learned yet";Unsupported "private decoder fragment role/count/depth refused"])
         "nested decoder outcomes/order";
       check (List.map (fun (o:DngComponents.outcome) -> o.decoder_id,o.implementation_sha256) outcomes=
         List.map (fun (b:DngComponents.binding) -> b.decoder.id,b.decoder.implementation_sha256) bindings)
         "decoder outcome provenance missing";
       check (ComponentHash.bytes_requested session=8435L) "DNG nested refinement locality";
       check (ComponentHash.full_sha256 initial=ComponentHash.full_sha256 refined) "DNG refinement full SHA";
       check (ComponentHash.projection initial ComponentHash.Encoded_pixels=
         ComponentHash.projection refined ComponentHash.Encoded_pixels) "DNG decoder changed pixel identity";
       check (ComponentHash.projection initial ComponentHash.Standard_metadata=
         ComponentHash.projection refined ComponentHash.Standard_metadata) "DNG decoder changed standard lane";
       check (ComponentHash.layout_sha256 initial<>ComponentHash.layout_sha256 refined)
         "DNG decoder provenance/view root unchanged") with
   | Ok () -> () | Error reason -> failwith reason);
 let failing=plugin "original.operational-failure/1" (fun _ ->
   raise (ComponentHash.Invalid "original injected decoder failure")) in
 let failed=match DngComponents.freeze_decoders [bind private_id failing] with
   | Ok value -> value | Error reason -> failwith reason in
 Layout_only.with_input (Layout_only.fixture true false (String.make 64 'A')) (fun file ->
   check (try ignore(DngComponents.with_snapshot ~decoders:failed ~max_read_bytes:8192L file
     (fun _ ~initial:_ ~refined:_ _ -> ()));false with
     ComponentHash.Invalid "original injected decoder failure" -> true)
     "operational decoder failure downgraded to unsupported");
 Printf.printf "DNG component controls: %d checks PASS\n%!" !checks
