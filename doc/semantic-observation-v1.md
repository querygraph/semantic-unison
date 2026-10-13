# Extension-defined observations and SIR/1

These are bounded, advisory descriptions of the observed current data forks.
Exact-byte classification, archives, conflict decisions, SDE/0 and SDR/0 remain
unchanged. An observer supplies meaning; it cannot authorize a patch or merge.

A trusted compiled format handle optionally declares `FormatExtension.observer`:
a versioned schema and a pure function receiving the complete retained editable
packet strings. Core accepts at most 128 unique, canonically sorted properties.
Each has a nonempty name of at most 512 bytes, a potential-meaning category and
one raw 32-byte SHA-256 digest with the schema's declared recipe. Schema IDs are
nonempty, at most 128 bytes, without NUL. Property names exclude NUL. Failures
carry at most 1024 bytes of diagnostic text. All terminal output is escaped.
The observer must bound its work and allocations; compiled code is trusted,
not sandboxed. A peer statement is bounds-checked but does not become a local
preservation proof.

Only explicit diff/details requests use the new `SemanticWorkers.observe`
operation. Inspection and full-packet interpretation run on a worker under the
existing CPU/resource budget. The worker rechecks cancellation and source
stability before returning. Ordinary transfers continue to use plain inspection
and incur no XML interpretation cost. Hash-only SDR claims cannot enter the
full-packet observation hook.

The category byte is 0 descriptive, 1 rendering, 2 identity, 3 workflow, or
4 opaque. These describe possible meaning, not safe-to-merge fields or pixel
identity. A second compiled synthetic format supplies its own workflow field
using unchanged worker, RPC and UI dispatch.

## Wire representation

Capability `semantic-inspect-v1` is separate from `semantic-inspect-v0` and has
`arcFormatChange=false`. Invoke `semanticInspectV1` only when both are negotiated
and the connection uses RPC encoding version 1 or later. The arguments match
the existing bounded path/profile/32-byte-nonce tuple. Replies have a 131072-byte
inner limit and a separate command-body limit before allocation. Source resource
leases cover response output. Otherwise use the existing SIR/0 command unchanged.

Canonical SIR/1 layout, with unsigned big-endian 64-bit lengths/counts restricted
to the declared bounds:

1. Eight magic bytes: ASCII `SIR`, five bytes `00 00 00 00 01`.
2. Length and byte-identical SIR/0 observation. Its profile and nonce bind the
   request; its existing size/extent/hash/sample validation remains mandatory.
3. One status byte: 0 absent, 1 unsupported interpretation, 2 properties.
4. For status 1, length and bounded reason. For status 2, length and schema ID,
   property count, then for each property: length/name, category byte, digest.

Properties are strictly increasing by bytewise name order, without duplicates.
Empty property sets are valid. Unknown categories/status/version, overflows,
truncation, trailing bytes and noncanonical/invalid fields reject. Status 1/2
requires a supported byte observation. SIR/0 encoding deliberately omits these
new fields and remains byte-identical. Peers with SIR/0 can still supply byte
classification and previews; their property interpretation is unavailable.

## DNG XMP property encoding schema

`dng-xmp-property-encoding-v0` interprets a supported bounded UTF-8 XML 1.0
subset of the complete embedded XMP packet. Names are expanded namespace names.
Camera Raw properties are potentially rendering-related; known descriptive,
identity and workflow properties have distinct categories. Unknown properties
remain opaque. Nested RDF/mask/AI encodings belong to their complete top-level
property subtree. Namespace aliases and scoped rebinding are resolved before
naming and included in the digest context.

Digest transcript defined by `XmpObservation`:

- ASCII `Unison-XMP-observation`, NUL, ASCII `v1`, NUL.
- One byte `A` for attribute-value bytes or `E` for child-element bytes.
- BE32 binding count; sorted in-scope prefixes and decoded namespace URIs,
  each framed by a BE32 byte length.
- BE32 length and exact property encoding bytes.

Inherited and property-local namespace mappings are bound, so identical subtree
bytes under a rebound namespace are not equated. Unused declaration changes
can conservatively change the digest. Entity spellings, prefix aliases, layout,
ordering and markup can differ despite equivalent RDF values; no canonical
RDF/value comparison or rendering equivalence is claimed. Packet declarations,
`rdf:about`, toolkit metadata and unsupported structures are not a complete
semantic view of every packet byte. Full packet/whole-file hashes remain present.
An unsupported XML/RDF graph returns an interpretation reason and leaves exact
transfer eligibility and byte verification intact. DTD/general/external entities
are not resolved; unsupported encodings and bounded-parser limits are explicit.

The CLI reports up to 32 added/removed/changed property encoding/context entries,
with categories and an omission count. Comparison requires matching observation
schema IDs. Additional interpretation never replaces the generic byte decision
or infers an archived base.
