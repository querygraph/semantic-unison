let sample label f input =
  let value=ref "" in
  let wall=Unix.gettimeofday() and cpu=Sys.time() in
  for _=1 to 16 do value:=f input done;
  let cpu=Sys.time()-.cpu and wall=Unix.gettimeofday()-.wall in
  if String.length !value<>32 then failwith "digest";
  Printf.printf "%s %.9f %.9f\n%!" label cpu wall
let () =
  let input=String.init 65536 (fun i -> Char.chr((i*113+29) land 255)) in
  if OldHash.reference_string input<>SemanticHash.reference_string input || OldHash.string input<>SemanticHash.string input then failwith "old/new digest";
  for i=1 to 9 do
    if i mod 2=0 then begin sample "old-reference" OldHash.reference_string input;sample "new-reference" SemanticHash.reference_string input end
    else begin sample "new-reference" SemanticHash.reference_string input;sample "old-reference" OldHash.reference_string input end;
    sample "old-native" OldHash.string input;sample "new-native" SemanticHash.string input
  done
