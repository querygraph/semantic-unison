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
| Metadata merge | Opt-in scalar merge and compact immutable common metadata bases; [quota/merge evidence](../tests/sdk_container_receive/quota-merge-qualification.json) | SDK-gated production merge receiving passed below; broader real-camera corpus remains; no general rendering-field or arbitrary RDF merge claim |
| Optional Adobe validation | Per-candidate off/warn/require gate, driver pin/receipt checks, CPU budget and cancellation; actual SDK receive/host/frozen-output pilots are separately pinned | Broader real-camera/copy-only corpus and representative receiving-path/camera coverage; experimental native host remains separate |
| Stock and OxCaml builds | Both current full Make builds+selftests, 41 helper groups/compiler and five receiving diagnostic cases/compiler [pass](../tests/validation_process/group-integration-qualification.json) | Preserve Make/Dune/platform qualification scopes; compiler-checked ML boundaries do not prove C/native contracts |
| Coordinated workers/resources | Immutable worker jobs, bounded mailboxes and shared weighted permits; [checked workers](../tests/checked_worker/qualification.json), [resource integration](../tests/dng_backend_resources/qualification.json) | Production native threads, RSS, cancellation and scaling; estimates/covered allocators are not whole-process enforcement |
| Performance | [Full warm128MiB x4 batch](../bench/sync/results/warm-128-v5-actual-return-20261015.json):18 configurations, five measured repetitions,108 total rows/324 CLI settlements; small synthetic matrices also exist | Representative warm/cold repeated full-sync measurements, stage timings, RSS/FD peaks and storage topology; no broad speedup claim |

## Actual live SDK merge milestone

The [six-call production live merge return](../tests/qualification/sdk-live-merge-v1-actual-return-20261015.json)
is **PASSED/CLOSED** after fresh explicit Root admission. Actual owner43830,
terminal699a51 exited0 with no session. Nine stock-client/Ox-server CLI runs and
six qualified SDKv1 validation receipts pass across three generated codecs; exact
outputs/no-op identity, nine CLI closures, six retained helper observations and
no unresolved markers were independently read back. Aggregate93039 closed/reaped
in32.486s, within300s. Wrapper preflight remained outside that aggregate limit.

Root independently accepted the sealed result; [receiver adoption](../tests/qualification/sdk-live-merge-v1-root-adoption-20261015.json) pins its receipt. The admission is consumed; no replay or
new SDK slot follows. This is functional exact generated-container receiving,
not a throughput, camera-corpus, decoded-pixel or preview-reuse qualification.
Broader native resource/scaling, real-camera corpus and representative performance
gates remain open. All Unison runtime allocations are closed.

## Completed first warm128 performance batch

The [raw measurements](../bench/sync/results/warm-128MiB-4files-20261015.json)
and [sealed closure](../bench/sync/results/warm-128-v5-actual-return-20261015.json)
prove the first prepared batch completed once after explicit user authorization
and Root scheduling ACK. Owner34823/c78138/0 and aggregate12254 closed/reaped;
all324 CLI/server settlements audited, unresolved markers empty,18credits released.
[Interpretation and all18 medians](../bench/sync/README.md) separate logical write
savings from modest warm-loopback elapsed gains. This supersedes the unstarted
status of this exact v5 batch; later sizes and broader performance remain open.

## Boundaries that remain explicit

The [bounded lifecycle controls](../bench/sync/results/bounded-lifecycle-qualification-20261015.json)
passed all eight fake-child/worker cases in6.528s, owner46880/86b330/0.
Root independently accepted25 artifact/source pins and all child settlements.
This closes the finite one-credit allocation; it does not admit timing work.
The earlier interrupted benchmark60597 remains incomplete (eight warmups,
zero measured samples), with its missing historical direct-client receipt
explicitly unqualified. Its source fix passed the later fake-child controls;
those controls do not reconstruct the missing historical receipt.

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
