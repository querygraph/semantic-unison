(* A small, bounded XML reader for advisory XMP property observations.  Full
   packet proofs and archive/conflict decisions remain separate. *)

type category = Descriptive | Rendering | Identity | Workflow | Opaque
type property = { name : string; category : category; digest : string }
type observation = { properties : property list }

exception Parse_error of string
let fail reason = raise (Parse_error reason)

let max_packet = 1024 * 1024
let max_properties = 128
let max_expanded_name = 512
let max_uri = 512
let max_prefix = 128
let max_local = 256
let max_bindings = 64
let max_depth = 64
let max_nodes = 8192
let max_element_attributes = 256
let max_attributes = 16384

let xml_uri = "http://www.w3.org/XML/1998/namespace"
let xmlns_uri = "http://www.w3.org/2000/xmlns/"
let rdf_uri = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
let meta_uri = "adobe:ns:meta/"
let crs_uri = "http://ns.adobe.com/camera-raw-settings/1.0/"
let dc_uri = "http://purl.org/dc/elements/1.1/"
let photoshop_uri = "http://ns.adobe.com/photoshop/1.0/"
let xmp_uri = "http://ns.adobe.com/xap/1.0/"
let xmpmm_uri = "http://ns.adobe.com/xap/1.0/mm/"

type qname = { raw : string; prefix : string option; local : string }
type raw_attribute = { qname : qname; first : int; last : int }
type attribute = {
  attribute_uri : string;
  attribute_local : string;
  value_first : int;
  value_last : int;
}
type namespaces = (string * string) list
type element = {
  element_uri : string;
  element_local : string;
  element_attributes : attribute list;
  namespaces : namespaces;
  first : int;
  last : int;
  children : node list;
}
and node = Element of element | Text of int * int | Comment

type reader = {
  input : string;
  length : int;
  mutable at : int;
  mutable nodes : int;
  mutable attributes : int;
}

let space = function ' ' | '\t' | '\r' | '\n' -> true | _ -> false
let ascii_letter = function 'a'..'z' | 'A'..'Z' -> true | _ -> false
let name_start c = ascii_letter c || c = '_'
let name_char c = name_start c || match c with
  | '0'..'9' | '.' | '-' | ':' -> true | _ -> false

let starts r s =
  let n = String.length s in
  r.at <= r.length - n &&
  let rec equal i = i = n || (r.input.[r.at + i] = s.[i] && equal (i + 1)) in
  equal 0

let skip_space r =
  let first = r.at in
  while r.at < r.length && space r.input.[r.at] do r.at <- r.at + 1 done;
  r.at <> first

let require r s =
  if not (starts r s) then fail "malformed or truncated XML";
  r.at <- r.at + String.length s

let add_node r =
  r.nodes <- r.nodes + 1;
  if r.nodes > max_nodes then fail "XMP node limit exceeded"

let xml_character n =
  n = 0x9 || n = 0xa || n = 0xd ||
  (n >= 0x20 && n <= 0xd7ff) || (n >= 0xe000 && n <= 0xfffd) ||
  (n >= 0x10000 && n <= 0x10ffff)

let validate_utf8 input =
  let length = String.length input in
  let rec loop at =
    if at < length then begin
      let first = Char.code input.[at] in
      let count, minimum, initial =
        if first < 0x80 then 1, 0, first
        else if first >= 0xc2 && first <= 0xdf then 2, 0x80, first land 0x1f
        else if first >= 0xe0 && first <= 0xef then 3, 0x800, first land 0xf
        else if first >= 0xf0 && first <= 0xf4 then 4, 0x10000, first land 0x7
        else fail "unsupported UTF-16 or malformed UTF-8" in
      if at > length - count then fail "truncated UTF-8";
      let value = ref initial in
      for offset = 1 to count - 1 do
        let byte = Char.code input.[at + offset] in
        if byte land 0xc0 <> 0x80 then fail "malformed UTF-8";
        value := (!value lsl 6) lor (byte land 0x3f)
      done;
      if !value < minimum || not (xml_character !value) then
        fail "unsupported XML character";
      loop (at + count)
    end
  in loop 0

