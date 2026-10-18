# Incoming RPC header limits

Every ordinary RPC message header now uses a separate endpoint-local raw-input
allowance before allocation. This covers request names, normal-result headers,
exception headers and stream-control headers in the existing receive loop.
Message IDs and write-permission tokens retain their existing fixed encoding.
No new wire tag, schema or negotiation feature is emitted.

| Endpoint-local setting | Default | Meaning |
| --- | ---: | --- |
| `rpcheadermaxbytes` | 8388608 | Maximum single header frame payload, including its RPC tag and Umarshal framing; excludes the fixed five-byte transport length prefix. |
| `rpcheaderinputbudget` | 16 | Aggregate in-flight raw header/startup payload MiB within this process. |
| `rpcheaderinputslots` | 256 | Aggregate headers/startup fields waiting for input, receiving payload or decoding, including empty frames. Maximum 65536. |

All settings must be positive; the maximum frame must fit the byte budget and
MiB conversion must be representable. Invalid configuration refuses before
reading a header prefix. An oversized announced length or exhausted allowance
fails the connection before payload allocation/read. No CPU, semantic transaction
or body-input admission is awaited. Header bytes and slots are independent from
`rpcboundedinputbudget`/`rpcboundedinputslots`, so work awaiting a reply cannot
consume the header service lane.

Each receive prepares a fresh ticket and charges its slot before reading the
length prefix. After sizing, its exact announced bytes are charged before
`Bytearray.create`. The current policy is checked again when granting bytes;
the frame's initial maximum also remains an upper bound. Raising settings does
not expand that already-started frame, and lowering settings does not revoke
existing slot/byte claims. Future grants obey the relevant limits. Charges last
through actual receipt and synchronous header decoding; success, malformed
input, allocation/read failure and disconnect settle the same ticket once.

Valid legacy encodings remain unchanged. A deliberately larger diagnostic header
can be allowed by raising the maximum and process byte budget together in the
endpoint's own profile/CLI configuration. There is no unbounded/off value.
These preferences are omitted from outgoing settings and ignore incoming peer
bytes before decoding. No user profile, installed binary or peer setting is
automatically modified by this source change.

## Boundaries

This is raw header reservation accounting, not a bound on decoded exceptions
retained by callers, transport buffers/FDs, all heap allocations, process-tree
memory or RSS. Ordinary unbounded legacy body/result/stream packets are not
covered. Protocol startup/handshake reads use their own field policy and share this raw-input
ledger; see [startup limits](rpc-startup-input-limits.md). Overall decoded-object admission and remaining
acquisition/baseline/resource enforcement remain open.

The slots include partial prefixes; they do not bound the number of connections
or child processes created before header receive starts. Each process has its
own counters. Do not relabel this as global machine or descendant containment.

## Fixed controls

Both compilers exercise the actual private Remote participant on synthetic pipes:
exact cap/wire parity; header-only oversize refusal through helper AND real
receive-loop routing; malformed decode; idle-prefix and payload slot exhaustion;
exact one-MiB byte exhaustion; allocation-failure rollback; current-policy
narrowing; disconnect settlement; empty/replayed sizing and repeated release;
independence from a full request-body allowance; invalid configuration; and
endpoint preference omission/poisoned incoming protection. Existing request,
reply-scope, decoded-expansion and output/disconnect regressions remain active.

A private payload-allocation safety guard stops an old receive-loop route before
it can allocate or wait for a missing body. That unbounded-route participant must
fail its designated assertion. A separate participant using legacy decoders for
bounded commands must still fail the decoded-expansion counterexample. No huge
allocation, real transport, SDK, camera, Photo payload, EXglobal IO or performance
qualification is involved. Actual process/group/token settlement and source pins
are recorded in the immutable qualification receipt.
