# Private-tag local whole-source clone controls

Run on the qualified macOS host with the retained stock/Ox build receipts:

```sh
SHARED_CPU_CREDITS=8 make -f tests/Makefile private-dng-local-clone
```

Eight cases: two compilers × two classic TIFF byte orders × clone off/auto.
Every fixture is a private generated1MiB DNG-shaped file with one XMP field and
an unknown private tag50740. These are not photographic/Adobe-valid image claims.
Every case seeds, changes an equal-length metadata string and synchronizes,
then checks a no-op. All24 CLIs use local roots with Adobe validation disabled.
A hardlink to the receiver's old inode belongs solely to the synthetic fixture;
its original bytes must remain intact after publication.

With cloning off, local ordinary copying bypasses semantic planning. With auto,
the existing whole-source clone completes **before** semantic planning. That
ordering is explicitly asserted and receiver-basis/semantic debug traces must
be absent. Unknown private metadata therefore does not disable this local clone
path; exact target bytes and prior-basis/no-op preservation are checked.

This is NOT a receiver-basis semantic fallback test. Initial test assumptions
incorrectly expected that branch on local APFS roots; both failures and their
actual group/token closures are retained in the qualification receipt. A
transport-separated producer is required to exercise receiver-basis fallback
without defeating the preferred whole-source clone. No production preference
was added to force a less appropriate path for this test.

The runner uses prebuilt binaries pinned by two build receipts, no compiler or
SDK/Adobe/Photo inputs. It executes each local CLI serially in the containing
owned group and records its actual wait, command and log hash. The shared owner
retains the complete Unison CPUgrant through group census/reap. No server
session, socket proxy or separate helper process is launched. This adds no
physical block-sharing/write-volume, camera eligibility, decoded-pixel, timing,
new parallel-worker, canonical IO locking or full-corpus qualification.
