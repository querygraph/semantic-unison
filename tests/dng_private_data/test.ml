open DngPrivateData
let checks = ref 0
let check value why = incr checks; if not value then failwith why
let be n = String.init 4 (fun i -> Char.chr
  (Int64.to_int (Int64.logand 255L (Int64.shift_right_logical n (8*(3-i))))))
let section ?(order="II") ?(original=0L) payload =
  let data = order ^ be original ^ payload in
  let value = "MakN" ^ be (Int64.of_int (String.length data)) ^ data in
  value ^ if String.length value mod 2 = 1 then "\000" else ""
let inspect value =
  DngPrivateData.inspect_adobe_makn ~length:(Int64.of_int (String.length value))
    ~read:(fun offset length -> String.sub value (Int64.to_int offset) length)
let reject value = match inspect value with Error _ -> check true "decline"
  | Ok _ -> failwith "unsupported or malformed frame admitted"
let expect value = match inspect value with Ok frame -> frame
  | Error why -> failwith why
let () =
  let value = "Adobe\000" ^ section ~original:0xffffffffL "xyz" in
  let frame = expect value in
  check (frame.header_bytes_read = 21) "framing-only byte count";
  (match frame.sections with
  | [s] -> check (s.payload_offset=20L && s.payload_length=3L &&
                 s.original_offset=0xffffffffL && s.byte_order=DngPrivateData.Little)
                 "independent field expectations"
  | _ -> failwith "section cardinality");
  let two = expect ("Adobe\000" ^ section "aa" ^ section ~order:"MM" "bbbb") in
  check (List.length two.sections=2) "two sections";
  check ((List.nth two.sections 1).byte_order=DngPrivateData.Big) "second byte order";
  List.iter reject ["";"Adobe\000";"Other\000" ^ section "x";
    "Adobe\000" ^ "MakN" ^ be 0xffffffffL;
    "Adobe\000" ^ "MakN" ^ be 6L ^ "II" ^ be 0L;
    "Adobe\000" ^ section ~order:"ZZ" "x";
    "Adobe\000" ^ "Nope" ^ be 7L ^ "II" ^ be 0L ^ "x\000";
    "Adobe\000" ^ section "a" ^ "junk"];
  let padded = "Adobe\000" ^ section "a" in
  reject (String.sub padded 0 (String.length padded-1));
  reject (String.sub padded 0 (String.length padded-1) ^ "x");
  let max = "Adobe\000" ^ String.concat "" (List.init 256 (fun _ -> section "x")) in
  let many = expect max in
  check (List.length many.sections=256 && many.header_bytes_read=3846) "bounded work256";
  reject (max ^ section "x");
  let no_read _ _ = failwith "invalid length performed read" in
  List.iter (fun length ->
    check (match DngPrivateData.inspect_adobe_makn ~length ~read:no_read with
      | Error _ -> true | Ok _ -> false) "length preflight")
    [-1L;0L;5L;Int64.max_int;Int64.succ DngPrivateData.max_block_length];
  let short _ _ = "" in
  check (match DngPrivateData.inspect_adobe_makn ~length:20L ~read:short with
      Error _ -> true | Ok _ -> false) "short read";
  let count = ref 0 in
  let length = DngPrivateData.max_block_length in
  let sparse_read at n = incr count;
    match at,n with
    | 0L,6 -> "Adobe\000"
    | 6L,8 -> "MakN" ^ be (Int64.sub length 14L)
    | 14L,6 -> "MM" ^ be 123L
    | _ -> failwith "recognizer read private payload" in
  (match DngPrivateData.inspect_adobe_makn ~length ~read:sparse_read with
   | Ok f -> check (f.header_bytes_read=20 && !count=3) "64MiB virtual block bounded header reads"
   | Error why -> failwith why);
  (* Every possible incomplete prefix of a tiny valid frame must decline. *)
  for n=0 to String.length value-1 do reject (String.sub value 0 n) done;
  Printf.printf "PASS %d checks; framing evidence only, no semantic eligibility\n" !checks
