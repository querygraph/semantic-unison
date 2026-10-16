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
let integer little width value = String.init width (fun j ->
  let i = if little then j else width-1-j in
  Char.chr (Int64.to_int (Int64.logand 255L (Int64.shift_right_logical value (i*8)))))
let tiff ?(big=false) ?(little=true) ?(private_type=1L) ?(private_length=24L)
    ?(private_offset=512L) ?(version=true) ?(private_tag=true) ?(duplicate=false) () =
  let field = if big then 8 else 4 and entry = if big then 20 else 12 in
  let value_at = if big then 12 else 8 in
  let data = Bytes.make 1024 '\000' in
  let put at value = Bytes.blit_string value 0 data at (String.length value) in
  put 0 (if little then "II" else "MM");
  put 2 (integer little 2 (if big then 43L else 42L));
  if big then begin put 4 (integer little 2 8L);put 8 (integer little 8 32L) end
  else put 4 (integer little 4 32L);
  let count = (if version then 1 else 0) + (if private_tag then 1 else 0) +
              (if duplicate then 1 else 0) in
  let count_width = if big then 8 else 2 in
  put 32 (integer little count_width (Int64.of_int count));
  let n = ref 0 in
  let add tag typ length value =
    let at = 32+count_width+entry* !n in incr n;
    put at (integer little 2 tag);put (at+2) (integer little 2 typ);
    put (at+4) (integer little field length);put (at+value_at) value in
  if version then add 50706L 1L 4L "\001\007\001\000";
  let private_entry () = add 50740L private_type private_length (integer little field private_offset) in
  if private_tag then private_entry ();
  if duplicate then private_entry ();
  Bytes.to_string data
let locate value = locate_ifd0_private ~size:(Int64.of_int (String.length value))
  ~read:(fun at n -> String.sub value (Int64.to_int at) n)
let reject_tiff value = check (match locate value with Error _ -> true | Ok _ -> false)
  "malformed diagnostic TIFF admitted"
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
  List.iter (fun big -> List.iter (fun little ->
    let value = tiff ~big ~little () in
    let seen = ref 0 in
    let read at n =
      if Int64.add at (Int64.of_int n) > 512L then failwith "locator read private body";
      seen := !seen+n;String.sub value (Int64.to_int at) n in
    (match locate_ifd0_private ~size:1024L ~read with
    | Error why -> failwith why
    | Ok extent ->
        check (extent.block_offset=512L && extent.block_length=24L) "private extent";
        check (extent.is_big_tiff=big && extent.container_byte_order=
          (if little then Little else Big)) "container layout";
        check (extent.locator_bytes_read= !seen && !seen=(if big then 72 else 38))
          "exact locator read count");
    List.iter reject_tiff [tiff ~big ~little ~private_type:7L ();
      tiff ~big ~little ~private_length:0L ();
      tiff ~big ~little ~private_length:(Int64.of_int (if big then 8 else 4)) ();
      tiff ~big ~little ~private_length:(Int64.succ max_block_length) ();
      tiff ~big ~little ~private_offset:4L ();
      tiff ~big ~little ~private_offset:32L ();
      tiff ~big ~little ~private_offset:1010L ();
      tiff ~big ~little ~version:false ();
      tiff ~big ~little ~private_tag:false ();
      tiff ~big ~little ~duplicate:true ()];
    let mutated at replacement =
      let data=Bytes.of_string value in
      Bytes.blit_string replacement 0 data at (String.length replacement);Bytes.to_string data in
    reject_tiff (mutated 0 "ZZ");reject_tiff (mutated 2 (integer little 2 41L));
    reject_tiff (mutated (if big then 8 else 4) (integer little (if big then 8 else 4) 0L));
    reject_tiff (mutated 32 (integer little (if big then 8 else 2)
      (Int64.of_int (max_ifd0_entries+1))));
    if big then begin
      reject_tiff (mutated 4 (integer little 2 4L));
      reject_tiff (mutated 6 (integer little 2 1L));
      reject_tiff (mutated 8 (integer little 8 Int64.min_int))
    end
  ) [true;false]) [false;true];
  let small = tiff () in
  for n=0 to 37 do reject_tiff (String.sub small 0 n) done;
  check (match locate_ifd0_private ~size:Int64.max_int ~read:(fun _ _ -> "") with
    Error _ -> true | Ok _ -> false) "locator short read";
  check (try ignore (locate_ifd0_private ~size:1024L ~read:(fun _ _ -> failwith "trusted-reader"));false
    with Failure text -> text="trusted-reader") "trusted reader exception propagated";
  let little = true in
  let sparse_header = "II" ^ integer little 2 43L ^ integer little 2 8L ^ "\000\000" in
  let sparse_table = Bytes.make (max_ifd0_entries*20+8) '\000' in
  let table_put at s = Bytes.blit_string s 0 sparse_table at (String.length s) in
  table_put 0 (integer little 2 50706L ^ integer little 2 1L ^ integer little 8 4L ^ "\001\007\001\000");
  table_put 20 (integer little 2 50740L ^ integer little 2 1L ^ integer little 8 max_block_length ^
                integer little 8 1000000L);
  let total = ref 0 in
  let sparse_read at n = total := !total+n;
    match at,n with
    | 0L,8 -> sparse_header
    | 8L,8 -> integer little 8 32L
    | 32L,8 -> integer little 8 (Int64.of_int max_ifd0_entries)
    | 40L,n when n=Bytes.length sparse_table -> Bytes.to_string sparse_table
    | _ -> failwith "diagnostic locator unexpected or payload read" in
  (match locate_ifd0_private ~size:Int64.max_int ~read:sparse_read with
   | Error why -> failwith why
   | Ok extent -> check (extent.block_length=max_block_length &&
       extent.locator_bytes_read=max_locator_read_bytes && !total=max_locator_read_bytes)
       "maximum locator count has finite exact read budget");
  Printf.printf "PASS %d checks; diagnostic locator/framing only, no semantic eligibility\n" !checks
