type snapshot = { sha256 : string; size : int64; identity : string }
type context = {
  supervisor : HelperSupervisor.t;
  cancellation : HelperSupervisor.cancellation;
  cpu_budget : int;
  candidate : string;
  expected : snapshot;
  inspect : string -> snapshot Lwt.t;
  execute : (unit -> HelperSupervisor.result Lwt.t) -> HelperSupervisor.result Lwt.t;
}
module type S = sig
  val recognition : FormatRecognition.handle
  val select : unit -> (context -> unit Lwt.t) option
end
type handle = { recognition : FormatRecognition.handle; validator : (module S) }
type selected = {
  recognition : FormatRecognition.handle;
  validate : context -> unit Lwt.t;
}
let trusted ((module V : S) as validator) =
  {recognition=V.recognition;validator}
let recognition (handle:handle) = handle.recognition
let select handle =
  let module V = (val handle.validator : S) in
  match V.select () with
  | None -> None
  | Some validate -> Some {recognition=handle.recognition;validate}
