# Checked transfer instruction framing

The production Copy streaming codec reads a five-byte file identifier and returns
a view of the original raw packet. `Remote.decodeInt` now explicitly checks the
complete fixed field before any array access; Copy computes its payload slice
only after that check. Correct encoded fields and packet tags are unchanged.

Both generic and rsync transfer decoders preflight the complete selected token
slice before token payload writes. The check validates the slice, string headers
and payload lengths, block headers and nonzero counts, known tags and terminal
EOF placement. It uses the supplied slice boundary, not merely backing-array
capacity. Empty slices remain valid non-EOF chunks. Generic transfer refuses
rsync block tokens. Malformed framing produces a typed transient error instead
of relying on an array exception or assertion.

Rsync also validates positive block size, per-block arithmetic and progress
headroom, and block offsets/counts against a lazily observed basis length before
invoking the copy callback. The size observation is shared within one instruction
rather than adding a metadata syscall to every inherited range. Actual fallback
reads must return every requested byte before that chunk is written. Partial
copy fallback counts must be within the requested range before offset arithmetic.
These guards preserve full and partial optimized-copy callback contracts.

Syntactic preflight precedes token writes/progress callbacks, but the caller may
already have opened or truncated its private output channel. Dynamic basis
change can occur after preflight; earlier valid tokens may already have written
staging bytes before a later block/read fails. This is not atomic validation
against hostile writers, a publication acknowledgement or source epoch proof.
The receiver's existing identity/fence/hash/publication lifecycle still applies.

## Qualification scope

`tests/transfer_instruction_bounds/run.py` compiles the full current Transfer
module plus exact current integer/Copy-codec fragments against compiler-matched
objects. Private guards stop old mutation participants before invalid array reads
or malformed token writes; they do not instrument production CLI builds. Original
small inputs exercise malformed framing, range/arithmetic/fallback refusal,
actual disposable-basis truncation, valid literals/blocks, partial/full callbacks,
a prepopulated receiver-basis skip, and production generic/rsync encoders.

These controls do not invoke an actual transport, APFS clone syscall, Adobe/SDK,
Photo source, canonical bulk-IO lane or production publication. The skip case is
a callback contract on a disposable prepopulated file, not physical sharing.
[Final evidence](../tests/qualification/transfer-token-framing-actual-20261018.json)
binds 118 checks and seven guarded negative participants per compiler, four
current stock/Ox Make/Dune builds/selftests and 14 RPC negative participants per
compiler. Superseded intermediate builds are preserved: review found an else-
branch grouping bug and an overbroad size guard before sealing; final multi-
buffer, later-short-read and actual-count cases qualify the corrections. Broader transport/filesystem/failure and
performance qualification remains in SOL's acceptance map.

## Resource scope still open

The sole production custom stream codec passes a raw buffer view; the raw packet
owner covers its synchronous callback. Token consumption can allocate temporary
literal strings (16-bit token length) and an 8192-byte rsync copy buffer, as well
as fixed metadata. That workspace and custom-decoder metadata are separate from
Umarshal selected-cost argument admission. No complete managed/native heap/RSS
or outbound lifetime cap follows from framing checks. Per-command producer queue
size enforcement, client results and the remaining baseline/containment work
still need explicit qualification; the endpoint's existing outer frame cap is
not a claim that every custom codec has its own tighter cap.


## Caller-bound logical output allowance

Copy now creates one opaque output allowance per payload before opening lazy
channels. Ordinary data and resource payloads use the expected source length;
resumed data subtracts the existing prefix after checking nonnegative lengths
and `prefix <= total`. Resource container headers are not payload bytes, so the
allowance does not depend on absolute output-channel position.

The preflight pass counts complete frame materialization, including inherited
block skips. It checks integer arithmetic and reserves that entire logical
count before token writes or optimized-copy callbacks. All frames share the
same allowance. EOF must exactly exhaust it, and later payload work refuses.
A reservation is not refunded after a write/callback failure; the operation must
abort rather than replay. The owner-loop allowance is not a native settlement,
actual byte-write observation or publication receipt. Copy checks logical EOF
before it can reopen lazy basis/output channels, independently of decoder checks.

This bounds protocol-directed materialization relative to the caller's declared
payload length. It does not bound arbitrary callback side effects, total job/
physical IO, metadata/container-header writes or actual heap/RSS. Output channel
creation can precede first-frame refusal; publication and original epoch/hash
checks remain independent. Existing default Transfer APIs remain additive;
callers outside Copy must explicitly pass an allowance to use this policy.

Original controls include oversized/short EOF, cross-frame debit, no refund on
failure, repeated block skips, invalid prefixes, a valid maximum-int64 prefix
metadata case, and actual multi-frame generic/rsync roundtrips. Resumed and
resource-header-offset cases exercise the real generic encoder with disposable
files; they are not an actual AppleDouble/native resource-fork or transport test.

[Output allowance evidence](../tests/qualification/transfer-output-allowance-actual-20261018.json)
binds 163 checks and nine negative participants per compiler, plus all four
current stock/Ox Make/Dune builds/selftests. Actual encoder checks span multiple
packets; Copy's helper and both call-site/pre-open bindings are source checked
and compiled. Native clone/publication/transport qualification remains separate.
