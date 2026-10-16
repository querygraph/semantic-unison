let require b s = if not b then failwith s
let ok = function Ok x -> x | Error s -> failwith s
let error = function Error _ -> () | Ok _ -> failwith "expected rejection"
let write path s = let c = open_out_bin path in output_string c s; close_out c
let read path = let c = open_in_bin path in
  let s = really_input_string c (in_channel_length c) in close_in c; s
let with_file path f =
  let fd = Unix.openfile path [Unix.O_RDONLY] 0 in
  match SemanticFile.with_fd fd f with
  | x -> Unix.close fd; x | exception e -> Unix.close fd; raise e
let proof path = with_file path (fun f -> ok (SemanticDelta.inspect (module DngSemantic) f))
let put b little off width value =
  for j = 0 to width-1 do
    let i = if little then j else width-1-j in
    Bytes.set b (off+i) (Char.chr ((value lsr (8*j)) land 255))
  done
let fixture ?(little=true) ?(opaque='A') ?(xmp="<x>one</x>      ") () =
  let b = Bytes.make 8192 '\000' in
  Bytes.blit_string (if little then "II" else "MM") 0 b 0 2;
  let u16 o n = put b little o 2 n and u32 o n = put b little o 4 n in
  u16 2 42; u32 4 8; u16 8 4;
  let entry i tag typ count value = let p = 10+12*i in
    u16 p tag; u16 (p+2) typ; u32 (p+4) count; u32 (p+8) value in
  entry 0 273 4 1 4096; entry 1 279 4 1 1024;
  entry 2 700 1 (String.length xmp) 1024;
  entry 3 50706 1 4 0;
  Bytes.blit_string "\001\004\000\000" 0 b 54 4;
  Bytes.blit_string xmp 0 b 1024 (String.length xmp);
  Bytes.fill b 4096 1024 'R'; Bytes.set b 8191 opaque;
  Bytes.to_string b
let add_tag little tag typ count value s =
  let b = Bytes.of_string s in
  let count_byte = if little then 8 else 9 in
  let entries = Char.code (Bytes.get b count_byte) in
  let p = 10 + 12*entries in
  put b little 8 2 (entries+1);
  put b little p 2 tag; put b little (p+2) 2 typ;
  put b little (p+4) 4 count; put b little (p+8) 4 value;
  put b little (p+12) 4 0;
  Bytes.to_string b
let expect_reason expected = function
  | Error actual -> require (actual = expected) ("wrong fallback reason: " ^ actual)
  | Ok _ -> failwith "expected conservative fallback"
let large_packet_fixture ~little packet =
  let raw_offset = 1024 + String.length packet + 37 in
  let data = Bytes.make (raw_offset+1025) '\000' in
  Bytes.blit_string (fixture ~little ()) 0 data 0 62;
  put data little 18 4 raw_offset;
  put data little 38 4 (String.length packet);
  Bytes.blit_string packet 0 data 1024 (String.length packet);
  Bytes.fill data raw_offset 1024 'R';
  Bytes.set data (Bytes.length data-1) 'A'; Bytes.to_string data
