(* Original bounded framing recognizer; no SDK/native code is called.
   The block's semantic self-containment is NOT established by these headers. *)
type byte_order = Little | Big
type maker_section = {
  payload_offset : int64;
  payload_length : int64;
  original_offset : int64;
  byte_order : byte_order;
}
type framing = { sections : maker_section list; header_bytes_read : int }
let max_block_length = 67108864L
let max_sections = 256
exception Decline of string
let decline reason = raise (Decline reason)
let inspect_adobe_makn ~read ~length =
 try
  if length < 6L || length > max_block_length then decline "private block size limit";
  let bytes = ref 0 in
  let get offset count =
    if offset < 0L || offset > length || count < 0 ||
       Int64.of_int count > Int64.sub length offset then decline "private framing outside block";
    let value = read offset count in
    if String.length value <> count then decline "private framing short read";
    bytes := !bytes + count;
    value in
  let uint32_be value at =
    let result = ref 0L in
    for i = 0 to 3 do
      result := Int64.logor (Int64.shift_left !result 8)
        (Int64.of_int (Char.code value.[at+i]))
    done;
    !result in
  if get 0L 6 <> "Adobe\000" then decline "unrecognized private creator";
  let position = ref 6L and sections = ref [] and count = ref 0 in
  while !position < length do
    if !count >= max_sections then decline "private section count limit";
    let header = get !position 8 in
    if String.sub header 0 4 <> "MakN" then decline "unrecognized private section";
    let section_length = uint32_be header 4 in
    let start = Int64.add !position 8L in
    if section_length <= 6L || section_length > Int64.sub length start then
      decline "private section length outside block";
    let maker_header = get start 6 in
    let byte_order = match String.sub maker_header 0 2 with
      | "II" -> Little | "MM" -> Big | _ -> decline "private maker byte order" in
    let original_offset = uint32_be maker_header 2 in
    sections := {payload_offset=Int64.add start 6L;
                 payload_length=Int64.sub section_length 6L;
                 original_offset;byte_order} :: !sections;
    incr count;
    position := Int64.add start section_length;
    if Int64.logand !position 1L <> 0L then begin
      if get !position 1 <> "\000" then decline "nonzero private alignment padding";
      position := Int64.succ !position
    end
  done;
  if !count = 0 then decline "empty private section list";
  Ok {sections=List.rev !sections;header_bytes_read= !bytes}
 with Decline reason -> Error reason

type private_extent = {
  block_offset : int64;
  block_length : int64;
  locator_bytes_read : int;
  container_byte_order : byte_order;
  is_big_tiff : bool;
}
let max_ifd0_entries = 16384
let max_locator_read_bytes = 16 + 8 + max_ifd0_entries * 20 + 8
let locate_ifd0_private ~read ~size =
 try
  let bytes = ref 0 in
  let range offset length =
    if offset < 0L || length < 0L || offset > size ||
       length > Int64.sub size offset then decline "diagnostic extent outside file" in
  let get offset count =
    range offset (Int64.of_int count);
    if count < 0 || count > max_locator_read_bytes - !bytes then
      decline "diagnostic read budget";
    let value = read offset count in
    if String.length value <> count then decline "diagnostic short read";
    bytes := !bytes + count;
    value in
  let header = get 0L 8 in
  let container_byte_order = match String.sub header 0 2 with
    | "II" -> Little | "MM" -> Big | _ -> decline "diagnostic not TIFF" in
  let number value at width =
    let result = ref 0L in
    for j = 0 to width-1 do
      let i = if container_byte_order = Little then width-1-j else j in
      result := Int64.logor (Int64.shift_left !result 8)
        (Int64.of_int (Char.code value.[at+i]))
    done;
    if !result < 0L then decline "diagnostic unsigned integer outside signed domain";
    !result in
  let is_big_tiff, header_size, count_width, entry_width, field_width, value_at, primary =
    match number header 2 2 with
    | 42L -> false,8,2,12,4,8,number header 4 4
    | 43L ->
        if number header 4 2 <> 8L || number header 6 2 <> 0L then
          decline "diagnostic BigTIFF header";
        let tail = get 8L 8 in
        true,16,8,20,8,12,number tail 0 8
    | _ -> decline "diagnostic unsupported TIFF version" in
  if primary < Int64.of_int header_size then decline "diagnostic IFD0 overlaps header";
  let count = number (get primary count_width) 0 count_width in
  if count > Int64.of_int max_ifd0_entries then decline "diagnostic IFD0 entry limit";
  let count = Int64.to_int count in
  let table_length = entry_width * count + field_width in
  range primary (Int64.of_int (count_width + table_length));
  let table_end = Int64.add primary (Int64.of_int (count_width + table_length)) in
  let table = get (Int64.add primary (Int64.of_int count_width)) table_length in
  let version = ref false and private_block = ref None in
  for index = 0 to count-1 do
    let at = index * entry_width in
    let tag = number table at 2 in
    if tag = 50706L then begin
      if !version then decline "diagnostic duplicate DNGVersion";
      if number table (at+2) 2 <> 1L || number table (at+4) field_width <> 4L ||
         table.[at+value_at] <> '\001' then decline "diagnostic DNGVersion shape";
      version := true
    end else if tag = 50740L then begin
      if !private_block <> None then decline "diagnostic duplicate DNGPrivateData";
      if number table (at+2) 2 <> 1L then decline "diagnostic private type";
      let length = number table (at+4) field_width in
      if length <= Int64.of_int field_width || length > max_block_length then
        decline "diagnostic private size or inline value";
      let offset = number table (at+value_at) field_width in
      range offset length;
      let ending = Int64.add offset length in
      if offset < Int64.of_int header_size ||
         (offset < table_end && ending > primary) then
        decline "diagnostic private overlaps metadata structure";
      private_block := Some (offset,length)
    end
  done;
  if not !version then decline "diagnostic DNGVersion missing";
  match !private_block with
  | None -> decline "diagnostic DNGPrivateData missing"
  | Some (block_offset,block_length) -> Ok {block_offset;block_length;
      locator_bytes_read= !bytes;container_byte_order;is_big_tiff}
 with Decline reason -> Error reason
