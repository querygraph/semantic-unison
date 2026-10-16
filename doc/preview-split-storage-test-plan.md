# Bounded split-preview storage qualification

Status: **source/interface plan only; no execution or publication admission**.
This makes the lifecycle/recovery gates in [Lightroom placement](lightroom-preview-placement.md),
[component placement](component-placement-v0.md), [integration](preview-design-integration.md),
and the Photo owner's Astra/modern-storage reviews into a finite test roster.
The original Photo renderer/publisher owner remains the implementation owner.

## Admission and evidence prerequisites

1. The Root-owned [post-restart highest outcome](preview-native-highest-outcome-20261013.json)
   and its [independent review](preview-native-highest-independent-review-20261013.json)
   now pass for control A. Do not replay registration or change the sealed
   highest request. Current control `10031592` is crop-capped at
   **2272×1704**; it cannot prove a native 5120 large-crop or monitor/1:1 result.
2. Separately qualify an independently authored **Ten-only closed-cache metadata
   recipe** using preserved native JPEGs, independently observed commit/readback,
   and Root-owned native reopen/load, including natively absent and populated
   RootPixels templates. The one-control native `touchPyramid`
   success is not this recipe, a generic upsert, or a cross-volume journal proof.
3. Root must then admit the finite private publisher/recovery and native observer
   slots, bind current owners/processes/paths/nonces/deadlines, and own all normal
   Classic quit/reopen operations. Symlink recognition cannot supply this admission.
   A publisher lock alone does not exclude native writers or application launch.

Native save/regeneration/trim invocation paths are **open prerequisites**, not
qualified by the existing load/touch control. The original owner must qualify
their finite fixture hooks before states 04–06; missing hooks hold those cells.
This plan supplies no private Adobe ABI signature or invented native call.

Use one run-owned disposable catalog/cache family and private Ten/Quasar namespaces,
with fresh consistent closed DB-family snapshots, including actual WAL/journal state.
Main stays read-only; no live Main/cache SQL, new cache object against retained cache,
production Quasar unmount, formatting, full run or competing publisher is proposed.
Use the already authorized private fixtures only in Root's coordinated slots.

The roster below reserves **16 logical states total**, including failures/pilots;
charge any additional setup state against that ceiling rather than adding it silently.
Use at most **8 recursive photo sources** (prefer two): A is existing `10031592`,
B is a Root-selected current large-crop control that can natively produce `_5120`.
Use existing qualified aliases/variants; no Main edit is introduced by this roster.
Creating an edit/variant requires a separately bounded Root catalog-oracle slot.
Keep total worker/backend/native CPU reservations within **18 shared credits**;
Root separately bounds observers, callbacks, actual native loads and official restarts.
Timeouts do not interrupt native work or release its lease before actual settlement.

## Common independent acceptance oracle

- Capture current Main/catalog/dependency identity and raw ImageCacheEntry before
  load, after load and after decode. Bind fresh imageId/root UUID/current digest
  before comparing native-effective orientation; label nil/false normalization.
  Preserve explicit zero/empty values. A repaired post-load map is weaker than
  an originally current pre-load map surviving restart.
- Require current whole-pyramid UUID/digest and preserved native header/profile.
  Individual 15.6 Preview levels have **digest, no UUID**: bind level digest and
  actual decoded dimensions/orientation to qualified native PyramidLevel rows.
  Require positive registered fileSize equal to actual disk bytes; unknown holds.
  Compare returned-level quality/profile/orientation against each control's
  qualified current expectations; `final`/`AdobeRGB`/`AB` are control A's values,
  not invented defaults for B. Metadata guards do not prove pixel/color fidelity.
- Record requested and actually selected level, dimensions, final/proxy status,
  profile, canonical path type/link target, inode/mtime/bytes/hash and actual volume
  identity/generation. Do not accept pending memory, originals, Smart previews or
  old-digest `lastCacheEntryForImage(imageId)` fallback as a current disk hit.
- Observe durable payload/parent operations and independent DB visibility separately
  from queue acceptance, callback completion and native decode. Drain actual pending/
  active work before releasing ownership. Restart proof requires a fresh native disk
  load, not reopening a callback against the same in-memory pyramid.
- Preserve protected lower files, live names, unrelated rows, triggers, indexes,
  aliases, tombstones and opaque native fields exactly. Intentional changes are only
  to explicitly run-owned fixture keys, with before-images and expected row/file diffs.
  RootPixels is separate auxiliary state; face/motion objects are not monitor coverage.

## Sixteen-state roster: stop at the first failed gate

