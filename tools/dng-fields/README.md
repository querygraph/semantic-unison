# Bounded private-field decoder prototype

`PrivateIfdFields.freeze` builds a trusted compiled `ComponentHash.plugin` for
owner-selected ASCII fields in a classic12-byte-entry private directory. The
result fits the frozen `DngComponents` nesting API. It is a prototype consumer,
not an installed vendor plugin, family recognizer or semantic-ignore policy.
No private camera input has been read to qualify this implementation.

The parent must establish the directory's byte order, location and address-space
translation. `value_base` is a signed **parent-relative** translation for stored
32-bit offsets; inline values are relative to their actual entry. Nothing can
expand the core reader's parent capability. `max_span` bounds decoder requests,
not the actual parent's size or its later complete refinement rehash. All reads
and rehashes still consume the owner's shared component budget.

At most32 distinct tag/name selections,256 entries and4096 bytes per selected
value are accepted. Only TIFF-type2 shapes with a trailing NUL and printable
ASCII before it are decoded. Unknown entries, opaque payloads and next-directory
links are not followed. Missing/unsupported selected fields retain the original
opaque view through the normal plugin result. Operational reader/budget failures
propagate. Selected physical aliases refuse; other bytes stay exactly hashed as
opaque gaps. A declared span is not a proof of actual parent geometry: the core
reader enforces the real boundary, and an incorrect binding can fail operationally.

The decoder's provenance is SHA256 of length-prefixed frames: domain
`unison-private-ifd-ascii/0`, owner-supplied raw implementation SHA, component ID,
decoder ID, byte order, directory offset, signed value base, declared span,
entry limit and selected-field count, then tag/name/byte-limit triples sorted by
tag. Each frame uses canonical decimal byte length, colon, then exact bytes;
integer values inside frames use canonical decimal. Changing an address rule,
field policy or declared implementation changes provenance. Each child schema
also carries this digest, so private-role projections bind the decoder while
unaffected pixel nodes/hashes remain reusable within the same owned session.
The supplied implementation SHA is an owner declaration, not code introspection
or authentication of third-party binaries.

Labels such as `candidate-model` in the original fixtures are owner hypotheses;
ASCII syntax does not prove a vendor field's meaning or stability. There is no
automatic Hasselblad routing, live-source/cache access, plugin download, SDK,
subprocess or publication authority. A community contribution must separately
supply its wrapper/family binding and evidence for any stronger interpretation.
This small partial decoder does not require interpreting unrelated fields.

The finite `tests/semantic/private_field_controls.py` runner compiles the actual
core and DNG nesting modules under stock5.2.0 and Ox5.2.0+ox. Ox interfaces are
selected by the existing mode filter; the prototype interface gets its portable
module declaration in the isolated test build. Production integration remains a
separate versioned change. Fixtures are original generated4096-byte strings;
unknown links deliberately point outside the frame, without ever being followed.

[Actual prototype qualification](../../tests/qualification/private-ifd-fields-prototype-actual-20261017.json)
passed59 checks per compiler and47 contained calls, including actual frozen DNG
nesting. The first refinement charged6201 logical requested bytes (4096 initial,
57 decoder,2048 parent rehash). Pixel node/hash and full bytes stayed unchanged;
new declared implementation provenance changed the private projection. All
owners/groups/CPU8 closed. These are generated tests, not camera qualification.
