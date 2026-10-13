# Reviewed standalone preview design: integration findings

Status: **review integrated; renderer/publisher/runtime qualification pending**,
2026-10-13. This records the user's coordination request and the current
[handoff](../LIGHTROOM-MONITOR-PREVIEW-HANDOFF-20261013.json),
[Astra review](../../photo/preview-generator/ASTRA-MONITOR-REVIEW.md),
[modern storage design](../../photo/preview-generator/MODERN-STORAGE-DESIGN.md)
and [renderer feasibility findings](../../photo/preview-generator/common/RENDERER-FEASIBILITY.md).
The preview workspace currently contains design/receipt files, without a
generator implementation or qualified standalone renderer.

## Ownership and sequencing

The existing Lightroom takeover session owns receiver acceptance, finite
native oracles and the preview implementation/publisher. Unison's
`/root/preview_generators` task has received and acknowledged the reviewed
design and owns interface integration/review; it does not create a competing
native publisher. Rendering, registration and subsequent storage ownership
are separate acceptance gates.

The full review/findings were queued successfully to the takeover parent for
its existing preview implementation task. Direct input to that unloaded
spawned task was rejected by the app server, so forwarding uses its parent.
The [delivery receipt](../PREVIEW-REVIEW-FORWARD-20261013.json) records the queued
owner message, prior rejected attempt and local task acknowledgment. Queued
delivery is distinct from downstream acceptance or release of an oracle gate.
The updated shared handoff now records photo-parent forwarding and acknowledgment
by the original preview task at 2026-10-13 10:45:49 UTC. This closes downstream
review delivery for that recorded handoff. The later [exact oracle-contract
acknowledgment](/Users/alexy/src/photo/preview-unison-coordination-20261013/ORACLE-CONTRACT-CORRECTION-ACKNOWLEDGED.json)
records the original preview implementation owner accepting every correction,
reading the independent review and auditing the pinned direct-probe source.
The exact correction is acknowledged; the external oracle window remains closed.
The 2026-10-13 12:14:41 UTC acknowledgment now includes the orientation mapping
correction recorded in the [source audit](preview-oracle-source-audit-20261013.md).
The earlier logged-only ImageCacheEntry finding is historical. The current
server pin is `82c88b6612818c2f62fc22b42b840273ceaca1208813d8da7a755f7a771d8556`;
its fresh post-decode current-mapping comparison is present in source and has
independent source acceptance. The receipt records 48 mock/source cases, an
independent rerun of the 23 mapping cases, and unarmed syntax preparation, with
native mapping verification still false.
This does not establish current cache state, committed persistence or restart
recognition, and does not release an oracle window.

The takeover owner reports Lux adopted/accepted and open in stable Classic
15.6. Its newer [readiness receipt](/Users/alexy/src/photo/preview-unison-coordination-20261013/RECEIVER-AND-ORACLE-READINESS.json)
at 2026-10-13 10:45:07 UTC reports helper access verified and all seven performance
phases passed. The external oracle window is **not released**: the desktop was
last observed relocked and the root owns the catalog/oracle sequence. These
preparation/adoption receipts authorize no full generator run. This
coordination performed source/document reads and filesystem-capacity queries
only. It did not invoke Adobe, read Photo
payloads, modify Main/cache data, write preview volumes, build generators or
run heavy photo benchmarks. A handoff's transfer-status text is not a release
of the remaining oracle gate without the owner confirming the current window.

**Helper Accessibility is already granted and verified.** All seven startup
phases and the first full automatic renewal passed. The desktop was last
observed locked; the external finite oracle window remains unreleased. Receiver
acceptance is complete on active Morrobay generation 2; the owner reports stable
Classic 15.6 PID 10536 with the actual Lux Main descriptor verified. ABI
investigation continues source-only under the original photo implementation
owner, with no full generator run.

