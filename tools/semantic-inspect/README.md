This read-only developer command explains whether a file is supported by the
initial DNG profile and whether a pair permits an exact metadata patch:

```sh
python3 tools/semantic-inspect/run.py \
  --ocamlopt /absolute/compiler/bin/ocamlopt -- \
  --base /path/before.dng /path/after.dng
```

It builds in a temporary directory and prints one JSON object. No file contents, roots,
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

The standalone registration contains both compiled DNG profile versions. Its
inspection, classification and planning use the same generic semantic kernel
as Unison; adding another compiled profile requires adding its registration
and source to this small standalone build as well as to the application.

The developer tool retains `org.firstpair.dng-xmp/0` as its default. Select
`--profile org.firstpair.dng-xmp/1` for BigTIFF and the bounded embedded
camera-profile graph. Both versions require full-file hashing; see the
[v1 contract](../../doc/dng-profile-v1.md).

The diagnostic JSON schema is now `unison-semantic-inspect/1`. Supported DNG
observations add a versioned interpretation schema and bounded expanded XMP
property names, potential categories and encoding/context SHA-256 values.
Unsupported XMP interpretation carries a reason while retaining the whole-file
and preservation proof. These fields are advisory; they are not RDF value
canonicalization, rendered-pixel identity or merge authority. See
[the observation contract](../../doc/semantic-observation-v1.md).

## Build once without opening an input

A reusable inspector can be built in the standing Unison CPU lane:

```sh
SHARED_CPU_CREDITS=8 STOCK_PREFIX="$HOME/.opam/default/bin" \
  make -f tests/Makefile inspect-stock
SHARED_CPU_CREDITS=8 OX_PREFIX="$HOME/.opam/5.2.0+ox/bin" \
  make -f tests/Makefile inspect-ox
```

Run serially. Each uses one compiler job, retains a private build and prints its
report directory. `RESULT.json` contains the binary path/hash, compiler hash,
all copied source hashes, command, log hash and actual build exit. The build-only
branch invokes no inspector, opens no image and uses no Adobe SDK. The receipt's
`inspector_executions=0` describes that build, not future manual invocations.

The direct form is `python3 tools/semantic-inspect/run.py --ocamlopt /absolute/compiler
--build-only --report /fresh/path/build.json` (one shell line). It requires a fresh
report and forbids forwarded inspector arguments. Reusing an existing report is
refused rather than overwriting it. Builds retain failures for review. Normal
one-shot invocation still builds in a temporary directory and cleans it afterward.
The missing `xmpMerge` dependency required by current `SemanticDelta` is included.

[Stock/Ox build-only evidence](../../tests/qualification/inspector-build-only-actual-20261016.json)
and [command refusals](../../tests/qualification/inspector-command-controls-actual-20261016.json)
cover build/ownership only. They establish no real-camera layout eligibility,
Adobe validation or production receiving result. Coordinate source-copy IO before
using Photo-owned fixtures; never substitute this tool for a rendering fingerprint.

## Reuse the pinned build

`--use-build /absolute/build-receipt.json -- ...` checks a successful retained
build-only receipt, the exact current19-file kernel source set, the private
workspace/binary binding and binary SHA256, then forwards arguments without a
compiler lookup or rebuild. Receipt reads are bounded regular no-follow reads;
duplicate keys, changed files and stale/missing pins fail before input access.
The build's compiler/runner hashes remain historical provenance; reusing an
already compiled binary does not execute or require a compiler. A build receipt
is locally trusted developer input, not peer-provided code or a plugin sandbox.

For a separately consented private copy, the shared entry point is:

```sh
SHARED_CPU_CREDITS=8 INSPECTOR_RECEIPT=/absolute/build/RESULT.json \
  INSPECT_INPUT=/absolute/verified-private-copy.dng \
  make -f tests/Makefile inspect-file
```

It defaults to DNGprofile1. `INSPECT_PROFILE` can select profile0; optional absolute
`INSPECT_BASE` adds a comparison. One synchronous inspector plus2 owner credits
fits the lane; all source/binary checks precede the image open. The dispatcher
captures JSON in `SHARED-STDOUT.txt` in its printed private report directory.
No image/archive/preferences are written. This command is not an IO permission
for a Photo-owned copy or a new SDK/native-Photo allocation.

[Eight inert-artifact/refusal controls](../../tests/qualification/inspector-reuse-controls-actual-20261016.json)
pass with execution mocked; no photographic input or actual reused inspector
was executed in that qualification. Real-copy IO and receiving follow separately.
