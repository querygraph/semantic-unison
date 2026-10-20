# Framed decoder allocation checks

Umarshal now carries a private per-decode input context through its combinators.
Before allocating a string, bytearray or int32 bigarray, the decoder checks its
length against remaining framed bytes. Byte/string/bigarray entry points validate
the offset and eight-byte declared payload header before decoding; subtraction
checks avoid overflowing offset arithmetic before the native bigarray blit.
A short frame cannot claim a much larger inner payload and allocate it first.
Negative collection lengths also refuse.

The abstract codec API and valid writer encodings are unchanged. Ordinary
byte/string/bigarray decoders retain support for prefix decoding within a valid
frame and do not introduce a collection expansion limit. They reject malformed
or truncated framing that was previously ignored. Channel decoding checks the
advertised payload boundary; a non-seekable channel still requires a separately
bounded outer frame when its advertised header can itself be hostile.

Additive bounded bytearray/channel entry points accept nonnegative selected
allocation-charge and collection-element budgets. The counters belong to the
input context, aggregate across nested codecs and use non-allocating field
updates. Charges cover primitive scratch buffers, string buffer plus string,
bytearray payload plus scratch buffers, int32 array payload plus its primitive
reads, and both list spines. Collection counts include lists, bigarrays and
property lists. Overflow and budget exhaustion refuse before the next charged
allocation/iteration. Unbounded entry points do not multiply large legacy sizes
merely to compute a disabled charge.

These charges exclude input/framing/context objects, heap headers for most
values, user product/sum conversion functions, property-map callbacks, recursive
codec factory overhead and whole-process/native memory. They are not a complete
heap or RSS cap. Bounded channel budget validation precedes reading its header.

`Remote.registerBoundedServerCmd` uses bounded decoding for arguments and
normal results. Each decode has `65536 + 8 * frame_limit` charged bytes and
`1024 + 4 * frame_limit` collection elements. Unrepresentable declarations
refuse registration. A scope may decode arguments twice; each decode has its own
limit. This adds a local decoded-expansion policy to those explicitly bounded
commands. It changes neither tags nor bytes emitted on the wire. Authors of new
bounded command schemas must size their frame declarations for this decoded
policy too. Legacy unbounded registrations retain ordinary decoding.

Existing raw bounded-request credits still last through request/reply output
queue consumption, including decoded-input refusal before the server or scope
runs. The shared RPC header benefits from Umarshal's inner-length preflight.
Its outer header frame now uses the separately qualified
[header byte/slot policy](rpc-header-input-limits.md). Legacy body and stream frames now obey the
[common outer frame policy](rpc-outer-frame-limits.md); their retained raw lifetimes now follow
[body input admission](rpc-body-input-lifetimes.md). Aggregate decoded lifetimes
remain separate. Per-decode limits do
not form a global decoded-object reservation; connection/global aggregation,
recursive conversion/depth policies and complete FD/RSS limits remain open.

## Evidence scope

The fixed library controls compare current valid encodings with the source at
`dcaa1e08`, decode/re-encode them through bytes/bigarrays/bounded bigarrays, and
read consecutive channel frames. Invalid offsets, truncations, huge inner
claims, exact budget boundaries, nested counts and invalid policy inputs are
checked. Both current and reference variable-allocation sites have private test
safety guards: current rejection must be a typed decoder error before the guard,
while the old string decoder reaches its designated guarded allocation site.
No huge allocation is performed. Unsafe reference-offset cases are never run.

In-process RPC tests exercise decoded arguments with/without a scope, normal
results, a small header with an oversized inner claim, raw-ticket/output lifetime,
dynamic reply limits and disconnect cleanup. An exact participant using only
legacy decoders for bounded registrations must fail the designated assertion on
a finite 2000-unit input. Pipes and generated values only; no real transport,
SDK, camera, Photo payload, EXglobal or performance qualification.
