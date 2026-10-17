# Archive-owned managed component metadata loader

This successor connects the trusted optional archive reference to bounded UIX,
UDI and UCR metadata reads. It leaves component caching off by default and does
not yet provision a cache directory or install automatic scan/report routing.

`Update.load_component_owner_index` takes its manifest binding and digest only
from the loaded local root's optional archive hint. Disabled, unloaded, missing
or rejected optional hints return `None` without inspecting the supplied directory.
With a trusted hint it calls `DngComponents.load_owner_index`. The lower-level
loader also serves owners that already possess a separately authenticated prior
manifest reference; a newly computed self-hash is not such provenance.

The caller supplies an existing, exclusively held private0700 directory FD. The
loader opens only a trusted digest's lowercase64hex leaf, read-only, nonblocking,
no-follow and close-on-exec. Native prechecks reject known foreign objects before
open; subsequent name/FD checks require private0600 singly linked regular files,
exact bounded size and stable native metadata. Borrowed positional readers do
not duplicate or close the fresh descriptor. UIX authentication checks the full
manifest digest, binding and exact limits before following its entry digests;
every UDI entry is authenticated before the immutable index can return. Record
loading authenticates UCR binding, checkpoint and decoder inventory against the
selected trusted entry. These checks do not exclude a hostile same-UID writer;
the caller must retain exclusive snapshot access.

A missing selected manifest or record returns `None`. A missing entry referenced
by an existing manifest, foreign object, corrupt content or operational failure
propagates; no partial index or disk discovery is substituted. The owner can
pass a selected record to `SemanticWorkers.components_indexed` after metadata
read settlement. That worker still verifies the complete current source and
parser partition before refreshing views. A missing selected record is an
explicit incomplete capture there, not an invitation to silently extract afresh.

## Descriptor settlement and uncertainty

Successful loader return means every loader-owned leaf FD closed normally.
The directory remains borrowed and caller-owned. Before each close the loader
records the latest observable identity, retaining its earlier observation if the
last `fstat` fails. It marks the resource uncertain before making exactly one
native close attempt; an error never causes numeric retry.

`Cache_ownership_uncertain` carries the original read/validation failure, each
uncertain descriptor and close failure, known-held enclosing descriptors and the
borrowed directory identity. If an inner entry close is uncertain, the manifest
FD remains held rather than being automatically closed. Reader capabilities
expire, but no FD finalizer retries cleanup. The owner must retain the exception,
resource grants and directory lifetime and perform separately proved recovery.
The carrier is evidence for that work, not proof of process/group/FD settlement.
A descriptor number may already have been reused; never retry an uncertain one.

Cancellation is checked before opens and during borrowed reads and manifest
restoration. Known ordinary failures close owned leaves normally. If cleanup
itself fails, uncertainty takes precedence while preserving the original cause.

## Admission and remaining integration

The caller owns metadata-memory admission, source/cache device IO admission,
namespace lifetime and archive serialization. Metadata reads are bounded by
32848B UIX, 128KiB per UDI entry under the configured aggregate index limit, and
1MiB+80B per UCR record. These are logical metadata bounds, not RSS or physical
IO limits. No source photo, directory scan, cache creation, object deletion,
eviction, archive mutation or producer settlement happens in these readers.
No other platform silently falls back to pathname-based IO.

Next integration work is explicit namespace provisioning/lifetime management,
transactional capture and archive adoption, and normal report-path routing.
Those steps must preserve the same uncertainty carrier and resource ownership.
None requires complete private-field interpretation: opaque bytes remain exact
and later decoder revisions refine only their own dependency closure.

## Current evidence

`tests/qualification/component-cache-loader-actual-20261017.json` records current
stock/Ox Make/fullselftests and Dune compilation, 1272 production-source checks,
and all nine contained workers/groups/tokens closed under actual parent terminal
35813/42bf8f/exit0/no session. Per compiler:

- 80 loader controls cover exact metadata, missing/corrupt/foreign objects,
  symlink/hardlink/FIFO/directory refusal, private permissions, cancellation,
  normal and combined close failures, nested retention, descriptor loss and
  last-known-identity preservation, and no numeric retry/finalizer.
- Seven normal-loader checks link the unmodified native object, loading two
  trusted entries/records and retiring all leaf FDs.
- Existing 56 component/1005 checkpoint/27 publication-fault/13 reader-fault,
  1391 DNG/29 archive-publication-fault and126 worker controls pass.
- Fourteen direct archive-probe calls (two compilations plus six runtime phases
  per compiler) exercise restart loading and refusal,
  including a fresh-process load through the actual trusted archive hint and
  off/missing/corrupt-hint refusal without touching an arbitrary directory.

Fault interposition exists only in separately compiled disposable objects.
Tests use original tiny generated data, not camera/Adobe/SDK/transport or
production files. Earlier closed test-expectation and Ox owner-mode annotation
failures, and the pre-identity-fix pass, remain recorded with their own scopes.
This is not a hardware power-loss, physical-IO savings or production-deployment
certificate.
