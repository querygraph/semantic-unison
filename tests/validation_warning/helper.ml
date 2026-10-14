(* Protocol fixture only. No Adobe SDK, image decoder or camera data. *)
let read path =
  let channel = open_in_bin path in
  Fun.protect ~finally:(fun () -> close_in channel) (fun () ->
    really_input_string channel (in_channel_length channel))
let append path data =
  let channel = open_out_gen [Open_creat; Open_append; Open_binary] 0o600 path in
  Fun.protect ~finally:(fun () -> close_out channel) (fun () -> output_string channel data)
let () =
  if Array.length Sys.argv <> 10 || Sys.argv.(1) <> "--unison-dng-validation-v1" ||
     Sys.argv.(2) <> "--expected-sha256" || Sys.argv.(4) <> "--expected-size" ||
     Sys.argv.(6) <> "--threads" || Sys.argv.(7) <> "1" || Sys.argv.(8) <> "--" ||
     Filename.is_relative Sys.argv.(9) then exit 64;
  let candidate = Sys.argv.(9) in
  let own_control = Sys.file_exists (candidate ^ ".control") in
  let control = if own_control then candidate else Sys.executable_name in
  let mode = String.trim (read (control ^ ".control")) in
  let bytes = read candidate in
  let hash = SemanticHash.hex (SemanticHash.string bytes) and size = string_of_int (String.length bytes) in
  if hash <> Sys.argv.(3) || size <> Sys.argv.(5) then exit 65;
  append (control ^ ".calls") (Printf.sprintf "%d\t%s\t%s\t%s\t%s\n"
    (Unix.getpid ()) mode hash size candidate);
  if mode = "hang" then begin
    Sys.set_signal Sys.sigterm Sys.Signal_ignore;
    while true do ignore (Unix.select [] [] [] 0.02) done
  end;
  if mode = "mutate" then begin
    let channel = open_out_gen [Open_wronly; Open_append; Open_binary] 0 candidate in
    output_string channel "UNAPPROVED-FIXTURE-MUTATION"; close_out channel
  end;
  Printf.printf "UNISON-DNG-VALIDATION 1\ncandidate-sha256 %s\ncandidate-size %s\n\
driver-build validation-warning-synthetic-1\nstructure valid\ndecode success\n\
raw-digest missing\nerrors %d\nwarnings 0\nEND\n%!"
    hash size (if mode = "pass" then 0 else 1)
