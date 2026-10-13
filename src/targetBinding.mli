(** Bounded, single-use endpoint-local tickets for final-file publication.
    Only the random token crosses the wire; native handles remain here.
    Calls belong to the endpoint's cooperative Lwt controller thread. *)
type t
type completion = Guarded_producer | Legacy_backend

val supported : unit -> bool
(** Negotiated protocol support only; independent of this endpoint's native
    filesystem implementation. *)

val producer_supported : unit -> bool
(** Both producer and base ticket protocols were negotiated. Independent of
    this endpoint's native filesystem implementation. *)

val prepare : ?reservation:SemanticAdmission.reservation -> ?connection:Remote.connection -> ?require_producer:bool -> logical_root:Fspath.t ->
  local_path:Path.local -> working_dir:Fspath.t -> candidate:Path.local ->
  target:Path.local -> normalize:bool -> check_apple_double:bool -> unit ->
  string option
(** Reserve one of 128 slots before native preparation. Return a 64-character
    lowercase hexadecimal random token. Native unavailability at preparation
    or a non-directory logical root may return [None]; overload and operational
    errors fail explicitly. Record the current follow-link policy and the
    caller's Copy-only normalization policy, case mode and current resource-fork
    policy ([check_apple_double] must equal [Prefs.read Osx.rsrc]). No candidate
    is attached yet. [require_producer] defaults to false for the existing
    named-attachment protocol; true requires one producer operation before
    commit. The caller gates the additive protocol with [producer_supported]. *)

val prepare_admitted : ?connection:Remote.connection -> ?require_producer:bool ->
  logical_root:Fspath.t -> local_path:Path.local -> working_dir:Fspath.t ->
  candidate:Path.local -> target:Path.local -> normalize:bool ->
  check_apple_double:bool -> unit -> string option Lwt.t
(** Production preparation: acquire a durable consumer envelope before native
    preparation and retain it across Ready/Finalized through commit or abort.
    Recover settled orphan tickets before waiting. Legacy handoff retains the
    work envelope until its borrowed callback settles. [prepare] is the low-level
    synchronous primitive; production must use this admitted entry point. *)
val reservation : t -> SemanticAdmission.reservation option
(** Local resource owner for explicitly borrowing the selected work envelope.
    Never serialized, implicitly inherited or used to nest a second gate wait. *)

val with_producer : ?connection:Remote.connection -> token:string ->
  logical_root:Fspath.t -> local_path:Path.local -> working_dir:Fspath.t ->
  candidate:Path.local -> target:Path.local -> (t -> 'a Lwt.t) ->
  ('a * completion) Lwt.t
(** Borrow a strict Ready ticket once to materialize its actual candidate.
    The callback adopts its actual output descriptor, finishes planned fork/
    property changes, freezes that witness, and records its actual non-pseudo
    fingerprint. All helpers must settle before the callback returns. Success
    retains the frozen owner as Finalized through source checking until commit.
    Only explicit [legacy_handoff] produces [Legacy_backend]; stale/operational
    errors fail. Source transport connections are separate from this receiver
    control connection: a local receiver's owner is [None]. *)

val with_binding : ?connection:Remote.connection -> token:string ->
  logical_root:Fspath.t -> local_path:Path.local -> working_dir:Fspath.t ->
  candidate:Path.local -> target:Path.local -> (t -> 'a Lwt.t) -> 'a Lwt.t
(** Match the connection/session/root, revoke the token, then match all paths
    and await the callback. The callback must await all helpers using the
    handle. Connection close marks a borrowed handle closing, but keeps its
    descriptors and capacity reservation until that callback settles. Cleanup
    never removes a published live file. Wrong-owner requests do not revoke
    another owner's ticket; a matching-owner attempt consumes it even when
    path verification fails. Strict tickets require Finalized producer-origin
    proof and its local fingerprint; no named attachment is performed here.
    State-ineligible requests (including producer/commit replay while busy)
    fail before borrowing and preserve the current authorized operation. *)

val release_ticket : ?connection:Remote.connection -> logical_root:Fspath.t ->
  token:string -> unit -> unit
(** Revoke and close an unconsumed ticket without touching unattached paths.
    A consumed/expired token is an idempotent no-op. A wrong owner/root fails.
    If already borrowed, mark it closing and defer cleanup until settlement. *)

val native : t -> FinalPublication.t
val check_open : t -> unit
(** Reject closed, handed-off, closing or expired-session handles. *)

val closing : t -> bool
val published : t -> bool
(** Publication remains queryable after close or legacy handoff. *)

val requires_producer : t -> bool
val finalized : t -> bool
(** Producer origin was successfully frozen. Historical after close; use
    [check_open] and candidate checks for current operation eligibility. *)

val record_fingerprint : t -> Os.fullfingerprint -> unit
(** Once only in a strict producer borrow, after native producer freezing.
    Record the actual final paranoid fingerprint, including when the source
    archive fingerprint was pseudo. Reject pseudo values and fence the setter
    with frozen candidate checks. This trusted local receipt is not peer proof. *)

val fingerprint : t -> Os.fullfingerprint option
(** The recorded actual fingerprint remains available after close, as a
    historical receipt. No native identity or descriptor is serialized. *)

val recheck_resolution : t -> unit
(** Recompute [Fspath.findWorkingDir] from the recorded logical root/path,
    reject changed follow-link, case-mode or resource-fork policy, apply the
    SAME recorded normalization,
    then ask the native handle to compare resolved physical bindings. *)

val legacy_handoff : t -> unit
(** Relinquish proof ownership, closing descriptors without unlinking. Use
    before legacy directory, sidecar or conflict handling. Recheck current
    resolution/policies and any mutable or frozen candidate before handoff;
    stale/operational errors never become a legacy choice. Idempotent. *)

val quarantine : t -> unit
(** After validation helpers have settled, exclusively move an unpublished
    witnessed candidate to a nonce-derived private name before deleting it.
    A failed native operation remains an error; publication is never undone. *)
