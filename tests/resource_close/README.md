# Close-ownership candidate

`ownedClose` is a candidate primitive, not linked into Unison. Its caller prepares
slots and one group before descriptor acquisition, then adopts each descriptor
exactly once. `close_all` consumes close authority before each call. A callback
exception leaves the slot uncertain, records its cause, continues the other
closes, and raises the group's preallocated exception. Future calls never retry
a settled or uncertain numeric descriptor. The owning group must stay reachable;
catching its exception never authorizes resource-credit reuse.

The operations functor permits original fake integer descriptors in fixed
controls, avoiding casts and accidental OS closes. The future Unix adapter would
use `Unix.file_descr`, an unused placeholder, and `Unix.close`; that adapter and
real close-failure settlement are not qualified here. All group mutation belongs
to one owning thread. No concurrency, pre-close filesystem identity capture,
worker response propagation, admission reservation, or OS hard limit is implied.

`run.py` compiles and executes the exact candidate on each explicitly supplied
compiler, serially. The checked-in actual receipt records stock/Ox results and
sources. Pending integration must ensure nested reader/operation/input failures
share retained evidence; ordinary failure mapping cannot discard uncertainty.
The owner must retain reservations rather than deadlocking cleanup invisibly.
See `doc/resource-enforcement-current-20261018.md` for the full requirements.

`borrowedClose` is the next candidate owner-loop bridge. It stores the original
operation outcome, attempts owned closes, and settles its preallocated Lwt
promise only if the close group is known settled. Uncertainty preserves the
original result/error plus the close failure, while the promise stays sleeping.
The caller must keep the token/group in a reachable job ledger; merely keeping
the sleeping promise is insufficient to root this owner. No retry/rescue method
can turn uncertainty into known closure inside the same process.

`borrowed_run.py` compiles the current production Lwt and BorrowedWork modules
and the exact extracted `finish_borrow`/`with_borrow` function bodies with a fake
admission gate. Its only event-loop dependency stub is the timer; observer setup
failure/polling behavior is outside this test. On both compilers, success,
operation failure and cancellation release the retiring reservation after a
known close, but all three retain borrowing and leave the outer promise sleeping
on an uncertain close. Real workers, nested readers, shutdown, connection cleanup,
OS close faults and whole-process enforcement remain unqualified.

## Isolated real worker qualification

`worker_fault_run.py` links compiler-matched production objects with a private
`SemanticWorkers` copy that substitutes only the owned-duplicate close callback.
`worker_fault.ml` really closes each test descriptor, places a fresh `/dev/null`
reference at that number, then raises an injected error. It does not inject into
nested readers, native adapters or notification pipes. Each test uses its own
64-byte file and no external validator or photographic input.

The stock/Ox participants cover known digest plus normal shutdown, uncertain
single close, uncertain input/output close after Snapshot, and an operation
failure followed by uncertain close. Fault cases check the borrowed reply stays
sleeping, pending/retained/CPU accounting stays charged, cancellation does not
settle it, shutdown stays sleeping/idempotent, new submissions refuse and the
replacement descriptors remain live. Their external controller waits for actual
process exit. That exit is the fault case's OS settlement boundary; it is not
reported as successful pool shutdown.

A source-pinned pre-fix worker is separately linked with the same close callback
and a zero-valued `retained` observation field for API compatibility. The original
close-swallowing logic is unchanged. Its premature reply settlement must trigger
the participant's `expected-retained-reply` failure on both compilers.

Full current stock/Ox Make builds and selftests passed. This qualifies the named
worker-duplicate scope only. Nested reader/channel close uncertainty, pool
creation/notification-pipe errors, native contexts, caller descriptors and hard
whole-process FD/RSS enforcement still need their own integration and evidence.
The failed helper/link attempts remain in the actual qualification record.
