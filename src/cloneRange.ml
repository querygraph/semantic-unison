type binding = {
  volume_id : string;
  generation : int64;
  file_id : string;
  size : int64;
}
type bindings = {
  owner_instance : string;
  backend_revision : string;
  source : binding;
  destination : binding;
}
type range_capability = {
  alignment : int64;
  max_bytes : int64;
  same_volume_only : bool;
  same_file_allowed : bool;
}
type capabilities = {
  native_whole : bool;
  composed_whole : bool;
  range : range_capability option;
  max_copy_bytes : int64;
}
type request = {
  source_offset : int64;
  destination_offset : int64;
  length : int64;
}
type kind = Copy | Share
type operation = {
  kind : kind;
  source_offset : int64;
  destination_offset : int64;
  length : int64;
}
type prefix = { shared : int64; copied : int64 }
type mutation_state = Known_prefix | Indeterminate
type adapter_result =
  | Shared of int64
  | Copied of int64
  | Unsupported of { prefix : prefix; reason : string; mutation : mutation_state }
  | Error of { prefix : prefix; error : exn; mutation : mutation_state }
type receipt = { bindings : bindings; request : request; progress : prefix }
type fault =
  | Invalid_request of string
  | Invalid_capability of string
  | Binding_changed of bindings
  | Observation_failed of exn
  | Invalid_result of string
  | Adapter_unsupported of string
  | Adapter_error of exn
type stopped = { receipt : receipt; fault : fault; mutation : mutation_state }
type outcome = Complete of receipt | Stopped of stopped

let zero = { shared = 0L; copied = 0L }
let total p = Int64.add p.shared p.copied

let same_file expected =
  expected.source.volume_id = expected.destination.volume_id &&
  expected.source.file_id = expected.destination.file_id

let valid_binding b =
  b.volume_id <> "" && b.file_id <> "" &&
  b.generation >= 0L && b.size >= 0L

let interval_fits offset length size =
  offset >= 0L && length >= 0L && offset <= size &&
  length <= Int64.sub size offset

let validate capabilities expected (request : request) =
  if expected.owner_instance = "" || expected.backend_revision = "" ||
     not (valid_binding expected.source) ||
     not (valid_binding expected.destination) then
    Some (Invalid_request "invalid local binding identity, generation or size")
  else if same_file expected &&
          expected.source.size <> expected.destination.size then
    Some (Invalid_request "aliased file bindings disagree on size")
  else if not (interval_fits request.source_offset request.length
                 expected.source.size) then
    Some (Invalid_request "source interval exceeds established EOF")
  else if not (interval_fits request.destination_offset request.length
                 expected.destination.size) then
    Some (Invalid_request "destination interval exceeds established EOF")
  else if same_file expected && request.length > 0L &&
          request.source_offset <
            Int64.add request.destination_offset request.length &&
          request.destination_offset <
            Int64.add request.source_offset request.length then
    Some (Invalid_request "source and destination intervals overlap in one file")
  else if capabilities.max_copy_bytes <= 0L then
    Some (Invalid_capability "max_copy_bytes must be positive")
  else match capabilities.range with
    | Some cap when cap.alignment <= 0L || cap.max_bytes <= 0L ->
        Some (Invalid_capability "range alignment and max_bytes must be positive")
    | _ -> None

let next_operation capabilities expected (request : request) sharing completed =
  let source_offset = Int64.add request.source_offset completed in
  let destination_offset = Int64.add request.destination_offset completed in
  let remaining = Int64.sub request.length completed in
  let copy length =
    { kind = Copy; source_offset; destination_offset;
      length = min length capabilities.max_copy_bytes }
  in
  match capabilities.range with
  | Some cap when sharing &&
      (not cap.same_volume_only ||
       expected.source.volume_id = expected.destination.volume_id) &&
      (not (same_file expected) || cap.same_file_allowed) ->
      let source_residue = Int64.rem source_offset cap.alignment in
      let destination_residue = Int64.rem destination_offset cap.alignment in
      if source_residue <> destination_residue then copy remaining
      else if source_residue <> 0L then
        copy (min remaining (Int64.sub cap.alignment source_residue))
      else
        let interior =
          Int64.sub remaining (Int64.rem remaining cap.alignment) in
        let maximum =
          Int64.sub cap.max_bytes (Int64.rem cap.max_bytes cap.alignment) in
        if interior = 0L || maximum = 0L then copy remaining
        else { kind = Share; source_offset; destination_offset;
               length = min interior maximum }
  | _ -> copy remaining

let validate_prefix capabilities (operation : operation) prefix =
  if prefix.shared < 0L || prefix.copied < 0L ||
     prefix.shared > operation.length ||
     prefix.copied > Int64.sub operation.length prefix.shared then
    Some "reported prefix is negative or exceeds the operation"
  else if prefix.shared <> 0L then
    match operation.kind, capabilities.range with
    | Share, Some cap when Int64.rem prefix.shared cap.alignment = 0L -> None
    | Copy, _ -> Some "copy operation reported shared bytes"
    | _ -> Some "reported shared progress is not aligned"
  else None

let execute ?(check_cancel = fun () -> ()) ~capabilities ~expected
    ~(request : request) ~observe ~perform ~notify () =
  let receipt progress = { bindings = expected; request; progress } in
  let stopped progress fault mutation =
    Stopped { receipt = receipt progress; fault; mutation } in
  match validate capabilities expected request with
  | Some fault -> stopped zero fault Known_prefix
  | None ->
      let rec loop sharing progress =
        check_cancel ();
        match observe () with
        | Result.Error error ->
            stopped progress (Observation_failed error) Known_prefix
        | Result.Ok actual when actual <> expected ->
            stopped progress (Binding_changed actual) Known_prefix
        | Result.Ok _ ->
            let completed = total progress in
            if completed = request.length then Complete (receipt progress)
            else
              let operation =
                next_operation capabilities expected request sharing completed in
              let result = perform operation in
              let prefix, successful = match result with
                | Shared n -> { shared = n; copied = 0L }, true
                | Copied n -> { shared = 0L; copied = n }, true
                | Unsupported { prefix; _ } | Error { prefix; _ } -> prefix, false
              in
              let invalid = match validate_prefix capabilities operation prefix with
                | Some reason -> Some reason
                | None when successful && total prefix = 0L ->
                    Some "successful operation made no progress"
                | None -> None
              in
              match invalid with
              | Some reason ->
                  stopped progress (Invalid_result reason) Indeterminate
              | None ->
                  let advanced =
                    { shared = Int64.add progress.shared prefix.shared;
                      copied = Int64.add progress.copied prefix.copied } in
                  if total prefix > 0L then notify operation prefix;
                  match result with
                  | Shared _ | Copied _ -> loop sharing advanced
                  | Unsupported { mutation = Known_prefix; _ }
                      when operation.kind = Share ->
                      loop false advanced
                  | Unsupported { reason; mutation; _ } ->
                      stopped advanced (Adapter_unsupported reason) mutation
                  | Error { error; mutation; _ } ->
                      stopped advanced (Adapter_error error) mutation
      in
      loop true zero
