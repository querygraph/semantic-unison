# Lightroom monitor preview placement

Status: **architecture contract; runtime qualification pending**,
2026-10-13. This is the Lightroom binding of
[Component placement v0](component-placement-v0.md). It incorporates the
[session handoff](../LIGHTROOM-MONITOR-PREVIEW-HANDOFF-20261013.json) and the
reviewed preview-generator designs listed below. Another Codex session owns
the standalone Rust/OxCaml renderers and native publisher. This Unison work
defines the synchronization/placement boundary; it does not launch Lightroom,
edit Main/cache databases or write preview payloads to either volume.
The [integration findings](preview-design-integration.md) record the reviewed
renderer/dependency contracts, forwarding and current filesystem/capacity update.
Current coordination, verified 2026-10-14 02:18 UTC: the native window is
[suspended; all five helpers closed/restored](preview-finite-oracle-suspension-20261013.json)
after desktop relock. Three registration attempts returned
`WAIT_FOR_MAIN_CATALOG`, without native registration or UI/Main/cache mutation.
The six-file byte/full-decode result is independent-file proof only. Original
coordinator PID 18036 retains the Photo lease with zero native CPU credits;
the requested native mapping/load/decode packet remains pending. Root must
revalidate actual unlock and renew owner admission. No Adobe/cache work
starts in Unison.

Earlier release, verified 2026-10-14 02:04 UTC: the
[formal Photo Root release](../../photo/native-access-restored-59cae9953316406886d124d25ebe9be7/FINITE-ORACLE-WINDOW.json)
binds restored access, PID 2844 and the original Photo preview owner to a finite
control `10031592` registration-to-load slot, bounded to eight sources / sixteen
logical states and eighteen shared CPU credits. That owner retains
the serialized slot; Unison's [evidence request](preview-finite-oracle-request-20261013.json)
is queued through Photo Root.
Completion, native recognition and closure are pending. This supersedes earlier
locked/unreleased status below for that slot; cold restart and Quasar mount-loss
qualification remain separate. No parallel Adobe/cache work starts here.

The takeover owner reports Lux adopted/accepted and open in stable Classic
15.6. **Helper Accessibility is already granted and verified**, all seven startup
phases and the first full automatic renewal passed, and actual existing
PreviewServer transport is qualified. Receiver acceptance is complete on active
Morrobay generation 2, with historical PID 10536/start/Lux Main descriptor and owner
verified in the [canonical readiness receipt](/Users/alexy/src/photo/preview-unison-coordination-20261013/RECEIVER-AND-ORACLE-READINESS.json).
The newer [Photo-root repair receipt](../../photo/catalog-repair-progress-20261013.json)
at 15:47:03 UTC reports Lux reopened in stable Classic PID 2844 and the desktop
locked at 15:29:55 UTC / 08:29:55 PDT. Startup/menu continuation waits for unlock;
Date1540 catalog identity reconciliation and migration continuation remain
pending. Earlier process/transport/startup bindings are historical and require
fresh root-owned capture for this process. Receiver acceptance and verified
Accessibility persist. The external finite oracle window remains unreleased.
Registration/native recognition, standalone
rendering and split availability remain unqualified. Preparation/adoption
receipts authorize no full preview-generator run.
The current coordination scope is interface/review only. Receiver acceptance
and desktop unlock do not authorize native work here; the root must explicitly
release a finite oracle window bound to current ownership/application state.
No heavy Photo benchmarks, external Adobe invocations or production publisher
start from readiness receipts alone.
The original photo implementation owner [acknowledged the exact corrected
oracle contract](/Users/alexy/src/photo/preview-unison-coordination-20261013/ORACLE-CONTRACT-CORRECTION-ACKNOWLEDGED.json),
including its pinned independent review/direct-probe source. Private Adobe ABI
investigation remains source-only with that owner; project-interface compile
checks are separate, and acknowledgment is not a finite-window release.
The [source audit](preview-oracle-source-audit-20261013.md) preserves the earlier
logged-only ImageCacheEntry orientation gap and records its source correction.
The 2026-10-13 12:14:41 UTC acknowledgment pins the corrected raw post-decode
mapping guard and independent acceptance: 48 mock/source cases, an independent
23-case mapping rerun, and unarmed syntax preparation, with native mapping
verification false. It proves no
current cache, committed persistence or cold-restart result. This coordination
did not recheck the desktop or invoke Lightroom.

