# Preview storage: filesystem assessment and staged migration plan

Status: **read-only assessment and reviewable plan**, 2026-10-13. No files have
been moved, volume formatted, catalog edited or application stopped by this
work. [Component placement](component-placement-v0.md) and the
[Lightroom binding](lightroom-preview-placement.md) do not depend on reformatting
Ten. The user has offered the free space on Quasar, Apo and Lux for a possible
Ten migration; this document makes that option concrete without executing it.

**Current update:** Quasar was replaced/reformatted outside this thread and is
now 8 TB APFS, UUID `E31B795D-FA19-4938-97E2-B6ED56A7C78F`. Read-only checks
at 2026-10-13 10:05:17 UTC show 8,000,162,942,976 bytes available, or
7,200,060,972,236 after an illustrative 10% total-capacity reserve. Ten remains
Journaled HFS+, UUID `F807D30D-753C-3975-A919-AB63DECC389A`, with
10,336,529,219,584 bytes available. No further Quasar formatting is part of
the preview plan. The [current integration/capacity findings](preview-design-integration.md)
supersede the old Quasar capacity below. Earlier member/topology observations
and combined Ten-evacuation estimates remain historical; they must be reprobed
before any separately chosen migration.

## Recommendation and observed media

Use the **current APFS Quasar** and keep **Ten as HFS+ initially**. Earlier
Quasar members were observed as SSDs; the replacement's backing arrangement
requires a fresh topology check before storage operations that depend on it.
Ten reports rotational media. Apple supports APFS on both, while
optimizing it for flash/SSD. OWC specifically recommends APFS for SSD-only
SoftRAID volumes and cautions against HDD-containing volumes because prolonged
copy-on-write fragmentation can reduce performance. That supports the Quasar
choice, but supplies no evidence that reformatting Ten will speed this workload.
[Apple filesystem guidance](https://support.apple.com/en-ie/guide/disk-utility/dsku19ed921c/mac),
[OWC filesystem recommendation](https://software.owc.com/knowledge-base/should-i-format-my-softraid-volume-as-apfs-or-hfs/).

The earlier `diskutil` and canonical SoftRAID CLI/IOKit checks on 2026-10-13,
before replacement of Quasar, established this historical inventory:

| Volume | Earlier format and backing | Use relevant to this plan |
| --- | --- | --- |
| Quasar | Journaled HFS+; SoftRAID RAID 5 on four Crucial MX500 2 TB SATA SSDs | Approximately empty, proposed monitor payload root |
| Apo | Journaled HFS+; SoftRAID RAID 5 on four WD 2 TB SATA SSDs | Existing contents retained; possible temporary evacuation space |
| Lux | Journaled HFS+; SoftRAID RAID 5 on four Samsung 860 EVO 2 TB SATA SSDs | Existing contents retained, including the live Classic catalog |
| Ten | Journaled HFS+ on the reported OWC Mercury RAID 0 device; `SolidState=false`, SATA | Existing previews plus other user data; optional conversion only |

The earlier Quasar, Apo and Lux had disjoint physical-member sets in that IOKit
probe. No other SoftRAID virtual volume was observed on those three sets.
There is consequently no observed shared-member requirement to unmount Lux
when recreating Quasar. Recheck topology and all mounted sibling partitions
before the operation; names, BSD device numbers and a previous probe are not
sufficient selection criteria. Physical serials/member identifiers belong in
the private execution record, not this public architecture contract.

APFS can avoid copying unchanged blocks when cloning a candidate on the same
qualified volume. It does not remove the cost of writing newly rendered,
different JPEGs, accelerate cross-volume evacuation by cloning, or provide an
atomic transaction across Ten and Quasar. The benefit for mostly immutable
preview JPEGs is therefore smaller than for repeated metadata changes to an
existing large DNG. Snapshot retention can also hold space needed by a
migration; it must have an explicit budget.

## Installed SoftRAID support and operation boundary

`/Applications/SoftRAID.app/Contents/Info.plist` identifies the installed app as
**8.6.1**. The installed CLI is `/usr/local/bin/softraidtool`, resolving to
`/Library/Application Support/SoftRAID/SoftRAIDTool`. Its read-only Quasar result
agrees with IOKit's SoftRAID provider array. The app-bundled CLI instead
misidentified Quasar as an Apple Disk Utility volume during this inspection;
do not use that result as the execution inventory.

The installed manual exposes APFS as a volume-creation format. Bundled help
states that changing HFS+ to APFS requires **deleting and recreating the logical
SoftRAID volume**; its Erase Volume action cannot perform the format change.
OWC's published instructions agree. This is not a `diskutil apfs convert`
shortcut and does not authorize initializing the underlying physical members.
[OWC conversion guidance](https://software.owc.com/knowledge-base/does-softraid-support-encrypted-volumes/).

Local authoritative workflow references:

- [Installed CLI manual](</Applications/SoftRAID.app/Contents/Resources/softraidtool.1>)
- [Erase Volume help](</Applications/SoftRAID.app/Contents/Resources/SoftRAID Help/Contents/Resources/en.lproj/Maintaining_Volumes_Erasing.html>)
- [Create Volume help](</Applications/SoftRAID.app/Contents/Resources/SoftRAID Help/Contents/Resources/en.lproj/CreatingAndDeleting_Creating.html>)

The create help explains why other volumes on selected members may need to be
unmounted for partition-map changes. The earlier disjoint-member evidence removed
that particular coupling between Quasar and Lux; it does not replace an
immediate pre-operation check. Preserve RAID layout, optimization, capacity and
case behavior. Encryption, RAID level changes, drive initialization and software
upgrades are separate choices, not implicit parts of a filesystem change.

The Mac release notes list APFS support from 6.1 and a licensing fix in 8.6.1;
8.6 added macOS Tahoe support. APFS creation is therefore not a new feature
requiring an automatic upgrade for this installed version. Actual driver,
license, OS and volume state still need verification before a destructive
operation. [OWC Mac changelog](https://software.owc.com/support/softraid/downloads/).

## Preliminary capacity: feasible in aggregate, not yet allocated

All figures below are approximate **decimal TB** from the coordinator's
initial 2026-10-13 read-only measurements, before Quasar's replacement. These
are historical capacity figures, not current admission values. Reprobe bytes
after any reformat and
before admission. The 10% reserve is an explicit planning assumption per entire
destination volume, not a measured application requirement or approved policy.

| Destination | Earlier total | Earlier free | Illustrative reserve | Earlier evacuation budget |
| --- | ---: | ---: | ---: | ---: |
| Quasar | 6.000 | 5.999 | 0.600 | 5.399 |
| Apo | 6.000 | 2.990 | 0.600 | 2.390 |
| Lux | 6.000 | 3.491 | 0.600 | 2.891 |
| Combined | 18.000 | 12.480 | 1.800 | **10.680** |

Ten has about **9.664 TB used across all contents**, with 10.337 TB free out of
20.001 TB. Nominal headroom after these destination reserves is only about
**1.016 TB**. The approximately 9.18 TB preview figure excludes other data:
`LytroLibrary`, `ftv-takeout` and `LightroomBackups` must also be preserved.

Filesystem-used bytes are not a destination allocation manifest. Hard links,
sparse extents, allocation rounding, resource forks, extended attributes,
directories, file counts and copy-tool behavior can change the required space.
Every source item needs a destination assignment and an estimated/observed
allocation on that specific disk. A regular file cannot span these destination
volumes without introducing a separately qualified container/chunking format.
The plan should assign complete files and keep hard-link groups together.
Reserve DB/journal growth, verification artifacts, final deltas, rollback state
and maximum temporary copy overlap in addition to ordinary free-space margin.

This calculation answers whether evacuation is plausible; it does not prove
it fits. It also does not prove the future full monitor backlog fits Quasar.
The earlier rendering allowance was about 9.1 TB, requiring fresh measured
capacity work for the monitor policy. Until Ten is restored, temporary
evacuation capacity and permanent monitor payload capacity cannot both claim
the same free bytes.

## Staged execution contract

### 1. Record topology and choose the actual scope

Capture exact current volume identities, filesystem/mount generation, physical
member relationships, RAID state, free bytes, relevant sibling volumes and
active users. Record identities in a private local execution manifest with an
operation ID and a durable copy on storage outside Ten and the selected target.
Bind each proposed mutation to this record and recheck it immediately before
execution. A mount name or stale `diskN` identifier is insufficient.

Quasar is already APFS; no Quasar format action is outstanding. The optional
Ten procedure has independent
gates and should proceed only for a specific measured or user-selected benefit.
Current Lightroom Classic is active; catalog/cache quiescence, launches and
any required unmounts must be coordinated with the preview owner. This plan
does not quit it. Listing capacities does not establish a stable cache snapshot.

### 2. Bind and qualify the replacement APFS Quasar

The earlier format workflow is historical; use the already mounted APFS volume.
Verify current identity, capacity, mount path and relevant backing topology
before admitting work. Capture its **new volume identity and binding
generation**; the same mount name does not preserve old capabilities or
reservations. Qualify clone/durability operations on private owned fixtures
only in the coordinated test window, and clean those fixtures afterward.
No production split-preview profile is enabled merely because the filesystem
supports cloning; its separate native lifecycle gates remain.

### 3. Inventory all Ten data and plan a reversible evacuation

The Photo cleanup owner now protects exact-version Atlas/Bumer archives that
were formerly listed under delete. Treat them as retained source objects,
including their exact versions, in the manifest and destination budget. A
historical delete/quarantine label is not permission to bulk-delete them.
The newer [preview alignment](../../photo/mass-preview-alignment-20261013-v2/COMPLETE.json)
is metadata classification; it is not a complete evacuation manifest, verified
payload copy or free-space credit. Its 895,491 current still keys are not an
updated monitor-generation backlog. Reconcile actual reuse/build/level cohorts
before revising the older Quasar forecast.

Produce an exhaustive source manifest with root-relative names and object
types, byte lengths, exact content hashes, forks/attributes, ACLs, flags,
required times, hard-link groups and symlink text. Do not follow arbitrary
symlinks into other volumes. Classify unreadable objects and OS-managed
rebuildable material explicitly; no silent omitted directories or failed reads
may pass the erase gate. Retain source identity/change fences so a live change
invalidates the affected manifest entry.

Assign every retained item to a destination-owned operation namespace on
Quasar, Apo or Lux, preserving its original relative path in the manifest.
Avoid collisions and traversal into existing user data. Qualify the selected
copy/verification tool on representative fixtures, including macOS metadata,
large files, Unicode names and cross-volume hard-link behavior, before moving
terabytes. Copy originals; do not delete Ten files to make room during this
phase. Use per-volume I/O limits and the shared CPU budget for hashing. Eighteen
CPU workers is not a reason to run eighteen competing large copies on one disk.

### 4. Copy, freeze the final source, independently verify

Copy stable items incrementally and journal completion. Dynamic cache/catalog
families cannot be certified by independently reading their files while the
application writes. Before final acceptance, establish the coordinated closed
application/launch-exclusion window and capture consistent complete database
families, including required WAL state. Apply a final manifest delta, retaining
versions needed to detect intervening source edits.

Read back each destination independently and compare exact data/fork hashes,
metadata and namespace/hard-link expectations. Reconcile the full source tree
against the manifest and allocation ledger, not just file counts, copy exit
status or a sample. Persist a receipt for each destination and an aggregate
receipt accounting for every retained Ten object and explicit exclusion.
No unreadable, changed, unassigned or unverified item may remain at cutover.

Once Ten is erased, the distributed evacuation is only **one remaining copy**
of each assigned file, not three redundant copies. Keep verified independent
backups of irreplaceable catalogs and other user data; record recovery coverage
and any remaining single-copy exposure in the concrete cutover review. The
temporary namespace must remain protected from cleanup and new rendering jobs.

### 5. Optional Ten format, then full restore

Only after the capacity, identity, exclusion and complete verification gates
pass should the exact Ten filesystem operation be executed. Ten's currently
reported device is separate from the SoftRAID virtual volumes; select the
appropriate supported filesystem workflow from the fresh topology. Do not
reuse Quasar's SoftRAID recipe or a historical BSD disk number for Ten. Preserve
the intended partition/enclosure scope and avoid changing unrelated volumes.

Record the new Ten identity/generation and exact restore capacity. Restore all
assigned namespaces, data and required metadata to their original logical
paths, then independently verify against the retained manifest. Resolve mount
name collisions before native application access: an unintended `Ten 1` mount
is not the expected root. Update local identity bindings explicitly and reprove
capabilities; never accept the new identity just because the name matches.

### 6. Native acceptance, then release temporary storage

Run the coordinated native cache/catalog acceptance against the restored paths,
with the preview owner's existing readback/current-digest controls. Reconcile
all migration and component-publication journals before releasing exclusion.
Keep evacuation copies intact until complete restore verification and native
acceptance are recorded. Clean only owned temporary artifacts identified by
the operation manifest; preserve Apo/Lux contents and permanent Quasar payloads.

Before Ten formatting, abandonment leaves Ten authoritative and cleanup is
limited to verified owned copies. After formatting, recovery depends on those
copies: resume restore and inspection, never infer completion from a phase
label or delete a destination because its source volume is temporarily absent.
This is a journaled migration with a long recovery window, not an atomic
cross-volume switch or an already implemented Unison group transaction.

## Remaining evidence and useful measurements

No complete Ten manifest, per-disk allocation plan, source freeze, destination
verification receipt or destructive-operation record exists from this review.
Those are required outputs before the optional Ten cutover becomes executable.
The mixed HFS+/APFS architecture can proceed without it.

For a Ten decision, measure representative cache scans, random level reads,
DB registration and sustained create/delete/rewrite patterns on a suitable
disposable HDD test setup. Measure clone-candidate benefits separately from
new JPEG generation and include longer-run fragmentation/retained snapshot
cost. Report wall time, actual read/write bytes, allocated space and memory;
do not infer an HDD win from cached hash throughput or an empty APFS volume.
Use equivalent 1/6/18-worker runs where concurrency matters, with one shared
native-thread budget. Preserve current HFS+ performance evidence before any
optional migration removes that baseline.
