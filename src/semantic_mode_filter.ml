(* Build-only, stock-compatible selector for individually qualified OxCaml
   contracts. It neither receives peer code nor suppresses portability errors. *)
let read path =
  let ch=open_in_bin path in
  try
    let length=in_channel_length ch in
    if length>1048576 then invalid_arg "mode filter source limit";
    let text=really_input_string ch length in close_in ch;text
  with error -> close_in_noerr ch;raise error
let replace text needle replacement =
  let size=String.length needle in
  let output=Buffer.create(String.length text) and count=ref 0 in
  let rec loop at =
    if at+size>String.length text then
      Buffer.add_substring output text at (String.length text-at)
    else if String.sub text at size=needle then begin
      incr count;Buffer.add_string output replacement;loop(at+size)
    end else begin Buffer.add_char output text.[at];loop(at+1) end in
  loop 0;Buffer.contents output, !count
let is_ox version = snd(replace version "+ox" "")>0
let transform version path =
  let name=Filename.basename path in
  let source=read path in
  let component,interface=match name with
    | "semanticHash.ml" -> "semanticHash",false
    | "semanticHash.mli" -> "semanticHash",true
    | "semanticFile.ml" -> "semanticFile",false
    | "semanticFile.mli" -> "semanticFile",true
    | "semanticMailbox.ml" -> "semanticMailbox",false
    | "semanticMailbox.mli" -> "semanticMailbox",true
    | _ -> invalid_arg "unqualified mode-filter module" in
  if not(is_ox version) then source
  else if interface then begin
    let body = if component="semanticMailbox" then
      let body,count=replace source "type 'a t" "type 'a t : value mod portable contended with 'a" in
      if count<>1 then invalid_arg "mailbox mode type declaration changed";body
    else source in
    let expected="@@ portable\n"^body in
    let template=read(Filename.concat(Filename.dirname path)(component^".ox.mli.in")) in
    if template<>expected then invalid_arg "checked mode template differs from qualified interface";
    template
  end else begin
    let expected=match component with "semanticHash" -> 3 | "semanticFile" -> 2 | _ -> 0 in
    let result,count=replace source "(* ox-portable-ffi *)" "@@ portable" in
    if count<>expected then invalid_arg "qualified native mode declarations changed";
    result
  end
let () =
  if Array.length Sys.argv<>3 then invalid_arg "usage: semantic_mode_filter COMPILER_VERSION INPUT";
  let result=transform Sys.argv.(1) Sys.argv.(2) in
  set_binary_mode_out stdout true;
  print_string result
