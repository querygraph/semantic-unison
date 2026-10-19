(* Original synthetic protocol producer; no DNG or SDK operations. *)
let () =
  if Array.length Sys.argv <> 11 then exit 64;
  let mode=Sys.argv.(1) in
  List.iter (fun (index,value) -> if Sys.argv.(index)<>value then exit 65)
    [2,"--unison-dng-validation-v1";3,"--expected-sha256";5,"--expected-size";
     7,"--threads";8,"1";9,"--";10,"/synthetic/policy-candidate.dng"];
  let choose name yes no = if mode=name then yes else no in
  let raw = match mode with
    | "missing" -> "missing" | "raw-mismatch" -> "mismatch"
    | "raw-unsupported" -> "unsupported" | "raw-not-checked" -> "not_checked"
    | _ -> "valid" in
  let structure=match mode with "structure-invalid"->"invalid"
    | "structure-unsupported"->"unsupported" | _->"valid" in
  let decode=match mode with "decode-failure"->"failure"
    | "decode-unsupported"->"unsupported" | "decode-not-checked"->"not_checked"
    | _->"success" in
  let receipt=Printf.sprintf
    "UNISON-DNG-VALIDATION 1\ncandidate-sha256 %s\ncandidate-size %s\ndriver-build %s\nstructure %s\ndecode %s\nraw-digest %s\nerrors %d\nwarnings %d\nEND\n"
    (choose "wrong-hash" (String.make 64 'b') Sys.argv.(4))
    (choose "wrong-size" "24" Sys.argv.(6))
    (choose "wrong-build" "wrong" "original-policy-finding-1") structure decode raw
    (if mode="error-zero" then 1 else 0) (if mode="warnings" then 3 else 0) in
  print_string (match mode with "malformed"->"success\n"
    | "trailing"->receipt^"extra\n"
    | "truncated"->String.sub receipt 0 (String.length receipt-1) | _->receipt);
  flush stdout;
  if mode="nonzero" then exit 4
