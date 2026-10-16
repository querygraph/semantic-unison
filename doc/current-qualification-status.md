# Implementation status, 2026-10-15

The full SOL.md goal is active. This is a current evidence index and remaining-work
list, not a completion certificate. Historical qualifications retain their pinned
source/platform scopes; a passing current build does not rerun every historical
fault or compatibility test.

Shared-machine transition: equal8/8/2 policyv3 adopted. [Build/parser and inherited locks](../tests/qualification/shared-entrypoints-actual-20261016.json) passed, followed by [actual shared sync](../tests/qualification/shared-functional-actual-20261016.json): stock/Ox workers1/2/3,18rows54CLI with independent strict client/supervisor/server/pump proofs, exact results and all tokens released. Physical IO lanes, aggregate memory and shared throughput remain unqualified. No Photo tokens or Adobe work used.

| Requirement | Implementation and evidence | Remaining qualification |
| --- | --- | --- |
| Reuse upstream clone paths | `wholeFileClone`, `CloneRange`, `copy.ml`; [whole-file controls](../tests/whole_file_clone/qualification.json) | Preserve upstream/platform behavior; no new ZFS/ReFS runtime claim |
| General receiver-basis APFS updates | Ordinary files use the generic sink, independent of DNG; [cross-volume tests](../tests/cross_volume/qualification.json) | Representative workloads, physical-device performance and broader failure/property combinations |
| Semantic extensions and SDE | Static format registry; exact DNG/JPEG profiles, bounded envelopes, advisory classification and conservative fallback; `doc/semantic-delta-v0.md` | [Twelve-row audit](acceptance-matrix-audit.md) records partial coverage and open fixture/platform scopes; unsupported layouts remain ordinary exact transfer |
| Metadata merge | Opt-in scalar merge and compact immutable common metadata bases; [quota/merge evidence](../tests/sdk_container_receive/quota-merge-qualification.json) | SDK-gated production merge receiving passed below; broader real-camera corpus remains; no general rendering-field or arbitrary RDF merge claim |
| Optional Adobe validation | Per-candidate off/warn/require gate, driver pin/receipt checks, CPU budget and cancellation; actual SDK receive/host/frozen-output pilots are separately pinned | Broader real-camera/copy-only corpus and representative receiving-path/camera coverage; experimental native host remains separate |
| Stock and OxCaml builds | Both current full Make builds+selftests, 41 helper groups/compiler and five receiving diagnostic cases/compiler [pass](../tests/validation_process/group-integration-qualification.json) | Preserve Make/Dune/platform qualification scopes; compiler-checked ML boundaries do not prove C/native contracts |
| Coordinated workers/resources | Immutable worker jobs, bounded mailboxes and shared weighted permits; [checked workers](../tests/checked_worker/qualification.json), [resource integration](../tests/dng_backend_resources/qualification.json) | Production native threads, RSS, cancellation and scaling; estimates/covered allocators are not whole-process enforcement |
| Performance | [Full warm128MiB x4 batch](../bench/sync/results/warm-128-v5-actual-return-20261015.json):18 configurations, five measured repetitions,108 total rows/324 CLI settlements; small synthetic matrices also exist | Representative warm/cold repeated full-sync measurements, stage timings, RSS/FD peaks and storage topology; no broad speedup claim |

Reusable inspector receipt/argument checks are implemented; [eight inert-artifact
controls](../tests/qualification/inspector-reuse-controls-actual-20261016.json)
and shared entrypoint controls passed with execution mocked. [Actual stock/Ox reuse on tiny independent DNGgoldens](../tests/qualification/inspector-reuse-synthetic-actual-20261016.json)
also passed, with matching16B metadata classification and full/complement hashes.
Actual [private DA clone/inspection](../tests/qualification/private-dng-clone-inspection-actual-20261016.json)
closed under one manual IO window: clone SHA/source preservation passed; both
inspectors safely declined50740. Real-camera semantic eligibility/receiving remain
unqualified. [Private-data framing groundwork](dng-private-data-next-profile.md)
now includes an inactive bounded IFD0 diagnostic locator;
[162fixedchecks/compiler](../tests/qualification/dng-private-locator-actual-20261016.json)
passed. Neither locator nor framing evidence is an eligibility proof; profiles0/1
remain unchanged and no camera payload was read in these controls.

[Physical IO coordination](shared-physical-io.md) is now source-proposed with
an unknown-global barrier and complete-member union planner. Ten pure controls
passed. Root provisioned the sole `io-lanes-v1` EX_GLOBAL barrier, adopted in
[proposalv3](shared-physical-io-proposal-v3.json). Disposable backend combined-close
controls passed; the [canonical lock-only probe](../tests/qualification/canonical-io-probe-actual-20261016.json)
and [one tiny complete-local dispatcher job](../tests/qualification/shared-io-local-job-actual-20261016.json)
passed and closed. The latter covers8synthetic cases/24CLI with both IO and CPU
released after group settlement; it does not prove receiver-basis semantic fallback.
Topology provider, general production integration and cross-project payload
qualification remain pending. CPU sharing is already implemented.

