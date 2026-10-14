module Recognition = struct
  let format = "test/late-activation-v0"
  let identify _ = FormatRecognition.Not_matched
end
module Validator = struct
  let recognition = FormatRecognition.trusted (module Recognition)
  let enabled = ref false
  let select () = if !enabled then Some (fun _ -> Lwt.return ()) else None
end
let () =
  let resources () = BackendResources.make ~backend:"test/late-activation-v0"
    ~cpu_lanes:1 ~covered_bytes:0 ~uncovered_estimate:1024 ~descriptor_credits:1
    ~coverage:BackendResources.Accounting_only in
  let handle = CandidateValidator.trusted ~resources (module Validator) in
  assert (CandidateValidator.select handle=None);
  Validator.enabled := true;
  try
    ignore (CandidateValidator.select handle);
    failwith "DESIGNATED late resource backend accepted without reserved workspace"
  with Util.Fatal _ -> print_endline "PASS late activation rejected"
