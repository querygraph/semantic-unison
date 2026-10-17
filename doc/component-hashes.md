# Component hashes and incremental decoder refinement

`ComponentHash` implements the worker-local hashing/composition core of SOL.md's
gradual-understanding design. The DNG adapter below now supplies physical
components; wire protocol, archive identity and persistent-cache integration
remain open. It grants no transformation,
conflict-resolution, publication or decoded-pixel-equivalence authority.

An owner supplies an immutable input snapshot and a root specification covering
the whole file. Nodes have a logical ID, schema, role, relative extent and
children. Roles distinguish encoded pixels, standard metadata, private metadata,
structural bytes and opaque bytes. Children are canonicalized by physical
position; uncovered gaps become opaque atoms. Overlap, out-of-parent extents,
duplicate or out-of-namespace IDs, excessive depth/count and malformed bounds
are rejected before reading. Limits are1024 total nodes, depth16,256-byte IDs/
schemas and1MiB per explicit decoder read. Gaps count toward those limits.

Initial hashing reads every file byte once at the delivered-read level, feeding
its leaf and ancestor contexts together. The root's content hash is ordinary
full-file SHA256. Each node also has a schema/role/identity-bound view hash.
Opaque bytes never disappear merely because a decoder does not understand them.

Role projections collect nonempty leaf components in logical-ID order and
exclude physical offsets. They include a hash, component count and byte count.
No components yields **None**, not an empty pixel identity. A projection covers
only the parser's claimed ranges; even matching nonempty partial pixel
projections cannot establish complete image or rendering equality. Encoding,
logical pixel-unit schema and interpretation dependencies must be provided by
the format integration. Calibration/orientation/rendering inputs stay separate.

## Nested plugins and refinement

A trusted compiled plugin declares a bounded versioned ID, a raw32-byte
owner-pinned implementation SHA, and a portable decoder callback. The digest
is provenance supplied by the owner, not introspection of the function's machine
code. The callback receives a reader restricted to one parent component. It can
delegate to `with_subreader` for nested structures; children share the same read
budget and cannot expand their extent or lifetime. Reader nesting is bounded.
There is no registry mutation, code download, subprocess or write handle in
this interface. Trusted native code is not sandboxed by an OCaml record type.

The decoder returns a child fragment or an explicit unsupported reason. A valid
fragment refines a leaf, retaining unknown gaps as opaque. The core rereads only
that parent span and checks its raw SHA against the prior content hash, then
replaces that view and recomputes its ancestors. Unaffected nodes and their
hashes are retained. Implementation provenance participates in the refined view;
different decoder versions do not silently reinterpret the old root.

The shared read budget charges requests before IO, without refunds on failure.
Decoder reads and parent-span rehashing both count. The old parent digest cannot
produce the new children's hashes; those bytes must actually be read. Library
accounting concerns requested/delivered logical bytes, not physical reads,
prefetch, filesystem allocation, RSS or a systemwide IO limit.

The session borrows a `SemanticFile`; it does not acquire, close or release the
owner's descriptor/CPU/IO resources. All session and reader capabilities expire
on callback return. Snapshots may escape as historical observations, but cannot
be refined in another session. The owner must retain immutable snapshot access
for reuse: consistency checks do not exclude a hostile concurrent writer, and
this implementation does not authorize timestamp-only cross-session reuse.
Operational/read errors propagate; an unsupported decoder preserves the old
snapshot and its opaque coverage.

## Version0 canonical framing

`I(n)` is an unsigned eight-byte big-endian nonnegative integer. `F(s)` is
`I(byte_length(s)) || s`; strings/digests are bytes without Unicode normalization.
All content digests are raw32-byte SHA256 values. Role names are
`encoded-pixels`, `standard-metadata`, `private-metadata`, `structural`, `opaque`.

The node view preimage is:

```text
F("unison-component-view/0") F(id) F(schema) F(role) I(length) I(child_count)
  leaf:   F(content_sha256)
  branch: F(child1.view_sha256) ... F(childN.view_sha256)
```