The independently accepted [finite source packet](../../photo/preview-generator/oracle-source-v1/SOURCE-READY-FINAL.json)
was accepted as an uncompiled typed project interface, bounded to eight recursive
photographic inputs and sixteen logical states including negatives/pilots.
The [integration findings](preview-design-integration.md) adopt synchronous
ownership, exactly-once result release and a sole backend reservation authority
under the shared eighteen-credit ceiling. Source preparation does not qualify
private Adobe initialization/rendering signatures, a generator, pixels,
registration or publication. The pinned
[ABI assessment](../../photo/preview-generator/abi-layout-qualification-20261013T223153Z/ASSESSMENT.json)
records eight C/Rust structs, 56 fields / 172 metrics, 15 synthetic typed
signatures and genuine OxCaml 5.2.0+ox C-stub transport with the accepted header
unchanged. Full uint64 uses Int64 bit containers with explicit unsigned handling;
signed status uses Int32. The [interface qualification](preview-design-integration.md)
scopes this synthetic proof to the observed target, with no private Adobe
prototypes, host/backend runtime or renderer qualification. Current inputs
must be recaptured after repairs.

The latest [private v3 staging](../../photo/mass-preview-alignment-current-20261013-v3/COMPLETE.json)
at 22:03:07 UTC and [handoff](../../photo/mass-preview-alignment-publication-66241f91142d4992a7333c88d2a8ba22/HANDOFF.json)
complete metadata alignment against 905,928 images / 895,491 current still
keys. The full stat refresh covers 966,181 files / 9,178,878,944,015 bytes;
156,253 registration-candidate keys represent 156,255 images, split into
146,476 explicit-root legacy, 984 old-format identity-bound and 8,793 modern
filename-only keys. All 987 former header holds are metadata-resolved.
All 4,299 registered sizes match actual positive bytes; 1,338 current-native
keys have exact captured associations/orientations. Decode, source freshness,
committed native recognition, restart and monitor geometry remain unqualified.
Preserve all 55 still-mapped deletion markers with the owner-reported installed
queue exclusion; they do not add a blanket unregistered-candidate hold. RootPixels
metadata, 48,046 face crops and 3,411 motion thumbnails add no ordinary monitor
or 1:1 coverage. Known standalone gaps of 485,185 other-digest / 252,676 no-file
keys total 737,861 known exact-current standalone-file gaps; with 39 unknown
empty digests, they do not define a regeneration/capacity cohort. Every
registration candidate remains production-admitted=false.
The final [geometry packet](../../photo/mass-preview-jpeg-geometry-planning-20261013-v1/RETURN-PACKET.json)
and [publication](../../photo/completed-preview-geometry-publication-324918754b8644e3ba5f5ef8b40d428f/COMPLETE.json)
complete all requested passes with all readers closed: 39,982 modern files,
4,299 native targets and 147,460 highest legacy sections, totaling 191,741
files/sections and 6,308,224 returned marker/SOF bytes. Framing holds, dimension
mismatches and observed identity changes are zero. Return-byte counters measure
neither physical read amplification nor decoded pixels. Stored crop, proxy and
quality plus provisional 5120x2880 axis fit remain conditional planning; they
prove no current crop/orientation, edit freshness, decoded integrity, native
chosen level, monitor acceptance or original-detail 1:1 coverage. Preserve all
67 missing-container historical records separately; the 1,469 modern
alternatives beside qualified legacy containers were outside the inspected
modern cohort. Its original
uninvoked image 10031592 remains the next registration/load/restart control.
The user reports desktop access unavailable, current helper owner undispatched
and native window unreleased; no full generator or unqualified offline publisher
is admitted. The handoff was relayed via Photo parent and acknowledged by the
original owner. The [durable acknowledgment](../../photo/mass-preview-alignment-publication-66241f91142d4992a7333c88d2a8ba22/ORIGINAL-PREVIEW-OWNER-ACKNOWLEDGED.json)
pins the exact mass/v3, modern geometry and compiled-interface receipts;
that acceptance does not release native admission. The same ORIGINAL owner
has [durably acknowledged the final closed geometry](../../photo/completed-preview-geometry-publication-324918754b8644e3ba5f5ef8b40d428f/ORIGINAL-PREVIEW-OWNER-ACKNOWLEDGED.json)
as source/interface evidence and retains renderer/publisher ownership. Its
seventeen verified artifact pins supply no native/runtime/publication/full-run
admission; the finite native window remains UNRELEASED. No fresh receiver/publication
admission is inferred from geometry completion or the stat-only unchanged
database-family observation.

