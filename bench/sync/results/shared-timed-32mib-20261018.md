# Repeated warm generated 32 MiB sync observations

One admitted run: two generated files, three modes, workers 1/2/3 per endpoint,
stock OCaml and OxCaml, one warmup plus five measured repetitions. All 108 rows
and 324 seed/update/noop calls completed with exact output, unchanged receiver
basis and true no-op checks. All raw samples remain in the pinned result; no
replacement or retry. Shared eight-core allowance, EXglobal IO, disclosed host
activity; no quiet-machine claim.

Median **update** wall seconds (includes invocation/supervisor lifetime):

| Compiler/mode | 1 worker | 2 workers | 3 workers |
| --- | ---: | ---: | ---: |
| Stock ordinary | 1.389 | 1.380 | 1.386 |
| Stock receiver clone | 1.365 | 1.370 | 1.369 |
| Stock semantic | 2.399 | 1.707 | 1.666 |
| Ox ordinary | 1.381 | 1.355 | 1.354 |
| Ox receiver clone | 1.363 | 1.347 | 1.358 |
| Ox semantic | 2.396 | 1.667 | 1.663 |

Semantic updates reported 6,144 successfully returned logical write bytes and
201,327,048 primary-reader bytes at three workers on both compilers. Primary
reads exclude nested/legacy/helper reads; they are not total physical IO.
Ordinary/clone write counters are unknown here, not zero. Semantic wall time is
higher than ordinary and receiver clone in this dataset despite small returned
logical writes. This result supports no general speedup claim. Inclusive worker
hash/parse/verify/write and native publication samples are present, retained
separately and never summed into total commit time. CPU endpoints remain
separate; maxrss is lifetime process high water, not an aggregate hard cap.
Five samples give a nearest-rank p90 equal to the maximum, not a reliable
population-tail estimate.

The parent auditor rejected nullable group-absence booleans emitted by the
performance runner's non-strict group mode. The exact pinned Darwin producer
instead records an explicit pre-reap census of only the owned leader zombie.
A source-bound supplemental audit qualified that branch for all 324 calls;
raw bytes and nullable fields were preserved. The idle retaining parent needed
scoped recovery: actual tool53602 terminal301032/exit137/no session. Normal
parent exit and the original parent's worker wait4 are **not** claimed.
Independent recovery verified disappearance and reacquired/closed EXglobal
then Unison tokens00..07. Resource release preceded report generation.

Machine-readable samples/distributions:
[shared-timed-32mib-20261018.json](shared-timed-32mib-20261018.json).
Receipt and raw-input pins:
[actual qualification](../../../tests/qualification/shared-timed-32mib-actual-20261018.json).
This is one warm generated dataset; broader SOL sizes/topologies/upstream
comparisons and hard aggregate FD/RSS enforcement remain open.
