This read-only developer command explains whether a file is supported by the
initial DNG profile and whether a pair permits an exact metadata patch:

```sh
python3 tools/semantic-inspect/run.py \
  --ocamlopt /absolute/compiler/bin/ocamlopt -- \
  --base /path/before.dng /path/after.dng
```

It builds in a temporary directory and prints one JSON object. No files, roots,
archives or preferences are changed. Omit `--base` to inspect one file. A supported
file report includes full and complement SHA-256 identities and editable extents.
The comparison reports `exact_bytes`, `editable_metadata` or `other_bytes`,
logical metadata payload size, and bounded SDE/SDR sizes or a fallback reason.
Unchanged packets are included in the current plan's payload; `exact_bytes`
means no synchronization is necessary despite that possible plan.

Unsupported profile layouts are a normal result, not evidence of corruption.
I/O or unstable-file errors exit 2. Each supported input is fully read; this does
not avoid hashing costs or predict APFS physical writes. The report is an
observation of separately stable reads, not a future commit authorization.
This tool neither decodes raw samples nor invokes Adobe validation.

The standalone registration currently contains the DNG implementation. Its
inspection, classification and planning use the same generic semantic kernel
as Unison; adding another compiled profile requires adding its registration
and source to this small standalone build as well as to the application.

The diagnostic JSON schema is now `unison-semantic-inspect/1`. Supported DNG
observations add a versioned interpretation schema and bounded expanded XMP
property names, potential categories and encoding/context SHA-256 values.
Unsupported XMP interpretation carries a reason while retaining the whole-file
and preservation proof. These fields are advisory; they are not RDF value
canonicalization, rendered-pixel identity or merge authority. See
[the observation contract](../../doc/semantic-observation-v1.md).
