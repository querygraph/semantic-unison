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
