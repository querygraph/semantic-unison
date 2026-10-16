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
