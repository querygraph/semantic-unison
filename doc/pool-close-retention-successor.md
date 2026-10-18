# Returned-domain publication slots (2026-10-18)

DomainOwner now prepares every owner slot and join carrier before pipe/spawn.
The returned unit-domain handle is adopted by nonallocating stores, eliminating
the post-spawn list insertion and its local-only fallback. A private monomorphic
slot uses Obj.repr as a GC root; only the typed adopter stores a handle and only
a Held state can read it as a unit Domain.t. The empty unit placeholder is never
cast or joined. No domain-layout inspection or unchecked caller cast is exposed.
The adoption allocation-counter check equals its measurement-only baseline on
both compilers. This addresses a different issue from the previously rejected
idea of an unchecked fabricated domain handle.

Join authority is consumed before each API call; the array preserves all handles
and causes. join_all attempts every held slot and never retries an uncertain or
joined slot. Eighteen actual pool lifecycle modes, two direct slot participants
and four Runtime regression rejections pass stock/Ox, including original failure
immediately after the first/second handle publication with all returned handles
joined in cleanup. Make+selftests pass; evidence
`tests/qualification/domain-owner-publication-actual-20261018.json`.

Still open: current Dune qualification, queued/cancelled borrower regressions,
aggregate FD/RSS enforcement, broader benchmark and final integration. Failure
inside toolchain Domain.spawn before a returned handle remains outside arbitrary
OOM recovery guarantees. Earlier sections below preserve historical analysis.

# Runtime handoff and lifecycle fault qualification (2026-10-18)

Runtime now retains a successfully constructed pool when observer setup, tracing
or singleton publication raises. A prepared failure latch also refuses a new
pool after an unresolved constructor/publication, preserving the same carrier.
Fourteen actual stock/Ox fixed controls cover creation and shutdown stop/join
errors (before and after real join) and singleton publication. Four designated
old-runtime/no-latch regression failures prove both safeguards. Evidence:
`tests/qualification/pool-lifecycle-handoff-actual-20261018.json`. Current Make
builds/selftests pass both compilers. Prior analysis below is historical.

Still open: partial domain-handle publication under allocation failure, current
Dune builds, queued borrowers/cancellation regression, and aggregate FD/RSS
enforcement. Domain.spawn internals have a separate unrecoverable allocation
boundary; these tests do not claim arbitrary-OOM recovery.

# Current pool lifecycle checkpoint (2026-10-18)

NotificationPipe is now in the production object order and integrated into
SemanticWorkers construction cleanup, pump and shutdown. Runtime recognizes
its typed ownership carrier. Make+selftests pass stock/Ox, and twelve actual
pool fixed controls cover normal shutdown, read/write/dual close uncertainty,
and constructor failures before domains or after a domain starts but before
reader wrapper installation. Source-bound evidence is
`tests/qualification/pool-pipe-integration-actual-20261018.json`.

Stop/join errors now retain the ledger and published handles instead of being
suppressed or clearing the handle list; this source path still needs injected
join/stop qualification. Runtime singleton post-construction handoff and the
local returned-domain allocation-failure boundary remain open. Dune current
pipe integration, queued borrowers/cancellation regression, and aggregate FD/RSS
enforcement remain open. The historical analysis below is retained as design
ancestry, not a claim that old close_noerr paths remain unchanged.

# Pool ownership integration following reader qualification

Current source checkpoint: isolated branch `implementation/owned-close-retention`,
production source qualified by nested-reader-retention-actual-20261018.json and
nested-reader-dune-actual-20261018.json. This document does not claim the pool
changes below are implemented. Existing worker duplicate/reader retention stays
in force; whole-process FD/RSS enforcement remains open.

Pool creation allocates a pipe and starts domains before returning its `t`.
Its current failure cleanup suppresses stop/join and both pipe-close exceptions.
Normal shutdown closes the Lwt reader in `pump`, then closes the notification
writer with `close_noerr`. A failure can therefore lose a creation-time owner or
become an ordinary shutdown failure. These are source findings, not observed
leaks in the completed builds/tests.

