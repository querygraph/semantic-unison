(** Typed file-hash workers for OCaml 5 / pinned OxCaml.
    All public calls belong to the legacy Lwt owner thread. Domain workers
    receive only an owned descriptor and atomic cancellation flag; they never
    access Lwt, HelperSupervisor, archives, registries, or owner callbacks. *)
type t
type fingerprint = { digest : string; stats : Unix.LargeFile.stats }
type inspection = { proof : (SemanticDelta.proof, string) result;
                    stats : Unix.LargeFile.stats }
type observation = { inspection : inspection;
  meaning : (FormatExtension.observation, string) result option }
type reconciliation = { merge_plan : (SemanticDelta.t, string) result;
                        stats : Unix.LargeFile.stats }
type identification = { formats : string list; fingerprint : fingerprint option;
                        stats : Unix.LargeFile.stats }
type recognition = { formats : string list; stats : Unix.LargeFile.stats }
type component_summary = { full_sha256 : string; layout_sha256 : string;
  projections : (ComponentHash.role * ComponentHash.projection option) list;
  refinements : DngComponents.outcome list; hash_bytes_requested : int64;
  checkpoint : ComponentHash.checkpoint option;
  checkpoint_capacity_exhausted : bool;
  reused_components : string list; invalidated_components : string list }
type component_inspection = { components : (component_summary, string) result;
                              stats : Unix.LargeFile.stats }
type usage = { workers : int; pending : int; running : int; peak_running : int; retained : int }
exception Failed of string
val recommended_workers : unit -> int
val create : workers:int -> max_pending:int -> budget:HelperSupervisor.t -> t
(** Positive workers; max_pending must be1..65536. Runtime uses4096. Both job
    and completion mailboxes reserve that many messages; admission includes
    outstanding completions, preventing independent unbounded queues. *)
val create_with_io : io:IoAdmission.t -> workers:int -> max_pending:int ->
  budget:HelperSupervisor.t -> t
(** Share an owner-loop filesystem execution gate with helpers. Reserve source
    and output devices atomically before a domain slot and CPU permit. The
    lease lasts through active worker completion and worker duplicate closure;
    waiting I/O jobs consume neither domain slots nor CPU credits. *)
val set_read_observer : ?measure_stages:bool -> t -> (int -> SemanticFile.read_stats -> unit) option -> unit
(** Optional [measure_stages] includes reader-local inclusive SDE/hash phases;
    disabled by default. Snapshot readers remain excluded. See SemanticFile.
 Owner-only opt-in read reporting; requires an idle open pool. Worker-local
    counters cross the completion mailbox as immutable data. Observer executes
    on the owner after reply settlement; its exceptions use existing completion
    error delivery without stranding sibling replies. Reports cover successfully
    returned, stable reader jobs only, not partial/cancelled reads or other I/O.
    Disable with [None]; no counter state is allocated for disabled jobs. *)
val usage : t -> usage
(** [retained] counts owner-observed unresolved duplicate-close jobs, not OS FD
    counts. Nested readers, native adapters and notification pipes need separate
    ownership qualification; this field is not a whole-process resource bound. *)
val digest : t -> HelperSupervisor.cancellation -> Unix.file_descr -> fingerprint option Lwt.t
(** Borrows the caller's regular descriptor until the promise settles. Its
    position is shared with the worker-owned duplicate: the caller must not
    seek, read, write, or close it meanwhile. Duplicates get one close attempt.
    An uncertain worker-owned duplicate keeps the reply and reservations
    unsettled, rejects new work and prevents shutdown from claiming completion.
    None means cancelled; failures are [Failed]. Cancellation is checked at
    64 KiB boundaries and permits remain reserved until the worker finishes. *)
val snapshot : t -> HelperSupervisor.cancellation -> max_bytes:int64 ->
  source:Unix.file_descr -> output:Unix.file_descr -> ValidationSnapshot.report option Lwt.t
