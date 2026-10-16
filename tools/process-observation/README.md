# Per-process OS observations

`task_info.c` queries Darwin `proc_pidinfo(PROC_PIDTASKINFO)` using the installed
OS SDK's struct and its returned-size check. It reports resident/virtual bytes,
thread/running-thread counts and raw native CPU-time counters. CPU counter units
are deliberately uncalibrated. A failed/missing observation reports
`available:false`; it is never a zero resource count or process-absence proof.
Other platforms have an explicit unqualified result, not a hand-written ABI.

The probe does not retain a PID or own processes. A future integration must bind
its exact artifact and queried PID to an actual retained child, bracket query
times, preserve missing samples, and separately establish process/group/FD
closure. It must not query a released/reusable PID or infer sampled peaks,
process-tree RSS, CPU affinity, hard thread/RSS caps or physical IO savings.

[Actual source/component qualification](../../tests/qualification/os-process-observation-actual-20261016.json)
compiles with installed headers and observes one original Python child with six
waiting threads plus its main thread. Three snapshots report at least seven
threads and positive RSS; six invalid PID forms reject, unavailable remains
unknown, and the child/group/outerUnison8 ownership closes. No SDK, Adobe,
camera/Photo payload or EXglobal IO is used.

This observer is **not integrated into the frozen shared SDK V1 request**.
That request remains validation/task/allocator parity only. Any later SDK
observation requires a fresh source-bound executor and its own native admission.
The observer's subprocess overhead must be disclosed in timing interpretation.

`tests/process_observation/retained.py` adds a synchronous owner-thread sample
collector. It refuses released/replaced child reservations and cross-thread
queries, skips terminal children without reaping, bounds sample count and
brackets each query with monotonic timestamps. Missing observations have no
synthetic counters. Query exceptions propagate so an unresolved probe cannot
be mislabeled as a missing measurement. The adapter remains responsible for
its own probe-process settlement; the collector never proves release.

[Six injected controls](../../tests/qualification/retained-process-observation-source-20261016.json)
passed under canonical Unison00..07, with actual test child/group settlement and
closed tokens. These controls use no OS probe or SDK. The collector is not yet
integrated into an SDK owner loop and does not extend the completed V1 matrix.

The direct-child component now accepts an optional synchronous observation
factory. Its default unobserved path stays unchanged. Observations occur while
the leader is unreaped, stop at terminal state, and remain separate from the
subsequent group census, wait4 and capture closure. Observer failures propagate
as retained ownership with the observer and child attached; no signal or reap
is inferred from measurement failure. Observation deadlines are observation
budgets, not hard bounds on a separately owned query adapter.

[Actual child-loop integration](../../tests/qualification/observed-child-integration-actual-20261016.json)
passed two integration groups, three unobserved-child regressions and six inert
fault groups. Two original observed Python children exited0/7 and were reaped
after group closure; bounded injected unavailable observations survived exactly.
No OS probe or SDK ran. A native successor still needs a pinned probe adapter,
separate probe-child closure and independent observation-result audit before
review/admission. Completed SDK V1 receipts keep their historical source pins.

`tests/process_observation/probe.py` is the pinned query adapter. Each call
checks the probe's no-follow regular-file identity and SHA before and after
execution, bounds capture and observes a separately retained probe process.
It records actual probe outcomes before parsing and propagates close/ownership
uncertainty. Artifact checks are cooperative mutation fences, not atomic
execution against a hostile path replacement.

[Actual adapter integration](../../tests/qualification/retained-os-probe-actual-20261016.json)
collected three Darwin OS snapshots on one original Python child, with all
three probe children independently reaped after group closure. The observed
child and outer owner also closed, and canonical Unison8 tokens were released.
No compiler, SDK, photo payload or EXglobal IO ran. This qualifies this finite
probe integration; it does not measure SDK resources or authorize native work.
