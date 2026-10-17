let checks=ref 0
let check ok why = incr checks;if not ok then failwith why
let field tag name max_bytes : PrivateIfdFields.field = {tag;name;max_bytes}
let schema order : PrivateIfdFields.schema = {
  component_id="dng/private";decoder_id="original.partial-fields/0";
  implementation_sha256=SemanticHash.string "original private field implementation/0";
  byte_order=order;directory_at=0L;value_base=(-128L);max_span=2048L;max_entries=8;
  fields=[field 21 "candidate-model" 9;field 22 "short-code" 4]}
let plugin schema = match PrivateIfdFields.freeze schema with Ok p -> p | Error s -> failwith s
let put b order at width value =
  for i=0 to width-1 do
    let shift=match order with PrivateIfdFields.Little -> i | Big -> width-1-i in
    Bytes.set b (at+i) (Char.chr ((value lsr (8*shift)) land 255))
  done
let fixture order =
  let b=Bytes.init 4096 (fun i -> Char.chr ((i*37+17) land 255)) in
  let n at width value=put b order (2048+at) width value in
  n 0 2 3;
  n 2 2 21;n 4 2 2;n 6 4 9;n 10 4 256;
  n 14 2 22;n 16 2 2;n 18 4 4;Bytes.blit_string "abc\000" 0 b (2048+22) 4;
  n 26 2 65000;n 28 2 13;n 30 4 1;n 34 4 0xfffffff0;
  n 38 4 0xdeadbeef;
  Bytes.blit_string "MODEL123\000" 0 b (2048+128) 9;
  Bytes.to_string b
let layout : ComponentHash.spec = {id="dng";schema="original-field-fixture/0";
  role=ComponentHash.Structural;offset=0L;length=4096L;children=[
  {id="dng/pixels";schema="encoded-original/0";role=Encoded_pixels;offset=0L;length=2048L;children=[]};
  {id="dng/private";schema="unknown-original/0";role=Opaque;offset=2048L;length=2048L;children=[]}]}
let with_input bytes action =
  let path=Filename.temp_file "original-private-fields-" ".bin" in
  let out=open_out_bin path in output_string out bytes;close_out out;
  let fd=Unix.openfile path [Unix.O_RDONLY] 0 in
  Fun.protect ~finally:(fun () -> Unix.close fd;Sys.remove path) (fun () -> SemanticFile.with_fd fd action)
let apply bytes config budget action = with_input bytes (fun file ->
  ComponentHash.with_snapshot ~max_read_bytes:budget file layout (fun session initial ->
    action session initial (ComponentHash.apply_plugin session initial ~component:"dng/private" (plugin config))))
