# Remote semantic producer lifetime

The receiver now invokes publish, the synchronous producer and disarm inside
borrowed_with_publication. A producer may run an inner Lwt event loop, so its
synchronous type does not authorize connection cleanup to close its descriptors
or abort its name while the callback is still active. Cleanup marks closing;
after callback return, ordinary interruption closes/aborts through the existing
known owners. Original callback errors remain terminal, not copy fallback.

The borrowed classifier now includes DirectoryOwner.Uncertain. Catching that
carrier only at global admission is insufficient: the remote pair/name owner
must retain before its ordinary failure cleanup can close descriptors or unlink
the working output. Nested file or directory uncertainty retains the pair,
creation-parent/native context and exact working bytes, leaving admission pending.
Native transfer acknowledgement and close attempt semantics remain unchanged.

## Actual checkpoint — 2026-10-18

Evidence: tests/qualification/remote-producer-actual-20261018.json. Stock/Ox Make
and Dune builds+selftests pass on329 current production hashes. Four directed
cases per compiler pass: normal, connection cleanup during producer, nested
NotificationPipe carrier from actual EBADF, and nested DirectoryOwner carrier
from actual kernel close followed by EIO. Known cases restore FD census; unknown
cases retain both actual pair descriptors, stage bytes and transaction through
repeated cleanup. Foreign directory close is never retried.

Each compiler rejects two counterexamples: exact historical Remote65de6192 closes
the active producer's descriptor; removing only DirectoryOwner classification
loses the stage borrower even though global admission still observes uncertainty.
Private planner delivery is in-process, not actual transport. The24 pair-close,
8native-publication and64final publisher handoff regressions also pass. All inputs
are original8192B generated DNGs, no camera/Photo/SDK/EXglobal activity. All groups
and CPU scopes closed. Unknown fixture ownership settles at process exit, not by
an asserted normal native teardown.

Separate compact-base capture/scalar-merge descriptors and nested cache quota/
record/temp-name owners remain unfinished. Aggregate descendant FD/RSS accounting,
hard memory containment, broader benchmarks and final consolidated integration
are not established by these controls.
