# Advisory component reports, SIC/0

This separately negotiated protocol reports current DNG component hashes. It
does not change SIR/0, SIR/1, SDE, archives, transfer selection or merge authority.
A peer reply is a trusted-connection statement, not a local source snapshot,
preserved-byte proof, validated image or reusable archive capability.

Capability `semantic-components-v0`, bounded command `semanticComponentsV0`,
requires RPC connection version at least1, feature intersection and an enabled
built-in DNG profile. `semanticcomponents` selects explicit details on the
initiating owner; ordinary scans/transfers do not add this pass. No peer code or
private decoder is selected: both ends use the empty frozen decoder set. Old
peers and unselected DNG profiles report unavailable without this new command.

The Umarshal request is an absolute NUL-free path (at most16384 bytes), contract
name (at most128 bytes), and32-byte fresh nonce. The only accepted contract is
`dng-physical-partition/0;component-projection/0;no-decoders`. Other names refuse
before source inspection. Argument allocation limit17568 bytes, result limit3072
bytes, contained report limit2048 bytes; legacy RPC header limits are unchanged.

Integers below are eight-byte big-endian values restricted to0..2^63-1. High-bit
integers refuse. A string is its byte length followed by exactly those bytes.
Digests are raw32-byte SHA256 values.

| Field | Encoding |
|---|---|
| Magic/version | `53 49 43 00 00 00 00 00` |
| Request nonce |32 bytes, exact request match |
| Projection contract | string,1..256 bytes, NUL-free, exact request match |
| Status | one byte:0 observation,1 unavailable |
| Unavailable body | string reason, at most1024 bytes |
| Observation body | full-file SHA256, layout-view SHA256, then five role slots |

Fixed role order: encoded pixels, standard metadata, private metadata, structural
bytes, opaque bytes. Each slot has a one-byte presence flag.0 has no body and
means unavailable, never equal empty content.1 is followed by projection SHA256,
component count (1..1024), and positive total component bytes. Other flags/status,
trailing bytes, oversize fields, truncation or request substitution refuse. Fixed
slots forbid duplicate roles/ordering ambiguity; omitted encoder lanes still
encode a zero flag.

Full-byte hashes are independently comparable; component comparisons require the
same projection contract. Layout views include knowledge refinement, not just
physical placement. Equal encoded units do not establish equal rendered pixels;
unknown private/opaque content remains hash-covered, never silently ignorable.

Source transaction admission lasts through encoding/queued output. Worker core
shares that scope without nested transaction acquisition. The declared model
envelope uses the existing eight-times1MiB plus256KiB estimate, including bounded
model construction and its summary; this is not an RSS ceiling. Component read
budget equals opened size, with bounded DNG geometry reads additional. Existing
worker/descriptor cancellation and settlement rules remain. Local path epochs
invalidate one-shot displays; remote replies carry no local preservation binding.

Original codec controls cover an independent byte vector, canonical round trips,
every truncation, substituted nonce/schema, invalid flags, zero/overflowed counts,
trailing/oversize replies and encoder limits. Actual new-command loopback,
mixed-version and failure transport qualification is separate from codec and
linked local-owner controls.
