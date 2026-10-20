(* Build-only Dune flag generator. No linked runtime registry or discovery.
   Explicit OpenSSL3 selection uses installed headers/libraries; no downloads. *)
let directory name value =
  if value <> "" && Filename.is_relative value then
    invalid_arg (name ^ " must be an absolute directory");
  String.iter (function
    | '\000' | '\n' | '\r' | '$' | '#' | '\\' ->
        invalid_arg (name ^ " contains an unsupported build-path character")
    | _ -> ()) value;
  value

let flags backend include_dir library_dir =
  match backend with
  | "platform" -> [], []
  | "openssl" ->
      let include_dir = directory "SEMANTIC_OPENSSL_INCLUDE" include_dir
      and library_dir = directory "SEMANTIC_OPENSSL_LIB" library_dir in
      ["-DUNISON_SEMANTIC_HASH_OPENSSL"] @
        (if include_dir = "" then [] else ["-I" ^ include_dir]),
      (if library_dir = "" then [] else ["-L" ^ library_dir]) @ ["-lcrypto"]
  | _ -> invalid_arg "SEMANTIC_HASH_BACKEND must be platform or openssl"

let write path values =
  let channel = open_out path in
  Fun.protect ~finally:(fun () -> close_out channel) (fun () ->
    output_char channel '(';
    List.iter (fun value -> Printf.fprintf channel " %S" value) values;
    output_string channel ")\n")

let () =
  if Array.length Sys.argv <> 6 then invalid_arg "hash-config backend include lib cflags libs";
  let cflags, libs = flags Sys.argv.(1) Sys.argv.(2) Sys.argv.(3) in
  write Sys.argv.(4) cflags; write Sys.argv.(5) libs
