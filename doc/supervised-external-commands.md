# Supervised external commands

POSIX external copy, merge and diff commands use `SupervisedExternal`, sharing
the same CPU/child supervisor as SDK validation and semantic domain jobs.
Helper-only invocation initializes that shared owner without starting worker
domains or semantic resource/I/O admission. Later worker startup reuses the
same supervisor. This prevents separate independent CPU budgets in one
endpoint process; it is not a machine-wide cross-process quota.

Settings are endpoint-local and are not installed by remote preferences:

| Setting | Default | Meaning |
| --- | --- | --- |
| `externalhelperthreads` | 1 | Declared complete CPU weight of each configured helper, within `semanticworkers`. |
| `externalhelpertimeout` | 3600 | Maximum execution seconds after CPU admission; increase for long foreground jobs. |
| `externalhelperoutput` | 4 | Captured MiB per stdout/stderr stream. |

The thread weight reserves permits; it does not limit arbitrary programs'
thread creation. Child memory, child/global descriptor ceilings and physical
disk I/O limits remain outside this contract. Windows retains the explicitly
unsupervised legacy backend pending a native supervisor implementation.

Copy argv calls preserve the caller's original argv[0], argument boundaries,
startup PATH resolution and inherited environment, including SSH settings.
They add no shell. Existing formatted merge/diff command strings still execute
through `/bin/sh -c`. Helpers receive EOF on stdin and must remain foreground,
finishing their output before exit. Interactive GUI launchers need a mode that
waits for their actual job; deliberately detached processes are outside the
process-group contract. Existing stdout/stderr result formatting is retained.

CPU admission waits asynchronously on the owner loop. Active work uses no
hash/parse worker domain. Cancellation, signals, deadlines, output overflow or
supervisor errors reject only after the direct child is reaped and owned
resources settle. Connection teardown retains the existing synchronous
kill/reap safeguard. Unexpected kernel refusal/uninterruptible waits and
escaped descendants are not bounded by this layer.

Ordinary nonzero merge/diff exit statuses remain available to their callers.
External copying now rejects a nonzero exit before receiving validation or
publication, even when the helper wrote a complete, correctly sized candidate.
That failed temporary may still be available to Unison's separate exact resume
policy on a later attempt; this is not transactional rollback of helper writes.
No helper may use timeout or truncated output as successful production.

The [qualification](../tests/supervised_external/qualification.json) combines
real generic helpers, an actual shared-budget hash worker, copy publication
controls and the existing receiving/ownership/settlement suites. Synthetic
bytes establish lifecycle/routing, not Adobe validity, pixel fidelity, measured
throughput or hard whole-process resource caps.