The role projection preimage uses `F("unison-component-projection/0") F(role)
I(count)` followed by framed leaf-view digests in logical-ID order. No digest is
reported for an empty projection. The layout-view preimage starts with
`F("unison-component-layout/0")`, then preorder entries containing framed ID,
schema, role, absolute offset/length/count integers and framed node-view digest.
It binds the knowledge manifest's geometry and provenance: it may change after
decoder refinement even when the file's bytes and full SHA remain unchanged.
It must not be displayed as independent evidence that the physical file changed.

## Actual scope and next integration

[Evidence](../tests/qualification/component-hash-core-actual-20261017.json)
records41 checks per stock/Ox compiler,22 contained calls (including three
expected Ox refusal compilations for escaping session/snapshot/reader scopes),
and four full Make/Dune builds. Independent `SemanticFile` delivered-read
accounting matches8192initial bytes plus only the refined parent/nested spans
and explicit decoder reads; the pixel node is physically reused. Tests cover
unsupported/expired readers, source changes, shared budget, partition/depth/
count failures, unknown projections, placement-independent pixel views and
decoder provenance. Two initial compile-only failures are preserved. All
owners/groups/CPU8 closed; no SDK, retained media or canonicalIO was used.

The DNG adapter below supplies value and encoded-image-unit fragments and
exposes inspector observations. Next: freeze actual nested vendor decoders on
the owner and add persistent cache import/export with independently qualified
input/preservation bindings. No persistent/cross-session skip, real-camera pixel coverage, receiving
or full-goal acceptance is established by this core alone.

## DNG adapter and inspector

`DngComponents.describe` now maps the existing bounded TIFF/DNG graph reader to
this partition. It handles classic TIFF and BigTIFF in both byte orders. Inline
and outlined values are separated from entry descriptors, inline padding,
directory counts/links and headers. Known value tags occupy the standard lane;
unrecognized values, including opaque MakerNotes/DNG private data, occupy the
private lane. Here “private” means unrecognized by this parser, not a verified
vendor classification. Value schemas bind TIFF type/count and byte order.

Strip, tile and JPEG-interchange ranges in image directories become encoded
image-unit leaves. Their logical IDs use bounded graph traversal and unit order;
they do not establish complete raw/previews/thumbnail classification or decoded
pixel identity. Geometry, compression, orientation and calibration fields are
separate metadata dependencies, not silently part of the encoded-byte digest.
Reordering a graph can change logical IDs; this version does not promise a
canonical semantic image identity across arbitrary directory rewrites.

All physical claims must be disjoint. A shared value, image/metadata overlap or
other alias causes an unsupported result rather than double-counting bytes as
independent components. At most480 explicit regions are admitted, leaving room
for automatic opaque gaps under the core1024-node limit. This conservative
component refusal does not change ordinary exact transfer or grant any merge
behavior. Component description does not require XMP; existing transfer profiles
retain their own XMP requirement and rules.

The read-only inspector accepts `--components [--base FILE] TARGET`. It reports
full SHA256, layout-view hash and the five optional projections, each with its
claimed byte/component count. An unavailable lane is JSON null. This mode is
separate from transfer-profile selection and provides no patch eligibility.
The parser performs bounded geometry reads before hashing; `hash_bytes_requested`
counts the component hashing pass only, not those parser reads or physical IO.
There is still no persistent-cache import, sync/archive identity change, vendor
child decoder or real-camera pixel coverage qualification from this adapter.

[Adapter evidence](../tests/qualification/dng-components-actual-20261017.json)
records68 DNG checks per compiler plus unchanged layout/strict regressions,
57 contained calls, new/legacy inspector JSON, four full builds and stock/Ox
retained-inspector launcher builds. All owners/groups/CPU8 closed. Fixtures are
original generated byte strings; no retained camera file or SDK was invoked.