let utf8_character n =
  if n < 0x80 then String.make 1 (Char.chr n)
  else if n < 0x800 then
    String.init 2 (function
      | 0 -> Char.chr (0xc0 lor (n lsr 6))
      | _ -> Char.chr (0x80 lor (n land 0x3f)))
  else if n < 0x10000 then
    String.init 3 (function
      | 0 -> Char.chr (0xe0 lor (n lsr 12))
      | 1 -> Char.chr (0x80 lor ((n lsr 6) land 0x3f))
      | _ -> Char.chr (0x80 lor (n land 0x3f)))
  else String.init 4 (function
      | 0 -> Char.chr (0xf0 lor (n lsr 18))
      | 1 -> Char.chr (0x80 lor ((n lsr 12) land 0x3f))
      | 2 -> Char.chr (0x80 lor ((n lsr 6) land 0x3f))
      | _ -> Char.chr (0x80 lor (n land 0x3f)))

(* [at] points to an ampersand.  An entity cannot cross the supplied span. *)
let entity input at last =
  let finish code next =
    if not (xml_character code) then fail "invalid XML character reference";
    next, code in
  if at + 1 >= last then fail "truncated XML entity";
  if input.[at + 1] = '#' then begin
    let hexadecimal = at + 2 < last && input.[at + 2] = 'x' in
    let first = at + if hexadecimal then 3 else 2 in
    let base = if hexadecimal then 16 else 10 in
    let rec number cursor value digits =
      if cursor >= last then fail "truncated XML character reference";
      if input.[cursor] = ';' then begin
        if digits = 0 then fail "empty XML character reference";
        finish value (cursor + 1)
      end else begin
        let digit = match input.[cursor] with
          | '0'..'9' as c -> Char.code c - Char.code '0'
          | 'a'..'f' as c when hexadecimal -> Char.code c - Char.code 'a' + 10
          | 'A'..'F' as c when hexadecimal -> Char.code c - Char.code 'A' + 10
          | _ -> fail "malformed XML character reference" in
        if digit >= base || value > (0x10ffff - digit) / base then
          fail "invalid XML character reference";
        number (cursor + 1) (value * base + digit) (digits + 1)
      end
    in number first 0 0
  end else begin
    let rec ending cursor =
      if cursor >= last then fail "truncated XML entity";
      if input.[cursor] = ';' then cursor
      else if cursor - at > 5 then fail "general XML entities are unsupported"
      else ending (cursor + 1) in
    let ending = ending (at + 1) in
    let name = String.sub input (at + 1) (ending - at - 1) in
    let code = match name with
      | "amp" -> 0x26 | "lt" -> 0x3c | "gt" -> 0x3e
      | "quot" -> 0x22 | "apos" -> 0x27
      | _ -> fail "general XML entities are unsupported" in
    finish code (ending + 1)
  end

let validate_entities input first last =
  let rec loop at =
    if at < last then
      if input.[at] = '&' then let next, _ = entity input at last in loop next
      else loop (at + 1)
  in loop first

(* XML attribute normalization for structural values only.  Hashes retain raw
   encodings, including character-reference spelling and literal whitespace. *)
let decode_attribute input first last =
  let output = Buffer.create (min 512 (last - first)) in
  let rec loop at =
    if at < last then
      match input.[at] with
      | '&' ->
          let next, code = entity input at last in
          Buffer.add_string output (utf8_character code); loop next
      | '\r' ->
          Buffer.add_char output ' ';
          loop (if at + 1 < last && input.[at + 1] = '\n' then at + 2 else at + 1)
      | '\t' | '\n' -> Buffer.add_char output ' '; loop (at + 1)
      | c -> Buffer.add_char output c; loop (at + 1)
  in loop first; Buffer.contents output

let read_qname r =
  let first = r.at in
  if r.at >= r.length || not (name_start r.input.[r.at]) then
    fail "unsupported or malformed XML name";
  r.at <- r.at + 1;
  while r.at < r.length && name_char r.input.[r.at] do
    r.at <- r.at + 1
  done;
  let length = r.at - first in
  if length > max_prefix + 1 + max_local then fail "XML name limit exceeded";
  let raw = String.sub r.input first length in
  match String.index_opt raw ':' with
  | None ->
      if length > max_local then fail "XML local-name limit exceeded";
      { raw; prefix = None; local = raw }
  | Some colon ->
      if colon > max_prefix || colon + 1 >= length ||
         not (name_start raw.[colon + 1]) then fail "malformed XML qualified name";
      let local_length = length - colon - 1 in
      if local_length > max_local then fail "XML local-name limit exceeded";
      let local = String.sub raw (colon + 1) local_length in
      if String.contains local ':' then fail "malformed XML qualified name";
      { raw; prefix = Some (String.sub raw 0 colon); local }

