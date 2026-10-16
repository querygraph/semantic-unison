(* A deliberately tiny second format proves registration-only dispatch.
   This fixture profile is linked only into disposable test executables. *)
module Toy = struct
  let profile = "org.unison.test-fixed/0"
  let inspect file =
    if SemanticFile.size file < 8L || SemanticFile.read file 0L 4 <> "TOY0"
    then Error "not a toy fixture"
    else Ok {FormatExtension.regions=[{offset=4L;length=4}]}
end
let observer : FormatExtension.observer = {
  schema="org.unison.toy-properties/0";
  observe=(function [packet] -> Ok [{FormatExtension.name="toy:workflow-state";
    category=FormatExtension.Workflow;digest=SemanticHash.string packet}]
    | _ -> Error "expected one toy packet")
}
let () = SemanticFormats.register ~max_payload:FormatExtension.max_region ~observer (module Toy)
