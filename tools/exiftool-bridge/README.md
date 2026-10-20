# exiftool-rs MakerNote interpretation inside DNG inspection

The optional DNG inspector path now reuses the actual local exiftool-rs library,
pinned to commit `3cd699a2e6633fcf28e39c260c71709b6a6049a7` of
[alexy/exiftool-rs](https://github.com/alexy/exiftool-rs). Its tables/parser target
ExifTool13.59. The existing checkout is read only: a private build snapshots the
pinned git tree, without corpus images, and builds a small library consumer. No
Perl subprocess, metadata writer, SDK, renderer or peer-supplied command is used.
Both projects use GPL3. Keep the source revision pinned when the fork advances;
a later merge requires a newly built/qualified interpretation version.

## Build and use

Run builds within the project's owned CPU budget (at most2 compiler jobs). Output
must be an absent private directory. Cargo resolves offline, freezes the resulting
lockfile, then builds with `--locked --offline --jobs2`; its lock digest, compiler
versions, source inventory and executable digest are recorded in BUILD.json.

```sh
python3 tools/exiftool-bridge/build.py \
  --source /Users/alexy/src/exiftool-rs \
  --output /private/tmp/unison-exiftool-build-UNUSED-NONCE

python3 tools/semantic-inspect/run.py \
  --use-build /absolute/qualified-component-inspector/RESULT.json \
  --exiftool-build /private/tmp/unison-exiftool-build-UNUSED-NONCE/BUILD.json \
  -- --components /absolute/authorized/input.dng
```

`--exiftool-build` is optional and accepts exactly one component-observation input.
Without it, the existing inspector schema/behavior remains unchanged. It does
not select a transfer profile or change sync defaults. The caller must coordinate
CPU and physical IO; commands are not a retained-camera payload admission.
The old camera request's source pins are stale after this runner addition; do not
execute or silently repin that request. Its original bytes remain preserved.

## Nested knowledge view

The output is `unison-dng-knowledge-observation/1`:

- exact source SHA256 and eight-field identity fence;
- existing exact DNG component forest summary, including encoded-pixel and
  private/opaque projections;
- `dng/exiftool-rs/makernotes` interpretation, grouped by vendor then field;
- engine revision, bridge executable/source identities, warnings and actual
  helper lifecycle receipts.

MakerNote records preserve group/document/name/tag ID, duplicates, and typed
library values. Rationals retain numerator/denominator; float values use exact
bit strings; binary/undefined values are hex; lists and structures stay typed.
These are exiftool-rs `raw_value` observations after its library conversions,
not necessarily original source-field encodings. Vendor and per-field hashes
are separately domain/version bound. Adding a field preserves unrelated field
hashes within the same engine domain. Engine/artifact changes produce a distinct
interpretation view; old observations are not relabeled or migrated implicitly.

The current Tag API provides no source spans. Therefore these are **knowledge
annotations alongside the exact byte partition**, not newly proven partition
children. Unknown bytes remain covered exactly; no MakerNote field is excluded
from transfer hashes. There is no new semantic equivalence, merge, rewrite,
receiving, archive/cache adoption or rendering authority. Empty decoded output
means no MakerNote tags were observed, not proof that a note is absent.
Field-span/dependency provenance is the next prerequisite for stronger operations,
not a prerequisite for this advisory interpretation or exact transfer deployment.

## Bounds and ownership

The current POSIX helper (qualified on macOS) accepts only an inherited readonly source FD, reads at most256MiB,
and uses in-memory library decoding with a fixed synthetic DNG filename. It
accepts no path to an original or writer operation. The owner hashes the source,
passes the FD, validates its identity before/after, and closes it exactly once
only after known helper/group settlement. Unknown child/capture ownership retains
the source FD and original carrier; close uncertainty is never retried numerically.
Existing component inspection is separately supervised and its full SHA must
match the source observation when supported.

Limits:4096MakerNote tags,4096list/structure entries per value, depth16,
64KiB per binary field,262144encoded bytes per field and240000total output bytes.
Oversize observations refuse rather than silently omit fields. The parent bounds
captures at262144bytes. Input/output limits and a60s observation window do not
establish a hard RSS/OS-thread/CPU cap on the trusted library; timeout retains
ownership instead of claiming settlement. There is no sandbox claim.

## Actual qualification

[Evidence](../../tests/qualification/exiftool-rs-integration-actual-20261017.json)
records an offline two-job Rust build and original1KiB Canon TIFF/DNG controls.
The actual library decoded SerialNumber123456/654321. The changed field changed
private interpretation and private-byte hashes while encoded-pixel projection
stayed identical. Both the new inspector CLI and its default path passed.
Duplicate records, field-hash composition and engine-domain separation passed.
Five fake descriptor/call controls cover retained unknown ownership, no close
retry, known helper failure evidence and truncated-output refusal.

This proves the integration mechanism and that one original fixture's Canon
field was decoded. It does not prove every vendor, camera, field or original
ExifTool behavior. dng-compare's richer flags still have documented parity gaps;
use its post-merge analysis and scoped oracle tests when qualifying more families.
No source photo, retained camera file, Adobe, SDK or transport was invoked here.