| State | Smallest decisive operation | Required distinction/result |
| --- | --- | --- |
| 01 | Offline split A's qualified highest 2272 level; native highest and one lower request | Quasar target durable before canonical Ten link/registration. Decode actual selected levels; lower remains on Ten. This tests Policy B's bounded-highest exception only. |
| 02 | Native unsplit B baseline on approved current crop | Observe actual `_5120` geometry/profile/registration. Insufficient crop/detail holds B; never upscale A to stand in for B. |
| 03 | Offline split B; native high/lower reads | Same qualified native JPEG bytes and registration semantics, only placement changed. Actual 5120 disk hit differs from physical viewport fit/1:1 and may still select a lower Ten level. |
| 04 | One actual native same-key save/rewrite, with a bounded concurrent reader | Record link/target/temp/DB transitions. Following the target, atomically replacing the link on Ten, and partial in-place target writes are different outcomes. No torn accepted read; no strict-placement pass if highest ends up a Ten regular file. |
| 05 | Root-approved already-qualified current alias/digest variant regeneration, including native quality behavior | Verify new key/routing/aliases and accounted old generation. Preserve protected old/lower data. A changed digest or quality must not silently destroy an existing key's levels or escape the owned namespace. |
| 06 | Native trim/delete for one owned fixture key | Record actual link, Quasar target, levels/mappings/tombstone changes and owned orphan ledger. Reclaim only with no native, active/pending, retained-generation or journal reference. Never collect the retained 9.18 TB. |
| 07 | Make only the owned highest target unavailable; request a retained lower Ten level | Prove actual loader result, selected identity, task/registration changes and any regeneration path. Missing highest may block lower loading; record a hold unless a versioned fallback recipe actually passes. Restore only owned target. |
| 08 | Change only owned highest-target mtime; request lower | Separate timestamp invalidation from missing bytes. No false current hit, unbounded regeneration onto Ten, or unqualified registration repair. |
| 09 | Inject absent/wrong root identity or stale binding generation in the private resolver | No creation/reference/DB commit or writes to a same-named fallback directory. This proves controller admission behavior, **not** physical Quasar mount-loss or native fallback. Do not unmount production Quasar. |
| 10 | Root's scheduled normal reopen after owned rewrite/restoration | Revalidate paths/owners; fresh raw map before first load, fresh high/lower disk decode after memory is gone. Reconcile journal before launch. Reading a restored link without restart proves less. |
| 11 | Stop only owned publisher after durable PREPARED | No authoritative registration exposed; recover intent/before-images and exact owned artifacts without touching preserved state. |
| 12 | Stop after payload durability, before references | Unreferenced owned Quasar/Ten payloads may exist. Recovery verifies actual bytes/identities and either completes or retains/removes only proven-owned residue. |
| 13 | Stop after reference installation, before auxiliary commit | A link never precedes its durable target. Recovery inspects actual namespaces even if the journal's phase acknowledgement was lost. No declared complete registration yet. |
| 14 | Stop after required RootPixels transaction, before previews transaction | Qualify the one-sided two-DB state using the previously qualified populated auxiliary template; preserve the other DB and before-images. Absent/present template behavior belongs to prerequisite recipe qualification, not a hidden extra state here. |
| 15 | Stop at authoritative previews commit with outcome/phase acknowledgement uncertain | Recover from actual DB transaction/readback and verified references, not last journal label. Exactly old/complete-new registration, never a mixed or missing-component declared group. |
| 16 | Stop after VERIFIED, before launch-window release; repeat recovery | Idempotent recovery preserves committed references/aliases and never deletes now-referenced blobs on cancellation. Only then may Root release launch exclusion or advance future group/archive state. |

States 11–16 reuse the owned native-byte templates; they introduce no renderer,
new edit or extra photo source. Exercise an unacknowledged durable transition and
an interrupted commit within these reserved states. If another independent state
is needed, replace a reserved cell or obtain a new explicitly bounded Root packet.
Include a same-key/different-byte collision and an unowned sentinel in the fixture:
every recovery path must hold collisions and preserve sentinel bytes/identities.

## Receipts and decisions

Record exact Classic/schema/recipe/policy versions, input/alias/dependency pins,
volume/root generations, source guards, per-state byte/row/link before-after diffs,
owned allocation/reference ledger, callbacks/loads/credit settlement, durable
operations, independent commit readback and official reopen ownership/closure.
Capture actual durable state even when it disagrees with the journal phase.
These process-termination controls do not prove device/power-loss durability;
APFS and HFS+ flush policy needs its own explicitly scoped durability evidence.

A native writer replacing the link, unsafe concurrent target reads, unqualified
missing-highest fallback, or irreconcilable one-sided commit keeps strict split
placement held. A relinking watcher is not a passing substitute. A failed missing-
target test need not defeat separability, but affected groups must retain Quasar
as a required availability dependency until a qualified fallback exists.

Passing this roster qualifies only its finite native-byte storage/metadata recipe.
It does not qualify standalone current-edits rendering, masks/AI/dependencies,
pixel color fidelity, full-backlog capacity, performance or production admission.
Those remain separate gates; this file requests no native execution now.