let test_sparse_metadata_writes () =
  let length = 262150 in
  let original = String.init length (fun i -> Char.chr ((i*71+19) land 255)) in
  List.iter (fun little ->
    let base_bytes = large_packet_fixture ~little original in
    write "window-base" base_bytes;
    let base = proof "window-base" in
    let samples = SemanticDelta.samples base in
    require (List.length samples = 1 && String.length (List.hd samples).SemanticDelta.prefix = 4096 &&
      (List.hd samples).SemanticDelta.truncated) "bounded metadata sample";
    require (String.length (List.hd (SemanticDelta.samples ~max_total_bytes:13 base)).SemanticDelta.prefix=13)
      "smaller sample limit";
    List.iter (fun (positions,expected_bytes,expected_calls) ->
      let changed = Bytes.of_string original in
      List.iter (fun i -> Bytes.set changed i (Char.chr (Char.code (Bytes.get changed i) lxor 1))) positions;
      let target_bytes = large_packet_fixture ~little (Bytes.to_string changed) in
      write "window-target" target_bytes; write "window-stage" base_bytes;
      let plan = ok (SemanticDelta.plan ~nonce:(String.make 32 'w') ~base ~target:(proof "window-target")) in
      require (SemanticDelta.payload_size plan=length) "sparse optimization changed SDE payload";
      let output = Unix.openfile "window-stage" [Unix.O_RDWR] 0 in
      let report = with_file "window-base" (fun basis ->
        SemanticDelta.apply_report_with_extension (module DngSemantic) plan ~basis ~output) in
      Unix.close output;
      require (report.SemanticDelta.comparison_window=4096 &&
        report.SemanticDelta.logical_bytes_written=expected_bytes && report.SemanticDelta.write_calls=expected_calls)
        "actual writes did not skip or coalesce metadata windows";
      require (read "window-stage"=target_bytes && read "window-base"=base_bytes)
        "sparse metadata materialization changed source or result")
      [([],0,0);([5000],4096,1);([0],3072,1);([length-1],1030,1);
       ([5000;20000],8192,2);([5000;9000],8192,1);
       ([0;length-1],4102,2);([3071;3072],7168,1);
       (List.init length (fun i -> i),length,5);
       (List.init (length/2) (fun i -> 2*i),length,5)]) [true;false];
  let module Multi = struct
    let profile = "test.multi-window/0"
    let inspect _ = Ok {FormatExtension.regions=[{offset=5L;length=8190};{offset=20000L;length=10000}]}
  end in
  let bytes = String.make 35000 'A' in
  let target = Bytes.of_string bytes in Bytes.set target 5 'B'; Bytes.set target 25000 'C';
  write "multi-base" bytes; write "multi-stage" bytes; write "multi-target" (Bytes.to_string target);
  let get path = with_file path (fun f -> ok (SemanticDelta.inspect (module Multi) f)) in
  let base = get "multi-base" in
  let plan = ok (SemanticDelta.plan ~nonce:(String.make 32 'w') ~base ~target:(get "multi-target")) in
  let output = Unix.openfile "multi-stage" [Unix.O_RDWR] 0 in
  let report = with_file "multi-base" (fun basis ->
    SemanticDelta.apply_report_with_extension (module Multi) plan ~basis ~output) in
  Unix.close output;
  require (report.SemanticDelta.logical_bytes_written=8187 && report.SemanticDelta.write_calls=2 &&
    read "multi-stage"=Bytes.to_string target && read "multi-base"=bytes) "multi-region clipped writes";
  let samples = SemanticDelta.samples base in
  require (List.fold_left (fun n (s:SemanticDelta.sample) -> n+String.length s.prefix) 0 samples=8192 &&
    List.for_all (fun (s:SemanticDelta.sample) -> s.truncated) samples) "aggregate sample bound";
  List.iter (fun f -> try f (); failwith "sample ceiling ignored" with Invalid_argument _ -> ())
    [(fun () -> ignore (SemanticDelta.samples ~max_region_bytes:4097 base));
     (fun () -> ignore (SemanticDelta.samples ~max_total_bytes:8193 base))];
  print_endline "Sparse metadata: unchanged/first/last/disjoint/adjacent/full writes, both TIFF byte orders, multiple regions and bounded samples passed."
module Declared = struct
  let profile = "test.declared-payload/0"
  let inspect _ = Ok {FormatExtension.regions=[{offset=4L;length=8}]}