let read_attribute r =
  let qname = read_qname r in
  ignore (skip_space r); require r "="; ignore (skip_space r);
  if r.at >= r.length then fail "truncated XML attribute";
  let quote = r.input.[r.at] in
  if quote <> '\'' && quote <> '"' then fail "unquoted XML attribute";
  r.at <- r.at + 1;
  let first = r.at in
  while r.at < r.length && r.input.[r.at] <> quote do
    if r.input.[r.at] = '<' then fail "unescaped attribute markup";
    r.at <- r.at + 1
  done;
  if r.at = r.length then fail "truncated XML attribute";
  let last = r.at in
  validate_entities r.input first last;
  r.at <- r.at + 1;
  { qname; first; last }

type ending = Tag of bool | Declaration

let read_attributes r declaration =
  let rec loop attributes count =
    let spaced = skip_space r in
    if declaration && starts r "?>" then
      (r.at <- r.at + 2; List.rev attributes, Declaration)
    else if not declaration && starts r "/>" then
      (r.at <- r.at + 2; List.rev attributes, Tag true)
    else if not declaration && starts r ">" then
      (r.at <- r.at + 1; List.rev attributes, Tag false)
    else begin
      if not spaced then fail "missing XML attribute separator";
      if count = max_element_attributes then fail "XML attribute limit exceeded";
      r.attributes <- r.attributes + 1;
      if r.attributes > max_attributes then fail "XMP attribute limit exceeded";
      let attribute = read_attribute r in
      if List.exists (fun other -> other.qname.raw = attribute.qname.raw) attributes
      then fail "duplicate XML attribute";
      loop (attribute :: attributes) (count + 1)
    end
  in loop [] 0

let check_expanded uri local =
  let length = String.length local + if uri = "" then 0 else String.length uri + 2 in
  if length > max_expanded_name then fail "expanded XML name limit exceeded"

let expanded uri local =
  check_expanded uri local;
  if uri = "" then local else "{" ^ uri ^ "}" ^ local

let lookup namespaces prefix =
  match List.assoc_opt prefix namespaces with
  | Some uri -> uri
  | None -> fail "unbound XML namespace prefix"

let resolve namespaces attribute qname =
  let uri = match qname.prefix with
    | Some prefix -> lookup namespaces prefix
    | None when attribute -> ""
    | None -> (match List.assoc_opt "" namespaces with Some uri -> uri | None -> "") in
  (* Keep the shared URI and local token separately throughout the AST. Eager
     concatenation repeats a long ancestor URI for every nested attribute. *)
  check_expanded uri qname.local;
  uri

let namespace_declaration attribute = match attribute.qname.prefix, attribute.qname.local with
  | None, "xmlns" -> Some ""
  | Some "xmlns", prefix -> Some prefix
  | _ -> None

let validate_namespace_uri uri =
  let hex = function '0'..'9' | 'a'..'f' | 'A'..'F' -> true | _ -> false in
  let length = String.length uri in
  let rec loop at =
    if at < length then begin
      let c = uri.[at] in
      if Char.code c <= 0x20 || Char.code c = 0x7f ||
         List.mem c ['<'; '>'; '"'; '{'; '}'; '|'; '\\'; '^'; '`'] then
        fail "unsupported namespace URI";
      if c = '%' then begin
        if at + 2 >= length || not (hex uri.[at + 1] && hex uri.[at + 2]) then
          fail "malformed namespace URI escape";
        loop (at + 3)
      end else loop (at + 1)
    end
  in loop 0

let namespaces_for r inherited attributes =
  let declarations = List.filter_map (fun attribute ->
    match namespace_declaration attribute with
    | None -> None
    | Some prefix ->
        if String.length prefix > max_prefix then fail "namespace prefix limit exceeded";
        let uri = decode_attribute r.input attribute.first attribute.last in
        if String.length uri > max_uri then fail "namespace URI limit exceeded";
        validate_namespace_uri uri;
        if prefix = "xmlns" || uri = xmlns_uri ||
           (prefix = "xml" && uri <> xml_uri) ||
           (prefix <> "xml" && uri = xml_uri) ||
           (prefix <> "" && uri = "") then fail "invalid reserved namespace binding";
        Some (prefix, uri)) attributes in
  let namespaces = List.fold_left (fun bindings (prefix, uri) ->
    let rest = List.remove_assoc prefix bindings in
    if uri = "" then rest else (prefix, uri) :: rest) inherited declarations in
  if List.length namespaces > max_bindings then fail "namespace binding limit exceeded";
  namespaces

