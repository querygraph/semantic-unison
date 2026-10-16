(* Developer diagnostic only. Borrow one caller-owned read-only regular file
   through stdin; never open a pathname, mutate content or decide eligibility.
   The admitting owner must fence the exact native file epoch around this
   process. Unix.stats timestamps here are not a native nanosecond fence. *)
let quote text =
  let buffer = Buffer.create (String.length text+2) in
  Buffer.add_char buffer '"';
  String.iter (function
    | '"' -> Buffer.add_string buffer "\\\""
    | '\\' -> Buffer.add_string buffer "\\\\"
    | c when Char.code c < 32 -> Buffer.add_string buffer (Printf.sprintf "\\u%04x" (Char.code c))
    | c -> Buffer.add_char buffer c) text;
  Buffer.add_char buffer '"';Buffer.contents buffer
let object_ fields = "{" ^ String.concat "," (List.map (fun (key,value) -> quote key ^ ":" ^ value) fields) ^ "}"
let array values = "[" ^ String.concat "," values ^ "]"
let order = function DngPrivateData.Little -> "little" | DngPrivateData.Big -> "big"
let limit = DngPrivateData.max_locator_read_bytes + 3846
let max_requests = 5 + 3 * DngPrivateData.max_sections
let requested = ref 0 and delivered = ref 0 and calls = ref 0
let ranges = ref []
let read_ranges () = array (List.map (fun (offset,length) -> object_
  ["offset",Int64.to_string offset;"length",string_of_int length]) (List.rev !ranges))
let flags = ["diagnostic_only","true"; "semantic_eligibility","false";
             "full_file_sha256_computed","false"; "sdk_validation","false";
             "native_nanosecond_epoch_fence_performed_by_child","false"]
let main () =
  if Array.length Sys.argv <> 1 then invalid_arg "no pathname or inspection arguments accepted";
  let initial = Unix.LargeFile.fstat Unix.stdin in
  if initial.Unix.LargeFile.st_kind <> Unix.S_REG || initial.Unix.LargeFile.st_nlink <> 1 ||
     initial.Unix.LargeFile.st_perm <> 0o400 || initial.Unix.LargeFile.st_size < 0L then
    invalid_arg "caller must pass a private singly-linked mode0400 regular descriptor as stdin";
  let size = initial.Unix.LargeFile.st_size in
  let get offset length =
    if offset < 0L || length < 0 || offset > size ||
       Int64.of_int length > Int64.sub size offset || length > limit - !requested ||
       !calls >= max_requests then
      invalid_arg "diagnostic read range or total budget";
    requested := !requested + length;
    incr calls;
    ranges := (offset,length) :: !ranges;
    let position = Unix.LargeFile.lseek Unix.stdin offset Unix.SEEK_SET in
    if position <> offset then failwith "diagnostic seek mismatch";
    let bytes = Bytes.create length in
    let rec loop at = if at < length then
      match Unix.read Unix.stdin bytes at (length-at) with
      | 0 -> failwith "diagnostic short read"
      | count -> delivered := !delivered+count;loop (at+count)
      | exception Unix.Unix_error (Unix.EINTR,_,_) -> loop at in
    loop 0;Bytes.to_string bytes in
  let fields = match DngPrivateData.locate_ifd0_private ~read:get ~size with
    | Error reason -> ["locator_completed","false"; "framing_recognized","false";"reason",quote reason]
    | Ok extent ->
        let read offset length = get (Int64.add extent.DngPrivateData.block_offset offset) length in
        let framing = DngPrivateData.inspect_adobe_makn ~read ~length:extent.DngPrivateData.block_length in
        let location = ["locator_completed","true";
          "block_offset",Int64.to_string extent.DngPrivateData.block_offset;
          "block_length",Int64.to_string extent.DngPrivateData.block_length;
          "container_byte_order",quote (order extent.DngPrivateData.container_byte_order);
          "big_tiff",string_of_bool extent.DngPrivateData.is_big_tiff] in
        location @ (match framing with
        | Error reason -> ["framing_recognized","false";"reason",quote reason]
        | Ok value -> ["framing_recognized","true";"sections",array (List.map
            (fun (section : DngPrivateData.maker_section) -> object_
              ["payload_offset_in_private_block",Int64.to_string section.DngPrivateData.payload_offset;
               "payload_length",Int64.to_string section.DngPrivateData.payload_length;
               "original_offset",Int64.to_string section.DngPrivateData.original_offset;
               "byte_order",quote (order section.DngPrivateData.byte_order)]) value.DngPrivateData.sections)]) in
  let stamp (value : Unix.LargeFile.stats) =
    value.Unix.LargeFile.st_dev,value.Unix.LargeFile.st_ino,value.Unix.LargeFile.st_size,value.Unix.LargeFile.st_mtime,value.Unix.LargeFile.st_ctime,
    value.Unix.LargeFile.st_kind,value.Unix.LargeFile.st_perm,value.Unix.LargeFile.st_nlink,value.Unix.LargeFile.st_uid,value.Unix.LargeFile.st_gid in
  let final = Unix.LargeFile.fstat Unix.stdin in
  if stamp initial <> stamp final then failwith "borrowed descriptor metadata changed";
  print_endline (object_ (["schema",quote "unison-private-framing-diagnostic/1";
    "logical_read_bytes",string_of_int !delivered;"requested_read_bytes",string_of_int !requested;
    "read_requests",string_of_int !calls;"read_ranges",read_ranges ();
    "read_limit_bytes",string_of_int limit] @ flags @ fields))
let () = try main () with error ->
  prerr_endline (object_ (["schema",quote "unison-private-framing-diagnostic-error/1";
    "error",quote (Printexc.to_string error);"logical_read_bytes",string_of_int !delivered;
    "requested_read_bytes",string_of_int !requested;"read_ranges",read_ranges ()] @ flags));exit 2
