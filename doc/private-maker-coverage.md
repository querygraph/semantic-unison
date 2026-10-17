# Retained camera private-directory coverage

This analysis consumes the saved, redacted result of the already consumed
402-byte slice. It opens no DNG payload and makes no vendor identification.
The [qualification record](../tests/qualification/private-maker-coverage-actual-20261017.json)
pins that result, the pure analyzer, and seven original synthetic controls.

The candidate classic directory occupies bytes 0..401 of the 6,556-byte MakN
payload. Its 33 entries comprise 17 inline slots and 16 outlined values. The
outlined values do not overlap one another or the directory, and all declared
extents are inside the payload. Together with the directory, they cover 6,551
bytes. The five remaining bytes are at offsets 459, 477, 495, 1025 and 6545.
Their contents were not read: they are unclassified gaps, not verified padding.

Seven outlined UNDEFINED values total **5,939 bytes**:

| Candidate tag | Relative offset | Bytes |
|---|---:|---:|
| 23 | 460 | 17 |
| 24 | 478 | 17 |
| 25 | 496 | 512 |
| 51 | 1008 | 17 |
| 66 | 1122 | 1024 |
| 75 | 2168 | 256 |
| 90 | 2434 | 4096 |

Those bytes may contain nested structures or references. The 17 inline slots
may also encode pointers despite having scalar TIFF types. Spatial coverage
does not establish reference closure, XMP independence or safe relocation.
Production private-tag refusal remains unchanged.

## Next camera investigation

Three candidate ASCII fields offer a smaller identity investigation before
attempting the opaque structures: tag21 at relative450 length9, tag96 at6530
length15, and tag97 at6546 length10. These are **34 prospective bytes**, not
an executed read or a new admission. A successor reader would have to bind the
saved geometry/source epoch, bound each read and total, treat the values as
untrusted bytes, and avoid assuming that strings establish vendor identity.
No command or payload grant exists for this prospective step yet.

Even an identified vendor would still require an exact layout/version contract,
every private reference's base and width, nested and inline-pointer handling,
and independent fixtures/counterexamples before a production profile change.
ExifTool13.59's MakerNotes source still routes its Hasselblad branch to the
generic unknown table with a special base rule; that source example supplies
neither a complete private grammar nor identification of this retained sample.
The user's exiftool-rs work remains separate until its planned integration is ready.

The analyzer reports overlaps, outside extents, and the union of declared ranges
without interpreting payload contents. Synthetic tests cover adjacent ranges,
directory/value and value/value overlap, outside references, inline unknowns,
nonzero directory origins and contradictory/bool-as-integer records. All seven
passed under the Unison00..07 grant; the worker/group and CPU descriptors closed.
