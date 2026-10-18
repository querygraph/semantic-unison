open XmpObservation

let count = ref 0
let fixed_only = Array.length Sys.argv = 2 && Sys.argv.(1) = "--fixed-only"
let check name result =
  incr count;
  if not result then (prerr_endline ("FAIL: " ^ name); exit 1)

let rdf = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
let crs = "http://ns.adobe.com/camera-raw-settings/1.0/"
let dc = "http://purl.org/dc/elements/1.1/"
let xmp = "http://ns.adobe.com/xap/1.0/"
let ps = "http://ns.adobe.com/photoshop/1.0/"
let mm = "http://ns.adobe.com/xap/1.0/mm/"
let description ?(extra = "") attributes children =
  "<r:RDF xmlns:r=\"" ^ rdf ^ "\" xmlns:crs=\"" ^ crs ^ "\" " ^ extra ^
  "><r:Description r:about=\"\" " ^ attributes ^ ">" ^ children ^
  "</r:Description></r:RDF>"
let observe_ok name packet = match observe packet with
  | Ok observation -> observation
  | Error reason -> prerr_endline ("FAIL: " ^ name ^ " unexpected error: " ^ reason); exit 1
let rejected name packet = match observe packet with
  | Error reason -> check name (String.length reason > 0 && String.length reason <= 96)
  | Ok _ -> check name false
let property name observation =
  List.find (fun property -> property.name = name) observation.properties
let single name packet =
  let observation = observe_ok name packet in
  check (name ^ " property count") (List.length observation.properties = 1);
  List.hd observation.properties
let expanded uri local = "{" ^ uri ^ "}" ^ local
let exposure = expanded crs "Exposure2012"
let attr value = description ("crs:Exposure2012=\"" ^ value ^ "\"") ""
let child value = description "" ("<crs:Exposure2012>" ^ value ^ "</crs:Exposure2012>")

let classification namespace local expected =
  let packet = description ~extra:("xmlns:p=\"" ^ namespace ^ "\"")
      ("p:" ^ local ^ "=\"v\"") "" in
  let property = single ("category " ^ local) packet in
  check ("category " ^ local) (property.category = expected)

