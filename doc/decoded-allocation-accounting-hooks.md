# Caller-owned decoded allocation admission

The additive `Umarshal.from_bytes_accounted`, `from_channel_accounted`, and
`unmarshal_from_bytearray_accounted` readers accept mandatory local byte/element
bounds and a caller-owned incremental reservation callback. Local bounds are
checked first. The callback runs before each selected builtin allocation;
refusal propagates unchanged, without retry or refund. Existing reader entry
points and valid wire encodings are unchanged.

For the standalone Umarshal API, the caller owns every accepted debit, including charges preceding a later
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

## Regular server argument owner

Regular server registrations, including bounded registrations, now use a
caller-owned decoded owner around the scope,
handler, marshaling and actual queued-output continuation. The endpoint-local
policies are independent of raw packet reservations:

| Policy | Default | Admission |
| --- | --- | --- |
| `rpcdecodedrequestbudget` | 256 MiB | Aggregate selected builtin charges |
| `rpcdecodedrequestelements` | 1,048,576 | Aggregate collection element count |
| `rpcdecodedrequestslots` | 256, maximum 65,536 | Owner slot before decoding |

Ordinary `registerServerCmd` arguments use the finite owner policy as their
local decode limits; Host/Root wrappers inherit this path. A sparse collection's
valid encoding can be much smaller than its allocation, so this path does not
impose a guessed wire-expansion ratio. Explicitly bounded registrations retain
their additional declared frame-derived local limits. Both paths charge the
same aggregate lane and keep the existing tag/codec wire encodings.

These policies can refuse previously accepted large valid legacy requests.
That is explicit admission failure, not wire incompatibility or an unbounded
fallback. Operators can configure the endpoint-local limits for their workload;
raising a limit does not turn selected charges into a hard RSS guarantee.

All limits are positive; MiB conversion is checked for integer overflow. No
credit wait is introduced in the receiving loop. Each callback checks both
byte and element headroom before changing either debit. A reduced policy
refuses new charges without shrinking existing reservations. Ordinary decode
refusal settles its partial debit. A recognized uncertain borrower retains the
owner rather than producing an ordinary failed-prefix release.

Arguments decode once, and the scope and handler receive that same value. A
preallocated retained-owner link explicitly roots the decoded value: a failed
promise carrying an exception alone need not retain its old arguments. Live
requests also keep the value until actual handler/output settlement, including
across disconnect while a handler remains asleep. Typed uncertainty in the
original controls opens no directory/FD and retains its logical owner until
test-process exit; that is not normal in-process teardown.

The original reservation callback tests remain valid. The RPC owner controls
add byte/element/slot refusal, partial-debit settlement, policy reductions,
normal/error queued output, disconnected pending handlers and typed uncertainty.
Mutation participants bypass argument ownership, release at borrower launch, or
disable uncertainty classification; each must fail its designated witness.
[Current request-owner evidence](../tests/qualification/rpc-decoded-request-owner-actual-20261018.json)
binds all four stock/Ox Make/Dune builds/selftests, thirteen negative participants
per compiler, and seven fixed direct-RPC waiter/timer/socket controls per compiler.
The latter uses `tests/runtime_settlement/run.py --fixed-only --family rpc` and
the original `rpc_test.ml`; it does not claim current full report/IO-family
instrumentation or an SDK/native run. Earlier fixture refusals/assertion and
successful intermediate controls remain preserved. The separate decoder-hook
checkpoint retains its own original qualification bytes.

## Remaining lifetime and memory work

Client results still return arbitrary values, which can outlive parsing and
share tails or views. They need an explicit caller scope/lease; releasing on
decoder return or finalizing just the root does not prove storage is dead.
Custom streaming codecs still have only their existing raw packet/frame
policies for decoded values; their arguments do not yet have this selected-cost
owner. User conversion/mapping allocation or global escapes,
recursive depth, accounting metadata, outbound buffers and complete managed/
native heap/RSS are not included in the selected argument charge. Handler and
scope code must not retain arguments beyond their actual operation without a
separately owned lifetime. These exclusions remain SOL completion items.

Request argument ownership does not impose OS memory containment. Slot and
retained-link metadata need their own baseline accounting, and the remaining
client/streaming paths need ownership transfers and fault qualification. Valid
wire bytes are unchanged; no original photos, SDK or native renderer are used
by these original synthetic controls.


[Regular legacy extension evidence](../tests/qualification/rpc-legacy-decoded-owner-actual-20261018.json)
binds the current four stock/Ox Make/Dune builds/selftests and 14 negative
participants per compiler, including the ordinary-registration bypass. Legacy
and bounded requests contend in the same lane; the compact 2,000-unit legacy
collection is accepted without a wire-size heuristic. The seven waiter controls
per compiler cover the current shared owner through its bounded registration;
they are not an independent upstream/old-peer transport or physical IO test.
