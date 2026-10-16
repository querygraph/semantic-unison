let check yes message=if not yes then failwith message
let packet rating label extra =
  "<rdf:RDF xmlns:rdf=\"http://www.w3.org/1999/02/22-rdf-syntax-ns#\" xmlns:xmp=\"http://ns.adobe.com/xap/1.0/\"><rdf:Description rdf:about=\"\" xmp:Rating=\""^rating^"\" xmp:Label=\""^label^"\">"^extra^"</rdf:Description></rdf:RDF>  "
let () =
 let base=packet "1" "Blue" "" in
 let ok l r expected=match XmpMerge.merge ~base ~left:l ~right:r with Ok value->check(value=expected)"wrong exact output" | Error e->failwith e in
 let no l r=check(Result.is_error(XmpMerge.merge ~base ~left:l ~right:r))"conflict admitted" in
 ok base base base;
 ok (packet "2" "Blue" "") base (packet "2" "Blue" "");
 ok base (packet "1" "Red" "") (packet "1" "Red" "");
 ok (packet "2" "Blue" "") (packet "1" "Red" "") (packet "2" "Red" "");
 ok (packet "2" "Red" "") (packet "2" "Red" "") (packet "2" "Red" "");
 ok (packet "2" "Blue" "") (packet "&#50;" "Blue" "") (packet "&#50;" "Blue" "");
 no (packet "2" "Blue" "") (packet "3" "Blue" "");
 no (packet "1" "Red" "") (packet "1" "Green" "");
 no (packet "01" "Blue" "") base;
 no (packet "6" "Blue" "") base;
 no (packet "1" (String.make 257 'x') "") base;
 no (packet "1" "Blue" "<xmp:Rating>2</xmp:Rating>") base;
 no (packet "1" "Blue" "<xmp:Unknown>opaque</xmp:Unknown>") base;
 no (base^" ") base;
 no (String.sub base 0 (String.length base-3)) base;
 let left=packet "2" "Blue" "" and right=packet "1" "Red" "" in
 check(XmpMerge.merge ~base ~left ~right=XmpMerge.merge ~base ~left:right ~right:left)"replica order changed output";
 let b=packet "-1" "A&amp;B" "" in
 check(XmpMerge.merge ~base:b ~left:(packet "0" "A&amp;B" "") ~right:(packet "-1" "A&#38;B" "")=Ok(packet "0" "A&amp;B" ""))"entity normalization changed unchanged base encoding";
 let opaque="<u:Private xmlns:u=\"urn:opaque\"><u:Mask>AI&amp;data</u:Mask></u:Private>" in
 let b=packet "1" "Blue" opaque in
 check(XmpMerge.merge ~base:b ~left:(packet "2" "Blue" opaque) ~right:(packet "1" "Red" opaque)=Ok(packet "2" "Red" opaque))"opaque bytes not preserved";
 check(Result.is_error(XmpMerge.merge ~base:b ~left:(packet "2" "Blue" opaque) ~right:(packet "1" "Blue" (opaque^" "))))"opaque structural change admitted";
 let rendering="<crs:Exposure2012 xmlns:crs=\"http://ns.adobe.com/camera-raw-settings/1.0/\">0</crs:Exposure2012>" in
 let b=packet "1" "Blue" rendering in
 let changed="<crs:Exposure2012 xmlns:crs=\"http://ns.adobe.com/camera-raw-settings/1.0/\">1</crs:Exposure2012>" in
 check(Result.is_error(XmpMerge.merge ~base:b ~left:(packet "2" "Blue" rendering) ~right:(packet "1" "Blue" changed)))"rendering group admitted";
 let remove_label value=let needle=" xmp:Label=\"Blue\"" in
   let rec find i=if String.sub value i (String.length needle)=needle then i else find(i+1) in
   let i=find 0 in String.sub value 0 i^String.sub value(i+String.length needle)(String.length value-i-String.length needle) in
 no (remove_label base) (packet "1" "Red" "");
 no (packet "1" (String.make 4097 'a') "") base;
 no (packet "1" "&#0;" "") base;
 no (packet "1" "Blue" "<xmp:Label xml:lang=\"en\">Blue</xmp:Label>") base;
 let encoded="&#"^String.make 3996 '0'^"50;" in
 let b0=packet "1" "B" "" in
 let padding=String.make(1048576-String.length b0-5000)' ' in
 let b=b0^padding and l=packet encoded "B" ""^padding
 and r=packet "1" encoded ""^padding in
 List.iter(fun packet -> check(Result.is_ok(XmpObservation.scalar_view packet))"limit control input is unsupported") [b;l;r];
 check(XmpMerge.merge ~base:b ~left:l ~right:r=Error "merged packet limit")"combined packet limit escaped";
 let ratings=["-1";"0";"1";"2";"3";"4";"5"] in
 let decisions=ref 0 in
 List.iter(fun b -> List.iter(fun l -> List.iter(fun r ->
   let base=packet b "Blue" "" and left=packet l "Blue" ""
   and right=packet r "Blue" "" in
   let result=XmpMerge.merge ~base ~left ~right in
   let expected=if l=r then Some l else if b=l then Some r
     else if b=r then Some l else None in
   (match expected,result with
    | Some value,Ok actual -> check(actual=packet value "Blue" "") "rating truth-table output"
    | None,Error _ -> ()
    | _ -> failwith "rating truth-table conflict decision");
   check(result=XmpMerge.merge ~base ~left:right ~right:left)
     "rating truth-table replica symmetry";
   incr decisions) ratings) ratings) ratings;
 check(!decisions=343) "rating decision coverage changed";
 List.iter(fun kind ->
   let nested="<xmp:Label><rdf:"^kind^"><rdf:li>Blue</rdf:li></rdf:"^kind^"></xmp:Label>" in
   no (packet "2" "Blue" "") (packet "1" "Blue" nested)) ["Bag";"Seq";"Alt"];
 no (packet "2" "Blue" "")
   (packet "1" "Blue" "<xmp:Label rdf:parseType=\"Resource\"><rdf:value>Blue</rdf:value><xmp:Qualifier>q</xmp:Qualifier></xmp:Label>");
 print_endline "PASS25 original scalar controls +343 rating decisions/symmetry +4 RDF conflicts"
