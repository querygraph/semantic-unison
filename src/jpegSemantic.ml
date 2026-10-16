(* Exact standard APP1 XMP locator, not a JPEG decoder/validator. Every byte
   outside the packet is protected by the core complement/full-file hashes. *)
let profile = "org.firstpair.jpeg-xmp/0"
let signature = "http://ns.adobe.com/xap/1.0/\000"
let extended_signature = "http://ns.adobe.com/xmp/extension/\000"
exception Unsupported of string
let reject reason = raise (Unsupported reason)
let inspect file =
  try
    let size = SemanticFile.size file in
    let read at count =
      if at < 0L || at > size || Int64.of_int count > Int64.sub size at then
        reject "truncated JPEG header";
      SemanticFile.read file at count in
    if read 0L 2 <> "\255\216" then reject "not JPEG SOI";
    let position = ref 2L and markers = ref 0 and packet = ref None
    and frame = ref false and finished = ref false and total_fills = ref 0 in
    let byte at = Char.code (read at 1).[0] in
    let be16 s = Char.code s.[0] * 256 + Char.code s.[1] in
    let starts at count prefix = count >= String.length prefix &&
      read at (String.length prefix) = prefix in
    while not !finished do
      incr markers;
      if !markers > 4096 || !position > 16777216L then
        reject "JPEG header limit";
      if byte !position <> 255 then reject "invalid JPEG marker prefix";
      let fills = ref 0 in
      while byte !position = 255 do
        incr fills; incr total_fills;
        if !total_fills > 8192 then reject "JPEG cumulative fill limit";
        if !fills > 4096 then reject "JPEG fill limit";
        position := Int64.succ !position
      done;
      let marker = byte !position in
      position := Int64.succ !position;
      (* All accepted pre-scan markers have lengths. Restart/TEM/SOI/EOI,
         reserved JPEG extension markers and scan-data stuffing are excluded. *)
      let is_frame = List.mem marker
        [0xc0;0xc1;0xc2;0xc3;0xc5;0xc6;0xc7;0xc9;0xca;0xcb;0xcd;0xce;0xcf] in
      if not (is_frame || marker=0xc4 || marker=0xcc || marker=0xda ||
        marker=0xdb || marker=0xdd || marker=0xfe ||
        (marker>=0xe0 && marker<=0xef)) then reject "unsupported JPEG marker";
      let length = be16 (read !position 2) in
      if length < 2 then reject "invalid JPEG segment length";
      let payload = Int64.add !position 2L and count = length-2 in
      let ending = Int64.add !position (Int64.of_int length) in
      if ending > size || ending > 16777216L then reject "JPEG segment/header bounds";
      if is_frame then begin
        if !frame then reject "multiple JPEG frames";
        if count < 6 then reject "short JPEG frame";
        let h = read payload 6 in
        let components = Char.code h.[5] in
        if components=0 || count <> 6+3*components ||
          be16 (String.sub h 1 2)=0 || be16 (String.sub h 3 2)=0 then
          reject "unsupported JPEG frame geometry";
        frame := true
      end;
      if marker=0xe1 then begin
        if starts payload count extended_signature then reject "extended JPEG XMP unsupported";
        if starts payload count signature then begin
          if !packet <> None then reject "multiple standard JPEG XMP packets";
          let length = count-String.length signature in
          if length=0 then reject "empty JPEG XMP packet";
          packet := Some {FormatExtension.offset=Int64.add payload
            (Int64.of_int (String.length signature));length}
        end
      end;
      if marker=0xda then begin
        if not !frame then reject "JPEG scan without frame";
        if count < 4 then reject "short JPEG scan";
        let components = byte payload in
        if components=0 || components>4 || count <> 4+2*components then
          reject "unsupported JPEG scan header";
        if ending >= size then reject "missing JPEG scan bytes";
        finished := true
      end;
      position := ending
    done;
    match !packet with
    | Some region -> Ok {FormatExtension.regions=[region]}
    | None -> Error "no standard JPEG XMP packet"
  with Unsupported reason -> Error reason