The readiness receipt binds completed native Smart/core receiver acceptance
(both exit 0, zero skips/failures) to acceptance SHA-256
`9d2be438ea619913ace0ddb1da7626d736a8a504a6a19597d5b22768fb4a526e`,
active Morrobay generation 2, current Classic PID 10536/start time, actual Lux
Main descriptor and owner identity. It also records the first full automatic
renewal. These are owner-reported observations recorded in the receipt; this
interface review does not repeat native access. Current preview work here is
**interface/review only**. Desktop unlock alone does not release a window:
the root must explicitly release a finite scope. No heavy Photo benchmarks,
external Adobe invocations or production publication begin from these receipts.

The latest takeover update confirms that all seven native performance phases
pass on autostart and Cloud UI reports Synced/Pause Syncing. This is reported
native runtime/adoption evidence. The newer readiness receipt separately reports
actual existing PreviewServer entry/callback proof. Three legacy controls were
converted with 18 JPEGs preserved exactly, but terminal native metadata was
absent; one-control registration source was reviewed without invocation.
Load/cold recognition, independent rendering, publication and the full generation
run remain unqualified. Native oracles remain coordinated by that root. No
independent live-cache mutation is part of this work.

The [concrete native findings](../../photo/preview-registration-findings-20261013/FINDINGS.json)
add a required availability dependency: the installed loader checks the highest
registered file's existence/mtime even for a smaller requested level. Missing
Quasar may therefore block Ten lower levels. This is a source-based inference;
mount-loss fallback is not runtime-qualified. Treat Quasar as required for those
registered pyramids until the root qualifies native absent-target behavior.
Physical separability does not promise independent native loading.

## Architecture adopted before implementation

The current preview `DESIGN.md` already makes Astra's review authoritative and
preserves the earlier SDK-export, 2880-target and legacy-container design as
historical evidence. Retain four explicit boundaries:

1. Read-only planning and immutable capture of source/settings/dependencies.
2. Independently hosted rendering of the captured current Lightroom edits.
3. Separate standalone Rust and OxCaml engines for pyramid policy, scheduling,
   encoding, validation and accounting, using qualified shared backends where
   appropriate.
4. A qualified offline publisher for schema-13 cache registration/root pixels,
   file placement and recoverable publication while Classic is normally closed.

Modern outputs are per-level plain JPEGs, with explicit native color/profile,
geometry, quality and registration. Keep the retained approximately 9.18 TB,
lower levels and databases on Ten. Route each newly generated highest qualified
monitor level to Quasar through a candidate canonical Ten file symlink.
Policy B includes a small crop's native bounded highest level; no upscaling
to manufacture a `_5120` name. The actual 5120×2880 display, the native
80..5120 ladder and original-resolution 1:1 previews remain distinct concepts.

Use [component placement v0](component-placement-v0.md) for logical component
identity, endpoint-local roots, transport and publication ownership. Its group
runtime/archive/journal is still unimplemented. Exact single-file SDE/0 remains
independent of this future group protocol.

## Renderer findings and proposed shared interfaces

The inspected DNG SDK renderer supplies base DNG rendering but does not apply
the complete current CRS develop record. Its present path cannot establish
current edits, local-mask or AI fidelity. Installed Camera Raw's AgImageIO/
CRContext interfaces are promising leads; no independently initialized callable
ABI with qualified host services, ownership and threading has been established.
An exported function-table name does not supply typed signatures or safe
invocation. A generic RAW render must never receive a current native digest.

These are interface requirements, not implemented schemas or APIs:

