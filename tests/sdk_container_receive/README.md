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
