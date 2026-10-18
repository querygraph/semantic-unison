# Resource follow-up after I/O-scope retention

This source review follows the qualified pool/domain and Runtime scheduling-FD
changes, not a claim that all close owners have been audited. The companion JSON
pins the current files and the bounded self-task observation.

## Memory capability result

Installed Mach headers expose task_set_phys_footprint_limit, but the actual
self-task16-MiB request returned8/KERN_NO_ACCESS. No allocation followed that
refusal; a separate baseline touched32 MiB and returned normally. Neither the
header nor a successful setter would by itself prove hard RSS, inheritance or
whole-descendant containment. Leave production hard RSS refusal unchanged.
Do not replace the requirement with payload credits, allocator callback coverage,
RSS sampling, a watchdog, or macOS RLIMIT_AS/RSS assumptions.

## Validation file wrapper

CandidateValidation.with_descriptor aliases ValidationDescriptor.with_file.
That implementation already prepares/root-links its owner and pending promise
before opening, consumes close authority once, retains uncertain close evidence
and returns a pending promise instead of ordinary completion. Do not relabel it
as the plain-close implementation that used to exist in Runtime.with_io_file.
Its recognition/hash callbacks use qualified worker replies, which remain
unsettled on worker-reader/duplicate uncertainty. Other callback types and
pre-return/native wrapper failures need their own scope-specific review.

## Progress since the original inventory

Prepared raw-pair ownership, nonce single-close ownership and the tracked native
parent API now have separate qualification receipts under tests/qualification.
The current SemanticRemote successor also uses that native acknowledgement in its
prepared parent ledger; caller qualification and current builds are sealed
in remote-parent-caller-actual-20261018.json. These fixes replace the raw close
paths described in the historical inventory below; they do not establish opaque
directory ownership or aggregate process budgets.

CandidateValidation enumeration now uses Fs.with_directory with prepared opaque
DirectoryOwner metadata/callbacks before Unix.opendir. Close is single-attempt;
original scan/cancel and uncertain close failures remain together. Runtime's
carrier classifier and complete tree guard retain the borrowed lifetime, including
legacy unadmitted manifests. Both stock/Ox Make/Dune and actual fixed directory/
tree/Runtime regressions are qualified in directory-owner-actual-20261018.json.
See opaque-directory-ownership.md for exact scope and preserved failed controls.

This does not complete every directory consumer. Next audit Os.childrenOf and
Files.get_files_in_directory exception paths: the former legacy wrapper can lose
the original read error on uncertain close, while the latter only closes on EOF.
Their borrowed scopes must not retire on an ordinary prefix while a known-open or
uncertain directory remains. Prepared System wrappers alone do not prove those
callers' complete lifetimes. Do not guess numeric FD identities for directory
objects, retry uncertain closes, or infer native Windows runtime from a Darwin
signature compile. Aggregate descendant FD/RSS and full baseline accounting remain
separate.

## Original native/remote ownership inventory (historical)

SemanticRemote.held_files currently sets closed before iterating raw closes,
records only the first ordinary Unix error, and has no per-descriptor retained
carrier. close_files_noerr and close_unborrowed_files swallow those close errors.
Candidate cleanup can consequently unlink its private stage after unqualified
close settlement. The bound native publication path separately retains actual
StagePublication.Ownership_uncertain, but loose basis/output/parent raw-FD closes
still use close_fd_noerr and do not themselves set scope.uncertain. These are
source control-flow findings, not evidence that prior successful runs leaked.

The successor must prepare pair/single-descriptor ledgers and retention links
BEFORE clone-stage acquisition, adopt each returned raw handle before allocation,
and preserve each close error/identity plus the primary failure. Do not construct
an ownership list after acquisition and rely on a catch that swallows rollback
close errors. Native name ownership and descriptor ownership are separate:
unlink/disarm must be gated by actual known settlement and borrowed use, not a
closed flag set before calling the OS. Registry release_noerr must not erase the
retained state. Busy-work completion and protect_publication_scope must return
preallocated pending promises for any retained descriptor/native carrier, even
when an observer-installation error obscures the original cause.

The nonce /dev/urandom close and validation directory closedir wrappers also
need single-attempt retained ownership rather than a plain exception followed by
ordinary transaction retirement. Fs/System.opendir constructs callbacks after
Unix.opendir, so preparation failure and returned opaque directory handles need
explicit treatment; do not invent numeric FD ownership for a directory object.

Qualification should cover both closed-before-error/reused-FD and error-before-
settlement, paired failures, pre-record registry handoff, publication abort,
connection cleanup while borrowed, cancellation, and repeated cleanup. Keep
source bytes, original failed receipts and name-owner journals; no generic close
retry or automatic stage deletion on uncertainty. All control inputs can be
original synthetic disposable files; actual camera/SDK/transport bulk IO requires
its separate current coordination.

## Still separate

The optional endpoint FD96 qualification bounds each process, not the sum of
all descendants. Complete acquisition admission/baseline attribution, supported
memory containment, representative benchmark matrix and final integration still
remain in SOL scope. This review creates no execution admission or resource hold.
