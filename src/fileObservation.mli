(** Fresh facts about an endpoint-owned open descriptor. This is not a content
    snapshot, a capability guarantee, a mount-incarnation token or a pathname
    publication check. The caller must retain the descriptor until observation
    completes and must not close/reassign it concurrently. *)

type t = {
  device_id : string;
  file_id : string;
  kind : Unix.file_kind;
  size : int64;
  link_count : int64;
  file_flags : int64;
  filesystem_id : string;
  mount_flags : int64;
  volume_uuid : string option;
  mtime_seconds : int64;
  mtime_nanoseconds : int;
  ctime_seconds : int64;
  ctime_nanoseconds : int;
}
(** macOS identifiers are lowercase, fixed-width hexadecimal without prefixes:
    device_id has 8 digits, file_id 16, filesystem_id 16 (the two native 32-bit
    words in order), and a present volume_uuid 32. A missing/zero UUID is None;
    it must not be promoted to a persistent volume identity. File and mount flags
    preserve their unsigned 32-bit values in int64. *)

val observe : Unix.file_descr -> t
(** Observe file facts with fstat, filesystem facts with fstatfs and volume UUID
    with a separate fgetattrlist request. Recheck native identity and metadata
    after querying the filesystem. A detected concurrent change fails with
    Unix_error EBUSY; operational or malformed-attribute failures raise phased
    Unix_error and never become a weaker successful observation. No descriptors
    are opened/closed and file offsets are unchanged. Non-macOS raises ENOSYS.

    Equality does not prove stable file bytes or a mount lifetime. File writes
    legitimately change timestamps; owner generations, immutable basis proofs,
    placement policy and fresh precommit path checks belong to the caller. *)
