# Guarded rsync receiver clone ownership

Guarded producer tickets now select the owned native publication backend for
network rsync clone staging. Legacy/older-peer receivers keep the original API.
This is the receiver implementation and codec lifecycle qualification; it is
not a new actual transport run or a universal raw/channel close-error proof.

A receiver adapter captures loose clone descriptors, consumes the actual parent
through native adoption, then transfers the pair to tracked channel objects.
It attaches the enrolled range lease to the publication owner. Normal EOF still
flushes and truncates to the exact incoming length, checks the lease, exclusively
publishes the stage, adopts the actual producer descriptor and disarms the name
owner. No partially patched clone becomes an ordinary resumable prefix.

Preprocessing and each decoder invocation borrow the owned publication. Progress
callbacks may run connection cleanup: cleanup first invalidates range authority,
requests interruption, and defers native/channel closure until the borrower
settles. An intrusive preallocated active-owner list lets channel registries
recognize protected channel objects without relying on numeric descriptor reuse.
Normal EOF's deferred close is distinct from connection interruption and does not
turn successful completion into a cancellation. Normal closure unlinks its active
node without allocation. Unknown native closure retains the scope, reservation,
remaining channels and native carrier; failed cleanup cannot turn it into a known
failed-prefix release.

Original small controls execute actual Transfer.Rsync preprocessing, compression,
framing, decompression, Copy copyFn behavior, APFS clone staging, range lease,
native publication and admitted TargetBinding completion. Only compressRemotely
is substituted with in-process sender delivery through the actual receiver map.
No sockets, server process or SDK run. The normal cases include changed data,
growth, shrinking EOF and fully inherited bytes. Composed cases inject adoption/
disarm close errors and connection cleanup from inside a decoder progress callback,
checking lease invalidation and no early close while borrowed. A separate known
cancellation case checks normal reservation retirement. Both injected unknown
application owners intentionally remain until their disposable process exits;
external process/group closure is a separate observation.

Existing bound local clone controls are rerun because they share the active-owner
and borrower mechanism. Source/live bytes and metadata remain unchanged. Actual
transport/client/server/pump verification, legacy named/unbound staging and raw/
channel close uncertainty still need their separate evidence and, where required,
fresh admission. No Photo/camera/bulk IO, SDK, physical-sharing, throughput, hard
resource cap, production commit or automatic successor claim is made here.
