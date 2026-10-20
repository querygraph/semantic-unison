# Built-in DNG merge successor: actual result

Both compilers passed all 13 built-in DNG merge cases on 2026-10-20, with
production at `8581f357`:

- stock: `current-dng-merge-receiving-stock-20261019-01`;
- OxCaml: `current-dng-merge-receiving-ox-20261019-01`.

Each run made 29 CLI calls and 9 fake validator calls. The owner audited every
call from raw captures while it still held EXglobal IO and CPU00..07, then
closed both. An independent post-closure replay under CPU04 matched both owner
audits exactly. [Receipt](../tests/qualification/current-dng-merge-receiving-actual-20261020.json).

What the run shows:

- **Converging merges.** `disjoint` and `swapped` merge both replicas to the
  exact target bytes. One receive gate runs per replica, and the following
  no-op calls no validator.
- **Rejection and retry.** In `second-receiver-reject` the first replica keeps
  the merge and the second keeps its own bytes. The item fails with exit 2, and
  a retry re-gates both replicas and converges. That is the `10c5d159` fix
  observed end to end; the old harness had passed this case while Unison
  actually aborted with "New archives are not identical".
- **Declines with exact diagnostics.** Nine declines are accepted only with
  the exact client diagnostic each case designates, and they leave both
  replicas byte-identical and no merge temporaries:
  - competing scalar edits;
  - protected or non-allowlisted packet bytes;
  - a missing or stale common version;
  - an unknown policy version (`8581f357`'s explicit message);
  - the merge preference disabled (exit 1, skipped);
  - a resource fork.

This supersedes the bare `tests/dng_merge/run.py` evidence. Its scope is
synthetic 64 KiB containers with fake validators; it makes no SDK, camera
payload, Lightroom or performance claim.