let resolve_attributes namespaces attributes =
  let rec loop resolved = function
    | [] -> List.rev resolved
    | attribute :: rest ->
        if namespace_declaration attribute <> None then loop resolved rest
        else begin
          let uri = resolve namespaces true attribute.qname in
          if List.exists (fun other -> other.attribute_uri = uri &&
              other.attribute_local = attribute.qname.local) resolved then
            fail "duplicate expanded XML attribute";
          let resolved_attribute = {
            attribute_uri = uri; attribute_local = attribute.qname.local;
            value_first = attribute.first;
            value_last = attribute.last } in
          loop (resolved_attribute :: resolved) rest
        end
  in loop [] attributes

let read_comment r =
  add_node r; require r "<!--";
  let rec loop () =
    if starts r "-->" then r.at <- r.at + 3
    else if starts r "--" then fail "malformed XML comment"
    else if r.at = r.length then fail "truncated XML comment"
    else (r.at <- r.at + 1; loop ())
  in loop ()

let read_cdata r =
  add_node r; require r "<![CDATA[";
  let first = r.at in
  let rec loop () =
    if starts r "]]>" then begin
      let last = r.at in r.at <- r.at + 3; Text (first, last)
    end else if r.at = r.length then fail "truncated XML CDATA"
    else (r.at <- r.at + 1; loop ())
  in loop ()

let read_text r =
  add_node r;
  let first = r.at in
  while r.at < r.length && r.input.[r.at] <> '<' do
    if starts r "]]>" then fail "unescaped XML CDATA terminator";
    r.at <- r.at + 1
  done;
  validate_entities r.input first r.at;
  Text (first, r.at)

let rec read_element r inherited depth =
  if depth > max_depth then fail "XML depth limit exceeded";
  add_node r;
  let first = r.at in
  require r "<";
  if starts r "!" then fail "XML declarations and DTDs are unsupported";
  if starts r "?" then fail "nested processing instructions are unsupported";
  let qname = read_qname r in
  let raw_attributes, ending = read_attributes r false in
  let namespaces = namespaces_for r inherited raw_attributes in
  let element_uri = resolve namespaces false qname in
  let element_attributes = resolve_attributes namespaces raw_attributes in
  let self_closing = match ending with Tag value -> value | Declaration -> assert false in
  let rec content children =
    if starts r "</" then begin
      r.at <- r.at + 2;
      let closing = read_qname r in
      if closing.raw <> qname.raw then fail "mismatched XML closing tag";
      ignore (skip_space r); require r ">";
      List.rev children
    end else if r.at = r.length then fail "truncated XML element"
    else if starts r "<!--" then (read_comment r; content (Comment :: children))
    else if starts r "<![CDATA[" then content (read_cdata r :: children)
    else if starts r "<!" then fail "XML declarations and DTDs are unsupported"
    else if starts r "<?" then fail "nested processing instructions are unsupported"
    else if starts r "<" then
      content (Element (read_element r namespaces (depth + 1)) :: children)
    else content (read_text r :: children)
  in
  let children = if self_closing then [] else content [] in
  { element_uri; element_local = qname.local; element_attributes;
    namespaces; first; last = r.at; children }

let read_xml_declaration r =
  require r "<?xml";
  let attributes, _ = read_attributes r true in
  let values = List.map (fun attribute ->
    if attribute.qname.prefix <> None then fail "unsupported XML declaration";
    attribute.qname.local, String.sub r.input attribute.first (attribute.last - attribute.first)) attributes in
  let version, rest = match values with
    | ("version", value) :: rest -> value, rest
    | _ -> fail "malformed XML declaration" in
  if version <> "1.0" then fail "unsupported XML version";
  let rest = match rest with
    | ("encoding", value) :: rest ->
        if String.uppercase_ascii value <> "UTF-8" then fail "unsupported XML encoding";
        rest
    | _ -> rest in
  match rest with
  | [] | ["standalone", "yes"] | ["standalone", "no"] -> ()
  | _ -> fail "unsupported XML declaration"

let read_packet_instruction r =
  add_node r; require r "<?";
  let target = read_qname r in
  if target.raw <> "xpacket" then fail "unsupported processing instruction";
  if not (starts r "?>") && not (skip_space r) then
    fail "malformed processing instruction";
  let rec loop () =
    if starts r "?>" then r.at <- r.at + 2
    else if r.at = r.length then fail "truncated processing instruction"
    else (r.at <- r.at + 1; loop ())
  in loop ()