The [registration contract](../../photo/preview-mass-alignment-source-review-20261013/ELIGIBILITY-AND-REGISTRATION-CONTRACT.json)
separates retained-byte reuse, alias-only mapping gaps, absent registration,
partial/conflicting rows, missing payload levels, stale edits and render gaps.
Classification and staging of existing Ten bytes need neither a new-renderer
benchmark nor qualified Quasar split behavior; publication and native recognition
retain their own gates. Preserve each alias orientation, stale fallback and
before-image. Do not replay an absent-metadata touch over existing levels to
repair a mapping, or relabel old-edit bytes with a current digest.
The earlier 761,466-key capacity model must be reconciled with these classes
and actual required levels before a new Quasar forecast. Protected exact-version
Atlas/Bumer archives remain retained objects in placement and migration budgets.

## Requested arrangement and observed storage

Keep the existing regular-cache namespace, lower pyramid levels and native
databases at `/Volumes/Ten/Lightroom/Alexy Previews.lrdata`. Put newly generated,
qualified monitor-level JPEG payloads in a dedicated owned Quasar namespace,
proposed as `/Volumes/Quasar/Lightroom/Alexy Monitor Previews`. Retain the old
approximately 9.18 TB and its logical namespace. Placement alone requires no
bulk recopy or legacy conversion; the user's later, optional Ten filesystem
migration would temporarily offload and restore all Ten contents under the
separate [storage migration plan](preview-storage-migration.md).
Original-resolution 1:1 previews are a distinct role and are
not requested merely by selecting a monitor level.

Read-only `diskutil` and `statvfs` checks at 2026-10-13 10:05:17 UTC reported:

| Local binding | Observed volume UUID | Observed filesystem | Total bytes |
| --- | --- | --- | ---: |
| `preview-fast` / Quasar | `E31B795D-FA19-4938-97E2-B6ED56A7C78F` | APFS | 8,001,019,707,392 |
| `preview-native` / Ten | `F807D30D-753C-3975-A919-AB63DECC389A` | Journaled HFS+ | 20,001,285,144,576 |

These are local observations, not protocol constants. The prior 6 TB HFS+
Quasar identity `C611…` is obsolete. Its earlier SoftRAID/member observations
must not be inherited as current topology for the replacement 8 TB APFS volume.
No further Quasar formatting is needed by this design.
Ten is rotational storage, so keeping its current HFS+ format is recommended
unless measured clone/snapshot benefits justify the optional migration.

Recheck identities and free space at admission/publication. Quasar's APFS format
permits candidate same-volume cloning, subject to actual operation/file checks;
new rendered JPEGs have no assumed sharing savings. Bind the replacement Quasar
to a new local generation and verify its identity before use. The
APFS DNG/update backend remains separate: ordinary verified copy plus qualified
same-volume installation must support this layout. APFS does not share blocks
between Ten and Quasar or create a transaction across them. Other endpoints
resolve the same logical roles through their own local roots.

## Geometry is part of identity

The monitor target is **5120×2880 physical pixels**. It is not a requirement
that every JPEG be exactly that shape, nor a 2880-long-edge cache policy.
For an oriented cropped source `w×h` and actual physical viewport `Vw×Vh`, the
no-upscale fit factor is `min(1, Vw/w, Vh/h)`. Actual cache level selection also
depends on panels, backing scale, zoom and the native level ladder.

