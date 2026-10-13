# Independent SDE/0 and SDR/0 conformance

`reference.py` implements the experimental wire specification in
[`doc/semantic-delta-v0.md`](../../../doc/semantic-delta-v0.md) using only Python
integers, `struct`, and `hashlib`. It neither imports Unison production code nor
calls production programs to generate expected bytes. `vectors.py` builds
deterministic cases from that reference.

The committed `golden/` directory contains exact binary SDE and SDR messages,
base files, and expected target files for three cases:

- A four-region profile with adjacent regions, an unchanged region, binary
  packet contents, and editable ranges at both file edges. Empty complementary
  intervals remain part of the pinned preservation transcript.
- A single-packet classic TIFF/DNG in little-endian byte order.
- The same DNG layout in big-endian byte order. Inline DNGVersion bytes retain
  their TIFF BYTE representation.

`golden/manifest.json` pins every binary's length and SHA-256, plus the nonce,
regions and preservation digest. The larger boundary messages are fixed
deterministic recipes, with their exact sizes and SHA-256 values pinned in
`golden/boundary-manifest.json`; they are generated only in private test
directories. This keeps 16 MiB test payloads out of the repository. A run
recomputes these independent messages and requires agreement with both
committed manifests before compiling production code.

Run either compiler without creating build artifacts in the checkout:

```sh
python3 tests/semantic/conformance/run.py --ocamlopt /usr/local/bin/ocamlopt
python3 tests/semantic/conformance/run.py --ocamlopt /Users/alexy/.opam/5.2.0+ox/bin/ocamlopt
```

Each run preserves its compiler-local snapshot, build/test logs and receipt in
`/private/tmp/unison-sde-conformance-*`. `--report /path/receipt.json` chooses
where to save the receipt. Production sources are copied before compilation;
the receipt includes source/compiler hashes and whether the checkout still
matches that snapshot. `tests/semantic/run.py` also runs this suite by default;
`--skip-conformance` retains the original kernel/inspection-only invocation.

The production driver checks decoding and byte-for-byte re-encoding of accepted
messages. For all three file-backed goldens it independently checks inspection
proofs, request bytes, fresh and claimed-base planning, exact materialization
through both the selected extension and the populated production registry,
and unchanged source bytes. Every strict prefix of each golden request and
response must be rejected. Other cases cover version/profile/integer/count
limits, region order, overlap, bounds and payload hashes; 1 MiB region and
16 MiB aggregate ceilings; 64 operations; signed-int64 arithmetic; declared
payload limits; nonce construction lengths; file growth and opaque changes;
and every receiver proof field used for SDR response binding.

Structural decoding and local authorization are separate checks. Unknown
profiles and altered nonce/base/preservation/old-region hashes can be framed
correctly. Binding or the locally selected profile must reject them before
writing. A wrong target hash remains bound to a request, but final target
verification rejects the resulting private output after writes; that output
must be discarded. The tests explicitly preserve this distinction.

The maximum structurally valid message is 16,782,624 bytes for SDE (128-byte
profile, 64 operations, 16 MiB payload), and 3,328 bytes for SDR. The larger
outer limits, 16,842,752 and 8,192 bytes respectively, cannot be attained by a
valid version-0 encoding. Tests at and around those outer limits use malformed
messages and verify that a cap-plus-one input is rejected by the outer size
check. These checks operate on an already supplied string and do not establish
RPC preallocation protection or constant-memory transport.

Negative controls corrupt only the private production snapshot and must fail
the corresponding independent check:

```sh
python3 tests/semantic/conformance/run.py --negative-control nonce
python3 tests/semantic/conformance/run.py --negative-control preservation
```

Regeneration is explicit and uses no production encoder:

```sh
python3 tests/semantic/conformance/vectors.py --write-goldens
```

These are synthetic conformance tests, not an Adobe SDK validation, a claim
of general DNG coverage, or a filesystem allocation/performance benchmark.
