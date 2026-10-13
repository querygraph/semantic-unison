(* Locally compiled receiving validator, linked into private test binaries
   before main. It never claims Adobe format/pixel validation. *)
open Lwt
let log_path = Prefs.makeEndpointLocal
  (Prefs.createString "testvalidatorlog" "" ~local:true ~category:(`Advanced `General)
    "synthetic receiving-validator log" "Private test fixture only.")
let mode = Prefs.makeEndpointLocal
  (Prefs.createString "testvalidatormode" "pass" ~local:true ~category:(`Advanced `General)
    "synthetic receiving-validator mode" "Private test fixture only.")
module Recognition = struct
  let format = "org.unison.test-receiving-validator/0"
  let identify file =
    if SemanticFile.size file >= 4L && SemanticFile.read file 0L 4 = "TOY0"
    then FormatRecognition.Recognized else FormatRecognition.Not_matched
end
module Validator = struct
  let recognition = FormatRecognition.trusted ~suffixes:[".toy"] (module Recognition)
  let select () =
    let path = Prefs.read log_path and selected_mode = Prefs.read mode in
    if path = "" then None else
    Some (fun (context:CandidateValidator.context) ->
      context.inspect context.candidate >>= fun actual ->
      if actual <> context.expected then
        fail (Util.Transient "synthetic validator initial snapshot differs")
      else
        let line = Printf.sprintf "%s\t%s\t%Ld\t%s\n" context.candidate
          context.expected.sha256 context.expected.size selected_mode in
        let output = open_out_gen [Open_wronly;Open_append;Open_creat;Open_binary] 0o600 path in
        (try output_string output line; close_out output
         with error -> close_out_noerr output; raise error);
        if selected_mode = "reject" then
          fail (Util.Transient "synthetic registered validator rejected private candidate")
        else return ())
end
let () = CandidateValidators.register (module Validator)
