(* Original tiny TIFF fixtures. A writer's safe flag is not private grammar. *)
let put bytes little at width value =
  for j=0 to width-1 do
    Bytes.set bytes (at+(if little then j else width-1-j))
      (Char.chr ((value lsr (8*j)) land 255))
  done
let fixture little private_tag =
  let bytes=Bytes.make 4096 '\000' in
  Bytes.blit_string (if little then "II" else "MM") 0 bytes 0 2;
  let n at width value=put bytes little at width value in
  n 2 2 42; n 4 4 8; n 8 2 (if private_tag=0 then 3 else 4);
  let entry base i tag typ count value =
    let at=base+2+12*i in
    n at 2 tag;n (at+2) 2 typ;n (at+4) 4 count;n (at+8) 4 value in
  entry 8 0 50706 1 4 0;
  Bytes.blit_string "\001\004\000\000" 0 bytes 18 4;
  entry 8 1 700 1 16 1024;
  Bytes.blit_string "metadata packet!" 0 bytes 1024 16;
  entry 8 2 50741 3 1 (if little then 1 else 65536);
  if private_tag=37500 then begin
    entry 8 3 34665 4 1 2048;
    n 2048 2 1;entry 2048 0 37500 7 32 3072
  end else if private_tag<>0 then entry 8 3 private_tag 1 32 3072;
  Bytes.to_string bytes
let with_file bytes operation =
  let path=Filename.temp_file "safe-marker-" ".dng" in
  let output=open_out_bin path in output_string output bytes;close_out output;
  let fd=Unix.openfile path [Unix.O_RDONLY] 0 in
  match SemanticFile.with_fd fd operation with
  | value -> Unix.close fd;Sys.remove path;value
  | exception error -> Unix.close fd;Sys.remove path;raise error
let () =
  List.iter (fun little ->
    List.iter (fun (profile,inspect) ->
      with_file (fixture little 0) (fun file -> match inspect file with
        | Ok _ -> () | Error reason -> failwith ("safe scalar rejected: "^reason));
      List.iter (fun tag ->
        let bytes=fixture little tag in
        with_file bytes (fun file ->
          match inspect file with
          | Ok _ -> failwith "MakerNoteSafety bypassed unknown private grammar"
          | Error reason ->
              let expected=Printf.sprintf "unsupported TIFF tag %d (opaque or private graph)" tag in
              if reason<>expected then failwith ("unexpected private decline: "^reason));
        Printf.printf "%s %s tag%d safe-flag-still-declines\n%!"
          profile (if little then "little" else "big") tag) [37500;50740])
      [DngSemantic.profile,DngSemantic.inspect;DngExtended.profile,DngExtended.inspect]) [true;false];
  print_endline "PASS four scalar baselines/eight private safety refusals"
