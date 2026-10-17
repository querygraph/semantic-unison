(** Bounded worker-local component hashing over an owner-controlled snapshot.
    All bytes stay covered. Roles are parser claims, never transformation or
    rendering-equivalence authority. Authenticated checkpoint restore revalidates complete input; no automatic store. *)
type role = Encoded_pixels | Standard_metadata | Private_metadata | Structural | Opaque
type spec = { id : string; schema : string; role : role;
              offset : int64; length : int64; children : spec list }
type node = { id : string; schema : string; role : role;
              offset : int64; length : int64; content_sha256 : string;
              view_sha256 : string; children : node list }
type snapshot
type session
type reader
type plugin = { id : string; implementation_sha256 : string;
                decode : reader -> (spec list, string) result (* ox-portable-field *) }
type projection = { sha256 : string; components : int; bytes : int64 }
type checkpoint
exception Invalid of string
val with_snapshot : max_read_bytes:int64 -> SemanticFile.t -> spec ->
  (session -> snapshot -> 'a) -> 'a
(** The root must cover the whole file; children are parent-relative and gaps
    become opaque atoms. Initial hashing reads each byte once, feeding ancestor
    hashes without rereading. At most1024 nodes/depth16. Caller owns immutable
    snapshot access throughout the callback. Consistency checks are not hostile
    writer exclusion. Session/reader capabilities expire on return; snapshots
    can escape only as historical observations, not current-file authority. *)
val root : snapshot -> node
val full_sha256 : snapshot -> string
val layout_sha256 : snapshot -> string
val projection : snapshot -> role -> projection option
(** Versioned logical-role projection, ordered by component ID, excludes physical
    offsets. Counts describe claimed ranges only, not complete format coverage.
    None means no claimed nonempty component, not proof of absent pixels;
    equal partial projections are not whole-image or rendering equality.
    Encoded pixels are not decoded pixels; rendering dependencies remain separate.
    All opaque/structural bytes retain their lanes. *)
val bytes_requested : session -> int64
val refine : session -> snapshot -> component:string -> schema:string -> spec list -> snapshot
(** Replace one leaf's view with a bounded child partition. Reread only that
    parent span, verify its raw digest, reuse unaffected nodes and recompute
    ancestor views. Full-file digest stays the initial snapshot observation.
    Cross-session or expired reuse fails; never derive child hashes from the
    old parent digest. The shared budget charges attempted reads, no refunds. *)
val apply_plugin : session -> snapshot -> component:string -> plugin -> (snapshot, string) result
(** Trusted compiled decoder receives only a bounded parent-relative reader and
    shared budget; callback lifetime is checked. Explicit unsupported results
    preserve the old snapshot. Operational/read errors propagate. No registries,
    subprocesses, code loading or security sandbox is supplied. ID is at most128
    bytes; the raw32-byte implementation SHA is an owner-pinned declaration,
    included in refined provenance, not proof of a function's machine code. *)
val read : reader -> int64 -> int -> string
val with_subreader : reader -> offset:int64 -> length:int64 -> (reader -> 'a) -> 'a
(** Nested child decoder capability, parent-relative, sharing the same budget.
    Child and ancestor callback lifetimes are checked; at most16 reader levels. *)
val max_checkpoint_size : int
val checkpoint : session -> snapshot -> checkpoint
val checkpoint_bytes : checkpoint -> string
val checkpoint_sha256 : checkpoint -> string
(** Export at most1MiB of versioned canonical metadata, never payload or reader
    capabilities. Call while the snapshot's original session is live. Retain the
    digest in trusted owner state authenticated to that extraction; computing a
    digest from arbitrary peer/cache bytes is NOT equivalent provenance. *)
val checkpoint_root : checkpoint -> node
(** Bounded historical metadata only; no live input or session authority. *)
val checkpoint_record : binding:string -> checkpoint -> string
val checkpoint_from_record : expected_binding:string -> expected_record_sha256:string ->
  string -> checkpoint
(** Bounded UCR/0 owner-record framing (checkpoint limit plus80 bytes). Binding is
    a raw32-byte digest of the owner's root/path/generation/decoder contract.
    Keep the whole-record digest in separately trusted owner state at capture.
    A self-hash of supplied record bytes does not establish that provenance.
    Unpack checks exact binding, framing, digest and bounded checkpoint syntax;
    actual input/base-partition validation still requires restore. No filesystem,
    owner index, archive authority or automatic persistence is supplied. *)
val stage_metadata_bytes : max_bytes:int -> string -> Unix.file_descr -> string
(** Bounded80..max_checkpoint_size+80 metadata staging, fresh private0600 singly
    linked owned output only. Syncs/checks identity/size and returns intended SHA.
    Borrowed FD; no open/close/name publication or format/owner authority. *)
val write_checkpoint_record : binding:string -> checkpoint -> Unix.file_descr -> string
val read_checkpoint_record : expected_binding:string -> expected_record_sha256:string ->
  SemanticFile.t -> checkpoint
(** Borrowed-descriptor record storage. Write requires a fresh empty singly linked
    owner-private0600 regular output, uses bounded positional writes, syncs and
    checks its identity/size; returns the intended whole-record digest. Read bounds
    size, verifies the separately trusted digest and owner binding. Neither opens
    paths, closes FDs, publishes a name/index, nor supplies immutable access.
    Caller retains exclusive access/ownership, independently reads back before
    publication, and handles all errors/partial stages without automatic retry.
    A successful write is not a durable index or directory publication proof. *)
type metadata_quota
val metadata_reservation_bytes : int64
val prepare_metadata_quota : directory:Unix.file_descr -> max_bytes:int64 -> max_entries:int -> metadata_quota
val reserve_metadata_slot : metadata_quota -> Unix.file_descr -> bool
val metadata_slot_reserved : metadata_quota -> bool
val metadata_slot_name : metadata_quota -> string
(** macOS monotonic managed-cache admission, borrowed private0700 directory FD.
    Fixed2MiB payload reservation per capture; max_entries1..4096/max_bytes2MiB..8GiB.
    One immutable no-follow-read configuration symlink pins identical settings
    across cooperating owners; it is data, never followed. Atomic mkdir slots
    are never deleted/reused here, including failed/interrupted captures. Missing
    configuration over surviving slots refuses instead of resetting capacity.
    Reserve once per ticket: false means capacity exhausted; success consumes a
    slot. Native state records creation before later errors. Inspect reserved/name
    after error, retain any consumed slot, never infer rollback or retry a ticket.
    No FD opens/closes, payload creation, eviction or automatic cache activation.
    Caller must reserve before creating bounded cache payloads and never delete
    slots/config. Charge excludes filesystem overhead, source/staging outside this
    cache and RSS; this is admission accounting, not a physical filesystem quota. *)
val admit_metadata_stages : metadata_quota -> Unix.file_descr ->
  record_stage:Unix.file_descr -> entry_stage:Unix.file_descr -> unit
val seal_metadata_stages : metadata_quota -> Unix.file_descr ->
  record_stage:Unix.file_descr -> entry_stage:Unix.file_descr -> unit
(** One-use quota-bound paired stages in the reserved namespace: names are slot
    basename plus -record.tmp/-entry.tmp. Admit both fresh private empty distinct
    FDs before writes; seal the same identities after bounded writes, once only.
    Requires successful synced reservation, actual slot/directory identity and
    no-follow stage bindings. Borrows all FDs; no payload writes or closes. *)
type record_publication
val metadata_leaf_present : directory:Unix.file_descr -> name:string -> bool
val check_metadata_leaf : directory:Unix.file_descr -> name:string -> max_bytes:int ->
  Unix.file_descr -> unit
(** macOS known64hex-leaf no-follow lookup through borrowed private0700 directory.
    Presence reports any object, not valid content. Check binds a private0600
    singly linked regular FD to that leaf with bounded size and stable native
    metadata. No open/close/content read/write or hostile-writer exclusion. *)
val record_publication_available : unit -> bool
val prepare_record_publication : directory:Unix.file_descr -> stage:Unix.file_descr ->
  temporary:string -> expected_binding:string -> expected_record_sha256:string ->
  SemanticFile.t -> record_publication
val prepare_metadata_publication : directory:Unix.file_descr -> stage:Unix.file_descr ->
  temporary:string -> max_bytes:int -> expected_sha256:string -> SemanticFile.t -> record_publication
(** Same borrowed-FD immutable publisher, after bounded whole-stage SHA readback.
    Format and separately trusted owner/index binding remain caller duties. *)
val publish_checkpoint_record : record_publication -> Unix.file_descr -> Unix.file_descr -> unit
val record_published : record_publication -> bool
(** macOS immutable-record publication; directory and stage FDs are BORROWED,
    never opened/duplicated/closed or retained here. Keep them live, unreassigned
    and exclusively owned through settlement; do not share a ticket concurrently.
    Prepare verifies bounded record readback against separately trusted binding/
    digest, requires private0700 owner directory and private0600 singly linked
    regular stage, binds its no-follow temporary leaf, and requires absent target.
    Target is the record digest's64hex basename. Publish rechecks identities and
    full stage facts, syncs the stage, performs exclusive same-directory rename,
    checks the published object and requests directory sync. [record_published]
    records native rename success even if a later check/sync raises. Never retry
    a published ticket or remove its target after an error. Caller retains stage/
    directory ownership and closes them under its uncertainty protocol. No owner
    index advancement, hostile-writer exclusion, mount-incarnation or hardware
    power-loss durability claim. Unavailable platforms refuse, without fallback. *)
val with_checkpoint : expected_checkpoint_sha256:string -> expected_root_schema:string ->
  max_read_bytes:int64 -> SemanticFile.t -> string -> (session -> snapshot -> 'a) -> 'a
(** Authenticate metadata against the owner's prior trusted checkpoint digest,
    validate its bounded exact partition/schema, then rehash the complete current
    file before permitting cached component hashes in a fresh live session.
    Full-file verification is charged; subsequent refinement rereads only affected
    parents and preserves unrelated pixel hashes. This avoids recomputing each
    component digest, NOT the full input read. No epoch-only shortcut, immutable
    blob authority, archive trust source, disk writer, peer authority or automatic
    persistence is supplied. Wrong content/schema/digest refuses before callback. *)
val validate_base : session -> snapshot -> spec -> unit
(** Check a cached view against a freshly described base partition without payload
    reads. IDs, roles, extents and nonrefined schemas/children must match exactly.
    Only a base private/opaque leaf may retain a refined subtree, and that subtree
    cannot claim pixels or standard metadata. Requires the live bound session;
    this supplements authenticated restore, never establishes cache trust itself. *)
val reset_private_view : session -> snapshot -> component:string -> schema:string -> snapshot
(** Explicitly invalidate one refined private/opaque subtree before applying a
    different decoder/version. Preserves raw digest/extent/role, unrelated nodes
    and the previous immutable snapshot. Recomputes only view ancestors, with no
    payload read. Accepts private/opaque leaves too; refuses other roles and subtrees containing any pixel
    or standard-metadata claim. No bytes or preservation obligations are removed;
    interpretation can become unknown while a replacement decoder is pending. *)