The native Standard control observed levels with long dimensions 80, 160, 320,
640, 1280, 2560 and 5120. The initial high-level candidate is a **native
5120-long-edge Standard level**, with actual dimensions/rounding qualified
against Classic. For example, a 3:2 image fitting a full 5120×2880 viewport
needs approximately 4320×2880 pixels; a native 5120-long-edge level is larger.
Portrait and panorama requirements differ. Do not invent `_2880`, label a
5120-long-edge image “5120×2880,” or upscale a smaller crop to create `_5120`.

Use a versioned policy, with the variant explicit in every manifest:

- **`native-highest-at-most-monitor-ceiling/0` (preferred draft):** place the
  qualified native 5120 Standard level on Quasar when supported by source/crop;
  otherwise place that variant's one native bounded highest level on Quasar.
  Lower levels stay on Ten. Native geometry/ladder determines the component.
- **`native-5120-only/0` (alternative):** route only actual native `_5120` levels;
  small variants remain entirely on Ten. This is a different scope/capacity
  policy, not an implicit fallback from the preferred one.

Placing one highest level on Quasar does not prove every fit request reads that
disk; Classic may select a lower Ten level. If every displayed fit-level read
must come from Quasar, the renderer/native-oracle session must measure selected
levels, propose an expanded route set and re-budget it. Do not claim that
stronger result from highest-level placement alone.

**Native availability dependency:** the installed loader checks the highest
registered JPEG's existence and modification time even when loading a smaller
level. The [native findings](../../photo/preview-registration-findings-20261013/FINDINGS.json)
therefore imply that a missing Quasar highest-level target may block Ten lower
levels too. This is an installed-source inference awaiting a finite runtime
oracle, not measured mount-loss behavior. Treat Quasar as a required mount for
affected registered pyramids until native fallback passes qualification.
Independent blob placement does not attest independent native availability.

## Native identity and components

Target stable **Classic 15.6**, excluding the installed 16 prerelease. Main is
read-only at its configured catalog location. Bind a developed-variant group
to catalog identity, catalog image aliases, root-file UUID, current develop
digest, captured settings/dependency identity and render/geometry policy.

The reviewed native findings establish the following distinctions:

| Item | Required binding |
| --- | --- |
| Root UUID | `AgLibraryFile.id_global` reached through `Adobe_images.rootFile`; image-global UUID or `pyramidIDCache` is not interchangeable. |
| Current develop digest | Latest `Adobe_imageDevelopSettings` row ordered by `id_local DESC`; guard the read-only Main identity/settings snapshot before and after capture/publication. This digest is an opaque native identifier, not proof of JPEG correctness. |
| Modern level | An individual JPEG beginning at byte zero, plus actual dimensions, color/profile, quality, orientation convention, length and whole-file SHA-256. The qualified renderer attests current settings/dependencies and build. |
| Native canonical name | `<cache>/<UUID[0]>/<UUID[:4]>/<rootFileUUID>-<currentDevelopDigest>_<actualLongDimension>`, with native casing and no invented extension. A name alone proves neither registration nor current pixels. |
| Registration | Qualified schema-13 `Pyramid`, `PyramidLevel` and `ImageCacheEntry` relationships, including all aliases and native metadata conventions. |
| Root pixels | Separate `root-pixels.db` small first/root JPEG and metadata. Full cropped dimensions in its metadata do not make it a monitor or original-resolution preview. |
| Legacy preview | An AgHg `.lrprev` format-version-3 container packs levels together. A file link cannot split those internal levels. Retain it unchanged unless a separate native conversion is qualified and authorized. |

Modern PreviewDataStore schema 13, root-pixels schema 1, and legacy container
format 3 are separate contracts. Historical `PRAGMA user_version=0` does not
override the native StoreInfo versions. The native JPEG/ICC/color interpretation
must be qualified; an sRGB render cannot be relabeled AdobeRGB.
Embedded ICC is not universal: all 18 preserved JPEG sections from three native
legacy conversions lack it, while their saved external AgHg profile descriptor
is AdobeRGB. Another modern control embeds AdobeRGB ICC. Preserve actual native
profile evidence and bind its identity/location and interpretation to the group;
an absent embedded ICC alone is not a failed native-color control. An external
profile is a required dependency when the representation relies on it.

