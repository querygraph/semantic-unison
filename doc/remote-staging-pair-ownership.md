# Remote staging pair ownership successor

The receiver prepares its held-files record, descriptor pair ledger, retention
link, staging path and scope callback before either clone-stage API executes.
Returned basis/output FDs are adopted with nonallocating stores before candidate
record or registry allocation. No ownership list is constructed after acquisition.

Each endpoint close consumes its authority once and records pre-close identity
and failure separately. The pair is marked closed only after known settlement.
If either close is uncertain, the pair retains its stage metadata, the remote
scope is marked uncertain, and the transaction returns its prepared pending
promise. Registry/connection cleanup cannot erase that state, retry numeric FDs,
or unlink the stage. Original operation/record/registration errors remain
available alongside both close failures. Error-before-kernel-close and
kernel-close-success/recycled-number error are both uncertainty.

Borrowed worker calls also guard recognized nested ownership carriers. Such a
carrier keeps the parent pair/borrower lifetime and scope rooted instead of
running an ordinary failure cleanup that would close borrowed inputs. Observer
setup failure is handled through the qualified BorrowedWork/RetainedOwnership
path, not an assumption that only ordinary operation exceptions occur.

For bound publication, raw pair close precedes native abort/name cleanup once
no borrowed worker remains. The native name owner has its own captured parents
and duplicated witness, so it can abort after known pair closure. If pair close
is uncertain, native abort is skipped and its captured state/name is retained.
A later native abort error can therefore coexist with an already known-closed
pair; diagnostics no longer describe those raw numbers as live known handles.

`retained_publication_pair_ownership` supplies owner-loop forensic access to the
pair ledger. Inspect held/close-attempt/cause/identity states separately; historical
FD numbers must never be retried or interpreted as live from their current
number. This observation confers no cleanup/transfer authority. The existing
remaining-descriptor query lists only unconsumed local close authorities; native
owned evidence is reported independently.

## Qualified scope

The source-bound receipt is
`tests/qualification/remote-staging-pair-actual-20261018.json`. Stock/Ox Make and
selftests pass. Twenty-four original fixed receiver cases use actual APFS clone,
SDE inspection/materialization and publication with generated8192-byte DNGs;
only peer-supported selection and source-planner delivery are replaced for
in-process execution, with no actual network. Cases cover bound and legacy
paths, read/write/dual close errors, error-before-close, callback/record/registry
failure, connection cleanup, exact output and unchanged source/basis bytes.
Eight existing native-publication uncertainty controls also pass with corrected
known-closed-pair diagnostics. No camera/SDK/Adobe input or physical IO saving,
full transport, arbitrary allocation failure, RSS or aggregate FD claim follows.

## Remaining boundaries

The independently consumed native parent FD and its exact pre-entry/consumption
contract still need their own ledger/handoff qualification. Native context
preparation/adoption can fail before and after ownership changes; do not infer
consumption from a cleared ML boolean. The /dev/urandom nonce close and opaque
directory acquisition/closedir paths remain separate work. Current Dune,
post-integration regression, complete acquisition accounting, supported hard RSS,
aggregate descendant containment and representative benchmarks remain open.
Prior source epochs and successful/failing receipts remain immutable; no old
admission is reused and no transport/camera/SDK run is authorized by this change.
