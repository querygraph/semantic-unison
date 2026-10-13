(** Owner-side companion to a trusted content recognizer. Only [recognition]
    crosses into a worker; selection and execution stay on the Lwt owner. *)
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
(** Core owns the resource loan and private candidate. [inspect] schedules
    stable full hashing; [execute] wraps only supervised helper execution in
    the filesystem gate. A validator must settle all borrowed work/children
    before returning and must not nest admission or filesystem leases. *)
module type S = sig
  val recognition : FormatRecognition.handle
  val select : unit -> (context -> unit Lwt.t) option
end
(** [select] captures endpoint policy/tool settings on the owner. Requested
    validation must check its negotiated capability. None means disabled, not
    unsupported contents. A selected handler runs for filename claims, content
    matches and indeterminate recognition alike, independently of transfer. *)
type handle
type selected = {
  recognition : FormatRecognition.handle;
  validate : context -> unit Lwt.t;
}
val trusted : (module S) -> handle
val recognition : handle -> FormatRecognition.handle
val select : handle -> selected option
