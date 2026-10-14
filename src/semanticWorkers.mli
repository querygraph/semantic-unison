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
type identification = { formats : string list; fingerprint : fingerprint option;
                        stats : Unix.LargeFile.stats }
type usage = { workers : int; pending : int; running : int; peak_running : int }
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
val usage : t -> usage
val digest : t -> HelperSupervisor.cancellation -> Unix.file_descr -> fingerprint option Lwt.t
(** Borrows the caller's regular descriptor until the promise settles. Its
    position is shared with the worker-owned duplicate: the caller must not
    seek, read, write, or close it meanwhile. The duplicate is always closed.
    None means cancelled; failures are [Failed]. Cancellation is checked at
    64 KiB boundaries and permits remain reserved until the worker finishes. *)
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
