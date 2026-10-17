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
 Printf.printf "DNG component controls: %d checks PASS\n%!" !checks
