val try_transfer : connection:Remote.connection -> source:Fspath.t ->
  basis:Fspath.t -> directory:Fspath.t -> staging:Path.local ->
  expected_size:int64 -> bool Lwt.t
(** Negotiated exact SDE/0 transfer into private APFS staging. False means
    unsupported profile/layout/backend or an old peer: use ordinary transfer.
    A successful result still requires stock properties, resource-fork,
    source-stability and fullfingerprint checks before final replacement.
    Protocol/verification/operational failures propagate after cleanup. *)
type inspection = {
  observation : SemanticReport.observation;
  local_snapshot : (Fspath.t * Unix.LargeFile.stats) option;
}
val observe : root:Common.root -> path:Fspath.t -> extension:FormatExtension.handle -> inspection Lwt.t
(** Read-only observation of one absolute, already translated current path.
    The owner selects an enabled trusted handle. Local inspection uses workers;
    remote inspection requires the separate semantic-inspect-v0 capability and
    returns bounded digest/sample information. Older peers return unavailable.
    Source leases cover queued replies; no archives or destinations are changed.
    local_snapshot allows immediate owner-side stale-display checks without RPC. *)
