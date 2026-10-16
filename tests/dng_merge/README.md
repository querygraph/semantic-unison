# Built-in DNG merge integration

Run against an already-built current private CLI snapshot:

```sh
python3 tests/dng_merge/run.py --unison /absolute/path/to/unison \
  --receipt /private/tmp/dng-merge-result.json
```

The suite creates private loopback replicas, endpoint states, saved common versions
and synthetic validation drivers. It exercises the actual `merge` rule,
Stasher/previous-archive authority, worker materialization, ordinary two-replica
publication, receive gates and retry after second-receiver rejection. Inputs are
deterministic TIFF/DNG-shaped containers, with independently constructed target
bytes. No Adobe/Lightroom invocation or real photo is used. Logs and failures
are retained, and every subprocess has a finite timeout.

[Qualification](qualification.json) pins the source, actual built executables,
Make/Dune selftests and full integration receipts. [User contract](../../doc/dng-built-in-merge.md)
describes opt-in, conservative declines, backup retention and downgrade behavior.
