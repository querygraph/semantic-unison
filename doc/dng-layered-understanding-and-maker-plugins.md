# Layered DNG understanding and nested MakerNote plugins

Status: source design requested by the user; no new runtime, profile registration,
semantic eligibility, or camera support is established by this document.

The DNG plugin should describe what it knows without requiring an interpretation
of every private byte. Keep structural coverage, decoded meaning, reference
closure, edit authority, and validation results separate. These are independent
facts, not one confidence score or a single increasing support flag.

## Layers

1. **Container structure.** Enumerate supported TIFF/DNG directories, entries,
   declared value extents, and relationships under explicit read/node/extent
   bounds. Report overlaps, unresolved references, unsupported directory kinds,
   and holes. An extent is a location, not an assertion about its meaning.
2. **Standard metadata.** Identify supported standard fields and their bounded
   values. Retain unknown fields as opaque extents. Distinguish descriptive,
   rendering, identity, and workflow meaning; standard metadata is not all
   safely editable. Preserve the original serialization unless a separately
   admitted edit policy permits a change.
3. **Image data.** Delineate supported strip/tile/image-data extents and their
   associated dimensions, compression, samples, and directories. Encoded byte
   boundaries do not prove decoding, raw digest validity, visual equivalence,
   or that a primary image is the only image. Unsupported layouts remain
   explicitly unresolved rather than guessed from file size.
4. **Private containers.** Recognize a supported outer container, such as the
   already diagnostic Adobe/MakN framing, and describe its embedded sections
   and offset origins. Framing knowledge does not imply vendor grammar or a
   closed reference graph.
5. **Vendor MakerNotes.** Optional nested handlers add bounded structural and
   semantic facts for precisely recognized signatures and versions. Support
   can grow handler by handler; an unknown or ambiguous signature remains
   opaque. Reading a camera's Make/Model is a dispatch hint, not sufficient
   authentication of a private grammar.

The current production `DngSemantic` profile conservatively rejects private
50740 graphs. `DngPrivateData` currently supplies unlinked diagnostic framing
and locator APIs. Keep that production behavior until a new explicitly
versioned profile and its safety policy are qualified.

## Plugin inside the DNG plugin

The DNG extension remains the only outer `FormatExtension` provider. It owns
container traversal, image/metadata extent accounting, the aggregate read
budget, and the final eligibility decision. A MakerNote handler cannot register
an independent transfer profile or grant edit/publication authority.

Use an immutable, owner-resolved collection of trusted compiled handlers passed
to a worker. Avoid mutable worker registries, dynamic library loading,
subprocesses, filesystem paths, or SDK callbacks. This follows the current
`FormatExtension.trusted` worker-local contract; it is trusted code, not a
sandbox for hostile plugins.

Suggested nested interface (not yet an implementation):

- `probe(context, bounded_reader) -> no_match | recognized(signature, version)`
- `inspect(context, bounded_reader) -> facts | unsupported(reason)`

`context` binds the section's file extent, containing private-block extent,
byte order when established, and explicit offset-origin information. A reader
accepts only offsets inside the supplied authority and charges every requested
read against the DNG parent's shared budget. If a grammar needs file-wide
references, it requests that explicitly through the parent; it must not silently
escape a section-relative reader.

Returned facts contain:

- handler identifier/version and the exact recognized signature;
- known fields and their extents, without automatically publishing raw values;
- opaque/unparsed extents and parse limitations;
- reference edges with explicit origin and target extents;
- `reference_closure = proved | unresolved`, with the reason/evidence;
- advisory meaning categories and provenance.

No match, unknown version, conflicting handlers, malformed lengths, exhausted
budget, cyclic/deep references, or an extent outside authority produces a
conservative unsupported/opaque result. Reader/descriptor ownership errors
propagate through the existing retained-ownership path; they are not ordinary
format declines.

## What partial knowledge permits

Partial knowledge is immediately useful for diagnostics, indexing, standard
metadata display, exact-byte transfer, and receiver-basis fallback. Unknown
MakerNotes need not prevent those operations.

Partial knowledge alone must not permit semantic replacement of an XMP packet,
relocation of a private block, metadata merge, or reconstructed serialization.
An opaque region might reference changed bytes even when its own extent is
disjoint. A future edit policy needs either proved relevant reference closure
or a separately demonstrated preservation rule covering the proposed change.
Neither byte-range nonoverlap nor an SDK pass alone establishes that rule.

Keep exact bytes for everything outside the explicitly authorized editable
regions. Preserve existing conflict behavior and ordinary transfer fallback.
Report `semantic_eligible` independently from `standard_metadata_known`,
`image_extents_known`, `private_framing_known`, and `maker_fields_known`.

## Incremental implementation

1. Add a diagnostic DNG coverage result and bounded nested-handler API, leaving
   existing negotiated profiles and transfer behavior unchanged.
2. Connect the existing diagnostic private locator/framing recognizer to that
   result. Report current camera MakerNote coverage as framing/declared extents
   only; do not promote the 33-entry slice to vendor closure.
3. Add one precisely scoped vendor handler using original synthetic fixtures,
   malformed/unknown-version controls, endian/offset-origin boundaries,
   shared-budget exhaustion, ambiguous-dispatch controls, and stock/Ox parity.
4. Admit any real-copy diagnostic read separately with its existing identity,
   IO, read-byte, and lifecycle limits. No source recopy or full hash is implied.
5. Only after an independent edit-safety review, define a new negotiated DNG
   profile for the exact supported grammar and operation. Qualify receiver
   behavior and validation separately. Do not widen the old profile in place.

The same interface should support more vendors later without making broad
claims that all MakerNotes or every byte of a camera format is understood.
