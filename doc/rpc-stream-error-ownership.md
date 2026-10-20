# Retained stream error ownership

The owner-loop stream error table has two independent endpoint-local limits:
`rpcstreamerrorslots` (default256, maximum65536) and `rpcstreamerrorbudget`
(default8MiB of selected known string fields). Count includes errors already
removed from the table but still borrowed by an actual ping reply. New stream
work refuses without waiting when capacity is exhausted; chunks for an already
aborted ID continue the existing abort handshake without another admission.

Standard diagnostic exceptions retain their exact value and existing abort/ping
behavior: `Transient`, `Fatal`, `Failure`, `Invalid_argument`, `Sys_error`,
`Unix_error`, match/assert failures, and the listed constant builtin exceptions.
Known string fields are charged without copying. Custom exceptions can contain
arbitrary graphs whose cost is unknown: they propagate unchanged immediately
instead of entering this persistent table. They are not translated to a fake
bounded diagnostic. Recognized ownership uncertainty takes the existing retained
body path before ordinary error admission.

Ping borrows the error before dispatch, and its scope spans response marshaling
and actual queued output consumption. Known settlement removes any remaining
matching table entry and releases once. Disconnect/reset releases only unborrowed
table entries; it cannot revoke an outstanding ping consumer. Recognized scope
uncertainty retains the entry and selected debit in a prepared root. Duplicate
stored IDs and duplicate borrowers refuse without replacing the original owner.

These are persistent owner-count/selected-string limits, not limits on creating
an exception, all exception/promise/node memory, general outbound buffers, custom
workspaces, allocator/RSS peaks or OS/native resource ownership. Converted/global
escapes and legacy decoded client results remain separate work.

Directed controls exercise exact byte/count boundaries, pre-handler refusal,
standard exception identity, unknown-cause propagation, actual ping output,
borrowed reset, duplicate ownership and synthetic typed uncertainty. Seven
mutations test those boundaries. All four stock/Ox Make/Dune+selftest builds and31 designated negative controls
per compiler passed, with all581 recorded build inputs and tested source hashes
matching. [Actual evidence](../tests/qualification/rpc-stream-error-ownership-actual-20261018.json)
preserves earlier fixture and compatibility failures plus the corrections;
no new transport/SDK/Photo payload/production acceptance is implied.
