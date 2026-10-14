(** Owner-side companion to a trusted content recognizer. Only [recognition]
    crosses into a worker; selection and execution stay on the Lwt owner. *)
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
  resources : BackendResources.t;
}
(** Optional immutable owner policy. Capture on first enabled selection; a
    changed declaration requires process restart, before staging/validation.
    Resource-bearing enabled/disabled participation is also pinned: enabling
    after an initially disabled selection or disabling an enabled resource-
    bearing backend requires restart. Otherwise a later validator could borrow
    metadata capacity without its own declared workspace having been reserved.
    Legacy companions declaring [BackendResources.none] retain policy toggles.
    Default none preserves existing companions. Requirements are accounting
    declarations; backend qualification/enforcement is a separate contract. *)
val trusted : ?resources:(unit -> BackendResources.t) -> (module S) -> handle
val recognition : handle -> FormatRecognition.handle
val select : handle -> selected option
