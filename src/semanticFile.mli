type t
exception Invalid of string
type writer
val prepare_writer : ?check_cancel:(unit -> unit) -> Unix.file_descr -> writer
(** Borrow a private, singly linked regular output. Does not duplicate, close
    or own its FD. Keep the FD live and its flags stable, with exclusive output
    access, until the writer is retired. POSIX admission also rejects read-only
    and append-mode descriptors. On Windows, only kind/link checks are added to
    the existing seek/write backend; no new native Windows guarantee is made.
    EINTR admission retries check cancellation. Prepare even for an unchanged
    plan. No mount, immutable-content or hostile flag-mutation proof. *)
val write_at : writer -> string -> int -> int -> int64 -> int
(** One bounded write attempt, at most 64 KiB; checked slice and absolute offset.
    POSIX uses native pwrite without changing the shared file position. Input is
    copied into native stack storage before runtime release. Windows retains
    seek/write, which changes that position. The caller owns short-write/EINTR /
    cancellation looping; operational failures never select another backend.
    Input strings must remain immutable during the call. Neither entire-file
    inspection nor materialization is promised to preserve FD positions. *)
val with_fd : ?check_cancel:(unit -> unit) -> Unix.file_descr -> (t -> 'a) -> 'a
(** Duplicates a caller-owned regular descriptor. Use only in one worker;
    the duplicate shares its file position with the original descriptor.
    The optional worker-local cancellation check runs before opening, reading,
    each 64 KiB iteration, and final stability checks. *)
val size : t -> int64
val check : t -> unit
val same_inode : t -> Unix.file_descr -> bool
val read : t -> int64 -> int -> string
(** Checked, exact read, at most 1 MiB per call. *)
val iter : t -> int64 -> int64 -> (bytes -> int -> unit) -> unit
val digest : t -> string
