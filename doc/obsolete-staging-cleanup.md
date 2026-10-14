# Obsolete staging-leaf cleanup

The guarded producer uses `FinalPublication.clear_obsolete` before creating a
normal candidate or receiver-clone scratch sibling. Its prepared context pins
the logical root, working directory and candidate/target parents. Cleanup
verifies current resolution against these held identities, so a replaced
pathname parent cannot redirect removal. The supplied relative parent must
resolve to the candidate parent; arbitrary directory traversal is refused.

Absence is a no-op. An existing leaf must be regular and singly linked. Full
Darwin stat observations exclude only atime and are compared around binding,
sidecar and live-target checks before descriptor-relative unlink. Case and
normalization aliases are fenced by live-target device/inode identity as well
as exact spelling. No obsolete payload is opened, read or chmodded. This
preserves mode-000 cleanup under ordinary directory unlink permissions.

The operation is valid only before producer adoption. It neither adopts the
old leaf nor changes producer state. Resumed, newly created and frozen producer
objects continue to use retained output descriptors. Hardlinks, symlinks,
directories, other kinds and enabled sidecar families are preserved with an
error; the guarded path never selects recursive pathname cleanup on failure.
Transient directories close before native exception delivery, with the first
error retained. A close failure after unlink remains an error with an already
removed obsolete name, not permission to retry another backend.

This is cooperative namespace fencing. The old stat snapshot does not pin an
inode, and lookup/unlink is not an atomic compare-and-swap against hostile
writers. There is no mount-incarnation or crash-durability guarantee. Unbound
and explicitly handed-off legacy callers retain their original cleanup; safe
directory/auxiliary-family cleanup and other-platform implementation remain
open. The native operation is local and changes no RPC/archive format.

The [qualification](../tests/obsolete_cleanup/qualification.json) distinguishes
actual native syscall controls, unmodified-native actual Copy/CLI controls,
the existing publication/old-peer matrix, compiler checks and root-owned source
review. No Adobe/Photo operation or performance claim follows from it.
