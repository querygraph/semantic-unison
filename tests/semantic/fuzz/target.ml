(* Read-only, synthetic-input AFL target. Expected parser rejection is normal;
   unexpected exceptions and broken round trips use a non-signal failure code. *)
let limit = 262144
let require condition message = if not condition then failwith message
let envelope data =
  match SemanticDelta.decode ~max_payload:limit data with
  | Error _ -> ()
  | Ok decoded ->
      let canonical = SemanticDelta.encode decoded in
      match SemanticDelta.decode ~max_payload:limit canonical with
      | Error _ -> failwith "accepted SDE failed canonical decode"
      | Ok again -> require (SemanticDelta.encode again = canonical) "SDE round trip"
let request data =
  match SemanticDelta.decode_request data with
  | Error _ -> ()
  | Ok (nonce, proof) ->
      let canonical = SemanticDelta.encode_request ~nonce proof in
      match SemanticDelta.decode_request canonical with
      | Error _ -> failwith "accepted SDR failed canonical decode"
      | Ok (nonce, proof) ->
          require (SemanticDelta.encode_request ~nonce proof = canonical) "SDR round trip"
let inspect implementation fd =
  SemanticFile.with_fd fd (fun file ->
    match SemanticDelta.inspect ~max_payload:limit implementation file with
    | Error _ -> ()
    | Ok proof ->
        let description = SemanticDelta.describe proof in
        let end_at = ref 0L in
        List.iter (fun (region : FormatExtension.region) ->
          require (region.length > 0 && region.offset >= !end_at) "region ordering";
          end_at := Int64.add region.offset (Int64.of_int region.length);
          require (!end_at <= description.size) "region containment") description.regions;
        request (SemanticDelta.encode_request ~nonce:(String.make 32 'F') proof))
let run mode path =
  let fd = Unix.openfile path [Unix.O_RDONLY; Unix.O_NONBLOCK] 0 in
  Fun.protect ~finally:(fun () -> Unix.close fd) (fun () ->
    let stat = Unix.fstat fd in
    if stat.Unix.st_kind <> Unix.S_REG || stat.Unix.st_size > limit then ()
    else match mode with
    | "dng" -> inspect (module DngSemantic) fd
    | "dng-v1" -> inspect (module DngExtended) fd
    | "jpeg" -> inspect (module JpegSemantic) fd
    | "sde" | "sdr" | "xmp" | "oracle" ->
        let data = Bytes.create stat.Unix.st_size in
        let rec read at =
          if at < Bytes.length data then
            let count = Unix.read fd data at (Bytes.length data - at) in
            if count = 0 then failwith "short synthetic input" else read (at + count)
        in
        read 0;
        let data = Bytes.to_string data in
        (match mode with
        | "sde" -> envelope data
        | "sdr" -> request data
        | "xmp" -> ignore (XmpObservation.observe data); ignore (XmpObservation.scalar_view data)
        | "oracle" -> require (data <> "UNISON-FUZZ-NEGATIVE") "synthetic negative oracle"
        | _ -> assert false)
    | _ -> invalid_arg "unknown fuzz mode")
let () =
  try
    if Array.length Sys.argv <> 3 then invalid_arg "target MODE INPUT";
    run Sys.argv.(1) Sys.argv.(2)
  with
  | SemanticFile.Invalid _ -> ()
  | error ->
      prerr_endline (String.sub (Printexc.to_string error) 0
        (min 512 (String.length (Printexc.to_string error))));
      exit 86