Model monitor/lower JPEGs as independently placed immutable blobs. Root-pixels
and preview registration are adapter-managed records on Ten, with dependency
edges to all declared required levels. Main and source RAW/settings/mask/profile
bundles are read-only inputs, not publication outputs. Unknown settings,
missing AI/mask/profile dependencies or unqualified rendering produce a hold.
A default RAW render must never be published under the current develop digest.

Native conversion is not registration: 18/18 converted JPEG files match their
preserved sections exactly, but all three converted controls remain unregistered.
A terminal observation found no Pyramid/PyramidLevel/ImageCacheEntry rows for
six inspected keys, with no pending/active per-key tasks and a clean store.
Canonical names and byte equality therefore establish payload provenance only;
registration, real native loading and cold restart are separate acceptance gates.
An immediate nil loader return does not establish an unrecoverable cache miss;
use completed native task/registration observations and actual load results.

## Native namespace and payload references

The candidate native reference is one **absolute file symlink** at Ten's exact
canonical level name, pointing to the verified Quasar payload. The peer-facing
group manifest carries a portable blob/component reference and logical root ID;
each receiver constructs its own absolute link from local bindings. Ordinary
Unison symlink copying is not the implementation of this policy.

Lower-level canonical files and native database paths remain on Ten. Do not
substitute an entire-cache or UUID-shard symlink: both move lower levels too.
Hard links cannot implement the requested cross-volume split. The reviewed
native Lua path builders supplied no qualified per-resolution root setting;
this is a scoped finding, not proof about every native implementation.

Existing same-key files, links, levels and aliases require identity readback.
An exact reusable payload may stay where the selected retained-data policy
allows it. A deficient or differently encoded same-key object is a collision
requiring a qualified update recipe, not permission to overwrite retained
content. New renderer/policy identities can collide with native filenames;
resolve that explicitly before publication.

## Closed-cache publisher and durable order

An offline writer is a **candidate**, conditional on native qualification. Main
writes and live cache SQL remain forbidden. Classic must be normally closed;
the controller must exclude other native/cache writers and own the launch
window. A publisher lock alone cannot prevent someone launching Lightroom.
If exclusion cannot be established, hold publication.

Before mutation, preserve fresh consistent closed database families for both
`previews.db` and `root-pixels.db`, including journal/WAL state as required by
actual SQLite state. Historical database copies are not a fresh rollback point.
Do not discard a WAL, use `immutable=1` against possibly live state, or restore
an old database after a later native session without accounting for its changes.

The qualified recipe must preserve native triggers, indexes, unrelated records,
image aliases and tombstones. In the inspected schema, deleting a Pyramid
also removes ImageCacheEntry mappings; DeletedPyramid holds tombstones. A blind
`INSERT OR REPLACE`/generic upsert is therefore not an accepted recipe.

Use the generic durable journal with the Lightroom-specific interpretation:

1. **PREPARED:** bind exact inputs/current native identities, volume identities,
   recipe/schema versions, before-images, owned output names and per-disk
   admission. No Main changes.
2. **PAYLOADS_DURABLE:** independently parse/decode/hash each staged JPEG and
   verify geometry/profile/provenance. Stage on its final volume. Flush with
   the selected, qualified per-volume durability policy, whether APFS or HFS+;
   no cross-volume sharing or rename assumption.
3. **REFERENCES_DURABLE:** install qualified lower files on Ten and verified
   high targets on Quasar before atomically installing their Ten links.
   Account for same-key collisions and preserve old payloads.
4. **AUXILIARY_COMMITTED:** apply required root-pixels records using the exact
   native recipe and its own transaction, if qualification says they are
   required. Both absent and existing root-pixels cases need controls.
5. **PUBLICATION_COMMITTED:** after every required component/reference is
   ready, commit authoritative preview registrations on Ten. Record exact
   aliases, dimensions, orientation, quality, timestamps and fingerprints;
   never invent opaque fields merely to satisfy a SQL schema.
