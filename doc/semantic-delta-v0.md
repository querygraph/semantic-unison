# Semantic Delta Envelope 0 (experimental)

This is an experimental exact-byte transfer profile, not an adopted standard.
It complements existing rsync/VCDIFF binary deltas with named format policies,
complete preservation proofs and a receiver commit contract. The implementation
is `src/semanticDelta.ml`; synthetic conformance tests are in `tests/semantic`.
Experimental local and remote DNG transfer are implemented. Remote peers
negotiate `semantic-delta-v0` and `dng-xmp-v0` and require RPC version 1;
unmodified peers fall back to ordinary transfer without an archive change.

## Contract

An envelope describes same-size replacement of explicitly editable ranges in
an exact base file. The target must match its whole-file SHA-256. Every byte
outside these ranges is retained at its original offset. Version 0 implies
policy `exact`, hash `sha256` and WRITE-only operations. There are no optional
fields, paths, commands, URLs, insertions, or dependency chains. A new policy or
encoding needs a new version; semantic merging is not part of version 0.

All integers below are unsigned 64-bit big-endian. Values above `2^63-1` are
rejected. Hashes are raw 32-byte SHA-256, not hexadecimal strings. Offsets are
zero-based byte offsets in the data fork; resource forks and filesystem
properties remain the synchronizer's separate responsibility.

| Field, in wire order | Bytes | Meaning |
| --- | ---: | --- |
| Magic/version | 8 | `53 44 45 00 00 00 00 00` |
| Profile length | 8 | 1..128 |
| Profile | profile length | Exact registered identifier, currently `org.firstpair.dng-xmp/0` |
| Transaction nonce | 32 | Receiver transaction binding; not authentication |
| Base and target length | 8 | One shared length; version 0 cannot resize |
| Base SHA-256 | 32 | Entire base data fork |
| Target SHA-256 | 32 | Entire target data fork |
| Preserved SHA-256 | 32 | Domain-separated transcript defined below |
| Operation count | 8 | 1..64 |
| Operations | variable | The records below, ascending by offset |

Each operation is `offset:u64, length:u64, old_sha256:32, new_sha256:32,
payload:length`. Length is 1..1,048,576. Total payload is at most 16,777,216 bytes;
total envelope is at most that plus 65,536 bytes. No trailing bytes are allowed.
Operation extents must be within file bounds and must not overlap. Adjacent
extents are permitted. Zero-length files cannot have a valid version-0 plan.
The core requires the exact region list returned by the locally installed
profile, including packets whose contents happen to be unchanged; an untrusted
sender cannot authorize a new writable extent by naming it in an envelope.

The decoder checks framing, arithmetic, limits, sorted extents and replacement
hashes. It does not authorize a plan. Before writing, the materializer resolves
the exact local profile, parses the actual base again, recomputes the complete
base and preservation proofs, and checks old-range hashes and region identities.
It repeats the base checks on the private staging file. The immutable basis and
staging must be different inodes; staging must be a single-link regular file.
Only then may it overwrite the ranges and verify the complete target digest.
The current materializer writes only differing absolute 4 KiB comparison
windows within those ranges, clipped to editable boundaries and coalesced when
adjacent. Its report counts actual logical write bytes and syscall attempts;
packet transport still carries the complete declared regions. This local write
policy does not change SDE/0, permit writes outside the regions, or promise a
filesystem allocation unit or physical write saving.

## Preservation hash transcript

SHA-256 is fed the following concatenation, with no implicit encoding:

1. ASCII `SDE/0-preserved` followed by one NUL byte.
2. File length as u64, then region count as u64.
3. For every editable region: offset as u64, length as u64.
4. For every complementary interval, in order: offset as u64, length as u64,
   then the exact bytes of that interval.

The complementary intervals are `[0, first.offset)`, every gap between editable
regions, and `[last.end, file.length)`. Include empty intervals in the transcript
with length zero. Thus identities bind placement as well as contents. Unknown
tags, unused padding, previews, embedded originals and opaque trailers are never
silently omitted from byte preservation. A profile can decline files whose
pointer/alias structure it cannot establish safely.

