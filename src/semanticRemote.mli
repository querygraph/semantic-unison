val try_transfer : connection:Remote.connection -> source:Fspath.t ->
  basis:Fspath.t -> directory:Fspath.t -> staging:Path.local ->
  expected_size:int64 -> bool Lwt.t
(** Negotiated exact SDE/0 transfer into private APFS staging. False means
    unsupported profile/layout/backend or an old peer: use ordinary transfer.
    A successful result still requires stock properties, resource-fork,
    source-stability and fullfingerprint checks before final replacement.
    Protocol/verification/operational failures propagate after cleanup. *)
val try_transfer_with_producer : producer:(Unix.file_descr -> unit) ->
  connection:Remote.connection -> source:Fspath.t -> basis:Fspath.t ->
  directory:Fspath.t -> staging:Path.local -> expected_size:int64 -> bool Lwt.t
(** Bound receiver variant. The actual verified output descriptor stays open
    through captured-parent publication to [staging] and the synchronous
    [producer] callback. Only successful callback completion relinquishes
    temporary-name ownership; callback failures remain terminal with their
    original exception. Initial unsupported/preparation cases may return false. *)
type inspection = {
  observation : SemanticReport.observation;
  local_snapshot : (Fspath.t * Unix.LargeFile.stats) option;
}
type component_inspection = {
  component_observation : (SemanticReport.component_observation, string) result;
  component_snapshot : (Fspath.t * Unix.LargeFile.stats) option;
}
val component_details_enabled : unit -> bool
val observe_components : root:Common.root -> path:Fspath.t -> component_inspection Lwt.t
val observe_components_with_worker : local_worker:(pool:SemanticWorkers.t ->
  cancellation:HelperSupervisor.cancellation -> decoders:DngComponents.decoders ->
  max_read_bytes:int64 -> Unix.file_descr -> SemanticWorkers.component_inspection option Lwt.t) ->
  root:Common.root -> path:Fspath.t -> component_inspection Lwt.t
(** Explicit full-file DNG component inspection with an empty frozen
    decoder set, using existing owner admission/worker/descriptor settlement.
    The owner retains local snapshot facts for stale-display checks. Remote
    roots require separately negotiated semantic-components-v0 and an enabled
    DNG profile, with bounded nonce/schema-bound SIC/0. Peer results are advisory
    current observations, not local snapshot/preservation capabilities. *)
val observe : root:Common.root -> path:Fspath.t -> extension:FormatExtension.handle -> inspection Lwt.t
(** Read-only observation of one absolute, already translated current path.
    The owner selects an enabled trusted handle. Local inspection uses workers;
    remote inspection requires the separate semantic-inspect-v0 capability and
    returns bounded digest/sample information. Older peers return unavailable.
    Source leases cover queued replies; no archives or destinations are changed.
    local_snapshot allows immediate owner-side stale-display checks without RPC. *)

val try_transfer_reserved : reservation:SemanticAdmission.reservation ->
  producer:(Unix.file_descr -> unit) option -> connection:Remote.connection ->
  source:Fspath.t -> basis:Fspath.t -> directory:Fspath.t -> staging:Path.local ->
  expected_size:int64 -> bool Lwt.t
(** Borrow the receiver's retained envelope. Source RPCs keep their independent
    source admission and headroom; None producer covers explicit legacy handoff. *)

val component_retained_ownership : unit -> DngComponents.cache_ownership list
(** Owner-loop diagnostics only. Uncertain component-cache, semantic-report or transfer-planning source cleanup retains its
    carrier and a non-cancellable pending promise INSIDE its transaction admission.
    No cleanup, numeric-FD retry, implicit settlement or release authority. *)


type retained_publication
val retained_publications : unit -> retained_publication list
val retained_publication_cause : retained_publication -> exn
val retained_publication_native : retained_publication -> StagePublication.owned option
val retained_publication_descriptors : retained_publication -> Unix.file_descr list
(** Owner-loop observations for bound remote receiver native publication
    uncertainty. Remaining known descriptors and transaction admission remain
    held. No numeric retry, cleanup or implicit settlement authority. *)
