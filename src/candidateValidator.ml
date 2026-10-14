type snapshot = { sha256 : string; size : int64; identity : string }
type context = {
  supervisor : HelperSupervisor.t;
  cancellation : HelperSupervisor.cancellation;
  cpu_budget : int;
  candidate : string;
  expected : snapshot;
  resources : BackendResources.t;
  inspect : string -> snapshot Lwt.t;
  execute : (unit -> HelperSupervisor.result Lwt.t) -> HelperSupervisor.result Lwt.t;
}
module type S = sig
  val recognition : FormatRecognition.handle
  val select : unit -> (context -> unit Lwt.t) option
end
type handle = { recognition : FormatRecognition.handle; validator : (module S); resources : unit -> BackendResources.t; snapshot : BackendResources.t option ref }
type selected = {
  recognition : FormatRecognition.handle;
  validate : context -> unit Lwt.t;
  resources : BackendResources.t;
}
let trusted ?(resources=(fun () -> BackendResources.none)) ((module V : S) as validator) =
  {recognition=V.recognition;validator;resources;snapshot=ref None}
let recognition (handle:handle) = handle.recognition
let select handle =
  let module V = (val handle.validator : S) in
  match V.select () with
  | None -> None
  | Some validate ->
    let resources = handle.resources () in
    (match !(handle.snapshot) with
     | None -> handle.snapshot := Some resources
     | Some previous when BackendResources.equal previous resources -> ()
     | Some _ -> raise (Util.Fatal "Restart Unison to change backend resource declarations"));
    Some {recognition=handle.recognition;validate;resources}
