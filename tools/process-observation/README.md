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

`tests/process_observation/audit.py` independently binds returned samples to
exact probe argv/PID, the expected artifact SHA, bounded raw frames and each
probe child's actual group-before-reap settlement. It rejects duplicate raw
fields, inconsistent clocks, unknown/duplicated probe outcomes and typed-value
substitutions. Missing remains missing. This audits records; it does not rehash
the live artifact, establish parent/FD closure or infer sampling coverage.

[Audit controls](../../tests/qualification/os-observation-audit-actual-20261016.json)
reparse the saved three-snapshot component result and reject eleven corruptions.
A separate unavailable-frame case passes without zero counters. No new probe,
SDK or payload was invoked; child/group and canonical Unison8 tokens closed.

`tests/sdk_host_matrix/shared_observed.py` composes the observed child call and
probe adapter under an exact four-field contract (canonical path, SHA, sample
limit, interval). Its independent audit checks every returned probe outcome.
The SDK parent auditor accepts a separately supplied observation contract and
otherwise rejects unexpected observation records. No current SDK entrypoint
selects this mode; it still requires a versioned plan/source/dispatcher closure.

[Composed-call controls](../../tests/qualification/sdk-observed-call-component-actual-20261016.json)
passed on one original Python child plus two actual OS probes, with missing
probe-reap evidence and changed-budget records rejected. Nine existing parent
audit controls also passed. CPU8 and all test/probe groups closed; zero SDK,
photo payload or EXglobal IO calls occurred. This is component integration,
not a new native admission or resource measurement on SDK work.

The SDK entry now supports `unison-shared-sdk-host-plan/2`, whose additional
`process_observation` contract requires an exact probe path/SHA,32 samples and
a100ms interval. V1 plans cannot carry it. The execution source closure includes
the observer/probe/auditor sources and C probe source. Each selected SDK call
uses the observed component; the parent dispatcher supplies the exact pinned
contract to its independent audit before releasing worker/CPU/IO ownership.
At most384 probe calls are possible across the twelve SDK calls; query overhead
is part of observed elapsed time and precludes a direct unobserved speed claim.
The probes are sequential and share the existing two owner credits alongside
the native target1/2/6 declaration; no hard OS-thread limit is implied.

[Thirty source controls](../../tests/qualification/sdk-observed-v2-entry-source-actual-20261016.json)
passed for entry, parent and dispatcher, including V1/extra-field and missing
observation refusal. No native SDK, payload or EXglobal ran. Full fake-worker
composition and a newly frozen V2 request remain required before any new
reviewed native admission; the completed V1 grant remains consumed.

[Full observed worker composition](../../tests/qualification/sdk-observed-worker-lifecycle-actual-20261016.json)
now passed one actual worker, twelve original fake validators and twenty-five
OS probe children through the dispatcher and independent parent audit. Every
call had available samples, all groups settled, and disposable locks were
freshly reacquired; outer canonical Unison8 closed. Admission, inventory,
child argv and interpreter SHA were explicit doubles; no canonical EXglobal,
SDK or photo payload was used.

The distinct [native V2 request](../../doc/shared-sdk-host-request-v2.json) freezes
136 execution sources and29 prerequisites, including V1 actual acceptance and
the new component/worker evidence. Its plan passed metadata-only checked_plan.
It is source-prepared, not admitted or dispatched, and does not reuse V1.
