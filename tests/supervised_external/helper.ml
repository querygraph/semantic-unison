let write path text =
  let out = open_out_bin path in output_string out text; close_out out
let () =
  let mode = Sys.argv.(1) and pid = Sys.argv.(2) in
  write pid (string_of_int (Unix.getpid ()));
  match mode with
  | "echo" ->
      Printf.printf "argv0=%S env=%S\n" Sys.argv.(0) (Sys.getenv "SUPERVISED_FIXTURE_ENV");
      for i=3 to Array.length Sys.argv-1 do Printf.printf "arg=%S\n" Sys.argv.(i) done
  | "hold" ->
      while not (Sys.file_exists Sys.argv.(3)) do ignore (Unix.select [] [] [] 0.01) done
  | "hang" ->
      Sys.set_signal Sys.sigterm Sys.Signal_ignore;
      while true do ignore (Unix.select [] [] [] 0.01) done
  | "stdout-flood" | "stderr-flood" ->
      let out = if mode="stdout-flood" then stdout else stderr in
      let data = String.make 16384 'x' in
      for _=1 to 129 do output_string out data; flush out done
  | "signal" -> Unix.kill (Unix.getpid ()) Sys.sigterm
  | _ -> exit 7
