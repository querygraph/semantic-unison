# Experimental scalar XMP three-way policy, v0

`org.firstpair.xmp-scalars-three-way/0` reconciles complete XMP packet bytes for
an explicit common base. The current implementation is a pure packet kernel;
automatic Unison reconciliation, base-cache storage and DNG materialization are
not yet enabled. It does not establish a trusted base or rendering equivalence.

The initial allowlist is the XMP basic namespace Description attributes Rating
and Label. Rating must decode exactly to -1 or0..5. Label must decode to at most
256 UTF-8 bytes; either attribute has at most4096 encoded bytes. XML entity and
attribute whitespace normalization supplies scalar equality; there is no Unicode
normalization, numeric spelling coercion, set union, array or language merge.
Element forms, duplicate properties and unsupported XML structures decline.

Capture uses the existing bounded parser and complete property/subject checks.
Only the two allowed value spans are masked with NUL markers (NUL is forbidden
in XML); every other byte forms the packet shell. All three shells and ordered
expanded property names must match exactly. Namespace bindings, subjects,
unknown data, develop/crop/orientation/mask/AI bytes, attribute names/quotes,
qualifiers, packet instructions and padding therefore cannot change unnoticed.
Advisory Descriptive categories never grant merge authority.

For each supported scalar: if neither decoded value changes, retain the base
encoding; if one side changes, select that exact encoding; if both change to the
same decoded value, choose the lexicographically smaller encoding independent
of replica order; competing values decline. Additions/deletions or any shell
change decline. Compose a single exact packet from the base shell and selected
encodings. No semantic-only equality is installed into Unison fingerprints.

The kernel output may differ in length. A future container publisher must prove
current file/base/preserved identities, metadata capacity and protected bytes,
create one exact target artifact, and use normal two-replica merge staging and
validation. It cannot invent padding, infer an archive base from a current side,
or treat this packet result as authority to commit. Required base binding is the
archive generation, full and preserved file identities, profile, parser and
policy versions. Missing/stale/untrusted base keeps the ordinary conflict.
Rendering/identity/workflow/opaque edits remain grouped conflicts. Optional
Adobe validation must run on each resulting receiving candidate before publish.

[Kernel qualification](../tests/xmp_merge/qualification.json) covers25 controls
per compiler, including independent scalar composition, equal decoded entity
forms, replica-order symmetry, unchanged opaque subtree preservation, rendering
changes, deletion versus update, unsupported forms, invalid XML and value bounds.
The checked OxCaml interface executes all25 controls concurrently in four
Safe.spawn domains. Output is capped at1MiB even when composing two individually
supported edits; a genuine oversized-composition control checks that boundary. This is the first M5
implementation step; it is no complete archive, materialization or merge-lifecycle
qualification. No photos, Lightroom or Adobe were accessed.
