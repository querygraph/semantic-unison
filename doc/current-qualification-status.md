# Implementation status, 2026-10-15

The full SOL.md goal is active. This is a current evidence index and remaining-work
list, not a completion certificate. Historical qualifications retain their pinned
source/platform scopes; a passing current build does not rerun every historical
fault or compatibility test.

| Requirement | Implementation and evidence | Remaining qualification |
| --- | --- | --- |
| Reuse upstream clone paths | `wholeFileClone`, `CloneRange`, `copy.ml`; [whole-file controls](../tests/whole_file_clone/qualification.json) | Preserve upstream/platform behavior; no new ZFS/ReFS runtime claim |
| General receiver-basis APFS updates | Ordinary files use the generic sink, independent of DNG; [cross-volume tests](../tests/cross_volume/qualification.json) | Representative workloads, physical-device performance and broader failure/property combinations |
| Semantic extensions and SDE | Static format registry; exact DNG/JPEG profiles, bounded envelopes, advisory classification and conservative fallback; `doc/semantic-delta-v0.md` | Full acceptance-matrix coverage must be audited against exact fixture scopes; unsupported layouts remain ordinary exact transfer |
| Metadata merge | Opt-in scalar merge and compact immutable common metadata bases; [quota/merge evidence](../tests/sdk_container_receive/quota-merge-qualification.json) | SDK-gated production merge receiving request below; no general rendering-field or arbitrary RDF merge claim |
| Optional Adobe validation | Per-candidate off/warn/require gate, driver pin/receipt checks, CPU budget and cancellation; actual SDK receive/host/frozen-output pilots are separately pinned | Broader real-camera/copy-only corpus and production-path merge receiving; experimental native host remains separate |
| Stock and OxCaml builds | Both current full Make builds+selftests, 41 helper groups/compiler and five receiving diagnostic cases/compiler [pass](../tests/validation_process/group-integration-qualification.json) | Preserve Make/Dune/platform qualification scopes; compiler-checked ML boundaries do not prove C/native contracts |
| Coordinated workers/resources | Immutable worker jobs, bounded mailboxes and shared weighted permits; [checked workers](../tests/checked_worker/qualification.json), [resource integration](../tests/dng_backend_resources/qualification.json) | Production native threads, RSS, cancellation and scaling; estimates/covered allocators are not whole-process enforcement |
| Performance | Functional read/write/wire measurements and small synthetic sync matrices exist | Representative warm/cold repeated full-sync measurements, stage timings, RSS/FD peaks and storage topology; no broad speedup claim |

## Immediate next gate

[Fresh six-call request](../tests/qualification/sdk-live-merge-request-v1-20261015.json)
is **source-ready, runtime-unadmitted**. It proposes stock-client/Ox-server
production receiving over three retained generated codecs, twelve scalar states,
six SDK calls and four CPU credits, with an independently owned 300-second worker
aggregate. Wrapper preflight before supervision is explicitly outside that limit.

[Full mock receiving](../tests/sdk_container_receive/live-merge-full-mock-qualification.json),
[CLI-owner lifecycle](../tests/sdk_container_receive/live-merge-owner-lifecycle-qualification.json)
and [aggregate lifecycle](../tests/sdk_container_receive/live-merge-aggregate-qualification.json)
pass. Source-only native preflight and seven admission refusal controls pass.
No SDK execution has occurred under this new request. Root must issue a fresh
exact admission/deadline; old slots are consumed. No retry follows ambiguity.

After actual native closure, independently verify both endpoints' SDK receipts,
exact output hashes, no-op identity, every actual parent/CLI/aggregate terminal,
six retained-helper observations and unresolved-marker absence. A mock result or
an observed zero before reap is not a substitute for that native result.

## Boundaries that remain explicit

- Photo Root/original preview owner owns Lightroom, renderer fidelity, preview
  generators, Ten/Quasar placement and publisher recovery. Those are not Unison
  deliverables and do not establish semantic-DNG validation or preview reuse.
- Source photos and production workflows remain untouched. Current fixture work
  uses generated inputs in private temporary roots.
- Deterministic and manual Make checks are available. Fuzz/sanitizer campaigns
  remain user-run, as requested; no automatic campaign is started by a goal turn.
- Physical APFS block sharing/write amplification, power-loss durability and
  escaped-process/owner-SIGKILL recovery are not inferred from logical counters,
  exact hashes, process-group observations or ordinary restart tests.
