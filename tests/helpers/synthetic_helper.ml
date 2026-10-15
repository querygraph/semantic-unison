(* Synthetic child only: no Adobe installation or real photographs needed. *)
let sleep seconds = ignore (Unix.select [] [] [] seconds)
let argument name =
  let rec find i =
    if i + 1 >= Array.length Sys.argv then failwith ("missing " ^ name)
    else if Sys.argv.(i) = name then Sys.argv.(i + 1) else find (i + 1) in
  find 1
let report mode =
  let hash = if mode = "wrong-hash" then String.make 64 'b'
    else argument "--expected-sha256" in
  let build = if mode = "wrong-build" then "wrong" else "synthetic-1" in
  let raw = match mode with
    | "mismatch" -> "mismatch" | "missing" -> "missing"
    | "unsupported" -> "unsupported" | _ -> "valid" in
  Printf.printf "UNISON-DNG-VALIDATION 1\ncandidate-sha256 %s\ncandidate-size %s\ndriver-build %s\nstructure valid\ndecode success\nraw-digest %s\nerrors %d\nwarnings 0\nEND\n"
    hash (argument "--expected-size") build raw (if mode = "error-zero" then 1 else 0);
  flush stdout
let () =
  match Sys.argv.(1) with
  | "echo" -> print_endline Sys.argv.(2)
  | "identity" -> Printf.printf "%d\n%!" (Unix.getpid ())
  | "pid-wait" -> Printf.printf "%d\n%!" (Unix.getpid ()); sleep 10.
  | "sleep" -> sleep (float_of_string Sys.argv.(2))
  | "ignore-term" -> Sys.set_signal Sys.sigterm Sys.Signal_ignore; sleep 10.
  | "pid-sleep" ->
      Sys.set_signal Sys.sigterm Sys.Signal_ignore;
      let out = open_out Sys.argv.(2) in
      Printf.fprintf out "%d\n" (Unix.getpid ()); close_out out;
      sleep 10.
  | "check-inherited" ->
      let target = Unix.stat Sys.argv.(2) in
      let found = ref false in
      for fd = 3 to 128 do
        try let st = Unix.stat ("/dev/fd/" ^ string_of_int fd) in
          if st.Unix.st_dev = target.Unix.st_dev && st.Unix.st_ino = target.Unix.st_ino
          then found := true
        with Unix.Unix_error _ -> ()
      done;
      print_endline (if !found then "leaked" else "closed")
  | "flood" ->
      let data = String.make 4096 'x' in
      for _ = 1 to 1000 do output_string stdout data; flush stdout;
        output_string stderr data; flush stderr done
  | "descendant" ->
      let pid = Unix.create_process Sys.executable_name
        [|Sys.executable_name; "marker"; Sys.argv.(2)|]
        Unix.stdin Unix.stdout Unix.stderr in
      Printf.printf "%d\n%!" pid
  | "marker" -> sleep 0.4; let out = open_out Sys.argv.(2) in close_out out
  | "malformed" -> print_endline "success"
  | "exit-nonzero" -> report "valid"; exit 4
  | mode -> report mode
