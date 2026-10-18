# Joint compact-base cache ownership

`SemanticMergeCache` prepares a rooted synchronous scope before opening cache
resources. Each file node contains an opaque `NotificationPipe` single-read
ledger and is linked before `Unix.openfile`; adoption follows the returned FD
immediately. Each directory node is linked before `DirectoryOwner.open_with`.
Opaque directory handles never become guessed numeric descriptors.

Known operations close each resource at its existing lifecycle point. On an
ordinary operation failure, joint cleanup attempts every independent remaining
file and directory close once, preserving the original error in their ledgers.
Any uncertain close keeps the scope and its evidence rooted. A nested uncertain
scan leaves its still-known outer directory and quota descriptor held; it does
not release them while unwinding. Repeated cleanup does not retry historic
numbers or directory handles. Enabled future cache operations refuse before
acquisition while any process-local cache scope is retained, avoiding new cache
opens/closes against an unresolved quota/namespace lifetime.

The carrier is an existing `NotificationPipe.Uncertain` on a prepared scope
anchor. The anchor itself need not contain an OS descriptor: it roots the joint
cache evidence and lets the earlier runtime layer retain transaction admission
without a module dependency cycle. Its underlying cause and all per-file and
per-directory causes remain separately inspectable. `load` catches only its
ordinary compatibility/missing/corruption errors; ownership uncertainty cannot
become a cache miss or authorize a saved-file fallback. Full asynchronous
capture/scalar-merge guards retain their input scopes as well.

The temporary candidate path and opening phase exist before exclusive creation.
Interruption after FD adoption but before the caller resumes is reconciled from
the prepared ledger, so it cannot silently forget the created name. A known
open failure does not authorize removing a colliding path. The original inode
is observed before close; cleanup checks the current name against that identity
before unlink. An unavailable/mismatching identity or thrown unlink preserves
the namespace journal and raises the retained carrier. The unlink authority is
consumed before the syscall, and no repeated cleanup retries it. These are
cooperative same-UID private-state checks, not an atomic hostile-namespace
security boundary.

Quota framing, checksum, nonblocking locking, trust checks, bounded directory
scans and monotonic entry/byte charging are unchanged. Failed captures may
consume capacity; recovery bases are never evicted to reclaim it. Retaining a
temporary file after uncertainty does not roll its charge back. This quota is
not a filesystem allocation or process RSS bound.

The directed private controls preserve complete compiler-matched production
implementations, substituting close/unlink calls and body interruption points.
A private alias of `DirectoryOwner` allows opaque-handle injection without
inventing numeric FD identity. Twenty scenarios per compiler include known
storage, before/after-kernel file and directory closes, FD recycling, nested
quota scans, combined original/quota/directory failures, temporary acquisition
interruption, uncertain unlink, name replacement, and full async capture/merge
propagation. Every retained scenario rejects fresh cache work and repeated
cleanup. A deliberately close-swallowing participant must fail the designated
retention assertion. Unknown fixtures end at process exit, not normal native
teardown.

Existing acquired-resource exception, storage/quota, full capture and scalar
merge, and merge-error regressions run separately. All data is generated private
synthetic DNG/state. No camera input, Adobe SDK, Photo cache, real transport,
canonical EXglobal IO admission or aggregate descendant FD/RSS claim is involved.
The immutable qualification receipt records actual owners and the exact scope.