6. **VERIFIED:** independently read back rows and references, validate the
   complete declared group and finish its publication receipt. Advance future
   Unison group archive state only here; release the launch window only after
   all unfinished journal entries have been reconciled.

Two databases plus two volumes do not commit atomically. Early interruption can
leave owned orphan payloads/auxiliary entries; recovery must not expose a false
complete registration. Roll forward only verified artifacts, or restore owned
before-images under generation checks. Never delete a now-referenced payload
just because the initiating sync was canceled.

Native restart/readback is a mandatory **qualification** of this recipe. It is
not a requirement to run Lightroom for each production render/publish operation:
the requested production generators and publisher remain standalone once the
native-compatible recipe and renderer are actually qualified.

## Native writer ownership remains an open gate

The live native store normally owns a persistent `Auto` savepoint:
`getAutoCommit()==false` and `ds._inTransaction==true`. Finite root-owned oracles
must leave its commit/rollback/heartbeat/flush lifecycle to Lightroom. This is
distinct from the future standalone publisher's own transactions while Classic
is normally closed. Our integration never repairs this state or flushes unrelated
native work.

The root's prepared one-control `touchPyramid` registration source is unexecuted.
It requires the actual preserved current root UUID, develop digest, header and
orientation, exact section bytes, and freshly absent Pyramid, all matching level
rows and target image mapping with no tasks. Existing metadata must hold the control:
`touchPyramid` can delete registered level files on a quality change. This narrow
oracle is not an upsert recipe or authorization for bulk registration. Native
owner readback still needs independently observed persistence, real load and a
normal restart before recognition is claimed.
Its independent source review passed 25 transport/registration tests with zero
real Lightroom invocations; actual registration remains unobserved.

`AgBlob.writeToFile` is native code. A successful symlink read does not establish
whether same-key native saves follow the link, replace it with a Ten regular
file, use a temporary directory elsewhere, or partially rewrite the target.
Likewise native trim may unlink the Ten name while leaving a Quasar orphan.

Qualification must exercise same-key rewrite, digest-changing edits, quality
changes/regeneration, trim/delete, missing private target, restart and bounded
concurrent readers. Record link inode/type/target, target inode/bytes, temporary
paths and registration changes after pending/active tasks drain. If Classic
replaces links, display correctness alone does not meet strict placement. If
it writes through links, concurrent-reader integrity needs proof. A repair or
relink watcher is not an accepted substitute for a consistent writer contract.

The unavailable-target gate must request smaller Ten levels while the registered
highest Quasar target is absent, unavailable through its canonical link, or
present with changed mtime. Record native loader result, returned level/current
identity, task/registration changes and any regeneration location. Qualify the
actual fallback and recovery before promising lower-tier independence; do not
assume a lower JPEG existing on Ten bypasses the highest-file check. Any fallback
recipe that changes registration needs its own qualified offline/native-owner
publication and recovery contract, with preserved before-images.

Maintain an allocation ledger for newly owned Quasar data; reclaim only after
native references, pending work and publisher/recovery references are absent.
Do not walk or collect the retained 9.18 TB merely to clean this new namespace.
Test missing targets privately without unmounting production disks. Missing
Quasar must not authorize false current-digest hits or uncontrolled backlog
regeneration onto Ten.

## Qualification and capacity handoff

The preview session's ordered gates remain authoritative:

1. Establish native geometry/ICC/metadata/registration controls in a disposable
   catalog/cache, with finite copied inputs and read-only current Main guards.
2. Prove independent offline registration using preserved native JPEGs, then
   independently encoded JPEGs from known pixels. Exclude original/Smart,
   older-digest and pending in-memory fallbacks.
3. Qualify a standalone current-develop renderer against native pre-JPEG pixels,
   including masks/local edits/profiles/crop/orientation and dependencies.
4. Prove split link/writer lifecycle and journal recovery at every transition.
5. Confirm actual physical-display level selection and representative per-disk
   capacity, then compare equivalent Rust/OxCaml 1/6/18-worker end-to-end runs.