let projection s role = match ComponentHash.projection s role with Some p -> p | None -> failwith "missing lane"
let () =
 List.iter (fun order ->
  let config=schema order and bytes=fixture order in
  check ((plugin config).implementation_sha256=(plugin {config with fields=List.rev config.fields}).implementation_sha256)
    "field order changes canonical decoder provenance";
  check ((plugin config).implementation_sha256<>(plugin {config with value_base=0L}).implementation_sha256)
    "address-space policy missing from provenance";
  apply bytes config 10000L (fun session initial result ->
    let refined=match result with Ok s -> s | Error s -> failwith s in
    check (ComponentHash.bytes_requested session=6201L) "partial fields read beyond parent/budget";
    check (ComponentHash.full_sha256 initial=ComponentHash.full_sha256 refined) "full bytes changed";
    check (ComponentHash.projection initial ComponentHash.Private_metadata=None) "unknown lane mislabeled known";
    check ((projection refined ComponentHash.Private_metadata).bytes=13L) "selected ASCII byte count";
    check (ComponentHash.projection initial ComponentHash.Encoded_pixels=
      ComponentHash.projection refined ComponentHash.Encoded_pixels) "partial decoding invalidated pixels";
    check (ComponentHash.layout_sha256 initial<>ComponentHash.layout_sha256 refined) "refinement view unchanged";
    check (List.hd (ComponentHash.root initial).children == List.hd (ComponentHash.root refined).children)
      "unaffected pixel node replaced";
    let next={config with implementation_sha256=SemanticHash.string "original implementation version2"} in
    let upgraded=match ComponentHash.apply_plugin session initial ~component:"dng/private" (plugin next) with
      | Ok value -> value | Error reason -> failwith reason in
    check (ComponentHash.projection upgraded ComponentHash.Private_metadata<>
      ComponentHash.projection refined ComponentHash.Private_metadata) "private projection omitted decoder provenance";
    check (ComponentHash.projection upgraded ComponentHash.Encoded_pixels=
      ComponentHash.projection refined ComponentHash.Encoded_pixels) "decoder version changed pixel projection");
  let refuse changed expected = apply changed config 10000L (fun _ _ result ->
    check (result=Error expected) expected) in
  let change at width value = let b=Bytes.of_string bytes in put b order (2048+at) width value;Bytes.to_string b in
  refuse (change 0 2 257) "private directory entry limit";
  refuse (change 4 2 7) "selected private ASCII shape unsupported";
  refuse (change 6 4 10) "selected private ASCII shape unsupported";
  refuse (change 2 2 23) "selected private field absent";
  refuse (change 26 2 21) "duplicate private directory tag";
  refuse (change 10 4 150) "selected private fields alias";
  refuse (change 10 4 999999) "private field outside declared span";
  let malformed=Bytes.of_string bytes in Bytes.set malformed (2048+136) 'X';
  refuse (Bytes.to_string malformed) "private ASCII lacks terminator";
  Bytes.set malformed (2048+136) '\000';Bytes.set malformed (2048+129) '\001';
  refuse (Bytes.to_string malformed) "private ASCII encoding unsupported";
  check (try apply bytes config 4096L (fun _ _ _ -> ());false with ComponentHash.Invalid _ -> true)
    "operational shared-budget failure downgraded";
  apply bytes {config with value_base=Int64.max_int} 10000L (fun _ _ result ->
    check (result=Error "private field offset overflow") "offset overflow not refused");
  let dng=Bytes.of_string bytes in
  let little at width value=put dng PrivateIfdFields.Little at width value in
  Bytes.blit_string "II" 0 dng 0 2;little 2 2 42;little 4 4 8;little 8 2 4;
  let entry index tag typ count value =
    let at=10+12*index in little at 2 tag;little (at+2) 2 typ;
    little (at+4) 4 count;little (at+8) 4 value in
  entry 0 50706 1 4 1025;entry 1 273 4 1 1024;
  entry 2 279 4 1 1024;entry 3 50740 1 2048 2048;little 58 4 0;
  let component_id="dng/ifd/0/tag/50740/value" in
  let decoder=plugin {config with component_id} in
  let bindings=match DngComponents.freeze_decoders [{component_id;decoder}] with
    | Ok value -> value | Error reason -> failwith reason in
  with_input (Bytes.to_string dng) (fun file ->
    match DngComponents.with_snapshot ~decoders:bindings ~max_read_bytes:6201L file
      (fun session ~initial ~refined outcomes ->
        check (List.map (fun (o:DngComponents.outcome) -> o.status) outcomes=[DngComponents.Refined])
          "private field plugin not dispatched inside DNG";
        check (ComponentHash.bytes_requested session=6201L) "nested DNG field read budget";
        check (ComponentHash.projection initial ComponentHash.Encoded_pixels=
          ComponentHash.projection refined ComponentHash.Encoded_pixels) "nested DNG pixels invalidated";
        check ((projection refined ComponentHash.Private_metadata).bytes=13L) "nested private field coverage") with
    | Ok () -> () | Error reason -> failwith reason)
 ) [PrivateIfdFields.Little;Big];
 List.iter (fun config -> check (match PrivateIfdFields.freeze config with Error _ -> true | _ -> false)
   "malformed schema accepted") [
   {(schema PrivateIfdFields.Little) with component_id="outside"};
   {(schema PrivateIfdFields.Little) with fields=[]};
   {(schema PrivateIfdFields.Little) with fields=[field 21 "x" 9;field 21 "y" 9]};
   {(schema PrivateIfdFields.Little) with fields=[field 21 "../x" 9]};
   {(schema PrivateIfdFields.Little) with implementation_sha256="bad"};
   {(schema PrivateIfdFields.Little) with max_entries=257};
   {(schema PrivateIfdFields.Little) with max_span=Int64.max_int}];
 Printf.printf "PASS %d original private-field controls; no camera semantics or IO ownership\n%!" !checks
