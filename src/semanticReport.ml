type supported = {
  description : SemanticDelta.description;
  samples : SemanticDelta.sample list;
}
type observation = Supported of supported | Unsupported of string * string |
                   Unavailable of string * string
type classification = Exact_bytes | Metadata_only | Other_bytes | Unknown
let max_size = 32768
let reason value = if String.length value <= 1024 then value else String.sub value 0 1024
let from_proof proof = Supported {description=SemanticDelta.describe proof;
  samples=SemanticDelta.samples proof}
let profile = function Supported value -> value.description.SemanticDelta.profile
  | Unsupported (profile,_) | Unavailable (profile,_) -> profile
let same_layout left right =
  left.SemanticDelta.profile = right.SemanticDelta.profile && left.size=right.size &&
  left.regions=right.regions
let classification left right = match left,right with
  | Supported left,Supported right ->
      if left.description.size=right.description.size && left.description.digest=right.description.digest
      then Exact_bytes
      else if same_layout left.description right.description &&
              left.description.preserved_digest=right.description.preserved_digest then
        if List.map (fun (s:SemanticDelta.sample) -> s.digest) left.samples <>
           List.map (fun (s:SemanticDelta.sample) -> s.digest) right.samples then Metadata_only
        else Unknown
      else Other_bytes
  | _ -> Unknown
exception Bad of string
let validate ~max_payload observation =
  let profile = profile observation in
  if profile="" || String.length profile>128 || String.contains profile '\000' then raise (Bad "invalid profile");
  match observation with
  | Unsupported (_,why) | Unavailable (_,why) ->
      if String.length why>1024 then raise (Bad "reason limit")
  | Supported value ->
      let d = value.description in
      if d.size<0L || String.length d.digest<>32 || String.length d.preserved_digest<>32 ||
         value.samples=[] || List.length value.samples>64 ||
         List.map (fun (sample:SemanticDelta.sample) -> sample.region) value.samples<>d.regions
      then raise (Bad "invalid observation description");
      let rec check stop payload prefix = function
        | [] -> ()
        | (sample:SemanticDelta.sample)::rest ->
          let r = sample.region and length = String.length sample.prefix in
          if r.offset<stop || r.offset>d.size || r.length<=0 || r.length>FormatExtension.max_region ||
             Int64.of_int r.length>Int64.sub d.size r.offset || payload>max_payload-r.length ||
             String.length sample.digest<>32 || length>4096 || length>r.length || prefix>8192-length ||
             sample.truncated<>(length<r.length) then raise (Bad "invalid observation region");
          if not sample.truncated && SemanticHash.string sample.prefix<>sample.digest then
            raise (Bad "complete metadata sample digest mismatch");
          check (Int64.add r.offset (Int64.of_int r.length)) (payload+r.length) (prefix+length) rest
      in check 0L 0 0 value.samples
let u64 value =
  let bytes = Bytes.create 8 in
  for i=0 to 7 do Bytes.set bytes i (Char.chr (Int64.to_int
    (Int64.logand 255L (Int64.shift_right_logical value (56-8*i))))) done;
  Bytes.to_string bytes
let magic = "SIR\000\000\000\000\000"
let encode ~nonce observation =
  if String.length nonce<>32 then invalid_arg "semantic report nonce";
  (try validate ~max_payload:FormatExtension.max_payload observation with Bad why -> invalid_arg why);
  let buffer = Buffer.create 1024 in
  let put value = Buffer.add_string buffer value in
  let integer n = put (u64 n) and small n = put (u64 (Int64.of_int n)) in
  let string value = small (String.length value); put value in
  put magic; string (profile observation); put nonce;
  begin match observation with
  | Unsupported (_,why) -> put "\001"; string why
  | Unavailable (_,why) -> put "\002"; string why
  | Supported value ->
      put "\000"; integer value.description.size; put value.description.digest;
      put value.description.preserved_digest; small (List.length value.samples);
      List.iter (fun (sample:SemanticDelta.sample) ->
        integer sample.region.offset; small sample.region.length;
        put sample.digest; string sample.prefix; put (if sample.truncated then "\001" else "\000")) value.samples
  end;
  let encoded = Buffer.contents buffer in
  if String.length encoded>max_size then invalid_arg "semantic report size";
  encoded
