# RPC startup input limits

`rpcstartupmaxbytes` is an endpoint-local positive integer, default65536.
Delimiter reads count **every byte consumed by the field parser**, including the terminating separator
and ignored carriage returns. The original separator inclusion and CR stripping
rules are unchanged. A field that reaches its allowance without a separator
refuses immediately; no additional byte or EOF is needed. This is a byte policy,
not an inactivity timeout or a limit on all fields over a connection lifetime.

Before a delimiter read allocates or waits for peer input, it reserves one
shared header/startup input slot and twice its maximum field length from
`rpcheaderinputbudget`. A fixed-size bytearray replaces the growing Buffer.
Twice the maximum covers its payload plus the returned string payload. The
one-byte input scratch, object/continuation/connection metadata, framing and
allocator overhead are not covered by this charge. A fixed-length startup read
charges twice its requested length, including a slot for a zero-length read.
The legacy compatibility magic packet is capped by the same field policy and
conservatively reserves twice that maximum, although its payload is discarded.
The shared message-header per-frame cap remains independent of this field cap.

Reservations use the same nonwaiting raw-input byte/slot ledger as message
headers, independent of bounded request bodies. Insufficient allowance refuses
before buffer allocation or input. Existing read ownership remains with its
borrowed operation through read settlement and conversion. Every successful or
failed settled operation releases exactly once. A blocked read keeps its
reservation; this does not authorize forcibly cancelling a borrowed read.
Policies are captured at startup-field entry, not retroactively changed while a
field is being read. Invalid policies refuse before input. Very large configured
values can exhaust the shared input allowance and refuse without allocating.

The connection input buffer can prefetch up to16384bytes beyond the consumed
field; that preexisting fixed buffer is outside this reservation.

The preference is omitted from outgoing peer preferences and incoming peer
values cannot override it. Valid normal version/OK/NOK handshakes and the legacy
magic packet remain byte-compatible. Fixed connection-banner validation was
already bounded by compiled expected-banner lengths. Diagnostic peeks still
copy at most the existing16384-byte connection input buffer; they are not
charged to this field reservation. Returned values and version-list/error
conversions can outlive the raw reservation and need separate decoded-object
accounting. The common outer packet cap additionally limits the magic packet. Legacy
body/result/stream aggregate admission, total connection
baseline, process-tree FD/RSS and protocol timeouts are separate requirements.

`tests/remote_startup_bounds.ml` uses original tiny pipe data. It checks exact
limits, separator/CR compatibility, absent delimiters, all-CR input, fixed-length
refusal, OK/NOK/version fields, legacy magic acceptance/oversize refusal, shared
byte/slot refusal before input, disconnect settlement, allocation-failure rollback, empty buffered diagnostics
and preference isolation. Empty fixed reads now return the empty string without
calling the positive-length-only low-level reader.
The private negative participant removes only the delimiter byte-limit check:
a nine-byte terminated field is then incorrectly accepted and must fail the
specified assertion. Its fixed8-byte destination receives only8data bytes;
there is no large allocation or out-of-bounds reference write. Existing header
and bounded-decoder counterexamples remain independently checked. No network,
SDK, camera, Photo or canonical physical-IO payload test is used.
