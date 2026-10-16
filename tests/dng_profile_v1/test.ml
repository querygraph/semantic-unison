(* Real public inspectors and semantic kernel, independently produced bytes. *)
external filesystem : string -> string = "fixture_dng_v1_filesystem"
let assertions = ref 0 and commands = ref 0 and maximum_checks = ref 0
let check condition message = incr assertions; if not condition then failwith message
let ok name = function Ok value -> value | Error reason -> failwith (name ^ ": " ^ reason)
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
let with_file path f =
  let descriptor = Unix.openfile path [Unix.O_RDONLY] 0 in
  let checks = ref 0 in
  let check_cancel () =
    incr checks;
    if !checks > 20000 then failwith "synthetic inspector/proof read budget exceeded" in
  let finish () =
    maximum_checks := max !maximum_checks !checks;
    Unix.close descriptor in
  match SemanticFile.with_fd ~check_cancel descriptor f with
  | result -> finish (); result
  | exception error -> finish (); raise error
let extension = (module DngExtended : FormatExtension.S)
let proof name path = with_file path (fun file -> ok name (SemanticDelta.inspect extension file))
let manifest name path expected_offset expected_length =
  with_file path (fun file ->
    let direct = ok name (DngSemantic.inspect_extended file) in
    let wrapped = ok name (DngExtended.inspect file) in
    let expected = [{FormatExtension.offset=Int64.of_string expected_offset;
                     length=int_of_string expected_length}] in
    check (direct.FormatExtension.regions = expected) (name ^ ": direct /1 extent differs from fixture placement");
    check (wrapped.FormatExtension.regions = expected) (name ^ ": wrapper extent differs");
    check (direct = wrapped) (name ^ ": wrapper changed inspector result");
    List.iter (fun (r:FormatExtension.region) ->
      let packet = SemanticFile.read file r.offset r.length in
      check (String.length packet = r.length) (name ^ ": exact located packet read length")) expected)
let inspect name path expected_offset expected_length old_accepts =
  let before = read path in
  manifest name path expected_offset expected_length;
  with_file path (fun file -> match DngSemantic.inspect file with
    | Ok old ->
        check (old_accepts = "true") (name ^ ": unchanged /0 admitted new container grammar");
        check (old.FormatExtension.regions = [{FormatExtension.offset=Int64.of_string expected_offset;
                    length=int_of_string expected_length}]) (name ^ ": /0 classic extent changed")
    | Error _ -> check (old_accepts = "false") (name ^ ": unchanged /0 classic eligibility regressed"));
  check (read path = before) (name ^ ": read-only inspection changed source")
let reject name path expected_reason =
  let before = read path in
  with_file path (fun file ->
    match DngExtended.inspect file with
    | Ok _ -> failwith (name ^ ": malformed or unsupported container was admitted")
    | Error reason ->
        check (reason <> "" && String.length reason <= 512) (name ^ ": unbounded rejection reason");
        if expected_reason <> "-" then
          check (reason = expected_reason) (name ^ ": wrong rejection: " ^ reason));
  check (read path = before) (name ^ ": rejection changed source")
let apply name base_path stage envelope explicit expected =
  let before = read base_path in
  write stage before;
  let output = Unix.openfile stage [Unix.O_RDWR] 0 in
  let result = match with_file base_path (fun basis ->
    if explicit then SemanticDelta.apply_report_with_extension extension envelope ~basis ~output
    else SemanticDelta.apply_report envelope ~basis ~output) with
    | value -> Unix.close output; value
    | exception error -> Unix.close output; raise error in
  check (read stage = expected) (name ^ ": materialization differs from independent bytes");
  check (read base_path = before) (name ^ ": materialization changed basis");
  check (result.SemanticDelta.comparison_window = 4096) (name ^ ": comparison window changed");
  result
let golden name base_path target_path request_path envelope_path stage =
  let base_bytes = read base_path and target_bytes = read target_path in
  let base = proof name base_path and target = proof name target_path in
  check (SemanticDelta.classify ~base ~target = FormatExtension.Editable_metadata) (name ^ ": metadata classification differs");
  check (SemanticDelta.classify ~base ~target:base = FormatExtension.Exact_bytes) (name ^ ": identical bytes classification differs");
  let nonce, claimed = ok name (SemanticDelta.decode_request (read request_path)) in
  check (SemanticDelta.proof_profile base = DngExtended.profile) (name ^ ": proof profile identity differs");
  check (SemanticDelta.encode_request ~nonce base = read request_path)
    (name ^ ": independent SDR whole/complement/region proof differs");
  check (SemanticDelta.encode_request ~nonce claimed = read request_path) (name ^ ": SDR canonical roundtrip differs");
  let planned = ok name (SemanticDelta.plan ~nonce ~base ~target) in
  check (SemanticDelta.encode planned = read envelope_path) (name ^ ": independent SDE bytes differ");
  check (SemanticDelta.encode (ok name (SemanticDelta.plan ~nonce ~base:claimed ~target)) = read envelope_path)
    (name ^ ": peer proof plan differs");
  let decoded = ok name (SemanticDelta.decode (read envelope_path)) in
  check (SemanticDelta.profile decoded = DngExtended.profile) (name ^ ": decoded envelope profile differs");
  check (SemanticDelta.encode decoded = read envelope_path) (name ^ ": SDE canonical roundtrip differs");
  check (SemanticDelta.binds_request ~nonce ~base decoded) (name ^ ": receiver request binding failed");
  check (not (SemanticDelta.binds_request ~nonce:(String.make 32 'x') ~base decoded)) (name ^ ": wrong nonce admitted");
  let report = apply name base_path stage decoded true target_bytes in
  check (report.SemanticDelta.logical_bytes_written > 0 && report.SemanticDelta.logical_bytes_written <= 8257 &&
         report.SemanticDelta.write_calls > 0) (name ^ ": changed metadata write counters invalid");
  ignore (apply name base_path stage decoded false target_bytes);
  let unchanged = ok name (SemanticDelta.plan ~nonce ~base ~target:base) in
  let report = apply name base_path stage unchanged true base_bytes in
  check (report.SemanticDelta.logical_bytes_written = 0 && report.SemanticDelta.write_calls = 0)
    (name ^ ": unchanged metadata made data writes");
  (* Parsed classic containers eligible for both versions still cannot cross
     negotiated profile identity, even though their complete byte hashes agree. *)
  with_file base_path (fun file -> match SemanticDelta.inspect (module DngSemantic) file with
    | Error _ -> ()
    | Ok old ->
        check ((SemanticDelta.describe old).SemanticDelta.digest = (SemanticDelta.describe base).SemanticDelta.digest)
          (name ^ ": classic full digest changed across profiles");
        check (not (SemanticDelta.binds_request ~nonce ~base:old decoded)) (name ^ ": /1 envelope binds /0 proof");
        (match SemanticDelta.plan ~nonce ~base:old ~target with
         | Error _ -> incr assertions
         | Ok _ -> failwith (name ^ ": /0-to-/1 plan admitted")))
