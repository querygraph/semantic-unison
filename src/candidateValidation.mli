val enabled : unit -> bool
val unchanged_file_with_validators : validators:CandidateValidator.selected list ->
  staging_directory:Fspath.t -> source:Fspath.t -> destination:Path.local ->
  max_bytes:int64 -> unit Lwt.t
(** Same lifetime as [unchanged_file], with owner-captured callbacks/settings
    retained for a complete scan instead of reselecting policy per file. *)
val unchanged_file : staging_directory:Fspath.t -> source:Fspath.t ->
  destination:Path.local -> max_bytes:int64 -> unit Lwt.t
(** Internal unchanged-file entry, not scan selection or an enabled scope.
    Off selects no companions and opens nothing. Otherwise hold one bounded
    snapshot/backend envelope; recognize through the held read-only source
    before copying. Nonmatches skip full hashing/copying even above max_bytes.
    Selected files are validated only through a private snapshot in an existing
    owned0700 staging_directory. A one-file local gate partitions the existing
    envelope, never reacquiring global admission. Original/stage fences, final
    snapshot hash and actual callback settlement precede cleanup.
    Inspection/recognition borrow the stage's held output descriptor, not a
    separately reopened pathname. Execute groups filesystem admission from that
    descriptor. Separate readonly artifact inspection supports driver/limiter
    hashing; original-inode inspection is refused, including pathname aliases.
    The descriptor owner remains live across the entire callback promise.
    Unknown stage cleanup retains its owner/admission; existing worker/reader close-fault
    limitations remain separate. Resource, staging and integrity errors do not
    become permissive validator warnings. Regular nonsymlink source required. *)
val before_commit : directory:Fspath.t -> candidate:Path.local ->
  destination:Path.local -> unit Lwt.t
(** Validate finalized private received candidates, including descendants of
    staged directory trees, before any rename/archive mutation. Extension-owned
    policy/recognizers select validators by destination claim or file contents,
    independently of semantic transfer enablement and eligibility. *)

val before_commit_with_reservation : reservation:SemanticAdmission.reservation option ->
  directory:Fspath.t -> candidate:Path.local -> destination:Path.local -> unit Lwt.t
(** A bound receiver loans its retained envelope for serialized file validation,
    including explicit legacy directory handoff. Unbound trees use fresh per-file
    admission. With positive [validationtreememory], reserve both bounded
    retained-manifest estimates and fixed parallel file workspaces before
    enumeration. A local gate partitions held credits, never acquiring another
    global lease. Existing bound receivers remain serialized. With zero budget,
    manifests retain legacy unadmitted accounting. Initial property reading /
    serialization, SDK allocations and process RSS are not allocator-enforced.
    Helpers/worker jobs settle before returning. *)
