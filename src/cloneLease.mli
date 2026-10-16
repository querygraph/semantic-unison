(** Endpoint-local lease connecting held native objects to [CloneRange].
    No wire/archive representation, capability cache or mount-incarnation claim.
    Descriptors are borrowed: the owner retains them and admission credits until
    execution and all worker borrowers settle. This module never closes them. *)

type owner
type t
type endpoint = Source | Destination
type issue =
  | Owner_closed
  | Owner_invalidated
  | Lease_invalidated
  | Identity_unavailable of endpoint
  | Invalid_observation of endpoint * string
  | Not_regular of endpoint
  | Aliased_objects
  | Source_changed
  | Destination_constraints_changed
exception Invalidated of issue

val create_owner : instance_id:string -> owner
(** The trusted local controller supplies a nonempty, fresh identity, never
    reused across restart/rebind. No peer input or persisted token is accepted.
    Owner identity is independent of native volume UUID/filesystem ID. *)
val invalidate_owner : owner -> unit
(** Advance the owner epoch, invalidating every enrolled lease. Epoch exhaustion
    permanently closes the owner. Native observations do not detect every remount;
    the controller must invalidate on lifecycle/rebind events it observes. *)
val close_owner : owner -> unit

val enroll :
  ?observe:(Unix.file_descr -> FileObservation.t) ->
  owner -> backend_revision:string ->
  source:Unix.file_descr -> destination:Unix.file_descr -> (t, exn) result
(** Observe both held descriptors and check the epoch before/after observation.
    Regular, distinct objects and available volume identities are required.
    Expected operational/native errors retain their exception. The optional
    observer is a trusted local test/backend seam, never peer authority.
    Source stamps are a change detector, not an immutable-content proof. *)

val expected : t -> CloneRange.bindings
val observe : t -> (CloneRange.bindings, exn) result
(** Fresh native observations before every operation/completion, fenced by owner
    epoch. Changes to source stamps or non-binding native constraints stop the
    lease. Destination write timestamps are permitted, while its identity, size,
    kind, links, flags and mount constraints must remain enrolled. Disappearing
    required volume identity is an error, never a weaker identity fallback. *)
val invalidate : t -> unit

val execute :
  ?check_cancel:(unit -> unit) -> t ->
  capabilities:CloneRange.capabilities -> request:CloneRange.request ->
  perform:(source:Unix.file_descr -> destination:Unix.file_descr ->
           CloneRange.operation -> CloneRange.adapter_result) ->
  notify:(CloneRange.operation -> CloneRange.prefix -> unit) ->
  unit -> CloneRange.outcome
(** The adapter receives the same borrowed descriptors that are observed, so it
    need not resolve a pathname or select another FD. Explicit offsets are still
    required by its operation contract. The caller must pre-establish output EOF,
    retain a stable basis/content proof and private destination, discard on any stop/exception, verify
    exact bytes/properties and recheck root/parent/stage bindings at publication.
    A completed range receipt does not qualify pathname-based rename. *)
