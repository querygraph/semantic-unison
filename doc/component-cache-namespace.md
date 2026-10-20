# Private component-cache namespace ownership

This successor supplies a one-use macOS directory ticket under an existing,
caller-held private0700 parent. The only child name is `component-cache-v0`.
It does not automatically open the user's Unison state, provision anything in
production, select a cache for a file or enable capture/report routing.

A fresh `prepare_cache_namespace` ticket has no expected identity. Provision
attempts one `mkdirat(0700)` and refuses EEXIST rather than adopting a directory
merely because it looks private. It checks the observed child and syncs the
parent. Actual creation is recorded before any later stat/sync failure. An error
never removes/chmods the directory or retries the ticket; created/observed-identity
queries preserve recovery evidence. Observed identity is not proof of sync or
of later process/descriptor settlement. A failed provision cannot open its ticket.

Reopening requires a fresh ticket with a separately trusted `(device,inode)`.
Existing-only mode never creates a missing child. It validates parent and child
ownership/permissions and refuses wrong identity, symlink or changed binding.
The caller must persist/derive this identity through a qualified owner contract;
there is no new mutable head file or automatic restart trust. Current lstat alone
is not prior ownership. Namespace identity also does not replace the separately
trusted archive/UIX digest needed to authenticate metadata.

`with_cache_namespace` makes one no-follow/directory/nonblocking/cloexec open,
records ownership before further validation, and binds the parent, name and FD
before and after a synchronous callback. The callback borrows the directory and
must finish all work and settle any additional resources before returning: no FD
or asynchronous-work escape. Success means this scope's owned directory FD
closed normally; the parent remains borrowed. Creation/provision and scoped open
are separately one-use so a failure never silently replays either operation.

The owner must hold stable descriptors and exclusive cooperative control of
parent/child names throughout. This is not hostile same-UID exclusion, inode
lifetime attestation or a hardware power-loss guarantee. A change that prevents
safe cache reuse can decline that cache operation while the qualified stateless
component/exact-byte path remains available; incomplete private-field mapping
is unrelated and remains no global deployment gate.

## Nested uncertainty

Both leaf readers and namespace scopes use the same once-only close machinery.
A close failure retains the original callback/read failure and last observable
identity. No finalizer or numeric FD retry is installed. An inner uncertain entry
close retains its enclosing manifest and namespace FDs instead of attempting
further cleanup. `cache_borrowed_directories` reports every enclosing borrowed
directory; the singular accessor still reports the originating directory.
Known-held descriptors and uncertain close identities stay distinct. The outer
owner retains resource admission and performs independently proved recovery.

Metadata quota configuration and monotonic slots survive normal scoped close
and exact-identity reopen; no slot/config reset, refund or eviction occurs here.
This opens a safe namespace boundary for future quota-admitted stage creation,
paired capture, manifest publication and archive adoption. It does not yet
orchestrate those writes or install the path in normal reports. Directory parent
provenance, durable identity binding, IO/memory admission and caller-created
stage FD settlement remain owner responsibilities.

## Qualification

`tests/qualification/component-cache-namespace-actual-20261017.json` binds four
current stock/Ox Make/fullselftest/Dune builds and1272production-source checks.
Per compiler,67namespace fault/security/lifecycle and9unmodified-native namespace
checks pass, together with80loader/7unmodified-native loader checks and the
existing56component/1005checkpoint/27publicationfault/13readerfault/1391DNG/
29archive-publication-fault/126worker controls. Fourteen archive-probe calls
include two compilations and12runtime phases. Namespace tests cover fresh and
existing paths, two distinct empty wrong parents, wrong/replaced/symlink names,
permission changes, actual mkdir retained on sync EIO, ticket replay refusal,
quota continuity and nested known/uncertain/borrowed descriptor preservation.
The copied native fault object is now retained separately and rehashed, rather
than overwritten when building the unmodified-native probe.

The first controller61854/d0ad68/exit1 stopped before starting a sixth step when
a fresh Root RPC admission appeared. Its five completed steps all passed/closed;
that was a scheduling guard, not a test failure. After the separate RPC actually
closed, controller18854/f0c867/exit0 ran only the four unstarted steps. All nine
contained workers/groups/token sets closed. The intervening RPC is separately
recorded as an original final-auditor failure, never a namespace result or replay.
Tests used original tiny disposable fixtures only, no camera/Adobe/SDK/transport
or production directory. No throughput, physical-IO savings or platform-wide
qualification follows.
