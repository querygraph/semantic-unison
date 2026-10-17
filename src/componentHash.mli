(** Bounded worker-local component hashing over an owner-controlled snapshot.
    All bytes stay covered. Roles are parser claims, never transformation or
    rendering-equivalence authority. No persistent/cross-session cache yet. *)
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
