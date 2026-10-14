(* Locally compiled receiving validator, linked into private test binaries
   before main. It never claims Adobe format/pixel validation. *)
open Lwt
let log_path = Prefs.makeEndpointLocal
  (Prefs.createString "testvalidatorlog" "" ~local:true ~category:(`Advanced `General)
    "synthetic receiving-validator log" "Private test fixture only.")
let mode = Prefs.makeEndpointLocal
  (Prefs.createString "testvalidatormode" "pass" ~local:true ~category:(`Advanced `General)
    "synthetic receiving-validator mode" "Private test fixture only.")
let memory = Prefs.makeEndpointLocal (Prefs.createInt "testbackendmemory" 4
  ~local:true ~category:(`Advanced `General) "test backend MiB estimate" "Private fixture.")
let lanes = Prefs.makeEndpointLocal (Prefs.createInt "testbackendlanes" 1
  ~local:true ~category:(`Advanced `General) "test backend CPU declaration" "Private fixture.")
let resources () = BackendResources.make ~backend:"org.unison.test-memory/0"
  ~cpu_lanes:(Prefs.read lanes) ~covered_bytes:0
  ~uncovered_estimate:(Prefs.read memory * 1048576) ~descriptor_credits:2
  ~coverage:BackendResources.Accounting_only
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
        let usage = SemanticRuntime.admission_usage () in
        let line = Printf.sprintf "%s\t%s\t%Ld\t%s\t%d\t%d\t%d\t%d\t%d\n" context.candidate
          context.expected.sha256 context.expected.size selected_mode
          (BackendResources.bytes context.resources) (BackendResources.cpu_lanes context.resources)
          (BackendResources.descriptors context.resources) usage.payload_bytes usage.descriptors in
        let output = open_out_gen [Open_wronly;Open_append;Open_creat;Open_binary] 0o600 path in
        (try output_string output line; close_out output
         with error -> close_out_noerr output; raise error);
        if selected_mode = "reject" then
          fail (Util.Transient "synthetic registered validator rejected private candidate")
        else return ())
end
let () = CandidateValidators.register ~resources (module Validator)