let decode ~nonce ~profile ~max_payload encoded =
  try
    if String.length nonce<>32 || max_payload<=0 || max_payload>FormatExtension.max_payload then
      raise (Bad "invalid report request binding");
    if String.length encoded>max_size then raise (Bad "report too large");
    let position = ref 0 in
    let take n = if n<0 || n>String.length encoded - !position then raise (Bad "truncated report");
      let result = String.sub encoded !position n in position:= !position+n; result in
    let integer () =
      let result = ref 0L in
      String.iter (fun c -> result:=Int64.logor (Int64.shift_left !result 8) (Int64.of_int (Char.code c))) (take 8);
      if !result<0L then raise (Bad "report integer overflow"); !result in
    let small limit = let value=integer () in
      if value>Int64.of_int limit then raise (Bad "report field limit"); Int64.to_int value in
    let string limit = take (small limit) in
    if take 8<>magic then raise (Bad "unknown report version");
    let received_profile = string 128 in
    if received_profile<>profile || take 32<>nonce then raise (Bad "report request mismatch");
    let result = match take 1 with
      | "\001" -> Unsupported (profile,string 1024)
      | "\002" -> Unavailable (profile,string 1024)
      | "\000" ->
          let size=integer () in let digest=take 32 in let preserved_digest=take 32 in
          let count=small 64 in
          let samples = List.init count (fun _ ->
            let offset=integer () in let length=small FormatExtension.max_region in
            let digest=take 32 in let prefix=string 4096 in
            let truncated = match take 1 with "\000" -> false | "\001" -> true
              | _ -> raise (Bad "invalid report sample flag") in
            {SemanticDelta.region={FormatExtension.offset;length};digest;prefix;truncated}) in
          Supported {description={SemanticDelta.profile;size;digest;preserved_digest;
            regions=List.map (fun (sample:SemanticDelta.sample) -> sample.region) samples};samples}
      | _ -> raise (Bad "unknown report observation") in
    if !position<>String.length encoded then raise (Bad "trailing report bytes");
    validate ~max_payload result;
    Ok result
  with Bad why -> Error why
let escaped value =
  let buffer = Buffer.create (String.length value) in
  String.iter (fun c -> match c with
    | '\n' -> Buffer.add_string buffer "\\n" | '\r' -> Buffer.add_string buffer "\\r"
    | '\t' -> Buffer.add_string buffer "\\t" | '\\' -> Buffer.add_string buffer "\\\\"
    | c when Char.code c>=32 && Char.code c<127 -> Buffer.add_char buffer c
    | c -> Buffer.add_string buffer (Printf.sprintf "\\x%02x" (Char.code c))) value;
  Buffer.contents buffer
let display_reason value = escaped (reason value)
let render ~left_label ~right_label left right =
  let lines = ref [] in
  let add value = lines:=value::!lines in
  add "Semantic observation of the current replicas' data forks";
  add ("Profile: " ^ escaped (profile left));
  add (match classification left right with
    | Exact_bytes -> "Classification: exact bytes match."
    | Metadata_only -> "Classification: editable metadata differs; all bytes outside those regions match."
    | Other_bytes -> "Classification: other bytes or the editable-region layout differ."
    | Unknown -> "Classification: unavailable; the two files cannot be equated by this observation.");
  let describe label = function
    | Unsupported (_,why) -> add (escaped label ^ ": unsupported: " ^ escaped why)
    | Unavailable (_,why) -> add (escaped label ^ ": unavailable: " ^ escaped why)
    | Supported value ->
        let d=value.description in
        add (Printf.sprintf "%s: %Ld bytes; SHA-256 %s" (escaped label) d.size (SemanticHash.hex d.digest));
        add (Printf.sprintf "  Protected-byte SHA-256: %s" (SemanticHash.hex d.preserved_digest));
        List.iter (fun (sample:SemanticDelta.sample) ->
          add (Printf.sprintf "  Editable region at %Ld: %d bytes; SHA-256 %s"
            sample.region.offset sample.region.length (SemanticHash.hex sample.digest));
          add ("  Escaped byte preview" ^ (if sample.truncated then " (truncated)" else "") ^ ": " ^ escaped sample.prefix)) value.samples in
  describe left_label left; describe right_label right;
  add "This compares the observed current files, without an archived base. Metadata can affect presentation; no rendering equivalence or conflict resolution is inferred.";
  let result=String.concat "\n" (List.rev !lines) ^ "\n" in
  if String.length result<=65536 then result else String.sub result 0 65480 ^ "\n[display truncated]\n"
