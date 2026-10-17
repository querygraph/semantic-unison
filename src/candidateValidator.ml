type snapshot = { sha256 : string; size : int64; identity : string }
type context = {
  supervisor : HelperSupervisor.t;
  cancellation : HelperSupervisor.cancellation;
  cpu_budget : int;
  candidate : string;
  destination : string;
  expected : snapshot;
  resources : BackendResources.t;
  inspect : string -> snapshot Lwt.t;
  execute : (unit -> HelperSupervisor.result Lwt.t) -> HelperSupervisor.result Lwt.t;
}
module type S = sig
  val recognition : FormatRecognition.handle
  val select : unit -> (context -> unit Lwt.t) option
end
type handle = { recognition : FormatRecognition.handle; validator : (module S); resources : unit -> BackendResources.t; snapshot : BackendResources.t option ref; enabled : bool option ref }
type selected = {
  recognition : FormatRecognition.handle;
  validate : context -> unit Lwt.t;
  resources : BackendResources.t;
}
let trusted ?(resources=(fun () -> BackendResources.none)) ((module V : S) as validator) =
  {recognition=V.recognition;validator;resources;snapshot=ref None;enabled=ref None}
let recognition (handle:handle) = handle.recognition
let select handle =
  let module V = (val handle.validator : S) in
  match V.select () with
  | None ->
    (match !(handle.snapshot) with
     | Some previous when not (BackendResources.equal previous BackendResources.none) ->
         raise (Util.Fatal "Restart Unison to disable a resource-bearing backend")
     | _ -> handle.enabled := Some false);
    None
  | Some validate ->
    let resources = handle.resources () in
    if !(handle.enabled) = Some false && not (BackendResources.equal resources BackendResources.none) then
      raise (Util.Fatal "Restart Unison to enable a resource-bearing backend");
    (match !(handle.snapshot) with
     | None -> handle.snapshot := Some resources
     | Some previous when BackendResources.equal previous resources -> ()
     | Some _ -> raise (Util.Fatal "Restart Unison to change backend resource declarations"));
    handle.enabled := Some true;
    Some {recognition=handle.recognition;validate;resources}