Native oracle work uses the existing processor cache, guarding actual
FileStore/DataStore paths. The handoff corrects `getServerHandle()` as serialized
data rather than a client with `asapRequest`; the existing-only
`activePreviewServer().previewServer.server` route has owner-reported actual
entry/callback proof in its 2026-10-13 10:45:07 UTC readiness receipt. That receipt
keeps the external oracle window closed and load/cold recognition pending.
The returned whole pyramid must match the current root
UUID/digest. Installed per-level Preview objects lack UUIDs; bind actual level
digest and actual decoded dimensions to native PyramidLevel rows with that
UUID/digest. Never require or synthesize `level.uuid`. Save expected row
dimensions before decode, then compare after `maybeMakePixels`; predecode
metadata alone is insufficient. Compare decoded orientation with captured
current Main, then bind the fresh raw post-decode ImageCacheEntry to current
image ID/UUID/digest before comparing its native-effective orientation. Preserve
the raw value and label installed nil/false-to-`AB` defaults explicitly; zero
and empty string retain Lua's truthy behavior. Stale pre-load mapping remains
fallback observation rather than evidence against a current post-decode row.
The current authored source enforces this relation; native behavior and durable
recognition are unverified. PyramidLevel has no assumed orientation column.
Positive registered `fileSize` must equal actual
stable disk bytes; positive mismatch fails evidence, while absent/zero/unknown
sizes remain unqualified. Native stale fallback is
`lastCacheEntryForImage(imageId)` and must satisfy the same current identity
binding. A cache-only
callback, `flushToQueue`, filename, accepted SQL or in-memory result is not proof
of durable current-pixel recognition. Never construct `makeForPath` against the
live retained cache for an experiment. The
[independent source review](../../photo/NATIVE-DIRECT-PREVIEW-INDEPENDENT-REVIEW-20261013.md)
supports these object/row/decoded-pixel distinctions. Expiration checks after
native load and decode complement the external watchdog; they do not preempt
a blocked native call. A sequence-complete marker does not establish that
every control passed.

Current free-space admission is per disk, not the combined total. Include
allocation rounding, directories/links, journal/DB growth, rollback copies,
renderer intermediates and maximum staging overlap. Current Policy B planning
budgets are about 7.200061 TB on Quasar and 8.336401 TB on Ten after illustrative
10% total-capacity reserves. The August-2024+ gap of 134,582 keys has allowances
1.837200 TB Quasar and 0.828267 TB Ten and fits this model. The 761,466-key full
backlog has Quasar mean 4.009232 TB and conservative allowance 9.100375 TB;
that allowance exceeds the new budget, so full fit remains **unproved**. Ten's
4.410985 TB allowance fits. The older 5.399 TB Quasar budget is historical.
Native output/allocation measurements are required before a full run; these
models are not qualification or an approved reserve. Do not silently lower quality, substitute
2880, omit the historical backlog or delete retained previews to make it fit.

Both engines must use equivalent captured inputs, renderer/codec policy,
geometry, placement, validation and publication work. Include source reads,
current-develop rendering, resizing/encoding, durable writes, metadata/recovery,
peak memory, per-volume allocation and held items. Reserve the renderer's total
native thread count from the same machine budget; 18 outer jobs must not each
create an independent all-core backend. Current Unison payload credits do not
bound decoded RAW or external-renderer memory.

No runtime gate above is marked passed by this document. The new architecture
is part of the Unison goal; actual renderer/native-cache publication is owned
by the coordinating preview session and must return qualification receipts
before Unison offers this group profile for production synchronization.

## Read-only source artifacts

- [Preview generator design](../../photo/preview-generator/DESIGN.md)
- [Modern storage design](../../photo/preview-generator/MODERN-STORAGE-DESIGN.md)
- [Modern storage receipt](../../photo/preview-generator/MODERN-STORAGE-RECEIPT.json)
- [Renderer feasibility](../../photo/preview-generator/common/RENDERER-FEASIBILITY.md)
- [Astra monitor review](../../photo/preview-generator/ASTRA-MONITOR-REVIEW.md)

The sibling-repository links are local handoff references, not files vendored
into Unison. No Adobe implementation text, private catalog rows or photo
payloads are reproduced here.