let read_document input =
  let length = String.length input in
  if length > max_packet then fail "XMP packet limit exceeded";
  validate_utf8 input;
  let r = { input; length; at = 0; nodes = 0; attributes = 0 } in
  if starts r "\239\187\191" then r.at <- 3;
  if starts r "<?xml" && r.at + 5 < length && space input.[r.at + 5] then
    read_xml_declaration r;
  let rec outside packets =
    ignore (skip_space r);
    if starts r "<!--" then (read_comment r; outside packets)
    else if starts r "<?" then begin
      if packets > 0 then fail "too many XMP packet instructions";
      read_packet_instruction r; outside (packets + 1)
    end in
  outside 0;
  if r.at = length then fail "missing XMP document root";
  let root = read_element r ["xml", xml_uri] 1 in
  outside 0;
  if r.at <> length then fail "multiple roots or trailing XML data";
  r, root

let whitespace input first last =
  let rec loop at = at = last || (space input.[at] && loop (at + 1)) in
  loop first

let structural_children r element =
  List.filter_map (function
    | Element element -> Some element
    | Comment -> None
    | Text (first, last) ->
        if not (whitespace r.input first last) then fail "unexpected RDF structural text";
        None) element.children

let is element uri local = element.element_uri = uri && element.element_local = local

let rdf_root r root =
  let rdf =
    if is root rdf_uri "RDF" then root
    else if is root meta_uri "xmpmeta" then begin
      List.iter (fun attribute ->
        if attribute.attribute_local <> "xmptk" ||
           (attribute.attribute_uri <> "" && attribute.attribute_uri <> meta_uri)
        then fail "unsupported XMP envelope attribute") root.element_attributes;
      match structural_children r root with
      | [rdf] when is rdf rdf_uri "RDF" -> rdf
      | _ -> fail "unsupported XMP envelope structure"
    end else fail "unsupported XMP document root" in
  if rdf.element_attributes <> [] then fail "unsupported RDF root attribute";
  rdf

let category uri local =
  if uri = crs_uri then Rendering
  else if uri = dc_uri && List.mem local
    ["contributor"; "coverage"; "creator"; "date"; "description"; "format";
     "identifier"; "language"; "publisher"; "relation"; "rights"; "source";
     "subject"; "title"; "type"] then Descriptive
  else if uri = photoshop_uri && List.mem local
    ["AuthorsPosition"; "CaptionWriter"; "Category"; "City"; "Country";
     "Credit"; "DateCreated"; "Headline"; "Instructions"; "Source"; "State";
     "SupplementalCategories"; "TransmissionReference"; "Urgency";
     "IntellectualGenre"; "Location"] then Descriptive
  else if uri = xmp_uri && List.mem local
    ["CreateDate"; "CreatorTool"; "Label"; "MetadataDate"; "ModifyDate";
     "Nickname"; "Rating"] then Descriptive
  else if uri = xmpmm_uri && List.mem local
    ["DocumentID"; "InstanceID"; "OriginalDocumentID"] then Identity
  else if uri = xmpmm_uri && List.mem local
    ["DerivedFrom"; "History"; "ManagedFrom"; "Manager"; "ManageTo";
     "ManageUI"; "ManagerVariant"; "RenditionClass"; "RenditionParams";
     "VersionID"; "Versions"; "Ingredients"; "Pantry"] then Workflow
  else Opaque

let hash_encoding input namespaces kind first last =
  let hash = SemanticHash.create () in
  let feed_string value =
    let bytes = Bytes.unsafe_of_string value in
    SemanticHash.feed hash bytes 0 (Bytes.length bytes) in
  let feed_length value =
    let bytes = Bytes.init 4 (fun index ->
      Char.chr ((value lsr (24 - 8 * index)) land 0xff)) in
    SemanticHash.feed hash bytes 0 4 in
  let feed_field value = feed_length (String.length value); feed_string value in
  feed_string "Unison-XMP-observation\000v1\000";
  feed_string (String.make 1 kind);
  let bindings = List.sort (fun (left, _) (right, _) -> String.compare left right) namespaces in
  feed_length (List.length bindings);
  List.iter (fun (prefix, uri) -> feed_field prefix; feed_field uri) bindings;
  feed_length (last - first);
  SemanticHash.feed hash (Bytes.unsafe_of_string input) first (last - first);
  SemanticHash.finish hash