The relevant close API is synchronous `Lwt_unix.close`. Its implementation
removes registrations, attempts `Unix.close`, then wakes detached operations and
raises either the close error or a callback error. Its caller cannot infer OS
settlement merely from the exception. Never retry its historic numeric FD.

Owner-scope guard source and fourteen fixed stock/Ox controls are now present.
Full production build qualification is in progress. The fixed controls use real
Lwt/BorrowedWork and extracted borrowed-admission bodies with a fake gate; they
do not by themselves qualify Runtime initialization or pool ownership.

Implementation order:

1. Add an owner-only retained-scope guard **inside** borrowed admission. Prepare
   a never-settled reply and a rooted evidence node before invoking work. For a
   recognized ownership exception, retain the original cause, actual returned
   promise and any observer-installation error; do not let ordinary failure
   mapping retire the reservation. An uncertain creation cannot rely on a pool
   object that was never returned. Do not provide a blind clear/retry API.
2. The guard must inspect the actual returned promise on failure. BorrowedWork
   intentionally reports a first observer-installation error after draining the
   borrower; that ordinary error can otherwise hide a later ownership exception.
   Preserve both causes. Classifier failure or an unexpectedly sleeping borrower
   is conservative retained ownership, not permission to release.
3. Preallocate a pool creation/pipe ledger and retention carrier before `pipe`.
   Register pipe numbers immediately after acquisition; preserve returned wrapper
   and domain handles. Do not clear a domain handle after an unqualified stop or
   join error. Known no-worker cleanup and uncertain live-domain cleanup differ.
4. Consume pipe close authority once. On uncertainty, preserve exact cause and
   pre-close evidence, root the ledger and keep shutdown/pump completion sleeping.
   Stop new work. Known close and repeated known shutdown keep normal behavior.
5. Qualify original fixed faults for partial pipe/domain/wrapper creation,
   read/write close-after-kernel-close and number reuse, callback failure,
   cancellation, repeated shutdown, concurrent queued borrowers and combined
   primary/cleanup errors. Real returned-process closure is distinct from normal
   pool shutdown. Keep prior actual source evidence immutable.

The owner-scope guard must also handle synchronous reader/cache ownership
carriers which legitimately escape the body. Worker reader uncertainty already
keeps its reply sleeping; it must not be turned into an ordinary failure by this
new layer. No generic Unix error should automatically mean uncertain ownership:
recognize source-defined carrier classes, and retain classifier failures.

Hard FD acquisition admission, pool/transport baseline accounting and supported
OS RSS containment remain separate work after ownership cannot be accidentally
released. More logging or sampled counters alone will not complete those gates.

Additional runtime boundary identified during integration review: `get` starts
the pool before storing the runtime singleton. Even after a successful pool
constructor, observer configuration, tracing and runtime record/publication can
raise. The future creation carrier must cover this handoff as well, or prepare
all fallible owner metadata before worker startup. A guard inside transaction
admission cannot alone prove singleton ownership when creation happens outside
that borrowed body. Preserve this distinction in tests and completion claims.

Domain publication needs its own fixed fault coverage. The present constructor
uses `domains := domain :: !domains` after `Domain.spawn`; this allocation can
fail while the local returned handle is the only owner. Its fallback currently
suppresses stop/join failures. A replacement must preserve both the local handle
and previously installed handles, and must not clear either on ambiguous join.
The qualified stock Domain.spawn implementation itself allocates its wrapper
after Raw.spawn. Therefore do not claim arbitrary allocation-failure recovery
inside the toolchain API from a caller-side ledger; distinguish API-returned
handle qualification from unrecoverable runtime allocation failure. A sentinel
FD or unchecked Obj cast is not an acceptable fabricated domain handle.
