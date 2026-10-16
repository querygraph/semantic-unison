(* Production kernel exercised against independently generated fixed bytes. *)
let require condition message = if not condition then failwith message
let ok = function Ok value -> value | Error reason -> failwith reason
let read path =
  let channel = open_in_bin path in
  match really_input_string channel (in_channel_length channel) with
  | value -> close_in channel; value
  | exception error -> close_in_noerr channel; raise error
let write path data =
  let channel = open_out_bin path in
  match output_string channel data with
  | () -> close_out channel
  | exception error -> close_out_noerr channel; raise error
let with_file path operation =
  let descriptor = Unix.openfile path [Unix.O_RDONLY] 0 in
  match SemanticFile.with_fd descriptor operation with
  | value -> Unix.close descriptor; value
  | exception error -> Unix.close descriptor; raise error
let regions text =
  List.map (fun text -> match String.split_on_char ':' text with
    | [offset;length] -> {FormatExtension.offset=Int64.of_string offset;length=int_of_string length}
    | _ -> failwith "invalid region fixture") (String.split_on_char ',' text)
let extension kind name region_text =
  if kind = "dng" then (module DngSemantic : FormatExtension.S)
  else
    let declared_regions = regions region_text in
    let module Fixture = struct
      let profile = name
      let inspect _ = Ok {FormatExtension.regions=declared_regions}
    end in (module Fixture : FormatExtension.S)
let inspect extension path = with_file path (fun file -> ok (SemanticDelta.inspect extension file))
let assertions = ref 0
let check condition message = incr assertions; require condition message
let accept expected = expected = "accept"

let decode_sde name path limit expected outer_error =
  let data = read path in
  match SemanticDelta.decode ~max_payload:(int_of_string limit) data with
  | Ok value ->
      check (accept expected) (name ^ ": invalid SDE accepted");
      check (SemanticDelta.encode value = data) (name ^ ": SDE is not canonical")
  | Error reason ->
      check (not (accept expected)) (name ^ ": valid SDE rejected: " ^ reason);
      if outer_error <> "-" then check (reason = outer_error) (name ^ ": outer SDE cap not checked first")
let decode_sdr name path expected outer_error =
  let data = read path in
  match SemanticDelta.decode_request data with
  | Ok (nonce, value) ->
      check (accept expected) (name ^ ": invalid SDR accepted");
      check (SemanticDelta.encode_request ~nonce value = data) (name ^ ": SDR is not canonical")
  | Error reason ->
      check (not (accept expected)) (name ^ ": valid SDR rejected: " ^ reason);
      if outer_error <> "-" then check (reason = outer_error) (name ^ ": outer SDR cap not checked first")

let golden name base_path target_path request_path envelope_path profile region_text kind =
  (* A profile must be representable by the local registry. Exercise every
     byte position, including embedded NULs rather than just empty names. *)
  let reject_nuls wire start decode =
    for index = 0 to String.length profile - 1 do
      let malformed = Bytes.of_string wire in
      Bytes.set malformed (start + index) '\000';
      check (match decode (Bytes.to_string malformed) with Error _ -> true | Ok _ -> false)
        (name ^ ": unregistrable NUL profile accepted at " ^ string_of_int index)
    done in
  reject_nuls (read request_path) 48 SemanticDelta.decode_request;
  reject_nuls (read envelope_path) 16 SemanticDelta.decode;
  let selected = extension kind profile region_text in
  let base_bytes = read base_path and target_bytes = read target_path in
  let base = inspect selected base_path and target = inspect selected target_path in
  let nonce, claimed_base = ok (SemanticDelta.decode_request (read request_path)) in
  check (SemanticDelta.encode_request ~nonce base = read request_path)
    (name ^ ": independently computed whole/region/preserved proof mismatch");
  let planned = ok (SemanticDelta.plan ~nonce ~base ~target) in
  check (SemanticDelta.encode planned = read envelope_path) (name ^ ": independent exact SDE mismatch");
  let received = ok (SemanticDelta.decode (read envelope_path)) in
  check (SemanticDelta.binds_request ~nonce ~base received) (name ^ ": local request binding failed");
  check (SemanticDelta.binds_request ~nonce ~base:claimed_base received) (name ^ ": decoded request binding failed");
  check (SemanticDelta.encode (ok (SemanticDelta.plan ~nonce ~base:claimed_base ~target)) = read envelope_path)
    (name ^ ": remote proof planning mismatch");
  let staging = base_path ^ ".staging" in
  write staging base_bytes;
  let output = Unix.openfile staging [Unix.O_RDWR] 0 in
  (match with_file base_path (fun basis -> SemanticDelta.apply_with_extension selected received ~basis ~output) with
   | () -> Unix.close output | exception error -> Unix.close output; raise error);
  check (read staging = target_bytes) (name ^ ": materialized bytes differ from independent target");
  check (read base_path = base_bytes) (name ^ ": source bytes changed");
  write staging base_bytes;
  let output = Unix.openfile staging [Unix.O_RDWR] 0 in
  (match with_file base_path (fun basis -> SemanticDelta.apply received ~basis ~output) with
   | () -> Unix.close output | exception error -> Unix.close output; raise error);
  check (read staging = target_bytes) (name ^ ": registry-selected materialization differs");
  check (read base_path = base_bytes) (name ^ ": registry-selected application changed source")