## Opaque-tag transport fallback

[Four stock/Ox client-server pairs](../tests/qualification/private-remote-fallback-actual-20261016.json)
passed12actualCLI calls under the scoped shared8+EX_GLOBAL coordinator. A tiny
generated tag50740 fixture declined semantics, then ordinary transfer used the
immutable receiver clone basis with3072logical inheritedbytes/case and exact
output/basis/complement/no-op/staging checks. All direct groups, server waits and
pumps settled, actual parent exit0, CPU/IO closed. No real-camera eligibility,
SDK/pixel validity, performance or physical storage savings follows from this.

[Distinct-byte coverage successor](../tests/qualification/private-remote-distinct-fallback-actual-20261016.json)
also passed4pairs/12CLI under a fresh admission, with1035264logical same-offset
inheritedbytes/case and all exact preservation checks. Both layouts' samples
remain preserved; no production algorithm or semantic eligibility changed.
This is reuse/path coverage, not a physical savings or throughput comparison.

## Current diagnostic module packaging

[Stock and Ox Dune build-only snapshots](../tests/qualification/current-dune-diagnostic-packaging-actual-20261016.json)
passed from matching424-input manifests (source headbbe9f60). Dune produced the
CLI and diagnostic module native/interface artifacts. Both owning tools exited0,
worker groups reaped, allUnison8 tokens closed. This is packaging evidence, not
a new CLI selftest/receiving run or semantic eligibility qualification.

## Private framing diagnostic tool

[Borrowed-stdin developer diagnostic](../tools/private-dng-framing/README.md)
built stock/Ox and passed22generated-input controls, with bounded read ranges
and native owner epoch comparisons. It has no input path argument or full-file
hash/decoder, never decides eligibility, and is not active in a DNG profile.
The executable's own timestamp check is not a native-nanosecond fence; any
camera-input executor/IO admission and exact owner epoch proof remain pending.

## Acceptance scope audit

The [twelve-row audit](acceptance-matrix-audit.md) maps the required SOL matrix to
40 pinned supporting receipt references. Every row is partially qualified;
receipt bytes were checked, not historical source parity or new runtime cases.
Real-camera receiving, power-loss recovery, hard whole-tree memory/resource
limits and broader platform/native coverage remain open. This source-only audit
ran no test, SDK, Adobe or Photo payload operation.

## Reusable read-only inspection build

[Stock and Ox inspector build-only controls](../tests/qualification/inspector-build-only-actual-20261016.json)
pass after restoring the missing xmpMerge build dependency. Retained builds pin
compiler, sources and binary; no inspector/image/SDK invocation occurred.
[Pure command controls](../tests/qualification/inspector-command-controls-actual-20261016.json)
pass under the shared owner. Copy-only real-camera eligibility/receiving is next,
subject to candidate/source-ancestry and physical IO coordination with Photo.

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

## Completed warm512 first partition

