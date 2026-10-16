# Compact common DNG merge bases

Enable the existing built-in scalar policy and local compact capture before
synchronizing the common version:

```text
semanticmergebasecache = true
merge = Name *.dng -> unison:dng-xmp-scalars/0
```

On the command line, use `-semanticmergebasecache` or
`-semanticmergebasecache=true`; a separate `true` is not a Boolean argument.
`backupcurrent` remains an independent preference for preserving full versions.
Compact bases do not replace general backups or preserve old image payloads.

Capture borrows one stable regular file without a resource fork. It computes
Unison's legacy data fingerprint from that held descriptor, restores its cursor,
and inspects the same descriptor through the checked workers. Name/held-file
identity and stability are checked around both operations. The cache stores the
lossless XMP packet, full content and protected-complement SHA-256 identities,
geometry, profile, scalar-policy/parser versions, and a canonical parsed view
(scalar names/spans/normalized-value hashes and the unedited shell hash).
It stores no image payload. Hashing still reads the full common file; this is a
storage improvement, not a measured capture-speed improvement. Legacy MD5 runs
on the owner under one CPU credit; metadata inspection uses the shared pool.

The previous archive entries must agree before merging. Only their non-pseudo
common fingerprint, local root and logical path select a base. An unchanged
content fingerprint can be reused across archive generations; a changed common
fingerprint selects a different record. Neither currently edited replica can
supply a guessed base. Lookup reparses the packet with the current version and
checks the stored parsed representation. Normal scalar reconciliation still
checks both replicas' protected bytes/layout, reinspects the live left file and
materializes one exact result through the existing merge/validation/copyBack
lifecycle. Partial second-receiver failure retains the original base for retry.
If an older Unison updates the common version without compact capture and no
full backup exists, its new archive fingerprint cannot select an older cached
base. A later conflicting merge is refused with a recoverable missing-base
diagnostic, preserving both edits. Re-enable capture before synchronizing the
next common version; reopening unchanged files alone does not create that base.

Records live in the endpoint's Unison state directory under
`semantic-merge-bases-v1`, sharded by the first three hex digits of the binding
key. Directory/shard ownership and mode 0700, regular-file ownership/mode 0600,
single-link status, size, held/name stability and checksums are required.
Record lookup does not trust symlinks or peer-supplied records. This is trusted
local state like the archive: checksums detect corruption, not an attacker who
can rewrite that user's private state. Publication writes/fsyncs an owned
exclusive temporary, then links without replacing an existing base. A crash
leaving a second link or a missing entry produces a cache miss; no crash/fsync
survival guarantee follows. Each shard's scan is bounded to 4096 entries; full
shards decline new capture without evicting recovery bases.

New captures also reserve charged payload bytes and one entry in the owned
`.quota-v1` ledger before creating a record. The default ceilings are 1024 MiB
and 1,048,576 reservations. Endpoint-local `semanticmergecachemaxmib` accepts
1..65536 MiB and `semanticmergecachemaxentries` accepts 1..16777216 reservations.
Cooperating processes sharing a state directory must use the same settings.
Calls remain on the sole Lwt/archive owner; POSIX locks serialize processes,
not concurrent threads within one process. This module is not a worker task.
An exclusive nonblocking POSIX file lock serializes reservations across processes;
a busy owner declines capture instead of blocking Unison's Lwt owner. A new
counter is written and fsynced before record creation. Reservations are never
returned, including failed or interrupted captures: overcount can stop capture,
but does not evict a recovery base. Existing identical records do not charge twice.
This deliberately bounds new managed payload and reservation count, not filesystem
metadata, physical block allocation, legacy data, process RSS or hostile same-UID
writers. Snapshot rollback and storage that violates fsync ordering are outside
this cooperative accounting contract.

The 79-byte ledger is `SBQ1 `, a zero-padded 20-digit decimal reservation count,
one space, a zero-padded 20-digit charged-byte count, newline, then SHA-256 of
those first 47 bytes. Corruption, invalid permissions/link/type, counter overflow,
capacity exhaustion and ambiguous initialization refuse new capture. A missing
ledger initializes only over an empty managed tree (empty private hex shards are
allowed); surviving records or temporaries prevent automatic counter reset.
No scanner deletes records or reconstructs a guessed allowance.

Older `semantic-merge-bases-v0` records remain a read-only fallback with the same
previous-common binding and trust checks. New code never writes or charges that
legacy tree, so it does not promise a size bound on already retained v0 data.
Neither tree is automatically removed. Lowering a ceiling below its monotonic
charge stops new capture while leaving existing bases readable.

Capture is best effort and skips a busy global resource gate to avoid recursively
waiting on a retained publication lease. Unsupported input, capacity/storage
failure or a lost capture can therefore leave no base. Lookup misses, stale
binding, disabled/incompatible policy, invalid permissions or damaged records
retain the verified full-backup fallback when available; otherwise the merge
declines and preserves the conflict. All previous fixed-region/scalar limitations
remain, including refusal of growth, deletion/addition, image/rendering/unknown
changes and resource forks. Cache capture and lookup consume the existing
resource/CPU budget; complete process RSS/FD and capture-I/O lifetime qualification
remain broader M6 work.

The option defaults off and is endpoint-local. No cache or archive data is sent
as a new wire feature and the archive format is unchanged. Remove this preference
and any `semanticmergecachemaxmib`/`semanticmergecachemaxentries` settings,
plus the reserved built-in merge command, before downgrading to a baseline binary;
its archives/backups remain readable and the cache can remain unused. The cache
implementation is disabled on Windows and qualified here on macOS only.

[Qualification](../tests/semantic_base_cache/qualification.json) uses original
DNG-shaped containers and mock validation. It establishes no Adobe decoding,
photographic rendering, preview reuse, SDK single-file parallelism or full goal
completion. Photo Root retains all preview/native work.

## Inner SDB/1 record

All lengths/offsets are unsigned big-endian 64-bit restricted to signed-int64 range.
The canonical sequence is 8-byte magic `SDB 00 00 00 00 01`, length+policy/parser
string, length+canonical SDR/0 description with a zero 32-byte nonce, length+full
XMP packet, length+parsed view, then SHA-256 of every preceding byte. The view is
shell SHA-256, scalar count, then ordered scalar name length/name, normalized
value SHA-256, first and last packet offsets. It is regenerated from the packet;
a checksum-valid disagreement rejects. Inner record limit is 1 MiB+8192+256 bytes,
packet limit 1 MiB, parsed view 4096 bytes. This is an experimental local format,
not transfer authority or a remote merge-base protocol.

The owner SBC/0 envelope is 8-byte magic `SBC 00 00 00 00 00`, 32-byte binding key,
SDB record and SHA-256 of all preceding bytes. The key hashes unambiguous
decimal-length-prefixed fields: SBC/0, local root, logical path, legacy full
fingerprint string, scalar policy and parser=1. Owner provenance checks and the
current previous-common archive are required in addition to either checksum.