(** Borrow a readable source and caller-owned exclusive empty private read/write
    output on a distinct inode. Both descriptors are duplicated before queueing,
    retained until actual worker settlement and admitted together through one
    source/destination I/O lease before CPU admission. Cancellation suppresses
    delivery but does not undo partial private staging. Caller must discard a
    failed/cancelled stage only after the returned work settles. Namespace,
    private-output provenance and outer memory/descriptor admission remain the
    caller's responsibility. No unchanged-file scan or helper is invoked. *)
val shutdown : t -> unit Lwt.t
(** Reject new jobs, cancel pending jobs, await completions, then join domains
    and close the notification pipe. Idempotent. Does not cancel unrelated
    operations sharing the HelperSupervisor budget. *)
val inspect : t -> HelperSupervisor.cancellation -> extension:FormatExtension.handle ->
  Unix.file_descr -> inspection option Lwt.t
(** Same ownership rules as [digest]. The owner selects the trusted extension;
    the worker invokes only that immutable handle, never the registry. *)
val identify : t -> HelperSupervisor.cancellation ->
  recognizers:(FormatRecognition.handle * bool) list ->
  Unix.file_descr -> identification option Lwt.t
(** At most sixteen unique, immutable validation recognizers and owner-computed
    destination filename claims. Claims, matches and indeterminate recognition
    select validation. A selected file is fully hashed on the same held file;
    an unmatched file is not hashed. Both outcomes require stable reads.
    Operational failure/cancellation never means no match. Same ownership,
    filesystem/domain/CPU admission and settlement rules as [digest]. *)
val recognize : t -> HelperSupervisor.cancellation ->
  recognizers:(FormatRecognition.handle * bool) list ->
  Unix.file_descr -> recognition option Lwt.t
(** Same bounded recognition/claim/error rules as [identify], but never add a
    full-file fingerprint pass. Use to select unchanged candidates before size-
    bounded private snapshotting. A trusted recognizer owns its own read bounds;
    this is not an instrumented physical-I/O ceiling. *)
val observe : t -> HelperSupervisor.cancellation -> extension:FormatExtension.handle ->
  Unix.file_descr -> observation option Lwt.t
(** Read-only inspection plus optional extension interpretation of the complete
    retained editable packets, under the same ownership/budget/stability rules.
    Only explicit report requests use this operation; ordinary transfers do not
    parse metadata semantics or pay that extra cost. *)
val apply : t -> HelperSupervisor.cancellation -> extension:FormatExtension.handle ->
  SemanticDelta.t -> basis:Unix.file_descr -> output:Unix.file_descr -> unit option Lwt.t
(** Generic verified materialization. Rejects an extension/profile mismatch
    before writing. Borrow/discard rules are identical to [apply_dng]. *)
val apply_report : t -> HelperSupervisor.cancellation -> extension:FormatExtension.handle ->
  SemanticDelta.t -> basis:Unix.file_descr -> output:Unix.file_descr ->
  SemanticDelta.application option Lwt.t
(** [apply] with immutable logical-write counters from the worker. The report
    is returned only after full target verification and basis stability checks. *)
val inspect_dng : t -> HelperSupervisor.cancellation -> Unix.file_descr -> inspection option Lwt.t
(** Same descriptor, cancellation and budget rules as [digest]. Returns the
    bounded built-in DNG profile proof, or a format eligibility reason. Does
    not access the extension registry or invoke external helpers. *)
val apply_dng : t -> HelperSupervisor.cancellation -> SemanticDelta.t ->
  basis:Unix.file_descr -> output:Unix.file_descr -> unit option Lwt.t
(** Borrows both descriptors until settled. The output must be a privately
    owned regular stage containing the exact basis bytes. Verifies basis and
    output before patching, then verifies the target digest. Never commits or
    changes filesystem properties. Discard output on cancellation or failure. *)

val reconcile_xmp : t -> HelperSupervisor.cancellation -> extension:FormatExtension.handle ->
  nonce:string -> base:SemanticDelta.proof -> left:SemanticDelta.proof ->
  right:SemanticDelta.proof -> Unix.file_descr -> reconciliation option Lwt.t
(** Build a deterministic exact XMP target plan in the shared domain/CPU pool.
    Owner supplies immutable inspected proofs and an archive-qualified common
    base; this does not choose or cache that base. Only one live left descriptor
    is borrowed. No output writes or commits occur. Cancellation, descriptor
    settlement and CPU ownership follow [inspect]; conflicting metadata returns
    an explicit Error in [merge_plan], never an automatic fallback merge. *)

val components : t -> HelperSupervisor.cancellation -> ?capture_checkpoint:bool -> decoders:DngComponents.decoders ->
  max_read_bytes:int64 -> Unix.file_descr -> component_inspection option Lwt.t
(** Explicit read-only component hashing and frozen private-decoder refinement.
    Same descriptor/domain/CPU/filesystem admission, cancellation and settlement
    rules as [digest]. The owner must retain immutable input access until settled;
    epoch checks alone are not hostile-writer exclusion. Only compact immutable
    observations cross the completion mailbox: no session, reader or snapshot
    capability escapes. The read budget counts component/decoder requests;
    preceding bounded DNG geometry reads are additional and appear in an enabled
    read observer. Unsupported format returns [components=Error _]; operational
    and budget errors fail the job, never become unsupported or no-match. No
    archive, persistent reuse, transfer, rendering or publication authority. *)
(** [capture_checkpoint] defaults false. Explicit capture exports at most1MiB of
    immutable metadata from the successful live extraction, before session expiry.
    The owner may retain its digest as prior extraction provenance; delivery alone
    does not publish an owner index or bind an archive generation. Account for up
    to max_pending times1MiB additional completion payload when enabling capture.
    No session/reader escapes. Cancelled/failed deliveries provide no checkpoint;
    ordinary observations and restore jobs leave [checkpoint=None]. *)

val restore_components : t -> HelperSupervisor.cancellation ->
  expected_checkpoint_sha256:string -> encoded:string -> max_read_bytes:int64 ->
  Unix.file_descr -> component_inspection option Lwt.t
(** Restore owner-authenticated historical DNG components on a worker using the
    same descriptor/CPU/IO/cancellation settlement as [components]. The prior
    trusted digest is mandatory; arbitrary peer bytes plus their self-hash are
    not trusted provenance. Verifies complete input and current DNG base geometry.
    Returned refinements are empty: no current decoder was invoked or approved.
    Only immutable summaries cross back; no session or reader escapes. No
    automatic cache selection, archive trust or persistence is supplied. *)

val refresh_components : t -> HelperSupervisor.cancellation ->
  previous:DngComponents.outcome list -> decoders:DngComponents.decoders ->
  ?capture_checkpoint:bool -> expected_checkpoint_sha256:string -> encoded:string ->
  max_read_bytes:int64 -> Unix.file_descr -> component_inspection option Lwt.t
(** Authenticated restore and decoder-inventory refresh on the coordinated worker.
    Prior outcomes must come from trusted owner capture, complete and bound to the
    supplied checkpoint. Reused/invalidated IDs distinguish historical retained
    interpretations from freshly run decoders. Optional capture exports the new
    live checkpoint; default false. Same cancellation/IO/CPU/FD settlement as
    [components]. Account for bounded input checkpoint plus optional output per
    pending job. No automatic owner index, peer code, archive or publication. *)

val refresh_owned_components : t -> HelperSupervisor.cancellation ->
  entry:DngComponents.owner_entry -> record:string -> decoders:DngComponents.decoders ->
  ?capture_checkpoint:bool -> max_read_bytes:int64 -> Unix.file_descr ->
  component_inspection option Lwt.t
(** Refresh an owner-selected retained capture on the coordinated worker. Derive
    checkpoint digest and complete historical decoder inventory only from the
    trusted entry after authenticating its bounded record; callers cannot mix
    an independently selected inventory with that record. Authentication runs on
    the worker before current-input hashing or any decoder invocation. Complete
    input/current-parser verification still precedes reuse. Same cancellation,
    IO/CPU/FD settlement and optional output capture as [refresh_components].
    The owner must select the entry from trusted state and independently settle
    its cache-read FDs before submission. This API consumes immutable metadata,
    not namespace presence/producer settlement proof; no opens, cache selection,
    fallback extraction, archive mutation or publication. Account for at most
    one bounded record plus entry and optional checkpoint per pending job. *)

val components_indexed : t -> HelperSupervisor.cancellation ->
  index:DngComponents.owner_index -> root_identity:string -> path:string ->
  generation_sha256:string -> record:string option -> decoders:DngComponents.decoders ->
  ?capture_checkpoint:bool -> max_read_bytes:int64 -> Unix.file_descr ->
  component_inspection option Lwt.t
(** Worker-side exact trusted owner/path/generation selection. A missing or stale
    entry uses fresh extraction with current frozen decoders. A selected entry
    requires its authenticated retained record and uses owner-bound refresh;
    missing record is explicit [components=Error _], corrupt/foreign records fail
    the job. Neither is silently downgraded to fresh extraction. Unselected record
    bytes are ignored, never promoted into authority. Optional capture applies to
    both routes; it does not publish or insert a new entry. Same CPU/IO/FD and
    cancellation rules as [components]. Caller owns index provenance, current
    generation selection, cache-read settlement and metadata memory admission.
    Immutable index snapshots may be shared across queued jobs within owner
    budgets. No opens, disk discovery, cleanup, archive mutation or automatic
    installation in the normal scan path. *)