let () =
  let value = single "attribute encoding" (attr "1&amp;2&#x20;3") in
  check "expanded Camera Raw attribute name" (value.name = exposure);
  check "raw SHA-256 width" (String.length value.digest = 32);
  check "attribute digest matches independent Python transcript"
    (SemanticHash.hex value.digest = Expected.attribute);
  let element = single "whole element encoding"
      (description "" "<crs:Exposure2012 a=\"q\">1&amp;2<!--x--><![CDATA[<z>]]></crs:Exposure2012>") in
  check "entire element digest matches independent Python transcript"
    (SemanticHash.hex element.digest = Expected.element);
  let self_closing = single "self closing" (description "" "<crs:Exposure2012/>") in
  check "self-closing digest matches independent Python transcript"
    (SemanticHash.hex self_closing.digest = Expected.self_closing);
  check "attribute and child encoding modes differ" (value.digest <> element.digest);
  let literal = single "literal scalar" (attr "A B") in
  let escaped = single "escaped scalar" (attr "&#65;&#x20;B") in
  check "value-equivalent entity spelling remains lexical change" (literal.digest <> escaped.digest);
  let quote_single = single "single quotation" (description "crs:Exposure2012='A B'" "") in
  check "attribute value span excludes delimiter quotation" (literal.digest = quote_single.digest);
  let attr_spaces = single "attribute markup whitespace"
      (description "crs:Exposure2012 = \"A B\"" "") in
  check "attribute value span excludes markup whitespace" (literal.digest = attr_spaces.digest);
  let top = single "nested masks"
      (description ~extra:"xmlns:mask=\"urn:mask:first\"" ""
        "<crs:MaskGroup><mask:Mask>AI</mask:Mask></crs:MaskGroup>") in
  check "nested digest matches independent Python transcript"
    (SemanticHash.hex top.digest = Expected.nested);
  let rebind = single "inherited nested namespace rebound"
      (description ~extra:"xmlns:mask=\"urn:mask:second\"" ""
        "<crs:MaskGroup><mask:Mask>AI</mask:Mask></crs:MaskGroup>") in
  check "identical child encoding with inherited rebind changes digest" (top.digest <> rebind.digest);
  let nested_change = single "nested mask data"
      (description ~extra:"xmlns:mask=\"urn:mask:first\"" ""
        "<crs:MaskGroup><mask:Mask>AI2</mask:Mask></crs:MaskGroup>") in
  check "nested mask data is bound in top-level digest" (top.digest <> nested_change.digest);
  let nested_decl = single "local child namespace declaration"
      (description ""
        "<crs:MaskGroup xmlns:mask=\"urn:mask:first\"><mask:Mask>AI</mask:Mask></crs:MaskGroup>") in
  check "declaration placement remains an encoding change" (top.digest <> nested_decl.digest);
  let unused = single "unused inherited declaration"
      (description ~extra:"xmlns:unused=\"urn:unused\"" "crs:Exposure2012=\"A B\"" "") in
  check "unused namespace changes conservatively change digest" (literal.digest <> unused.digest);
  let ordered = single "namespace declaration order"
      ("<r:RDF xmlns:crs=\"" ^ crs ^ "\" xmlns:r=\"" ^ rdf ^
       "\"><r:Description crs:Exposure2012=\"A B\" r:about=\"\"/></r:RDF>") in
  check "scope mappings are sorted independently of declaration order" (literal.digest = ordered.digest);
  let alias = single "namespace alias"
      ("<r:RDF xmlns:r=\"" ^ rdf ^ "\" xmlns:camera=\"" ^ crs ^
       "\"><r:Description camera:Exposure2012=\"A B\"/></r:RDF>") in
  check "alias resolves same expanded top name" (alias.name = literal.name);
  check "namespace alias is not a digest equivalence claim" (alias.digest <> literal.digest);
  let default = single "default namespace property"
      (description "" ("<Exposure2012 xmlns=\"" ^ crs ^ "\">1</Exposure2012>")) in
  check "default namespace applies to element" (default.name = exposure);
  rejected "default namespace does not apply to attribute"
    ("<r:RDF xmlns:r=\"" ^ rdf ^ "\" xmlns=\"" ^ crs ^
     "\"><r:Description Exposure2012=\"1\"/></r:RDF>");
  let scoped = single "scoped namespace rebind"
      (description ~extra:"xmlns:p=\"urn:old\"" ""
        "<p:Field xmlns:p=\"urn:new\"><p:Child xmlns:p=\"urn:nested\"/></p:Field>") in
  check "property declaration rebind precedes name resolution" (scoped.name = "{urn:new}Field");
  let siblings = observe_ok "sibling namespace scope"
      (description ~extra:"xmlns:p=\"urn:outer\"" ""
        "<p:Field xmlns:p=\"urn:inner\"/><p:Field/>") in
  check "child namespace rebind does not leak to sibling"
    (List.map (fun p -> p.name) siblings.properties = ["{urn:inner}Field"; "{urn:outer}Field"]);
  let undeclare = single "default namespace undeclaration"
      (description "" ("<crs:MaskGroup xmlns=\"urn:default\"><Value xmlns=\"\"/></crs:MaskGroup>")) in
  check "nested default namespace undeclaration is supported" (undeclare.category = Rendering);
  let namespace_entity = single "namespace character references"
      (description ~extra:"xmlns:p=\"urn:test&amp;value\"" "p:Field=\"1\"" "") in
  check "namespace references decode before expansion" (namespace_entity.name = "{urn:test&value}Field");
  let namespace_literal = single "namespace literal URI"
      (description ~extra:"xmlns:p=\"urn:test&#38;value\"" "p:Field=\"1\"" "") in
  check "namespace binding hashes decoded URI" (namespace_entity.digest = namespace_literal.digest);
  let property_order = observe_ok "attribute then child property order"
      (description "crs:Exposure2012=\"1\" crs:Contrast2012=\"2\""
        "<crs:MaskGroup/><crs:Blacks2012/>") in
  check "properties retain packet order"
    (List.map (fun p -> p.name) property_order.properties =
      List.map (expanded crs) ["Exposure2012"; "Contrast2012"; "MaskGroup"; "Blacks2012"]);
  classification crs "MaskGroup" Rendering;
  classification crs "UnknownAdobeCurrentEdit" Rendering;
  classification dc "title" Descriptive;
  classification dc "subject" Descriptive;
  classification dc "NotInDublinCore" Opaque;
  classification ps "Headline" Descriptive;
  classification ps "ICCProfile" Opaque;
  classification xmp "Rating" Descriptive;
  classification xmp "UnknownFutureProperty" Opaque;
  classification mm "DocumentID" Identity;
  classification mm "InstanceID" Identity;
  classification mm "OriginalDocumentID" Identity;
  classification mm "History" Workflow;
  classification mm "ManagedFrom" Workflow;
  classification mm "UnknownFutureProperty" Opaque;
  classification "urn:private-rendering" "MaskGroup" Opaque;
  let wrapper = "<x:xmpmeta xmlns:x=\"adobe:ns:meta/\" x:xmptk=\"Synthetic\">" ^
      attr "1" ^ "</x:xmpmeta>" in
  let envelope = single "xmpmeta envelope" wrapper in
  check "xmpmeta is structural rather than a property" (envelope.name = exposure);
  let packet = "\239\187\191<?xml version=\"1.0\" encoding=\"utf-8\" standalone=\"yes\"?>" ^
      "<?xpacket begin=\"\239\187\191\" id=\"synthetic\"?>\n<!--outside-->" ^ wrapper ^
      "\n   <?xpacket end=\"w\"?>    " in
  ignore (single "BOM declaration packet PI and padding" packet);
  let multiple_descriptions = observe_ok "same RDF subject across descriptions"
      ("<r:RDF xmlns:r=\"" ^ rdf ^ "\" xmlns:crs=\"" ^ crs ^
       "\"><r:Description r:about=\"urn:same\" crs:Exposure2012=\"1\"/>" ^
       "<r:Description r:about=\"urn:s&#97;me\" crs:Contrast2012=\"2\"/></r:RDF>") in
  check "same RDF subject descriptions combine" (List.length multiple_descriptions.properties = 2);
  let empty = observe_ok "empty RDF" (description "" "") in
  check "empty description has no metadata properties" (empty.properties = []);
  let utf8 = single "UTF8 metadata" (attr "café \240\159\147\183") in
  check "UTF8 values keep raw bytes" (String.length utf8.digest = 32);
  ignore (single "numeric valid non-BMP reference" (attr "&#x1F4F7;"));
  ignore (single "all predefined references" (attr "&amp;&lt;&gt;&quot;&apos;"));
  rejected "duplicate child expanded property"
    (description "" "<crs:Exposure2012/><crs:Exposure2012/>");
  rejected "duplicate aliased child expanded property"
    (description ~extra:("xmlns:a=\"" ^ crs ^ "\"") ""
      "<crs:Exposure2012/><a:Exposure2012/>");
  rejected "duplicate attribute and child property"
    (description "crs:Exposure2012=\"1\"" "<crs:Exposure2012/>");
  rejected "duplicate aliased expanded XML attribute"
    (description ~extra:("xmlns:a=\"" ^ crs ^ "\"")
      "crs:Exposure2012=\"1\" a:Exposure2012=\"2\"" "");
  rejected "duplicate lexical XML attribute"
    (description "crs:Exposure2012=\"1\" crs:Exposure2012=\"1\"" "");
  rejected "duplicate expanded property across descriptions"
    ("<r:RDF xmlns:r=\"" ^ rdf ^ "\" xmlns:crs=\"" ^ crs ^
     "\"><r:Description crs:Exposure2012=\"1\"/><r:Description crs:Exposure2012=\"2\"/></r:RDF>");
  rejected "multiple RDF subjects"
    ("<r:RDF xmlns:r=\"" ^ rdf ^ "\"><r:Description r:about=\"a\"/><r:Description r:about=\"b\"/></r:RDF>");
  let subjects first second =
    "<r:RDF xmlns:r=\"" ^ rdf ^ "\" xmlns:crs=\"" ^ crs ^ "\">" ^
    "<r:Description " ^ first ^ " crs:Exposure2012=\"1\"/>" ^
    "<r:Description " ^ second ^ " crs:Contrast2012=\"2\"/></r:RDF>" in
  rejected "two anonymous RDF descriptions" (subjects "" "");
  rejected "anonymous then explicitly empty RDF subject" (subjects "" "r:about=\"\"");
  rejected "explicitly empty then anonymous RDF subject" (subjects "r:about=\"\"" "");
  rejected "anonymous then named RDF subject" (subjects "" "r:about=\"urn:named\"");
  rejected "named then anonymous RDF subject" (subjects "r:about=\"urn:named\"" "");
  let repeated_empty = observe_ok "explicitly empty subject repeats"
      (subjects "r:about=\"\"" "r:about=\"\"") in
  check "repeated explicit empty subject combines" (List.length repeated_empty.properties = 2);
  rejected "RDF nodeID subject unsupported" (description "r:nodeID=\"n\"" "");
  rejected "RDF ID subject unsupported" (description "r:ID=\"id\"" "");
  List.iter (fun local ->
    rejected ("RDF structural XML " ^ local ^ " unsupported")
      (description ("xml:" ^ local ^ "=\"value\"") "<crs:MaskGroup/>"))
    ["base"; "id"; "lang"; "space"];
  rejected "DTD unsupported" ("<!DOCTYPE r:RDF []>" ^ attr "1");
  rejected "external entity declaration unsupported"
    ("<!DOCTYPE r:RDF [<!ENTITY ext SYSTEM \"file:///no-access\">]>" ^ attr "&ext;");
  rejected "general XML entity unsupported" (attr "&custom;");
  rejected "entity names are case sensitive" (attr "&amP;");
  rejected "truncated XML entity" (attr "&amp");
  rejected "empty numeric XML entity" (attr "&#;");
  rejected "empty hex XML entity" (attr "&#x;");
  rejected "numeric reference zero" (attr "&#0;");
  rejected "numeric reference surrogate" (attr "&#xD800;");
  rejected "numeric reference noncharacter" (attr "&#xFFFF;");
  rejected "numeric reference exceeds Unicode" (attr "&#1114112;");
  rejected "numeric reference overflow" (attr "&#999999999999999999999999999;");
  rejected "uppercase hex introducer unsupported" (attr "&#X41;");
  rejected "bad numeric digit" (attr "&#xG;");
  rejected "raw attribute markup" (attr "<tag>");
  rejected "raw XML CDATA terminator" (child "]]>");
  rejected "CDATA unclosed" (description "" "<crs:Exposure2012><![CDATA[unclosed</crs:Exposure2012>");
  rejected "comment internal double hyphen" (description "" "<!--a--b-->");
  rejected "truncated comment" ("<!--a" ^ attr "1");
  rejected "nested PI unsupported" (child "<?xpacket synthetic?>");
  rejected "unrecognized document PI" ("<?other data?>" ^ attr "1");
  rejected "truncated document PI" ("<?xpacket" ^ attr "1");
  rejected "multiple packet prelude instructions" ("<?xpacket?><?xpacket?>" ^ attr "1");
  rejected "XML declaration not first" (" <?xml version=\"1.0\"?>" ^ attr "1");
  rejected "XML declaration unsupported version" ("<?xml version=\"1.1\"?>" ^ attr "1");
  rejected "XML declaration unsupported encoding" ("<?xml version=\"1.0\" encoding=\"UTF-16\"?>" ^ attr "1");
  rejected "XML declaration references are malformed" ("<?xml version=\"&#49;.0\"?>" ^ attr "1");
  rejected "XML declaration wrong attribute order" ("<?xml encoding=\"UTF-8\" version=\"1.0\"?>" ^ attr "1");
  rejected "XML declaration invalid standalone" ("<?xml version=\"1.0\" standalone=\"maybe\"?>" ^ attr "1");
  rejected "UTF16 little-endian BOM" ("\255\254<\000r\000/\000>\000");
  rejected "UTF16 big-endian BOM" ("\254\255\000<\000r\000/\000>");
  rejected "NUL character unsupported" (attr "\000");
  rejected "UTF8 overlong sequence" (attr "\192\175");
  rejected "UTF8 surrogate encoding" (attr "\237\160\128");
  rejected "UTF8 truncated sequence" (attr "\240\159");
  rejected "UTF8 invalid continuation" (attr "\194x");
  rejected "UTF8 codepoint too large" (attr "\244\144\128\128");
  rejected "Unicode XML name outside subset"
    (description "" "<crs:Étiquette/>");
  rejected "unbound property prefix" (description "" "<notbound:Field/>");
  rejected "unbound nested prefix" (child "<notbound:Field/>");
  rejected "bad qualified XML name" (description "" "<crs:a:b/>");
  rejected "empty qualified local name" (description "" "<crs:/>");
  rejected "digit qualified local start" (description "" "<crs:1bad/>");
  rejected "mismatched closing prefix"
    (description ~extra:("xmlns:a=\"" ^ crs ^ "\"") "" "<crs:Exposure2012></a:Exposure2012>");
  rejected "mismatched closing tag" (description "" "<crs:Exposure2012></crs:Contrast2012>");
  rejected "missing attribute separator" (description "crs:Exposure2012=\"1\"crs:Contrast2012=\"2\"" "");
  rejected "unquoted attribute" (description "crs:Exposure2012=1" "");
  rejected "truncated element" "<r:RDF";
  rejected "multiple document roots" (attr "1" ^ attr "2");
  rejected "trailing XML data" (attr "1" ^ "bad");
  rejected "missing document root" "   <!--only comment-->";
  rejected "unknown XML root" "<root/>";
  rejected "unsupported envelope attribute"
    ("<x:xmpmeta xmlns:x=\"adobe:ns:meta/\" unknown=\"x\">" ^ attr "1" ^ "</x:xmpmeta>");
  rejected "multiple RDF roots in envelope"
    ("<x:xmpmeta xmlns:x=\"adobe:ns:meta/\">" ^ attr "1" ^ attr "2" ^ "</x:xmpmeta>");
  rejected "RDF root non-namespace attribute"
    ("<r:RDF xmlns:r=\"" ^ rdf ^ "\" xml:lang=\"en\"/>");
  rejected "non-Description RDF container"
    ("<r:RDF xmlns:r=\"" ^ rdf ^ "\"><r:Bag/></r:RDF>");
  rejected "RDF structural non-whitespace text" (description "" "bad");
  rejected "RDF namespace direct property" (description "" "<r:li/>");
  rejected "unqualified direct property" (description "" "<Field/>");
  rejected "invalid xml prefix rebind" (description ~extra:"xmlns:xml=\"urn:wrong\"" "" "");
  rejected "XML namespace cannot bind alias"
    (description ~extra:"xmlns:alias=\"http://www.w3.org/XML/1998/namespace\"" "" "");
  rejected "xmlns namespace cannot be declared"
    (description ~extra:"xmlns:p=\"http://www.w3.org/2000/xmlns/\"" "" "");
  rejected "xmlns prefix cannot be declared" (description ~extra:"xmlns:xmlns=\"urn:wrong\"" "" "");
  rejected "prefix cannot be undeclared" (description ~extra:"xmlns:p=\"\"" "" "");
  rejected "namespace URI whitespace unsupported" (description ~extra:"xmlns:p=\"urn: white\"" "" "");
  rejected "namespace URI decoded whitespace unsupported"
    (description ~extra:"xmlns:p=\"urn:&#x20;white\"" "" "");
  rejected "namespace URI braces unsupported" (description ~extra:"xmlns:p=\"urn:{ambiguous}\"" "" "");
  rejected "namespace URI decoded markup unsupported"
    (description ~extra:"xmlns:p=\"urn:&lt;invalid&gt;\"" "" "");
  rejected "namespace URI bad percent escape"
    (description ~extra:"xmlns:p=\"urn:percent%2G\"" "" "");
  rejected "namespace URI truncated percent escape"
    (description ~extra:"xmlns:p=\"urn:percent%2\"" "" "");
  ignore (single "namespace URI escaped characters accepted"
    (description ~extra:"xmlns:p=\"urn:percent%20space\"" "p:f=\"1\"" ""));
  rejected "duplicate namespace declaration"
    (description ~extra:"xmlns:p=\"urn:one\" xmlns:p=\"urn:two\"" "" "");
  let properties n = String.concat "" (List.init n (fun i -> "<crs:Field" ^ string_of_int i ^ "/>")) in
  let at_property_limit = observe_ok "128 properties accepted" (description "" (properties 128)) in
  check "property limit inclusive" (List.length at_property_limit.properties = 128);
  rejected "129 properties rejected" (description "" (properties 129));
  let base = attr "1" in
  ignore (single "1 MiB exact packet limit" (base ^ String.make (1024 * 1024 - String.length base) ' '));
  rejected "1 MiB plus one packet rejected" (base ^ String.make (1024 * 1024 + 1 - String.length base) ' ');
  let uri = "urn:" ^ String.make (512 - 2 - 1 - 4) 'u' in
  let at_name_limit = single "expanded name exactly 512"
      (description ~extra:("xmlns:p=\"" ^ uri ^ "\"") "p:f=\"1\"" "") in
  check "expanded name byte limit inclusive" (String.length at_name_limit.name = 512);
  rejected "expanded name 513 rejected"
    (description ~extra:("xmlns:p=\"" ^ uri ^ "x\"") "p:f=\"1\"" "");
  ignore (observe_ok "namespace URI exactly 512 accepted if unused"
    (description ~extra:("xmlns:p=\"urn:" ^ String.make 508 'u' ^ "\"") "" ""));
  rejected "namespace URI 513 rejected"
    (description ~extra:("xmlns:p=\"urn:" ^ String.make 509 'u' ^ "\"") "" "");
  let prefix = String.make 128 'p' in
  ignore (single "namespace prefix exactly 128"
    (description ~extra:("xmlns:" ^ prefix ^ "=\"urn:p\"") (prefix ^ ":f=\"1\"") ""));
  rejected "namespace prefix 129 rejected"
    (description ~extra:("xmlns:" ^ prefix ^ "p=\"urn:p\"") "" "");
  let local = String.make 256 'f' in
  ignore (single "local name exactly 256" (description ("crs:" ^ local ^ "=\"1\"") ""));
  rejected "local name 257 rejected" (description ("crs:" ^ local ^ "f=\"1\"") "");
  let declarations n = String.concat " " (List.init n (fun i -> "xmlns:p" ^ string_of_int i ^ "=\"urn:" ^ string_of_int i ^ "\"")) in
  ignore (observe_ok "64 active namespaces accepted" (description ~extra:(declarations 61) "" ""));
  rejected "65 active namespaces rejected" (description ~extra:(declarations 62) "" "");
  let nested n = "<crs:MaskGroup>" ^ String.concat "" (List.init n (fun _ -> "<Value>")) ^
      "x" ^ String.concat "" (List.init n (fun _ -> "</Value>")) ^ "</crs:MaskGroup>" in
  ignore (single "depth 64 accepted" (description "" (nested 61)));
  rejected "depth 65 rejected" (description "" (nested 62));
  let attributes n = String.concat " " (List.init n (fun i -> "a" ^ string_of_int i ^ "=\"v\"")) in
  ignore (single "256 element attributes accepted"
      (description "" ("<crs:MaskGroup " ^ attributes 256 ^ "/>")));
  rejected "257 element attributes rejected"
      (description "" ("<crs:MaskGroup " ^ attributes 257 ^ "/>"));
  let nodes n = "<crs:MaskGroup>" ^ String.concat "" (List.init n (fun _ -> "<Value/>")) ^ "</crs:MaskGroup>" in
  ignore (single "8192 nodes accepted" (description "" (nodes 8189)));
  rejected "8193 nodes rejected" (description "" (nodes 8190));
  let many_attributes = "<crs:MaskGroup>" ^
      String.concat "" (List.init 64 (fun _ -> "<Value " ^ attributes 256 ^ "/>")) ^ "</crs:MaskGroup>" in
  rejected "total packet attribute limit" (description "" many_attributes);
  let total_attributes final = "<crs:MaskGroup>" ^
      String.concat "" (List.init 63 (fun _ -> "<Value " ^ attributes 256 ^ "/>")) ^
      "<Value " ^ attributes final ^ "/></crs:MaskGroup>" in
  ignore (single "16384 packet attributes accepted" (description "" (total_attributes 253)));
  rejected "16385 packet attributes rejected" (description "" (total_attributes 254));
  (* Reuse one long namespace in a full, still-supported attribute packet.
     Public names/digests are unchanged; internal names need no expanded copies. *)
  let long_uri="urn:" ^ String.make 480 'x' in
  let names n=String.concat " " (List.init n (fun i -> "p:a" ^ string_of_int i ^ "=\"v\"")) in
  let long_children="<crs:MaskGroup>" ^
    String.concat "" (List.init 63 (fun _ -> "<Value " ^ names 256 ^ "/>")) ^
    "<Value " ^ names 252 ^ "/></crs:MaskGroup>" in
  let long_packet=description ~extra:("xmlns:p=\"" ^ long_uri ^ "\"") "" long_children in
  Gc.full_major ();
  let before=Gc.allocated_bytes () in
  let observed=observe long_packet in
  let allocated=Gc.allocated_bytes () -. before in
  let observed=match observed with Ok value -> value | Error why -> failwith why in
  check "long namespace full attribute packet remains accepted" (List.length observed.properties=1);
  check "long namespace digest unchanged against independent transcript"
    (SemanticHash.hex (List.hd observed.properties).digest = Expected.long_names);
  Printf.printf "XMP_LONG_NAMES packet_bytes=%d allocated_bytes=%.0f\n%!"
    (String.length long_packet) allocated;
  (* Every byte prefix of a nontrivial packet must be rejected until the root is
     complete.  This checks all token/attribute/entity/mask truncation positions. *)
  let truncation = description "crs:Exposure2012=\"1&amp;2\""
      "<crs:MaskGroup><Value><![CDATA[mask]]></Value></crs:MaskGroup>" in
  for length = 0 to String.length truncation - 1 do
    rejected ("truncation prefix " ^ string_of_int length) (String.sub truncation 0 length)
  done;
  (* Synthetic malformed-byte input only; no files or production metadata are
     used.  Accepted output must respect every public output bound. *)
  if not fixed_only then begin
  let random = Random.State.make [|0x584d50; 17|] in
  for sample = 0 to 511 do
    let data = String.init (Random.State.int random 1024) (fun _ -> Char.chr (Random.State.int random 256)) in
    match observe data with
    | Error reason -> check ("malformed-byte fuzz reason " ^ string_of_int sample)
        (String.length reason <= 96 && String.length reason > 0)
    | Ok observation -> check ("malformed-byte fuzz bounds " ^ string_of_int sample)
        (List.length observation.properties <= 128 &&
         List.for_all (fun p -> String.length p.name <= 512 && String.length p.digest = 32)
           observation.properties)
  done
  end;
  Printf.printf "PASS: %d bounded XMP observation checks\n%!" !count
