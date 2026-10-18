# Caller-owned decoded allocation admission

The additive `Umarshal.from_bytes_accounted`, `from_channel_accounted`, and
`unmarshal_from_bytearray_accounted` readers accept mandatory local byte/element
bounds and a caller-owned incremental reservation callback. Local bounds are
checked first. The callback runs before each selected builtin allocation;
refusal propagates unchanged, without retry or refund. Existing reader entry
points and valid wire encodings are unchanged.

The caller owns every accepted debit, including charges preceding a later
failure. Parsing completion and garbage collection do not release it. The
callback must obey the caller's thread/domain ownership rules. Logical selected
charges exclude framing/context overhead, recursive stack depth, user mappings
and conversions, and full heap/RSS. This API does not impose an OS memory cap.

## Actual qualification

[Evidence](../tests/qualification/umarshal-accounting-hooks-actual-20261018.json)
binds 78 original tiny-value checks and two mutation participants per compiler.
Private test instrumentation at the string and bytearray allocation sites
rejects allocation before reservation. Removing the callback or moving string
reservation after allocation causes designated failures. No production source
instrumentation is used in the CLI builds.

Both stock OCaml and OxCaml passed Make and Dune builds/selftests, and the
existing 233 decoder framing/bounds checks per compiler passed. Production
inputs match those build inventories. The test probe alone changed afterward
to add ordering witnesses; final probe checks passed separately. An initial
fixture ordering failure is preserved rather than rewritten as success.

## RPC integration remains open

`Remote.boundedMarshalingFunctions` currently supplies per-decode limits;
ordinary marshaling remains separate. Raw packet tickets bound raw buffers,
not decoded objects. The new callback is not yet installed into RPC dispatch.

Scoped server registrations now decode arguments once and pass the same value
to scope admission and the handler. The internal server continuation includes
queued reply consumption; the existing once-only dispatch guard and distinction
between pre-dispatch scope refusal and post-dispatch failure remain. This
removes duplicate argument expansion; it does not itself charge decoded values.

A correct integration still needs an explicit decoded-value owner:

1. Reserve a finite owner slot before decoding, and charge its aggregate budget
   through the callback, retaining all partial charges on failure.
2. Hold request arguments through actual handler settlement and serialization
   of results that may share argument storage. Retain uncertainty with the
   existing ownership carrier rather than turning it into an ordinary error.
3. Give returned client results an explicit caller scope or lease. Results can
   outlive parsing and share tails or views; releasing at decoder return or
   attaching a finalizer only to the root does not prove the storage is dead.
4. Cover stream callbacks, synchronous decode, queued replies, conversion
   failures and post-decode handoff failure, with admission before allocation.
5. Keep selected-cost admission distinct from complete managed/native memory,
   transport overhead, allocator retention, and platform hard containment.

No endpoint-wide decoded liveness bound is claimed until those ownership
transfers are implemented and qualified. The full SOL resource requirement
remains open; this checkpoint supplies its preallocation admission mechanism.

## Concrete next ownership boundary

For bounded server arguments, registration can supply a decoder continuation
that takes the existing raw body and invokes `use args` once. Its owner must
span both `withScope` and dispatch; dispatch includes the reply's actual output
queue settlement. The new single-decode server continuation provides this
boundary without a dynamic global "current decoder" variable, which would be
unsafe under nested or interleaved RPC work.

The aggregate owner needs independent finite slots, selected bytes and element
counts, with nonwaiting overflow-safe reservation before decoding. It must keep
partial debits after an ordinary decode failure until that invocation settles;
recognized borrower uncertainty must retain the owner alongside the existing
raw-body owner. Slot and accounting metadata are separate baseline costs. A
result can share argument storage through marshaling, so the reservation cannot
end at handler return. No production arbitrary-result caller release mechanism
has been implemented by this checkpoint.

A server request scope alone does not solve client result lifetime, conversions
that retain global state, legacy streaming registrations, outbound allocation,
or complete process memory. Those remain explicit completion items rather than
being silently covered by a request-scope counter.