**Timing caveat:** [Root's disclosed overlap and row flags](../bench/sync/results/warm512-part0-timing-overlap-addendum-20261015.json)
supersede the original quiet-window assumption. A59.49s static disassembler
interval definitely overlaps measured1 semantic seed/early update; the previous
receiver-clone row's post-noop tail is possibly affected. Keep all samples and
medians, with no retry/replacement. No clean quiet-performance claim; exactness
and actual process closure remain passed. Raw data/original return are unchanged.

The [first512MiB part](../bench/sync/results/warm512-v9-part0-actual-return-20261015.json)
passed18rows/54 synchronization invocations: stock OCaml, one worker, three
modes and five measured repetitions. Owner74730/c65a5b/0 and aggregate52671
closed/reaped in2293.507s; unresolved markers empty,18credits released.
Median update times37.423/36.700/69.659s (ordinary/clone/semantic); semantic
returned12KiB writes over a2GiB corpus but was slower sequentially. This is
not parallel/OxCaml512MiB, full six-part, single2GiB-file or physical-I/O proof.
[Raw data](../bench/sync/results/warm-512MiB-4files-part0-20261015.json) retain
all receipts. Later partition outcomes below retain the matched frozen provenance.

## Completed warm512 stock worker6 partition

The [part1 sealed return](../bench/sync/results/warm512-frozen-part1-actual-return-20261015.json)
and [raw rows](../bench/sync/results/warm-512MiB-4files-part1-20261015.json)
record actual owner89135/96b778/exit0/no session,18rows/54CLI and aggregate69503
closed/reaped/others absent in2059.198s. Independent per-CLI/client/server/supervisor
audit passes; zero SDK helpers expected, no unresolved markers. Exact source and
runner pins stayed matched to part0. Median ordinary/clone/semantic update times
are37.027/36.344/34.209s (five measured repetitions, stockworker6).
Semantic elapsed time is about7.6% below ordinary in this warm generated test.
See later partition outcomes below; the full six-part matrix remains incomplete.
The mandatory part0 overlap addendum remains attached; no clean-cohort claim,
sample replacement or successor execution follows. Actual closure sent to Photo
Root for independent resource adoption;18credits released on the Unison side.

## Boundaries that remain explicit

The [Oxworker8 part5 return](../bench/sync/results/warm512-frozen-part5-actual-return-20261015.json)
and [raw data](../bench/sync/results/warm-512MiB-4files-part5-20261015.json)
pass18rows54CLI: actualowner52232/2b05a9/0/no session; aggregate51654 reaped0/others
absent in2070.618s, fullclient/server/supervisor auditPASS/unresolved empty.
Frozen14execution21runner pins unchanged. Medians36.346/35.664/34.684s
(ordinary/clone/semantic), roughly4.6% lower semantic elapsed than ordinary in
this warm generated control. All five bounded source-activity disclosures stay
attached; exactrowimpact unknown, no absolutelyquiet claim. Five complete512
partitions now exist, but part3 remains failed/incomplete: no fullsix-part
qualification or physicalIO/compiler-speedup claim. Standing8/8 token ownership and finite functional sharing are qualified above;
physical IO/memory isolation and throughput remain unqualified.

The [Oxworker6 part4 result](../bench/sync/results/warm512-frozen-part4-actual-return-20261015.json)
passes18rows/54CLI: actual57036/f228d4/0/no session, aggregate30613 reaped0/others
absent in2082.230s, independently audited client/server/supervisor cleanup,
SDKhelpers0 and unresolved empty. Source14/runner21 pins unchanged. Ordinary,
clone and semantic medians36.490/35.854/35.019s; semantic about4% below ordinary
in this partition, slightly slower than stockworker6's separate-slot result.
No general compiler-speedup claim. Part3 stays incomplete; part5 passed above;
the series retains all timing caveats and no full-matrix/physicalIO claim.

The [settlement successor lifecycle](../bench/sync/results/native-settlement-lifecycle-actual-return-20261015.json)
passes seven original-Python cases under onecredit: actual owner3736/16df12/0,
aggregate1705 reaped/others absent in2.387s. Delayed normal EOF, legacy refusal,
fault TERM, TERM-ignore KILL, nonzero exit, expired budget and actual proxy echo
all retain cleanup proofs; no unresolved markers or source changes. This
qualifies the main-harness successor's finite lifecycle, not performance or
the cause/completion of historical failed part3. No nativeSDK/Photo/compiler
or benchmark ran; no new timing allocation follows.

The [Oxworker1 part3 attempt](../bench/sync/results/warm512-frozen-part3-failed-return-20261015.json)
is FAILED/INCOMPLETE:16completed exact rows/48successful CLI, then a seed's
post-output-EOF server settlement grace failure (client/server0, supervisor70).
Actual parent76640/df5ca2/exit1 and aggregate88119/reaped1/others absent closed.
Independent49CLI readback proves all clients/supervisors/servers reaped and
pumps joined; private fixtures removed. Generic expected_helpers0 unresolved
marker is preserved and explained, not erased or represented as successful
qualification. Homebrew compilation overlapped this attempt; impact and cause
of settlement failure remain unknown. Raw partial samples and timing disclosures
remain intact; no final medians/replacement/retry/fullpart success claimed.
Root has actual closure for resource adoption; no successor starts.

The [stockworker8 part2 return](../bench/sync/results/warm512-frozen-part2-actual-return-20261015.json)
and [raw rows](../bench/sync/results/warm-512MiB-4files-part2-20261015.json)
add18passed rows/54settled CLI: actual owner55681/d32adc/exit0/no session,
aggregate81032 reaped/others absent in2052.876s, unresolved empty. Source/runner
pins stay matched to the frozen cohort. Ordinary/clone/semantic medians are
37.028/36.299/34.232s. Six/eightworker semantic medians are nearly identical
on these four files. All three stock partitions exist; Ox6/8 passed and
Ox1 remains failed/incomplete, as recorded above. The part0 timing disclosure still applies to the
series; no clean full-cohort or physical-I/O claim. Actual closure sent to Root,
18credits released on Unison side; no successor authorized.

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