let binding name request_path envelope_path expected =
  let nonce, base = ok (SemanticDelta.decode_request (read request_path)) in
  let envelope = ok (SemanticDelta.decode (read envelope_path)) in
  check (SemanticDelta.binds_request ~nonce ~base envelope = (expected = "true"))
    (name ^ ": request proof binding mismatch")

let truncations name request_path envelope_path =
  let request = read request_path and envelope = read envelope_path in
  for length = 0 to String.length request - 1 do
    check (match SemanticDelta.decode_request (String.sub request 0 length) with Error _ -> true | _ -> false)
      (name ^ ": truncated SDR accepted at " ^ string_of_int length)
  done;
  for length = 0 to String.length envelope - 1 do
    check (match SemanticDelta.decode (String.sub envelope 0 length) with Error _ -> true | _ -> false)
      (name ^ ": truncated SDE accepted at " ^ string_of_int length)
  done

let rejected_plan name base_path target_path profile region_text kind nonce_length =
  let selected = extension kind profile region_text in
  let base = inspect selected base_path and target = inspect selected target_path in
  let nonce = String.make (int_of_string nonce_length) 'n' in
  check (match SemanticDelta.plan ~nonce ~base ~target with Error _ -> true | _ -> false)
    (name ^ ": ineligible plan accepted");
  if String.length nonce <> 32 then
    check (try ignore (SemanticDelta.encode_request ~nonce base); false with Invalid_argument _ -> true)
      (name ^ ": wrong request nonce length accepted")

let rejected_application name base_path envelope_path profile region_text kind when_rejected =
  let selected = extension kind profile region_text in
  let base_bytes = read base_path in
  let staging = base_path ^ ".rejected-staging" in
  write staging base_bytes;
  let output = Unix.openfile staging [Unix.O_RDWR] 0 in
  let envelope = ok (SemanticDelta.decode (read envelope_path)) in
  let rejected =
    try with_file base_path (fun basis ->
      if when_rejected = "unregistered" then SemanticDelta.apply envelope ~basis ~output
      else SemanticDelta.apply_with_extension selected envelope ~basis ~output); false
    with SemanticFile.Invalid _ -> true in
  Unix.close output;
  check rejected (name ^ ": unauthorized application accepted");
  check (read base_path = base_bytes) (name ^ ": application changed source");
  if when_rejected <> "after_writes" then
    check (read staging = base_bytes) (name ^ ": unauthorized application wrote before rejection")

let () =
  FormatExtension.register ~max_payload:1048576 (module DngSemantic);
  let module Multi = struct
    let profile = "org.firstpair.conformance-multi/0"
    let inspect _ = Ok {FormatExtension.regions=regions "0:3,3:2,11:4,27:5"}
  end in
  FormatExtension.register (module Multi);
  let manifest = open_in Sys.argv.(1) in
  let commands = ref 0 in
  (try while true do
    let line = input_line manifest in
    if line <> "" then begin
      incr commands;
      let fields = String.split_on_char '\t' line in
      (match fields with
       | ["sde";name;path;limit;expected;error] -> decode_sde name path limit expected error
       | ["sdr";name;path;expected;error] -> decode_sdr name path expected error
       | ["golden";name;base;target;request;envelope;profile;declared;kind] ->
           golden name base target request envelope profile declared kind
       | ["bind";name;request;envelope;expected] -> binding name request envelope expected
       | ["truncate";name;request;envelope] -> truncations name request envelope
       | ["reject_plan";name;base;target;profile;declared;kind;nonce_length] ->
           rejected_plan name base target profile declared kind nonce_length
       | ["reject_apply";name;base;envelope;profile;declared;kind;when_rejected] ->
           rejected_application name base envelope profile declared kind when_rejected
       | _ -> failwith ("unknown conformance command: " ^ line));
      Printf.printf "PASS %d %s\n%!" !commands (List.nth fields 1)
    end
  done with End_of_file -> close_in manifest);
  Printf.printf "CONFORMANCE commands=%d assertions=%d\n%!" !commands !assertions
