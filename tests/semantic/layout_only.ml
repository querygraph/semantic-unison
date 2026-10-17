(* Original synthetic TIFFs: opaque pointers deliberately reference changed XMP.
   Exact reconstruction is tested; vendor grammar and pixel decoding are not. *)
let checks = ref 0
let check ok reason = incr checks; if not ok then failwith reason
let put bytes little at width value =
  for j=0 to width-1 do
    Bytes.set bytes (at+(if little then j else width-1-j))
      (Char.chr ((value lsr (8*j)) land 255))
  done
let fixture little big packet =
  let bytes=Bytes.make 8192 '\085' in
  let n at width value=put bytes little at width value in
  Bytes.blit_string (if little then "II" else "MM") 0 bytes 0 2;
  let primary,cw,ew,iw,va = if big then begin
    n 2 2 43;n 4 2 8;n 6 2 0;n 8 8 16;16,8,20,8,12
  end else (n 2 2 42;n 4 4 8;8,2,12,4,8) in
  n primary cw 6;
  let entry i tag typ count value =
    let at=primary+cw+ew*i in
    n at 2 tag;n (at+2) 2 typ;n (at+4) iw count;
    for j=0 to iw-1 do Bytes.set bytes (at+va+j) '\000' done;
    let bytes_count=count*(if typ=1 then 1 else 4) in
    n (at+va) (if bytes_count<=iw then bytes_count else iw) value in
  entry 0 50706 1 4 0;
  Bytes.blit_string "\001\004\000\000" 0 bytes (primary+cw+va) 4;
  entry 1 700 1 64 1024;
  entry 2 273 4 1 2048;
  entry 3 279 4 1 512;
  entry 4 50740 1 128 3072;
  (* Scalar-shaped unknown IFD pointer: do not infer pointer independence. *)
  entry 5 65000 13 1 1024;
  n (primary+cw+ew*6) iw 0;
  Bytes.blit_string packet 0 bytes 1024 64;
  n 3072 4 1024;
  Bytes.to_string bytes
let with_input bytes f =
  let path=Filename.temp_file "layout-original-" ".dng" in
  let out=open_out_bin path in output_string out bytes;close_out out;
  let fd=Unix.openfile path [Unix.O_RDONLY] 0 in
  Fun.protect ~finally:(fun () -> Unix.close fd;Sys.remove path)
    (fun () -> SemanticFile.with_fd fd f)
let with_stage bytes f =
  let path=Filename.temp_file "layout-stage-" ".dng" in
  let out=open_out_bin path in output_string out bytes;close_out out;
  let fd=Unix.openfile path [Unix.O_RDWR] 0 in
  Fun.protect ~finally:(fun () -> Unix.close fd;Sys.remove path) (fun () -> f fd)
let inspect file = match SemanticDelta.inspect (module DngLayout) file with
  | Ok proof -> proof | Error reason -> failwith reason
let plan base target = match SemanticDelta.plan ~nonce:(String.make 32 'N') ~base ~target with
  | Ok plan -> plan | Error reason -> failwith reason
let () =
  let handle=FormatExtension.trusted (module DngLayout) in
  check (FormatExtension.span_semantics handle=FormatExtension.Opaque_spans)
    "layout handle must not imply interpreted metadata";
  List.iter (fun little -> List.iter (fun big ->
    let before=fixture little big (String.make 64 'A')
    and after=fixture little big (String.make 64 'B') in
    with_input before (fun basis -> with_input after (fun source ->
      List.iter (fun strict -> match strict basis with
        | Error _ -> incr checks | Ok _ -> failwith "strict private safety changed")
        [DngSemantic.inspect;DngExtended.inspect];
      let base=inspect basis and target=inspect source in
      check (SemanticDelta.classify ~base ~target=FormatExtension.Uninterpreted_regions)
        "layout confinement mislabeled interpreted metadata";
      check (SemanticDelta.classify ~base ~target:base=FormatExtension.Exact_bytes)
        "exact bytes must remain exact";
      let update=plan base target in
      with_stage before (fun output ->
        let report=SemanticDelta.apply_report_with_extension (module DngLayout) update ~basis ~output in
        check (report.logical_bytes_written=64) "unexpected patch byte count";
        let digest=SemanticFile.with_fd output SemanticFile.digest in
        check (digest=SemanticHash.string after) "opaque-reference target not exact donor");
      with_stage before (fun output ->
        let report=SemanticDelta.apply_report_with_extension (module DngLayout)
          (plan base base) ~basis ~output in
        check (report.logical_bytes_written=0 && report.write_calls=0) "noop wrote data");
      let encoded=SemanticDelta.encode_request ~nonce:(String.make 32 'N') base in
      let remote=match SemanticDelta.decode_request encoded with
        | Ok (_,proof) -> proof | Error reason -> failwith reason in
      check (SemanticDelta.classify ~base:remote ~target=FormatExtension.Uninterpreted_regions)
        "peer proof gained metadata meaning";
      (match SemanticDelta.reconcile_xmp (module DngLayout) ~nonce:(String.make 32 'N')
         ~base ~left:base ~right:target basis with
       | Error "unsupported XMP reconciliation profile" -> incr checks
       | _ -> failwith "layout profile inherited merge authority");
      let corrupt=Bytes.of_string (SemanticDelta.encode update) in
      let at=88+String.length DngLayout.profile in
      Bytes.set corrupt at (Char.chr (Char.code (Bytes.get corrupt at) lxor 1));
      let bad=match SemanticDelta.decode (Bytes.to_string corrupt) with
        | Ok value -> value | Error reason -> failwith reason in
      with_stage before (fun output ->
        check (try SemanticDelta.apply_with_extension (module DngLayout) bad ~basis ~output;false
          with SemanticFile.Invalid "target SHA-256 mismatch" -> true)
          "bad target hash was accepted");
      let opaque_changed=Bytes.of_string after in Bytes.set opaque_changed 3080 '\090';
      with_input (Bytes.to_string opaque_changed) (fun changed ->
        let target=inspect changed in
        check (SemanticDelta.classify ~base ~target=FormatExtension.Other_bytes)
          "changed opaque atom ignored";
        check (match SemanticDelta.plan ~nonce:(String.make 32 'N') ~base ~target with
          | Error "bytes outside editable regions changed" -> true | _ -> false)
          "changed opaque atom admitted to region-only update")));
    Printf.printf "PASS layout-only %s %s\n%!" (if little then "little" else "big")
      (if big then "BigTIFF" else "classic")) [false;true]) [false;true];
  Printf.printf "PASS %d layout checks; exact private preservation, no semantic merge\n%!" !checks