| Interface/artifact | Required contract |
| --- | --- |
| `preview-input-v0` | Catalog/settings snapshot identity; image aliases and virtual copies; root-file UUID; current develop-row identity and opaque digest; exact settings bytes; source byte identity; crop/orientation/process/profile policy; bounded dependency graph. Retain and hash exact manifest bytes. |
| Dependency objects | Immutable content-addressed source/profile/lens/mask/AI/auxiliary objects, with role, length, digest and relationships. Qualified capture owns any dependency-store extraction; paths or digest labels alone are insufficient. |
| Renderer capabilities | Pinned backend/build, supported process versions/operators/dependency types, output formats, threading and memory requirements. Unknown settings or missing dependencies hold the item. |
| Renderer request/result | Exact input bundle, qualified geometry/orientation, pixel format/profile, CPU/memory reservation and cancellation. Attest consumed inputs, supported settings, output dimensions/profile and pixel identity. |
| `preview-publication-v0` | Native pyramid identity/aliases, each level's numeric level and dimensions, long edge, length/hash, color/quality/orientation, qualified metadata-recipe provenance, root-pixels requirements and logical placement roles. Rendering emits this manifest without cache mutation. |
| Local publication binding | Actual Ten/Quasar identities and generations, owned namespaces, schema/recipe revision, capacity reservation and recovery state. Peer manifests contain no absolute link targets or executable SQL. |

For denoise, enhancement, generative edits and similar cases, establish whether
the backend consumes a derived source, stored mask/patch data or a reproducible
operation. Preserve exact dependency bytes or qualified immutable snapshots.
Do not infer `.lrcat-data` extraction semantics from a filename. Revalidate
current settings and dependencies before publication; changed inputs invalidate
prepared results.

Qualify native Library resize/sharpen/rounding/quality before assuming one
5120 render plus repeated resizing reproduces every native level. Compare
pre-JPEG pixels in matched geometry/color space, including mask regions and
edges. General export remains a separate oracle. Report held cases in coverage
and benchmark denominators.

Each run has an 18-credit CPU budget covering engine work, renderer and codec
threads. A six-thread backend reserves six credits, allowing at most three
such jobs subject to memory/I/O. Reservations last until work stops or child
termination/reap completes. Budget source-resolution RAW and intermediates,
not only final JPEG dimensions. Separate executables sharing a qualified
renderer do not represent two independently implemented Adobe develop engines.

## Native publication and oracle corrections

Preserve triggers, tombstones, aliases, unrelated records and opaque native
fields. Main/live-cache writes remain excluded. The offline recipe requires
normal Classic shutdown, controlled launch/writer exclusion, fresh complete
cache-DB/root-pixels families and before-images. Install durable payloads before
links and visible preview registration; journal every cross-volume boundary.
Native write/rewrite, trim/delete, missing-target and restart acceptance are
mandatory. Reading a symlink proves reading only. APFS does not provide a
transaction across Ten and Quasar.

All 18 JPEGs from three native legacy conversions equal their preserved sections,
yet those controls remain unregistered. Terminal observations found absent
Pyramid/level/image mappings for six inspected keys after per-key tasks cleared;
filenames and exact bytes alone do not establish recognition. Their external
AgHg AdobeRGB descriptor supplies profile evidence despite absent embedded ICC;
another modern control embeds AdobeRGB ICC. Bind the actual profile evidence as
a required dependency, rather than imposing embedded ICC on every native control.
An immediate nil loader return is not proof of an unrecoverable miss; completed
task/registration and native-load observations remain authoritative.

The existing store owns its persistent native `Auto` savepoint (autocommit false,
native transaction active). Root-owned finite oracles must never author commit,
rollback or flush that store. The prepared, unexecuted one-control `touchPyramid`
source requires preserved actual current UUID/digest/header/orientation, exact
JPEG sections, absent Pyramid/levels/mappings and no tasks. It cannot become a
generic upsert: quality changes can delete existing registered level files.
Committed readback, real load, independent bytes/metadata and cold restart remain
the next registration gates. These findings leave the production offline-only
publisher and cross-volume journal architecture in place.
Its independent source qualification comprises 16 transport and nine registration
tests (25 total), with no Lightroom request submitted. That source acceptance
does not prove registration, recognition or cold-restart persistence.

Split qualification must include smaller-level requests with the highest target
unavailable, a broken link, highest-file mtime changes, native rewrite and cleanup.
Record fallback results and any Ten regeneration/metadata changes. No independent
live oracle or mount manipulation is performed by this Unison task.

