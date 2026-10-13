let format = "org.firstpair.dng-validation/1"
exception Undecidable of string
let unknown why = raise (Undecidable why)
let identify file =
  let open FormatRecognition in
  let size = SemanticFile.size file in
  if size < 4L then Not_matched else
  let prefix = SemanticFile.read file 0L 4 in
  let endian = match String.sub prefix 0 2 with
    | "II" -> Some true | "MM" -> Some false | _ -> None in
  match endian with
  | None -> Not_matched
  | Some little ->
    let number bytes at width =
      let value = ref 0L in
      for j = 0 to width-1 do
        let i = if little then width-1-j else j in
        value := Int64.logor (Int64.shift_left !value 8)
          (Int64.of_int (Char.code bytes.[at+i]))
      done;
      if !value < 0L then unknown "unsigned TIFF position/count exceeds signed int64";
      !value in
    let magic = number prefix 2 2 in
    if magic <> 42L && magic <> 43L then Not_matched else
    try
      let extent offset length =
        if offset < 0L || length < 0L || offset > size ||
           length > Int64.sub size offset then unknown "incomplete TIFF primary directory" in
      let read offset length =
        extent offset (Int64.of_int length);
        SemanticFile.read file offset length in
      let header_size,count_width,entry_size,next_width,primary =
        if magic = 42L then
          8,2,12,4,number (read 0L 8) 4 4
        else begin
          let header = read 0L 16 in
          if number header 4 2 <> 8L || number header 6 2 <> 0L then
            unknown "unsupported BigTIFF header layout";
          16,8,20,8,number header 8 8
        end in
      if primary = 0L then Not_matched else begin
        if primary < Int64.of_int header_size then
          unknown "TIFF primary directory overlaps header";
        let count = number (read primary count_width) 0 count_width in
        if count > 65535L then unknown "TIFF primary recognition entry limit";
        let count = Int64.to_int count in
        let length = count_width + count * entry_size + next_width in
        extent primary (Int64.of_int length);
        (* The SDK's shared DNGVersion belongs to IFD0, even when the raw image
           resides in a SubIFD. Its tag is a claim, not a validity decision:
           malformed/future type/count/version is left to the validator.
           Read at most 1,024 entries per chunk; never follow image/private
           pointers or copy a whole directory into an unbounded buffer. *)
        let rec scan index =
          if index = count then Not_matched else
          let entries = min 1024 (count-index) in
          let offset = Int64.add primary
            (Int64.of_int (count_width + index * entry_size)) in
          let chunk = read offset (entries * entry_size) in
          let rec find at =
            if at = entries then scan (index+entries)
            else if number chunk (at*entry_size) 2 = 50706L then Recognized
            else find (at+1) in
          find 0 in
        scan 0
      end
    with Undecidable why -> Indeterminate why