let opaque name base_path target_path =
  let base_bytes = read base_path and target_bytes = read target_path in
  let base = proof name base_path and target = proof name target_path in
  check (SemanticDelta.classify ~base ~target = FormatExtension.Other_bytes)
    (name ^ ": opaque outside-XMP change classified editable");
  let a = SemanticDelta.describe base and b = SemanticDelta.describe target in
  check (a.SemanticDelta.regions = b.SemanticDelta.regions) (name ^ ": opaque recipe accidentally moved XMP");
  check (a.SemanticDelta.preserved_digest <> b.SemanticDelta.preserved_digest)
    (name ^ ": opaque change escaped complete complement proof");
  (match SemanticDelta.plan ~nonce:(String.make 32 'n') ~base ~target with
   | Error _ -> incr assertions
   | Ok _ -> failwith (name ^ ": opaque change was patch eligible"));
  check (read base_path = base_bytes && read target_path = target_bytes) (name ^ ": opaque proof changed source")
let sparse name path offset length expected_packet =
  let descriptor = Unix.openfile path [Unix.O_RDONLY] 0 in
  let before = Unix.LargeFile.fstat descriptor in
  Unix.close descriptor;
  check (before.Unix.LargeFile.st_size > 4294967295L) (name ^ ": sparse fixture is not beyond uint32");
  manifest name path offset length;
  with_file path (fun file -> check (SemanticFile.read file (Int64.of_string offset) (int_of_string length) = read expected_packet)
    (name ^ ": LargeFile exact packet read mismatch"));
  let descriptor = Unix.openfile path [Unix.O_RDONLY] 0 in
  let after = Unix.LargeFile.fstat descriptor in
  Unix.close descriptor;
  check (before.Unix.LargeFile.st_dev = after.Unix.LargeFile.st_dev &&
         before.Unix.LargeFile.st_ino = after.Unix.LargeFile.st_ino &&
         before.Unix.LargeFile.st_kind = after.Unix.LargeFile.st_kind &&
         before.Unix.LargeFile.st_size = after.Unix.LargeFile.st_size &&
         before.Unix.LargeFile.st_perm = after.Unix.LargeFile.st_perm &&
         before.Unix.LargeFile.st_nlink = after.Unix.LargeFile.st_nlink &&
         before.Unix.LargeFile.st_mtime = after.Unix.LargeFile.st_mtime &&
         before.Unix.LargeFile.st_ctime = after.Unix.LargeFile.st_ctime)
    (name ^ ": inspector changed sparse file identity/size/properties")
let () =
  if Array.length Sys.argv <> 3 then failwith "usage: test commands.tsv fixture-directory";
  let fs = filesystem Sys.argv.(2) in
  Printf.printf "Filesystem %s\n%!" fs;
  check (fs = "apfs") "synthetic fixture directory is not APFS";
  FormatExtension.register ~observer:DngSemantic.observer (module DngSemantic);
  FormatExtension.register ~observer:DngExtended.observer (module DngExtended);
  check (DngExtended.profile = "org.firstpair.dng-xmp/1" && DngSemantic.profile = "org.firstpair.dng-xmp/0")
    "negotiated profile names changed";
  check (DngExtended.observer == DngSemantic.observer) "extended observer is not shared";
  let manifest = open_in Sys.argv.(1) in
  (try while true do
    let line = input_line manifest in
    if line <> "" then begin
      incr commands;
      let fields = String.split_on_char '\t' line in
      Printf.printf "CASE %s\n%!" (List.nth fields 1);
      (match fields with
       | ["inspect";name;path;offset;length;old_accepts] -> inspect name path offset length old_accepts
       | ["reject";name;path;reason] -> reject name path reason
       | ["golden";name;base;target;request;envelope;stage] -> golden name base target request envelope stage
       | ["opaque";name;base;target] -> opaque name base target
       | ["sparse";name;path;offset;length;packet] -> sparse name path offset length packet
       | _ -> failwith ("unknown DNG fixture command: " ^ line));
      Printf.printf "PASS %s\n%!" (List.nth fields 1)
    end
  done with End_of_file -> close_in manifest);
  Printf.printf "All %d DNG /1 cases passed; %d assertions; maximum cancellation checks %d\n%!"
    !commands !assertions !maximum_checks
