(* Synthetic differential-test transport: each stdin line is a hex packet.
   This program is confined to the private test build. *)
let digit = function
  | '0'..'9' as c -> Char.code c - Char.code '0'
  | 'a'..'f' as c -> Char.code c - Char.code 'a' + 10
  | _ -> invalid_arg "test hex input"
let decode value =
  if String.length value mod 2 <> 0 then invalid_arg "test hex input";
  String.init (String.length value / 2) (fun index ->
    Char.chr ((digit value.[2 * index] lsl 4) lor digit value.[2 * index + 1]))
let () =
  try while true do
    let packet = decode (input_line stdin) in
    print_endline (match XmpObservation.observe packet with Ok _ -> "OK" | Error _ -> "ERROR")
  done with End_of_file -> ()
