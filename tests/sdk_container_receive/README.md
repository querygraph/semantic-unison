These tests receive **retained, SDK-generated synthetic containers** through the
current CLI with mock validators. They invoke no SDK, Adobe, Lightroom or Photo
work and read the retained originals without modifying them.

```sh
python3 tests/sdk_container_receive/run.py \
  --build-receipt /absolute/qualified-make-build.json \
  --sdk-result /absolute/completed-sdk-pilot-result.json \
  --fixtures /absolute/pilot-workspace/fixtures \
  --report /private/tmp/sdk-container-receive.json
```

The build receipt must match every current production input and binary. Each
fixture must match its recorded size and SHA-256 and have a previous positive
SDK raw-digest receipt. No consumed SDK admission is reused by this command.

For each of uncompressed, lossless JPEG and JPEG XL, four cases exercise:

* exact, same-size XMP date transfer using negotiated SDE and APFS receiver clone;
* exact transfer with cloning disabled;
* ordinary fallback when protected bytes also change;
* refusal to publish when the mock receiver validator rejects the staged result.

Old receiver hardlinks must keep their bytes, input fixtures keep their complete
identity and hash, successful transfers must converge byte-for-byte, and a fresh
no-op must leave the inode and validator-call count unchanged. SDE cases require
the actual semantic-clone debug event and exact packet payload size.

The original fixture SDK receipts do **not** validate the modified outputs. These
checks do not prove camera-corpus coverage, current Adobe acceptance, raw decode,
physical shared-block counts, power-loss durability or performance improvement.
A new coordinated SDK slot is needed for native output validation.

Compact common-base merging has a separate command with the same inputs:

```sh
python3 tests/sdk_container_receive/merge.py \
  --build-receipt /absolute/qualified-make-build.json \
  --sdk-result /absolute/completed-sdk-pilot-result.json \
  --fixtures /absolute/pilot-workspace/fixtures \
  --report /private/tmp/sdk-container-merge.json
```

It inserts Rating/Label attributes into disposable copies, consuming existing
XMP padding and preserving every byte outside the fixed packet. For each codec,
five cases check cache-only disjoint convergence, competing-scalar refusal,
protected-byte refusal, missing common-base refusal, and a second-receiver
rejection followed by fresh convergence. No `backupcurrent` is configured.
Cache objects must use profile `/1` and remain below 16 KiB for these approximately
38–48 MB containers. Successful no-ops must invoke neither validator again.

These changed bases and outputs are **not** SDK-validated; original-container
SDK positives do not extend to them. Validators remain mocks, and originals
retain complete file identity and SHA-256. This checks current merge/cache
compatibility, not general packet growth or Adobe rendering/current-edit reuse.


To freeze existing qualified merge results for a future native check:

```sh
python3 tests/sdk_container_receive/prepare_merged.py \
  --qualification tests/sdk_container_receive/quota-merge-qualification.json \
  --reference-manifest /absolute/qualified-v1/build-manifest.json \
  --output-dir /private/tmp/new-merged-output-preparation
python3 tests/sdk_container_receive/prepare_merged_test.py
```

Preparation verifies current production source/binary pins and all15 cases per
compiler, then checks all12 retained replica outputs against exact target hashes
and original bytes outside XMP. It freezes three identical stock/Ox results in a
fresh private directory, with read-only candidates and a pinned PREPARED.json.
Existing output directories are refused, including partial preparations. Changed
source/evidence/output bytes require fresh qualification, not relabeling.

[Preparation evidence](merged-preparation-qualification.json) records the actual
snapshot, deterministic controls and unchanged-directory refusal. Proposed three
single-thread SDK commands are data only. No SDK executor or native admission is
granted by preparation; future execution needs a separately reviewed contained
runner and fresh Root slot. The originals' SDK positives do not validate these
merged snapshots, which remain unqualified until that check actually runs.


`validate_merged.py` supplies the separately contained executor. Mock mode refuses
production identities; native mode requires the exact fresh Root admission state
`ROOT_ADMITTED_FINITE_UNISON_MERGED_OUTPUT_V1`, prepared file pin, command, limits,
source hashes and a current start deadline. It checks canonical three-codec argv,
input/tool/source pins, exact SDK receipt binding, valid decode/raw digest, zero
errors and the original four-warning count. Raw ENTRY/CALL files survive failure.
The aggregate is300s with60s child bounds; pre-supervision pin validation is outside
that aggregate. Parent tool terminal exit is a separate owner deliverable.

```sh
python3 tests/sdk_container_receive/validate_merged_test.py
```

This runs only original fake tools, tests normal closure and failed-receipt/exit
closure, refuses consumed workspaces and noncanonical argv before another call,
and checks seven pure admission cases. [Source qualification](merged-executor-qualification.json)
and [finite review request](../qualification/sdk-merged-output-request-v1-20261014.json)
are not runtime permission. No old slot may be reused.
