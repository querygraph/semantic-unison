# Outer RPC packet policy

Every call to the shared packet reader now captures the positive endpoint-local
`rpcpacketmaxbytes` limit (default268435456bytes,256MiB) before reading its
fixed-length size prefix. The announced payload must fit this limit **and** any
explicit command/header/startup limit. The check precedes the reservation
callback, payload allocation and body receipt. Zero-length packets still work.
Invalid nonpositive policies refuse before input. The integer policy must not
be limited by Sys.max_string_length: payloads are bigarrays, and the default
would otherwise be invalid on32bit. An empty-packet control checks a max_int
policy without allocating any large payload; this is not a32bit runtime test.
There is no unbounded/off value; an intentionally larger local archive frame
requires explicitly raising the endpoint's limit. This changes acceptance of
oversized frames, without changing any wire tags or valid encodings.

The reader is common to legacy requests, replies without registered bounds,
stream chunks, explicitly bounded RPCs, shared message headers and the legacy
startup magic packet. A caller-supplied limit can only tighten the outer policy.
This is one limit per incoming packet, not per file or whole transfer. Ordinary
file streams can transfer much larger files in separate bounded chunks; a large
single archive/metadata RPC result may need a larger configured limit. No user
profile, installed binary or remote setting is edited automatically. Incoming
peer preference values cannot override it; it is omitted from outgoing values.

This outer allocation check is separate from [raw body lifetime admission](rpc-body-input-lifetimes.md),
which now covers requests/streams and arrived normal-result buffers through
processing or consumption. Header/startup reservations remain independent.
Decoded collection expansion of legacy codecs, live decoded-object retention,
outbound marshaling, connection/heap overhead and aggregate descendant FD/RSS
remain separate requirements. The policy is captured per read; lowering it does not revoke an in-flight read.
There is no new wait or cancellation/timeout behavior.

`tests/remote_packet_bounds.ml` checks exact/zero sizes, the minimum with explicit
limits, invalid policy before input, refusal before the reservation callback,
all three actual legacy receiving branches, and successful tiny legacy
request/reply/stream dispatch. Original small pipe data only. Oversized body
cases supply only their size prefixes; current code must refuse without waiting
for a body. A private participant omits only the global outer limit; a test-only
allocation guard stops it before allocating or waiting for nine bytes, and the
expected designated failure is required. Existing bounded-decoder, header-route
and startup counterexamples remain independent. No actual transport, camera,
SDK/Adobe, Photo, physical-IO workload or performance claim follows.