let collect r rdf =
  let properties = ref [] in
  let names = Hashtbl.create max_properties in
  let subject = ref None in
  let add uri local namespaces kind first last =
    let name = expanded uri local in
    if Hashtbl.mem names name then fail "duplicate expanded XMP property";
    if Hashtbl.length names = max_properties then fail "XMP property limit exceeded";
    Hashtbl.add names name ();
    properties := { name; category = category uri local;
      digest = hash_encoding r.input namespaces kind first last } :: !properties in
  List.iter (fun description ->
    if not (is description rdf_uri "Description") then fail "unsupported RDF description";
    let about = List.find_opt (fun attribute ->
      attribute.attribute_uri = rdf_uri && attribute.attribute_local = "about")
      description.element_attributes in
    let current_subject = match about with
      | None -> `Anonymous
      | Some attribute -> `Named (decode_attribute r.input attribute.value_first attribute.value_last) in
    (match !subject, current_subject with
     | None, current -> subject := Some current
     | Some (`Named prior), `Named current when prior = current -> ()
     | Some `Anonymous, `Anonymous -> fail "multiple anonymous RDF descriptions are unsupported"
     | Some `Anonymous, `Named _ | Some (`Named _), `Anonymous ->
         fail "anonymous and identified RDF subjects are unsupported"
     | Some (`Named _), `Named _ -> fail "multiple RDF subjects are unsupported");
    List.iter (fun attribute ->
      if attribute.attribute_uri = rdf_uri then begin
        if attribute.attribute_local <> "about" then fail "unsupported RDF subject attribute"
      end else begin
        if attribute.attribute_uri = xml_uri then fail "unsupported RDF structural XML attribute";
        if attribute.attribute_uri = "" then fail "unqualified XMP property attribute";
        add attribute.attribute_uri attribute.attribute_local
          description.namespaces 'A' attribute.value_first attribute.value_last
      end) description.element_attributes;
    List.iter (fun property ->
      if property.element_uri = "" || property.element_uri = rdf_uri then
        fail "unsupported RDF property element";
      add property.element_uri property.element_local
        property.namespaces 'E' property.first property.last)
      (structural_children r description)) (structural_children r rdf);
  { properties = List.rev !properties }

let observe input =
  try
    let r, root = read_document input in
    Ok (collect r (rdf_root r root))
  with Parse_error reason -> Error reason

(* Policy data is deliberately separate from advisory property categories:
   Descriptive alone does not grant authority to merge. *)
type scalar = { scalar_name : string; first : int; last : int;
                value : string; encoded : string }
type scalar_view = { scalars : scalar list; shell : string }
let scalar_view input =
  try
    let r,root=read_document input in
    let rdf=rdf_root r root in
    ignore(collect r rdf);
    let selected=ref [] in
    let allowed uri local = uri=xmp_uri && (local="Rating" || local="Label") in
    List.iter(fun description ->
      List.iter(fun attribute ->
        if allowed attribute.attribute_uri attribute.attribute_local then begin
          let first=attribute.value_first and last=attribute.value_last in
          if last-first>4096 then fail "scalar encoding limit";
          let value=decode_attribute input first last in
          if attribute.attribute_local="Rating" then begin
            if not(List.mem value ["-1";"0";"1";"2";"3";"4";"5"])
            then fail "unsupported scalar rating"
          end else if String.length value>256 then fail "scalar label limit";
          selected:={scalar_name=expanded attribute.attribute_uri attribute.attribute_local;first;last;value;
            encoded=String.sub input first (last-first)} :: !selected
        end) description.element_attributes;
      List.iter(fun property ->
        if allowed property.element_uri property.element_local then
          fail "scalar element form unsupported") (structural_children r description))
      (structural_children r rdf);
    let scalars=List.sort(fun a b -> compare a.first b.first) !selected in
    let shell=Buffer.create(String.length input) in
    let at=ref 0 in
    List.iter(fun scalar ->
      Buffer.add_substring shell input !at (scalar.first- !at);
      (* NUL is forbidden in validated XML, so this marker cannot collide
         with a literal packet byte or a property boundary. *)
      Buffer.add_char shell '\000';at:=scalar.last) scalars;
    Buffer.add_substring shell input !at (String.length input- !at);
    Ok {scalars;shell=Buffer.contents shell}
  with Parse_error reason -> Error reason
