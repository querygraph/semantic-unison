val try_local : source:Fspath.t -> basis:Fspath.t -> directory:Fspath.t ->
  staging:Path.local -> bool
(** Sequential reference implementation for tests. Production uses
    [try_local_async]. Creates only transaction-owned staging; false means
    normal copy should be used. No live file is modified. *)
val is_enabled : unit -> bool
val try_local_async : source:Fspath.t -> basis:Fspath.t -> directory:Fspath.t ->
  staging:Path.local -> bool Lwt.t
(** Production local semantic transaction. Inspects source and private basis
    concurrently, materializes and verifies on typed workers under the shared
    CPU budget. The caller retains the stock source/property/fork/fingerprint
    lifecycle. False means ordinary copying should be used. *)
val try_local_async_with_producer : producer:(Unix.file_descr -> unit) ->
  source:Fspath.t -> basis:Fspath.t -> directory:Fspath.t ->
  staging:Path.local -> bool Lwt.t
(** Bound local semantic transaction. Promote the verified candidate through
    a captured creation-parent owner, then pass its still-open output descriptor
    to [producer] before relinquishing staging ownership and closing the
    transaction. Callback failures are terminal and retain their original
    exception. Unsupported initial preparation/layout may return false. *)

val try_local_async_reserved : reservation:SemanticAdmission.reservation ->
  producer:(Unix.file_descr -> unit) option -> source:Fspath.t -> basis:Fspath.t ->
  directory:Fspath.t -> staging:Path.local -> bool Lwt.t
(** Borrow the caller's retained publication envelope before clone/worker opens.
    None producer preserves an explicitly handed-off legacy materializer while
    retaining its work admission. No nested resource gate acquisition. *)

val capture_common_base_async : root:Fspath.t -> path:Path.local -> source:Fspath.t -> unit Lwt.t
(** Optional private packet capture; independently fingerprints and inspects a
    stable source under shared resource/CPU/worker admission. The later archive,
    not this capture, authorizes that exact fingerprint as common merge base. *)
val merge_local_async : base_fingerprint:Os.fullfingerprint -> base:Fspath.t ->
  left:Fspath.t -> right:Fspath.t -> output:Fspath.t ->
  SemanticDelta.application Lwt.t
(** Explicit built-in scalar merge, independent of transfer optimization prefs.
    All paths are private merge-owner files; output must already contain left's
    exact bytes. Verify a non-pseudo previous-archive fingerprint against the
    held saved-base identity, then inspect/reconcile/materialize on the shared
    workers. Resource forks, missing bases, incompatible profiles and conflicts
    fail without fallback to a guessed base. Borrowed jobs settle before closing
    any descriptor; admission/cancellation use the existing runtime. The caller
    owns output deletion on failure, original preservation, validation and
    ordinary two-replica commit/recovery. No archive format change or rename. *)

val merge_local_async_with_cache : cache:(Fspath.t * Path.local) ->
  base_fingerprint:Os.fullfingerprint -> base:Fspath.t -> left:Fspath.t ->
  right:Fspath.t -> output:Fspath.t -> SemanticDelta.application Lwt.t
(** Resolve a private compact base under the agreeing previous archive binding;
    a miss retains verified saved-file fallback. No current replica is a base. *)


type retained_publication
val retained_publications : unit -> retained_publication list
val retained_publication_cause : retained_publication -> exn
val retained_publication_native : retained_publication -> StagePublication.owned option
val retained_publication_descriptors : retained_publication -> Unix.file_descr list
(** Owner-loop diagnostics for local async descriptor/native publication uncertainty.
    Transaction admission and remaining known descriptors stay held inside the
    pending operation. These observations grant no cleanup/retry authority. *)

val retained_publication_pair_ownership : retained_publication -> NotificationPipe.t option
val retained_publication_source_ownership : retained_publication -> NotificationPipe.t option
val retained_publication_parent_ownership : retained_publication -> NotificationPipe.t option
(** Owner-loop forensic ledgers, including legacy async transactions. Known FD
    inventory excludes uncertain/closed/transferred numbers. No cleanup/retry
    authority or native known-close assertion is granted by these observations. *)
