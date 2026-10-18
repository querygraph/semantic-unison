# Correct output slice counts

RPC marshaling output triples are `(buffer, offset, length)`. The inherited
`fillBuffer2` helper interpreted its final parameter as an absolute end, but
`fillBuffer` passed the count unchanged. The actual original-source golden
`(__abc__, 2, 3)` fails the exact `abc` expectation. This source issue is also
present in the pinned upstream baseline; no upstream patch is proposed.

The successor validates the complete list before copying its first byte and
validates each dump before queuing it. Bounds use subtraction before calculating
`offset + length`; cumulative counts reject integer overflow. The internal
helper receives the checked absolute end. An empty slice performs no copy and
does not itself flush an already-full output buffer. Explicit urgent/final
flush behavior remains in its existing caller.

Stock/Ox controls compare exact49,161-byte output through a real private pipe,
across three buffer boundaries, using direct fill plus normal, idle and urgent
queue paths. Actual production `maybeFlush` promises are recorded and awaited
before closing descriptors. Read/copy/write primitives are not replaced. Eight
safe mutations cover count/end confusion, missing whole-list/prequeue checks,
empty flushing, arithmetic and bounds. The original failing golden and the
fixture's initial failed-promise observation correction are preserved.

All four current stock/Ox Make/Dune builds and selftests passed, with all582
recorded source/compiler/executable hashes checked. The full grouped suite passed
39 designated negatives/compiler. [Actual evidence](../tests/qualification/rpc-output-slices-actual-20261018.json)
binds the receipts and owning tool terminal. No Photo payload or SDK was used.

This fixes byte semantics and validates slices; it does not reserve encoded
allocation before serialization, cap queued owner/byte retention, account for
aliased backing storage, or supply a whole-heap/RSS bound. Those remain separate
[outbound ownership work](rpc-outbound-ownership-design.md). Earlier V3 source
requests were explicitly deferred and preserved; current transport qualification
requires a fresh fixed-source request and finite Root IO scheduling.