The newer handoff corrects a stale dispatch assumption in the reviewed storage
documents: `getServerHandle()` yields serialized data, not a client with
`asapRequest`. The existing-only `activePreviewServer().previewServer.server`
route now has owner-reported native entry/callback proof; the remaining current
content, load/cold recognition and durable publication checks are separate.
Do not invoke it from this integration task. Installed per-level Preview objects lack UUIDs: bind
whole-pyramid UUID/digest to current Main plus each level's digest and actual
decoded dimensions to native PyramidLevel rows containing that UUID/digest.
Never require or synthesize `level.uuid`. Preserve expected row dimensions
before decoding and compare after `maybeMakePixels`, which may update the
Preview's dimensions. Bind decoded orientation to captured current Main. The
current source also reads a fresh raw ImageCacheEntry after decode, binds its
image ID/UUID/digest to that current identity, and requires its native-effective
orientation to match captured Main. Raw nil/false may use the installed `AB`
default only after identity binding, with the receipt distinguishing native
default equality from stored equality. A stale pre-load mapping does not reject
a valid current post-decode mapping. This closes the scoped source comparison
gap; native/current-cache and cold-persistence proof remain unqualified. Do not
invent a PyramidLevel orientation column. Positive registered `fileSize` must
equal actual stable disk bytes;
positive mismatch fails evidence, while absent/zero/unknown size remains
unqualified. Native stale fallback is `lastCacheEntryForImage(imageId)` and
still requires current identity binding.

The [independent source review](../../photo/NATIVE-DIRECT-PREVIEW-INDEPENDENT-REVIEW-20261013.md)
also requires deadline checks immediately after potentially synchronous load
and decode, alongside an external watchdog. These checks cannot preempt native
code. A sequence-complete marker or existing in-memory pixel result does not
certify disk persistence or all controls passing. Fresh independent file
validation and restart/readback qualification remain required. This corrects
the oracle contract; per-level Quasar/Ten placement is unchanged. Current
handoff/design updates are acknowledged rather than overwritten by this task.

## Updated per-volume capacity

Read-only `diskutil` and `statvfs` verification at 2026-10-13 10:05:17 UTC
agrees with the newer [APFS capacity artifact](../../photo/quasar-apfs8tb-update-20261013/SPLIT-MONITOR-CAPACITY-APFS8TB.json):

| Volume | Current identity/format | Available bytes | Budget after illustrative 10% total-capacity reserve |
| --- | --- | ---: | ---: |
| Quasar | `E31B795D-FA19-4938-97E2-B6ED56A7C78F`, APFS | 8,000,162,942,976 | 7,200,060,972,236 |
| Ten | `F807D30D-753C-3975-A919-AB63DECC389A`, Journaled HFS+ | 10,336,529,219,584 | 8,336,400,705,126 |

The prior Quasar `C611…`/6 TB HFS+ identity and 5.399 TB budget are historical.
The new mount needs a new binding/capability generation; no source/backend
topology or clone receipt may be inherited solely from its reused mount name.

| Policy B cohort | Quasar planning allowance | Ten planning allowance | Model assessment |
| --- | ---: | ---: | --- |
| Capture since August 2024 gap, 134,582 keys | 1.837200 TB | 0.828267 TB | Within both current planning budgets |
| Full backlog, 761,466 keys | 9.100375 TB | 4.410985 TB | Quasar allowance exceeds budget by 1.900314 TB |

Full-backlog Quasar mean 4.009232 TB and summed per-photo P95 6.006848 TB fit
the new budget. The conservative envelope plus staging does not. Estimates
extrapolate 5,029 sampled pyramids, with sparse strata and unqualified quality/
metadata/allocation assumptions. Native output and actual allocated growth
must be measured before approving a full run. The gap fit is a planning result,
not completed rendering/registration qualification or omission of the backlog.

After the renderer/native/storage gates pass and the owner releases the
measurement window, compare both engines at 1/6/18 workers with matched input
bundles, backend/codec revisions and policy. Retain compute-only and full
end-to-end results, including reads, rendering, encoding, validation, durable
publication, DB/journal/recovery work, peak memory, per-volume allocation and
held cases. Run these before a full production build.