end
let () =
  List.iter (fun n -> let path = "vector-" ^ string_of_int n in
    let expected = read (path ^ ".sha256") in
    require (SemanticHash.hex (SemanticHash.string (read path)) = expected) "SHA string vector";
    require (SemanticHash.hex (SemanticHash.reference_string (read path)) = expected) "SHA reference vector";
    with_file path (fun f -> require (SemanticHash.hex (SemanticFile.digest f) = expected) "SHA streamed vector"))
    [0;1;55;56;63;64;65;119;120;127;128;65535;65536;65537;1048576];
  let limited = FormatExtension.trusted ~max_payload:4 (module Declared) in
  require (FormatExtension.payload_limit limited = 4) "declared payload bound lost";
  let hints = FormatExtension.trusted ~suffixes:[".DNG";".dng";".jpeg"] (module Declared) in
  require (FormatExtension.suffixes hints=[".dng";".jpeg"] &&
    FormatExtension.matches_filename hints "/some/FRAME.DNG" &&
    not (FormatExtension.matches_filename hints "frame.dng.backup")) "advisory suffix normalization";
  List.iter (fun suffixes ->
    try ignore (FormatExtension.trusted ~suffixes (module Declared));
      failwith "invalid suffix hints accepted" with Invalid_argument _ -> ())
    [["dng"];["."];[".bad/name"];[".bad\\name"];[".bad\000name"];List.init 17 (fun _ -> ".dng")];
  write "bounded-metadata" (String.make 32 'M');
  let file = Unix.openfile "bounded-metadata" [Unix.O_RDONLY] 0 and checks = ref 0 in
  let check_cancel () = incr checks;
    if !checks > 2 then failwith "oversized declaration reached core proof reads" in
  error (SemanticFile.with_fd ~check_cancel file (fun file ->
    SemanticDelta.inspect ~max_payload:(FormatExtension.payload_limit limited)
      (FormatExtension.implementation limited) file));
  Unix.close file;
  require (!checks = 2) "payload declaration was not checked before proof reads";
  List.iter (fun max_payload ->
    let rejected = try ignore (FormatExtension.trusted ~max_payload (module Declared)); false
      with Invalid_argument _ -> true in
    require rejected "invalid payload declaration accepted") [0;FormatExtension.max_payload+1];
  FormatExtension.register (module DngSemantic);
  test_sparse_metadata_writes ();
  List.iter (fun little ->
    let a = fixture ~little () and b = fixture ~little ~xmp:"<x>two</x>      " () in
    write "base" a; write "target" b; write "stage" a;
    let base = proof "base" and target = proof "target" in
    require (SemanticDelta.classify ~base ~target = FormatExtension.Editable_metadata) "XMP classification";
    let plan = ok (SemanticDelta.plan ~nonce:(String.make 32 'n') ~base ~target) in
    let request = SemanticDelta.encode_request ~nonce:(String.make 32 'n') base in
    let nonce,claimed_base = ok (SemanticDelta.decode_request request) in
    require (String.length request < 8192) "request bound";
    require (SemanticDelta.encode_request ~nonce claimed_base = request) "canonical request";
    let remote_plan = ok (SemanticDelta.plan ~nonce ~base:claimed_base ~target) in
    require (SemanticDelta.encode plan = SemanticDelta.encode remote_plan) "remote plan matches local";
    require (SemanticDelta.binds_request ~nonce ~base remote_plan) "response binding";
    require (not (SemanticDelta.binds_request ~nonce:(String.make 32 'x') ~base remote_plan)) "nonce mismatch accepted";
    require (not (SemanticDelta.binds_request ~nonce ~base:target remote_plan)) "base mismatch accepted";
    error (SemanticDelta.decode_request (request ^ "x"));
    error (SemanticDelta.decode_request (String.make 8193 'x'));
    for n = 0 to String.length request - 1 do
      error (SemanticDelta.decode_request (String.sub request 0 n)) done;
    let bad_request = Bytes.of_string request in
    (* SDR region count follows magic, nonce, profile length/name, size and two hashes. *)
    let count_at = 8 + 32 + 8 + String.length DngSemantic.profile + 8 + 64 in
    Bytes.fill bad_request count_at 8 '\255';
    error (SemanticDelta.decode_request (Bytes.to_string bad_request));
    let encoded = SemanticDelta.encode plan in
    let decoded = ok (SemanticDelta.decode encoded) in
    error (SemanticDelta.decode ~max_payload:8 encoded);
    require (SemanticDelta.encode decoded = encoded) "canonical encoding";
    error (SemanticDelta.decode (encoded ^ "x"));
    for n = 0 to String.length encoded - 1 do error (SemanticDelta.decode (String.sub encoded 0 n)) done;
    let corrupt = Bytes.of_string encoded in
    Bytes.set corrupt (Bytes.length corrupt-1) 'Z'; error (SemanticDelta.decode (Bytes.to_string corrupt));
    let output = Unix.openfile "stage" [Unix.O_RDWR] 0 in
    with_file "base" (fun basis -> SemanticDelta.apply decoded ~basis ~output);
    Unix.close output;
    require (read "stage" = b && read "base" = a) "exact result/source preservation";
    let same = Unix.openfile "base" [Unix.O_RDWR] 0 in
    (try SemanticFile.with_fd same (fun basis -> SemanticDelta.apply decoded ~basis ~output:same);
      failwith "accepted same inode" with SemanticFile.Invalid _ -> ());
    Unix.close same; require (read "base" = a) "same inode rejection precedes write";
    write "opaque" (fixture ~little ~opaque:'B' ~xmp:"<x>two</x>      " ());
    error (SemanticDelta.plan ~nonce:(String.make 32 'n') ~base ~target:(proof "opaque"));
    let aliased = Bytes.of_string a in
    put aliased little 18 4 1024; write "alias" (Bytes.to_string aliased);
    with_file "alias" (fun f -> error (DngSemantic.inspect f));
    let cycle = Bytes.of_string a in
    put cycle little 58 4 8; write "cycle" (Bytes.to_string cycle);
    with_file "cycle" (fun f -> error (DngSemantic.inspect f));
    let duplicate = Bytes.of_string a in
    put duplicate little 46 2 700; write "duplicate" (Bytes.to_string duplicate);
    with_file "duplicate" (fun f -> error (DngSemantic.inspect f));
    (* Ordinary image values and explicit EXIF/GPS/Interop graph links work;
       unrecognized fields must not masquerade as harmless scalar values. *)
    let ordinary = a |> add_tag little 256 4 1 32 |> add_tag little 257 4 1 32
      |> add_tag little 258 3 1 16 |> add_tag little 259 3 1 1
      |> add_tag little 262 3 1 32803 |> add_tag little 50717 4 1 65535 in
    write "ordinary" ordinary;
    with_file "ordinary" (fun f -> ignore (ok (DngSemantic.inspect f)));
    List.iter (fun tag ->
      write "private" (add_tag little tag 4 1 1024 a);
      with_file "private" (fun f ->
        expect_reason (Printf.sprintf "unsupported TIFF tag %d (opaque or private graph)" tag)
          (DngSemantic.inspect f))) [37500;50740;50933;65000];
    write "wrong-type" (add_tag little 256 13 1 1024 a);
    with_file "wrong-type" (fun f -> expect_reason "IFD type on non-pointer field" (DngSemantic.inspect f));
    let graph = a |> add_tag little 34665 4 1 2048 |> add_tag little 34853 4 1 2200
      |> Bytes.of_string in
    let entry base i tag typ n value = let p = base+2+12*i in
      put graph little p 2 tag; put graph little (p+2) 2 typ;
      put graph little (p+4) 4 n; put graph little (p+8) 4 value in
    put graph little 2048 2 2;
    entry 2048 0 36864 7 4 0; entry 2048 1 40965 4 1 2300;
    put graph little 2200 2 1; entry 2200 0 0 1 4 0;
    put graph little 2300 2 1; entry 2300 0 1 2 4 0;
    write "graph" (Bytes.to_string graph);
    with_file "graph" (fun f -> ignore (ok (DngSemantic.inspect f)));
    entry 2300 0 65000 4 1 1024;
    write "graph-private" (Bytes.to_string graph);
    with_file "graph-private" (fun f -> error (DngSemantic.inspect f));
    let fanout = add_tag little 330 4 256 2048 a |> Bytes.of_string in
    for j = 0 to 255 do put fanout little (2048+4*j) 4 6144 done;
    write "fanout" (Bytes.to_string fanout);
    with_file "fanout" (fun f -> expect_reason "IFD work limit" (DngSemantic.inspect f));
    write "stale-stage" b;
    let output = Unix.openfile "stale-stage" [Unix.O_RDWR] 0 in
    (try with_file "base" (fun basis -> SemanticDelta.apply decoded ~basis ~output);
      failwith "accepted wrong staging basis" with SemanticFile.Invalid _ -> ());
    Unix.close output; require (read "stale-stage" = b) "wrong stage rejection precedes write"
  ) [true;false];
  Random.init 7;
  for _ = 1 to 2000 do
    let s = Bytes.init (Random.int 400) (fun _ -> Char.chr (Random.int 256)) |> Bytes.to_string in
    error (SemanticDelta.decode s);
    write "random" s;
    with_file "random" (fun f -> error (DngSemantic.inspect f))
  done;
  print_endline "Semantic kernel: SHA-256 vectors, both TIFF byte orders, exact patch, opaque-byte rejection, malformed envelopes/IFDs passed."
