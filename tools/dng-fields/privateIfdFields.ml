type byte_order = Little | Big
type field = { tag : int; name : string; max_bytes : int }
type schema = { component_id : string; decoder_id : string;
                implementation_sha256 : string; byte_order : byte_order;
                directory_at : int64; value_base : int64; max_span : int64;
                max_entries : int; fields : field list }
exception Unsupported of string
let reject reason = raise(Unsupported reason)
let bounded limit text = text<>"" && String.length text<=limit && not(String.contains text '\000')
let freeze schema =
  let valid_name name = bounded 32 name && String.for_all (function
    | 'a'..'z' | '0'..'9' | '-' | '_' -> true | _ -> false) name in
  let rec fields count tags names = function
    | [] -> count>0
    | field::rest -> count<32 && field.tag>=0 && field.tag<=65535
      && field.max_bytes>=1 && field.max_bytes<=4096 && valid_name field.name
      && not(List.mem field.tag tags) && not(List.mem field.name names)
      && fields (count+1) (field.tag::tags) (field.name::names) rest in
  if not(bounded 200 schema.component_id) || String.length schema.component_id<4
    || String.sub schema.component_id 0 4<>"dng/" || not(bounded 128 schema.decoder_id)
    || String.length schema.implementation_sha256<>32
    || schema.max_entries<1 || schema.max_entries>256 || schema.directory_at<0L
    || schema.max_span<6L || schema.max_span>16777216L
    || schema.directory_at>Int64.sub schema.max_span 6L
    || not(fields 0 [] [] schema.fields) then Error "invalid bounded private-field schema"
  else
  let selected=List.sort(fun a b -> compare a.tag b.tag) schema.fields in
  (* Length-prefixed decimal byte lengths, then exact bytes. Signed offsets use
     canonical decimal. Policy/config changes never reuse the old decoder root. *)
  let provenance=Buffer.create 256 in
  let frame text = Buffer.add_string provenance (string_of_int(String.length text));
    Buffer.add_char provenance ':';Buffer.add_string provenance text in
  List.iter frame ["unison-private-ifd-ascii/0";schema.implementation_sha256;
    schema.component_id;schema.decoder_id;(match schema.byte_order with Little -> "II" | Big -> "MM");
    Int64.to_string schema.directory_at;Int64.to_string schema.value_base;
    Int64.to_string schema.max_span;string_of_int schema.max_entries;string_of_int(List.length selected)];
  List.iter(fun field -> List.iter frame [string_of_int field.tag;field.name;string_of_int field.max_bytes]) selected;
  let implementation_sha256=SemanticHash.string (Buffer.contents provenance) in
  let decode reader = try
    let bound offset bytes =
      if offset<0L || bytes<0L || offset>schema.max_span || bytes>Int64.sub schema.max_span offset
      then reject "private field outside declared span" in
    let read offset count = bound offset (Int64.of_int count);ComponentHash.read reader offset count in
    let number bytes at width =
      let result=ref 0L in
      for step=0 to width-1 do
        let index=match schema.byte_order with Little -> width-1-step | Big -> step in
        result:=Int64.logor (Int64.shift_left !result 8)
          (Int64.of_int(Char.code bytes.[at+index]))
      done;!result in
    let count=Int64.to_int(number (read schema.directory_at 2) 0 2) in
    if count>schema.max_entries then reject "private directory entry limit";
    let table=read schema.directory_at (2+12*count+4) in
    let seen=Hashtbl.create count and found=Hashtbl.create(List.length selected) in
    for index=0 to count-1 do
      let at=2+12*index in
      let tag=Int64.to_int(number table at 2) in
      if Hashtbl.mem seen tag then reject "duplicate private directory tag";
      Hashtbl.add seen tag ();
      match List.find_opt(fun field -> field.tag=tag) selected with
      | None -> ()
      | Some field ->
        let typ=number table (at+2) 2 and length=number table (at+4) 4 in
        if typ<>2L || length<1L || length>Int64.of_int field.max_bytes then
          reject "selected private ASCII shape unsupported";
        let offset=if length<=4L then Int64.add schema.directory_at (Int64.of_int(at+8))
          else begin
            let relative=number table (at+8) 4 in
            if schema.value_base>Int64.sub Int64.max_int relative then reject "private field offset overflow";
            Int64.add schema.value_base relative
          end in
        bound offset length;
        Hashtbl.add found tag (field,offset,length)
    done;
    if Hashtbl.length found<>List.length selected then reject "selected private field absent";
    let ranges=List.map(fun field -> Hashtbl.find found field.tag) selected in
    let ranges=List.sort(fun (_,a,_) (_,b,_) -> Int64.compare a b) ranges in
    let stop=ref 0L in
    List.iter(fun (_,offset,length) ->
      if offset< !stop then reject "selected private fields alias";
      stop:=Int64.add offset length) ranges;
    let children=List.map(fun (field,offset,length) ->
      let bytes=read offset (Int64.to_int length) in
      if bytes.[String.length bytes-1]<>'\000' then reject "private ASCII lacks terminator";
      String.iteri(fun index byte -> if index<String.length bytes-1 &&
        (Char.code byte<32 || Char.code byte>126) then reject "private ASCII encoding unsupported") bytes;
      {ComponentHash.id=schema.component_id^"/"^field.name;schema="private-ascii-bytes/0@"^SemanticHash.hex implementation_sha256;
       role=ComponentHash.Private_metadata;offset;length;children=[]}) ranges in
    Ok children
  with Unsupported reason -> Error reason in
  Ok {ComponentHash.id=schema.decoder_id;implementation_sha256;decode}
