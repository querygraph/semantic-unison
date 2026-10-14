(* Registry and selection belong to the owner. Workers receive recognizers
   only, never this registry or the selected owner-side callbacks. *)
let known = ref []
let frozen = ref false
let register ?resources validator =
  if !frozen then invalid_arg "candidate validators must register during startup";
  let handle = CandidateValidator.trusted ?resources validator in
  let id = FormatRecognition.format (CandidateValidator.recognition handle) in
  if List.length !known >= FormatRecognition.max_recognizers ||
     List.exists (fun h ->
       FormatRecognition.format (CandidateValidator.recognition h) = id) !known then
    invalid_arg "duplicate or excessive candidate validator";
  known := !known @ [handle]
let () = register ~resources:DngCandidateValidation.resources (module DngCandidateValidation)
let selected () =
  frozen := true;
  List.filter_map CandidateValidator.select !known

let maximum_resources validators = BackendResources.maximum
  (List.map (fun (selected:CandidateValidator.selected) -> selected.resources) validators)