Example: a 100-byte file with editable `[10,15)` has header lengths `100,1`,
region descriptor `10,5`, then complement records `0,10,<10 bytes>` and
`15,85,<85 bytes>`, all integers encoded as eight big-endian bytes. Its operation
offset begins `00 00 00 00 00 00 00 0a`, and length is
`00 00 00 00 00 00 00 05`. No XML reserialization is performed; payload bytes
must be copied exactly from the target packet.

## Transport and commit requirements

The receiver sends a separate compact `SDR/0` description. In order: eight-byte
magic `53 44 52 00 00 00 00 00`, nonce (32 bytes), profile length (u64) and profile,
file length (u64), whole-base SHA-256 (32), preservation SHA-256 (32), region
count (u64), then each region's offset (u64), length (u64), and old SHA-256 (32).
It contains no packet contents. The request limit is 8,192 bytes; identifiers,
regions and aggregate lengths have the same bounds as the response. Reject
zero count, unsupported ranges, trailing bytes, and malformed integers.

`semanticPlanV0` uses existing Umarshal framing to carry a source pathname
(maximum 16,384 bytes) and this bounded description. Its result is an optional
canonical SDE/0 envelope. `None` means ordinary transfer should be used. The
receiver retains its local proof and checks response nonce, profile, size,
whole-base hash, preservation hash, and every old-region descriptor/hash before
materialization. The nonce comes from the receiver's OS random source.

The additive `Remote.registerBoundedServerCmd` checks command request and
pending-response body lengths **before** allocating their body buffers. The
request body cap is 16,384 + 8,192 + 1,024 bytes; the response cap is 16,777,216 +
65,536 + 1,024 bytes. Each request narrows its response cap to the selected
profile's declared payload ceiling plus 65,536 + 1,024 bytes; DNG therefore
permits at most 1,048,576 + 65,536 + 1,024. `Umarshal.bounded_string` also checks individual field
lengths before allocation and retains the existing string wire encoding.
These are bounded messages, not an assertion of constant-size streaming for
all Unison RPCs. Shared legacy message-header decoding precedes identification
of the command and remains outside these new body limits. Tests send only a
header declaring a 1-GiB body and verify rejection before body reads/allocation.
The standalone decoder alone only checks a string already supplied by its
caller; arbitrary applications must supply their own bounded input framing.
Source resource leases remain held through marshaling and output consumption;
closing the connection settles queued replies and pending request promises.

Current local materialization uses a zero nonce because no peer
request/response exists; it must not be reused for remote transaction binding.

Only core-owned private staging may be modified. Verify source stability,
finalize source-selected properties/forks, perform any requested validator,
retain destination rechecks, and use the existing rename/archive lifecycle.
An atomic rename is not a compare-and-swap against external editors. No claim
about physical disk writes follows from a logical patch or a successful clone.

Reject stale bases, changed opaque bytes, unsupported profiles, unknown
versions, out-of-order/overlapping/out-of-bounds extents, bad hashes, aliased
staging, mutation during inspection, truncated input, and trailing garbage.
Unsupported eligibility falls back before writing; verification failures after
planning are errors and cannot commit. Hashes are integrity checks, not peer
authentication. Unison archive fingerprints remain unchanged.

Profile identifiers in both SDE and SDR must be nonempty, at most128bytes, and
contain no NUL byte, matching the locally registrable format identifier domain.
Unknown nonempty NUL-free identifiers can decode, but still require exact local
registry resolution before any authorization or write. Decoder rejection is not
a substitute for profile selection or content/proof validation.


An SDR proof contains no replacement packet contents. The source may use that
unverified proof as the base claim when planning against a fully inspected local
target. A decoded SDR proof cannot be used as the target: `plan` rejects a target
whose retained contents do not exactly fill each editable region. This check
prevents a local caller from emitting an envelope whose declared region length
has no corresponding payload; it does not authenticate a peer's base claim or
replace receiver-side verification and authorization.
