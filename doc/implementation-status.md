# Implementation status and remaining acceptance work

The receiving-validation checkpoint at `941b99f` adds registered owner-side companions
and typed worker content recognition, independent of semantic eligibility.
Renamed/no-XMP/private DNGs now receive requested validation; filename claims
and checked uncertainty also select it. Candidate inspection errors reject even
under warn. `dng-validation-v1` refuses suffix-only old peers under warn/require;
off remains compatible. One DNG companion covers both transfer profiles. See
[candidate validators](candidate-validators.md) and [the integration receipt](../tests/qualification/validation-companion-integration-20261013.json)
with its separate independent acceptance. Both compiler Make/clean Dune
builds/selftests match 328 inputs. New receiving, worker/helper, operational
fault, compatibility and FIFO controls pass alongside the unchanged 21
receiving-validation / 79 Files publication cases per compiler. This slice uses
Adobe-free synthetic helpers; real SDK/corpus, throughput and complete resource
limits remain unqualified.

The following DNG v1 checkpoint is historical evidence at `3f18015`.

The DNG v1 checkpoint adds bounded BigTIFF and embedded CR camera profiles
under a separate capability while retaining v0 eligibility and wire goldens.
Outgoing preference normalization preserves local BOOL/STRING_LIST values and
clears stale receiver shorthand. The [v1 contract](dng-profile-v1.md) records
exact byte proofs and remaining coverage limits. Both compiler Make/clean Dune
builds/selftests match 318 inputs; direct tests pass 1,091 cases / 5,534 assertions
with three private regressions each. Mixed-version and mixed stock/OxCaml sync,
18-domain v1 jobs, publication/validation and reporting regressions pass.
[The integration receipt](../tests/qualification/dng-profile-v1-integration-20261013.json)
binds that checkpoint's source; separate independent acceptance supersedes its initial
pending-audit status. SDK notes are source evidence, without Adobe invocation,
rendering equivalence, representative-corpus or physical-storage claims.

The following retained-resource checkpoint is historical evidence at `ebcfec6`.

The retained-resource checkpoint: target proofs acquire admission before
native prepare and remain charged through producer return, validation and commit.
Explicit loans replace nested Consumer waits. Selected descriptor allowances,
CPU/child ownership and early FD handoffs have finite fault controls; resource
credits remain estimates rather than a complete process FD/RSS policy. Both
stock/Ox Make and clean Dune builds/selftests pass with 316 matching production
inputs, plus all 79 publication / 21 synthetic receiving-validation cases per
compiler. Scope, qualification and remaining limits are current in
[SOL.md](../SOL.md), [resource-admission.md](resource-admission.md) and
[the combined receipt](../tests/qualification/resource-lifetime-integration-20261013.json).
No new Adobe/Lightroom or photographic-data invocation occurred.

The following positional-write checkpoint remains earlier independent evidence.

The positional-write follow-on now supplies an abstract borrowed output writer
and one bounded native POSIX `pwrite` per attempt. Admission rejects append /
read-only mode and nonregular/multiply linked outputs before writes, including
unchanged plans; subsequent calls rely on stable FD lifetime/flags and exclusive
output access. ML owns absolute short-write/EINTR/cancellation loops. Windows
retains seek/write with kind/link checks. The [foreign-boundary audit](foreign-boundary-audit.md)
records stack-copy/runtime roots, offset/slice bounds and the explicit contract.

Fresh stock/Ox Make `unison-build-n18n0eou` / `unison-build-yft6dgn_` and Dune
`unison-dune-positional-yj9ms_5y` build/selftest with 316 matching production /
package/INSTALL inputs. Kernels, independent 127-command / 2,033-assertion
conformance, 19 worker / 15 report groups, local/remote/bidirectional/old-peer
semantic callers and all 79 actual final-publication cases per compiler pass.
Direct fault/buffer controls pass 59 native/application cases / 1,070 assertions,
plus two artificial invalid-progress and three forced legacy-backend controls,
for 64 positive cases / 1,131 assertions per compiler. Three private regressions
fail their designated checks. Independent read-only review checked 492 hashes /
238 retained native artifact entries; [the direct receipt](../tests/positional_write/qualification-20261013.json)
preserves exact scope and sources. Four actual local/remote partial-write cases
across both compilers prove a real 64 KiB prefix followed by EIO preserves old
live bytes/inode, discards staging, retries exactly and leaves the next no-op
inode stable. Raw archive fingerprint-byte observations support those runs;
they do not decode archive headers or bind nodes. Eight finite process-cleanup
controls pass. Group ownership retains the leader PID until cleanup before
actual leader reap; capture settlement preserves the primary error. Independent
read-only integration audit checked 4,841 hash comparisons, including all 316
inputs across workspace/two Make/two Dune snapshots. [The integration receipt](../tests/qualification/positional-write-integration-20261013.json)
retains its original audit-pending status; [the separate acceptance receipt](../tests/positional_write/independent-review-20261013.json)
closes that audit. Entire materialization still
moves positions through proof/hash reads; only native write attempts preserve
the shared position. Physical writes/sharing, elapsed speedup, crash recovery,
resource lifetime limits and actual other-platform behavior remain unqualified
by this change. The older sync benchmark retains its seek/write source pins
and measurements. No Adobe or Photo operation was performed.

Reviewed and updated on 2026-10-13 on `feat/semantic-dng-oxcaml`, for the
user-requested `querygraph/unison` fork. The preceding native scratch follow-on replaces
absolute reservation/removal with bounded exclusive creation through the held
parent. Reservation, basis and admitted output cleanup now retain identity
witnesses; close slots clear before one attempt and first operational errors
survive cleanup. All three native ABIs and ML interfaces remain unchanged.
Both compilers pass 182 direct APFS cases / 1,984 assertions and two designated
private regressions through every ABI. Independent read-only review checked
137 file hashes and 1,776 retained artifact entries. Fresh Make stock
`unison-build-18qqtcuk` / Ox `unison-build-ksmidizw` and Dune 3.22.2
`unison-dune-scratch-drdljmjz` pass builds/selftests with 315 matching
production/package/INSTALL inputs. Current native status/handles/signal,
86 Copy publication, 40 adoption / 36 old-handoff controls, bound-range,
local/remote/bidirectional SDE and old-peer regressions pass both compilers.
The complete actual `Files` caller also passes 79 cases per compiler with no
exclusions. Evidence is in the [direct scratch receipt](../tests/clone_scratch/qualification-20261013.json),
[integration receipt](../tests/qualification/native-scratch-integration-20261013.json)
and [full Files receipt](../tests/qualification/native-scratch-final-files-20261013.json).
No Adobe, Photo or preview operation occurred.

The [scratch implementation record](native-scratch-next.md) keeps explicit
limits: clone-to-first-open admission cannot prove object birth, check/unlink
uses cooperative namespace assumptions, and some failures preserve artifacts.
Those artifacts are not durable quarantine; existing stale-temp pathname
cleanup can later act on their names. Initial old-temp cleanup, mount lifecycle,
complete-lifetime resource admission and crash recovery remain open.

The earlier retained-producer checkpoint follows
`2a05c4bf3ffffe4380ad7743c490992b2179f332`, based on
`8772d26a2eb77cfd0cb6da81807e81f24f51044c`. It added native/endpoint-local guards,
actual output handoff across ordinary/APFS/semantic producers, held-parent
resume admission, frozen actual-fingerprint receipts and source/validation /
publication fences. At that checkpoint stock/Ox Make and Dune builds/selftests
matched 311 inputs; native 170, registry 105 and semantic worker 32 controls
passed per compiler, along with 79 actual CLI caller cases and both stock
caller negative controls. Its exact source/test/binary/log evidence remains in
the [retained-producer receipt](../tests/qualification/retained-producer-publication-20261013.json).
Earlier receipts retain their exact historical scope and hashes.
The implementation goal remains unfinished. This is an evidence audit of
[SOL.md](../SOL.md), production sources and executable test definitions, not a
new reduction of the user's scope. The [held-FD checkpoint](../tests/qualification/filesystem-observer-20261013.json)
and [earlier filesystem checkpoint](../tests/qualification/filesystem-20261013.json)
retain their original source hashes and scope. The held-FD predecessor recorded
11 observation/21 lease cases, 40 current/36 old-handoff adoption controls and
9 groups/27 actual range-adapter scenarios on both compilers, with stock/Ox
Make/Dune builds and 303 matching Dune production inputs; its ordinary/local/
remote evidence remains historical to that source.


Latest Photo-root coordination includes completed private
[v3 metadata staging](../../photo/mass-preview-alignment-current-20261013-v3/COMPLETE.json)
and [handoff](../../photo/mass-preview-alignment-publication-66241f91142d4992a7333c88d2a8ba22/HANDOFF.json)
against 905,928 images / 895,491 current still keys: stat refresh covers 966,181
files / 9,178,878,944,015 bytes; 156,253 candidate keys / 156,255 images comprise
146,476 explicit-root legacy, 984 old-format identity-bound and 8,793 modern
filename-only keys. All 987 former header holds are resolved for metadata;
1,338 current-native associations/orientations and all 4,299 positive matching
registered level sizes remain distinct from native decode, freshness, durable
registration, restart and monitor coverage. The
[eligibility/registration contract](../../photo/preview-mass-alignment-source-review-20261013/ELIGIBILITY-AND-REGISTRATION-CONTRACT.json)
keeps reuse, mapping/registration gaps, conflicts, stale edits and builds
separate. Preserve all 55 mapped native deletion markers and their owner-reported
native queue exclusion; RootPixels/face/motion metadata adds no ordinary coverage.
Known standalone gaps of 485,185 other-digest and 252,676 no-file keys total
737,861 known exact-current gaps, not a definitive regeneration count; 39 empty
digests remain unknown and all 156,253 candidate sets are production-admitted=false.
The [final geometry packet](../../photo/mass-preview-jpeg-geometry-planning-20261013-v1/RETURN-PACKET.json)
and [publication](../../photo/completed-preview-geometry-publication-324918754b8644e3ba5f5ef8b40d428f/COMPLETE.json)
complete all requested inspections with readers closed: 191,741 files/sections
(39,982 modern + 4,299 native + 147,460 legacy highest), 6,308,224 returned
marker/SOF bytes, zero framing holds, dimension mismatches or identity drift.
No entropy/pixel decode, payload hashes/copies, registration or native invocation
occurred. Stored crop/proxy/quality and provisional 5120x2880 axis fit remain
planning evidence, not current edits, native selection, monitor or 1:1 acceptance.
Returned-byte counters do not measure physical disk read amplification.
Missing-container historical context and excluded modern alternatives remain
separate. The pinned
[ABI assessment](../../photo/preview-generator/abi-layout-qualification-20261013T223153Z/ASSESSMENT.json)
records eight C/Rust structs, 56 fields / 172 metrics, 15 synthetic typed
signatures and genuine OxCaml 5.2.0+ox C-stub transport. Full uint64 uses Int64
bit containers with unsigned handling; signed status uses Int32. Assessment/
completion hashes were checked from JSON, without a new Unison test run or
compiled-artifact access. This qualifies no production host/backend runtime
or private Adobe renderer. Its
original uninvoked image 10031592 native registration/load/restart control remains.
Receipt/document staging records zero production writes, native requests,
payload hashes or copies. The handoff was sent via Photo parent and acknowledged
by the original renderer/publisher owner. Its
[durable acknowledgment](../../photo/mass-preview-alignment-publication-66241f91142d4992a7333c88d2a8ba22/ORIGINAL-PREVIEW-OWNER-ACKNOWLEDGED.json)
binds the exact mass/v3 and compiled-interface pins; acceptance is not native
admission. The final geometry handoff was sent to the ORIGINAL owner for
source/interface ACK, which remains pending. No fresh receiver admission or
native-window readiness is inferred; the stat-only unchanged database-family
observation cannot supply publication admission.
The user reports desktop access unavailable, current helper owner undispatched
and native window unreleased; shared eighteen-credit limit and split placement
persist. Exact-version
Atlas/Bumer archives formerly under delete are now protected retained data for
placement/migration planning. Older monitor capacity estimates require cohort
reconciliation rather than extrapolation from the new total key count.

Earlier Photo-root coordination at 15:47:03 UTC reports stable Classic PID 2844
with Lux reopened and desktop locked at 15:29:55 UTC / 08:29:55 PDT. Receiver
generation-2 acceptance and Accessibility persist; old PID10536/start/Main-FD /
startup/transport bindings are historical. Date1540 filesystem repair is
complete but catalog identity reconciliation remains pending; migration1348
preflight closed before any move on 1,372 observed filename-shadow rows, with
an exact source-reviewed V3 successor. Original Photo implementation ownership
and the unreleased external oracle window remain unchanged.
The [accepted finite source packet](../../photo/preview-generator/oracle-source-v1/SOURCE-READY-FINAL.json)
bounds recursive photographic inputs to eight and logical states to sixteen,
with synchronous typed ownership and a sole backend atomic CPU/memory lease
under a global eighteen-credit ceiling through result release. It was accepted
as uncompiled, uninvoked source preparation; the later pinned synthetic project
ABI transport qualifies no private Adobe signatures. Those remain noncallable and
current source/settings/dependencies require post-repair recapture. No preview
build, benchmark, production publisher or full run is qualified by this update.


The filesystem execution slice now supplies `IoAdmission`, shared by actual
domain jobs and validator helpers. `semanticvolumejobs` is endpoint-local;
zero preserves the configured CPU ceiling and a positive value independently
bounds each filesystem device. Source/output keys are acquired atomically
before domain slots and CPU permits, with conflict fairness and disjoint-device
progress. No lease spans nested pre/post hashing, RPC waits or a transaction.
At the filesystem-execution checkpoint, Make stock `unison-build-9jpxa20z` /
Ox `unison-build-6x7ciag6` and Dune
3.22.2 build/selftests match 315 production/package/INSTALL inputs. Nineteen
actual worker groups, 33 helper groups, 20 gate groups / 243 assertions and
six linked-runtime scenarios / 107 assertions pass per compiler. Fairness and
post-open ownership negative controls detect their intended regressions.
The receiving-path suite now qualifies 21 actual CLI cases per compiler at
one filesystem execution credit on both endpoints, including completed/partial
resumption, hint-copy reuse, external copies, configured merges, second-receiver
partial commit/recovery, timeout/cancellation and measured serial helper overlap.
These are Adobe-free core invocation/publication tests; real SDK parity remains
separate. [The combined receipt](../tests/qualification/io-execution-20261013.json)
pins that checkpoint's scope and artifacts. Per-process I/O accounting is neither a
physical-disk scheduler nor a memory/global-descriptor cap. At that checkpoint,
eight transfer credits undercounted bound publication paths and ended too early.
The current retained-resource checkpoint closes that selected lifetime gap;
native transient census and a complete process resource policy remain open.

The semantic observation checkpoint adds optional extension-defined field observations and
separately negotiated [SIR/1](semantic-observation-v1.md), interpreting complete
packets in workers only on explicit report requests. DNG reports namespace-
bound XMP property encodings with potential categories; exact-byte transfer,
archives and conflict decisions remain unchanged. Fifteen report groups,
eleven actual CLI cases per compiler, second-format local/remote observations,
968 focused XMP checks and 1,029 independent XML mutations per compiler pass.
Independent SDE/SDR conformance now passes 127 commands / 2,033 assertions per
compiler. At that checkpoint Make/Dune builds/selftests match all 313 production inputs;
[the observation receipt](../tests/qualification/semantic-observation-20261013.json)
pins that evidence. Capped SDK area-task host source also compiles against
actual SDK headers and passes 789 Adobe-free scheduler assertions/sanitizers,
but remains a separately gated experimental artifact. No Adobe code ran;
actual multithread SDK parity, cancellation, resident threads/RSS and performance
remain unqualified and current callers retain the threads1 reference.

The intermediate-publication checkpoint implements actual creation-parent handles and the
ordinary receiver's exclusive held-parent stage-to-normal-temp transition.
Native handles pass 20 cases and StagePublication passes 58 cases on stock
OCaml 5.5.1 and OxCaml 5.2.0+ox, including the exact preparation-decline classifier.
Fresh Make stock `unison-build-eiyawftj` and Ox `unison-build-e0r79j3i` builds and
selftests exit zero. Fresh Dune 3.22.2 builds/selftests also exit zero in host-temp
`unison-dune-publication-final-evu31q2x`; all 306 production/package/INSTALL inputs
match frozen/workspace/both-snapshot after manifests, excluding generated
`.depend`. The [publication receipt](../tests/qualification/filesystem-publication-20261013.json)
pins current inputs and retained logs. Actual Copy publication/reference tests
pass 86 cases per compiler, with a stock cleanup-removal negative control.
Current ordinary clone/bound-range/adoption reruns pass both; Ox local/semantic/
remote/bidirectional/old-peer suites pass. Adobe, Photo and performance
receipts retain their earlier source/scope and were not rerun for this slice.
Current preview coordination is interface/review only: native receiver acceptance,
helper access and startup/renewal receipts are complete, but the root has not
released an external finite oracle window. The original photo implementation
owner has acknowledged the exact oracle correction; the canonical receipt binds
its independent review/direct-probe source pins. The ImageCacheEntry orientation
gap is closed in source under the original owner, with 48 focused cases and an
independent rerun of all 23 mapping cases; native verification remains false.
Native one-control source qualification passed 25 tests without invocation; recognition,
cold restart and split fallback remain open.

“Verified” below means an implementation exists, a relevant executable test
exists, and its passing run is recorded in the live handoff. Most evidence is
read from the independent receipts; this reviewer ran the latest isolated Dune
builds/selftests. “Partial” distinguishes working functionality from
unfinished design requirements or missing acceptance evidence. An optional
runtime policy can still be an unfinished planned milestone; disabled by
default does not mean removed from the plan.

## Original requests

| Request | Status and concrete evidence | Remaining work or limit |
| --- | --- | --- |
| Process DNG metadata separately from the binary payload, updating metadata when possible. | **Implemented and verified for fixed-layout v0 and v1 profiles.** [DngSemantic](../src/dngSemantic.ml) finds an owned XMP extent; [SemanticDelta](../src/semanticDelta.ml) proves every complementary byte and the complete source/target SHA-256. [SemanticSync](../src/semanticSync.ml) and [SemanticRemote](../src/semanticRemote.ml) materialize private candidates. Kernel, local and remote tests compare exact results. Materialization skips matching absolute 4 KiB comparison windows, clips writes to editable regions, and reports actual logical write bytes and syscall attempts. | One out-of-line BYTE tag 700, unchanged offset/length and total size, at most 1 MiB. v1 additionally protects BigTIFF and baseline CR camera-profile graphs. Unknown/private/modern graphs and layout changes decline safely. The wire payload still carries complete packets. The window policy is not minimal byte-run patching or evidence of physical APFS write savings. No raw digest is used as whole-file equality. |
| Make ordinary Unison transfers APFS-aware, with future ZFS/ReFS generalization. | **Working APFS optimization, portable range contract, held-FD receiver and intermediate publication integration.** [Copy](../src/copy.ml) reuses upstream hooks, private receiver-basis clones, same-offset skips, shifted immutable-basis reads and a bounded local producer. Strict [Fs.clone_stage_status](../src/fs.ml) preserves scoped declines/operational phases. [CopyRange](../src/copyRange.ml) passes 11 outcome tests; [CloneRange](../src/cloneRange.ml) passes 48 named constrained tests including 960 geometry combinations. [FileObservation](../src/fileObservation.mli) and [CloneLease](../src/cloneLease.mli) add native macOS facts and borrowed owner-epoch leases, passing 11/21 cases on stock/Ox. Ordinary receiver shifted matches use fresh observations, a 10 MiB maximum and `range = None`. Additive `Fs.clone_stage_handles` and [StagePublication](../src/stagePublication.mli) retain creation parent/witness and exclusively publish the normal temp; native suites pass 20/58 cases on both compilers. | Regular-file final `Files.renameLocal` and logical-root/follow-target binding are now qualified by 79 caller cases per compiler. Native scratch reservation/removal is now descriptor-relative, with 182 direct APFS cases / 1,984 assertions per compiler. Additional-name families and initial old-temp pathname cleanup remain open; first-admission gaps and cooperative namespace fencing remain explicit. No true mount-incarnation detection or capability cache. Production Copy publication/reference tests pass 86 cases per compiler, with a stock cleanup-removal negative control; current ordinary/bound-range/adoption and Ox local/remote reruns pass. Bound local/SDE materializers now hand over their actual output descriptors; declared legacy paths remain. Focused actual Copy-adapter tests pass 9 groups/27 scenarios on stock/Ox, with a stock negative control. Existing `clone_path`/`clone_file` still return booleans; successful `copy_file`/`Copied` does not attest sharing. Strict native range status, ZFS/ReFS runtime qualification, actual cross-volume performance and fault/crash recovery remain open. |
| Accept extensions that declare change semantics beyond binary difference. | **Generic exact-transfer mechanism and lazy CLI reporting verified; richer semantics partial.** [FormatExtension.S](../src/formatExtension.mli) declares a profile and inspector; registration adds a capability, payload ceiling and advisory suffix hints. [SemanticReport](../src/semanticReport.ml), [SemanticRemote](../src/semanticRemote.ml) and [Uicommon](../src/uicommon.ml) show current-pair classification, preservation hashes and bounded metadata previews on explicit diff/details. A second registration-only synthetic format exercises unchanged local/remote/worker dispatch and the same report path in [test_generic_format.py](../tests/test_generic_format.py). | The transfer interface describes editable ranges; core classification is `Exact_bytes`, `Editable_metadata`, `Other_bytes`. Separately registered owner-side validation companions receive typed worker recognition and the shared finalized-candidate context; a synthetic companion qualifies registration without core edits. Immutable handles now have a bounded optional field-observation hook, used by DNG namespace-aware XMP and a synthetic workflow format through SIR/1. Reconciliation hooks and authoritative scan/base labels remain absent. Reports are lazy, disposable observations of the current pair, without an archived base or authoritative scan-wide labels. Exact-byte conflict decisions remain unchanged. |
| Investigate existing systems and propose/implement a diff standard if needed. | **Research and experimental proposal delivered.** SOL records upstream Unison, rsync, VCDIFF, Git drivers, SQLite Session, Automerge and structured patch prior art. [SDE/0](semantic-delta-v0.md) specifies one canonical exact-byte envelope and SDR/0 request; [SIR/0](semantic-report-v0.md) separately describes bounded observations. Negotiated production RPCs implement both. | These are experimental interoperability proposals, not adopted standards or proof of novelty. Independent Python encoders/transcripts and fixed LE/BE DNG plus multi-region golden bytes now qualify 83 vectors, 1,836 truncations and exact materialization on both compilers (127 commands / 2,033 assertions each). External ecosystem adoption and representative-corpus interoperability remain separate. |
| Study `~/src/dng-compare` and the recreated Lightroom fingerprinting work. | **Source research completed and recorded.** SOL pins both canonical repositories, documents the opaque-trailer counterexample and distinguishes stored Adobe digest, recomputed raw identity, Lightroom original matcher, preserved bytes and whole-file identity. Both canonical SSH origins and pinned commits were reconfirmed during this audit. | There is no production invocation of the recreated Lightroom workers, no new source change in either supporting repository, and no independently qualified Lightroom UI oracle. Using them as differential oracles requires version/stratum-specific fixtures. The firstparty source review is evidence of distinctions, not execution parity. |
| Invoke Adobe validation directly for each synced DNG as an option. | **Implemented and substantially verified for received content.** [Files.renameLocal](../src/files.ml) invokes [CandidateValidation](../src/candidateValidation.ml) before commit. `off`, `warn`, `require`, receiver-local executable/pin/build settings, feature negotiation and shared scheduling are implemented. Registered validation companions select renamed DNGs by content independently of semantic eligibility; the v1 capability refuses old suffix-only validation peers and operational inspection failures reject even under warn. The [actual SDK driver](../tools/adobe-validator/driver.cpp) is qualified against synthetic positive/negative controls; actual receive-gate tests cover new files, XMP patches, corruption, recovery and directories. | Adobe-free actual CLI qualification now covers completed/partial staging resumption, moved-file hint reuse, external-copy results, generated merges and first/second receiver failures, with exact retry behavior. The corresponding actual SDK/corpus matrix remains needed. Rename-only moves and unchanged/property-only files are explicitly excluded. Optional `all-scanned` validation is not implemented. The validator does not claim full Lightroom Validate behavior. |
| Rewrite/port the core to OxCaml for speed and parallelism. | **Complete text CLI/core builds and worker refactor verified; full M6 qualification partial.** Make and Dune builds/selftests pass stock OCaml 5.5.1 and pinned OxCaml 5.2.0+ox. [SemanticWorkers](../src/semanticWorkers.ml) performs hashing, inspection and apply on actual domains; the owner alone handles Lwt/RPC/archive state. The native hash path has private contexts and an independently tested portable reference. | `Domain.spawn` retains OxCaml safety alerts and a manual ownership contract; it is not a compiler-checked portable boundary. No compiler-specific safe scheduler or measured representation optimization is delivered. GUI and other platform builds, randomized scheduling stress, supported race instrumentation and a complete end-to-end performance report remain open. |
| Use workers for all relevant invocations and account for SDK parallelism while using available cores. | **Shared CPU scheduling verified; SDK scaling/resource qualification partial.** [HelperSupervisor](../src/helperSupervisor.ml) supplies weighted permits, bounded queues/output, deadlines, process-group cancellation and reap. Domains and actual synthetic helper processes share one budget. The SDK/JXL one-thread path is source-audited; production Adobe invocations use this supervisor. The [actual SDK validation-core benchmark](../bench/adobe/README.md) completed 42 cached-synthetic batches with 2,811 correct receipts at 1/18/36-worker budgets and zero final credits. | The current driver accepts only `--threads 1`; a separately gated capped SDK area-task wrapper is source-implemented, compiled to unlinked objects and tested by 789 Adobe-free assertions/sanitizers. It is unavailable to current callers pending actual SDK qualification. Measured cached 24 MP multi-file validation does not establish full-sync or representative-corpus throughput; mixed actual Adobe/ExifTool/hash work is still unmeasured. No ExifTool semantic pipeline has been added. Execution-scoped per-filesystem I/O admission is implemented and qualified; ordinary transfer I/O, physical-device grouping and parent/child memory limits remain outside it. |
| Consider 18 physical cores versus 36 logical workers. | **Implemented and measured for cached hashing and SDK validation.** Auto queries physical cores on macOS, giving 18 here; positive `semanticworkers` permits 36. Runtime diagnostics report detected/effective counts. [Benchmark artifacts](../bench/semantic/README.md) contain five measured repetitions and raw samples; the [SDK comparison](../bench/adobe/README.md) independently measures decoding/validation. | 36 delivered about 10% more cached hash throughput. SDK validation medians improved 3.1%/12.3%/10.9% for uncompressed/JPEG/JXL while using 69–79% more CPU per batch. 18 remains balanced; 36 is an explicit throughput option. These cached synthetic results do not establish full-sync scaling. Both compilers use the same native SHA backend and show no demonstrated OxCaml-specific gain. |
| Configure fresh zsh shells for the system SSH agent; generate/upload `pomogi`; switch supporting repos to SSH. | **Operational setup recorded complete.** `.zshrc` preserves a live socket or discovers the launchd agent; canonical Lightroom and dng-compare origins are SSH URLs. Earlier session evidence records generation, loading, GitHub upload and authentication. | This audit rechecked shell configuration and repository origins, not a new key upload or authentication flow. No private key data belongs in this repository. |
| Keep SOL.md current for the model switch and continue implementation. | **Ongoing.** SOL contains the design, changing implementation evidence and remaining work; the user has switched to Sol. | Continue updating both the live handoff and this matrix as gates close. No goal-completion claim is warranted. |
| Make monitor-preview separation part of the Unison architecture: Quasar for monitor payloads, Ten for lower levels/native cache. | **New required architecture delivered; runtime qualification pending.** [Component placement v0](component-placement-v0.md) separates logical asset/component identities, endpoint-local placement and physical clone capabilities. [Lightroom binding](lightroom-preview-placement.md) specifies native identities, geometry, local references, closed-cache publication and cross-volume recovery from the reviewed preview-session handoff. | No component-group runtime, multi-root archive protocol, offline cache publisher or native symlink lifecycle is qualified by these documents. Current read-only checks observe Quasar as replacement 8 TB APFS and Ten as Journaled HFS+; old Quasar identity/capacity/member observations are historical. The new identity requires a new placement/capability generation. Quasar is conservatively required for affected pyramids until native missing-volume/highest-file fallback is qualified, even though lower bytes remain on Ten. The other Codex session owns standalone rendering/native registration tests; no catalog/cache/volume mutation was performed here. |
| Assess APFS on empty Quasar and optional Ten conversion using free Quasar/Apo/Lux space for evacuation. | **Read-only assessment and staged plan delivered.** [Storage migration plan](preview-storage-migration.md) records installed SoftRAID 8.6.1 support, the supported logical-volume recreate workflow, verified distinct SSD member sets, per-disk capacity assumptions and complete-copy/verification/restore gates. Quasar is already APFS after an external change; Ten remains HFS+ because no conversion benefit is measured. The plan marks earlier format/capacity observations as historical. | The earlier 1.016 TB aggregate evacuation headroom is historical, not a current allocation proof; fresh per-disk values and topology are required. A full Ten inventory, exact per-disk plan, application exclusion and verified receipts are still required before any optional cutover. No data was moved or volume reformatted by this thread. APFS neither supplies cross-volume cloning/atomicity nor automatically speeds HDD preview storage. |
| Integrate and forward the Astra-reviewed standalone Rust/OxCaml monitor-preview design before implementation. | **Review integration and forwarding delivered.** [Integration findings](preview-design-integration.md) retain independent capture/render/pyramid/offline-publisher boundaries, exact dependency identities, 18-credit native-thread accounting, native schema/color/geometry and cross-volume recovery. Our integration task acknowledged; the complete review/findings were queued through the takeover parent for the existing preview implementation owner, with a [receipt](../PREVIEW-REVIEW-FORWARD-20261013.json). | Standalone Adobe-current-edits rendering, mask/AI coverage, offline native publication and split lifecycle remain unqualified. The takeover session reports Lux adopted/accepted and open in stable 15.6, helper access and actual existing-server transport qualified; the external oracle window is closed pending desktop unlock/root sequencing. Native conversion preserved 18 JPEG sections but did not register the three controls. External AdobeRGB profile evidence can accompany JPEGs without embedded ICC. Installed-loader inference requires the highest registered file even for smaller requests, so affected pyramids require Quasar until mount-loss fallback qualifies. Preparation/adoption receipts authorize no full generator run. The oracle binds whole-pyramid identity and actual decoded level/row data, without a per-level UUID requirement; unknown registered sizes remain unqualified. Native output/allocation and matched 1/6/18 compute/full-pipeline benchmarks must precede full runs. The newer-gap planning allowances fit; full conservative Quasar allowance still exceeds the new 7.200 TB budget. No preview generator/native/cache/volume work was executed here. |
| Would a JPEG extension make sense; is JPEG metadata separable? | **Design explanation delivered; implementation explicitly future.** SOL documents ordinary XMP APP1, other segment identities, compressed scans, rendering implications and fixed-range limits. | JPEG was raised as a design question, not an explicit replacement for the DNG task. No JPEG profile exists; do not advertise one. |

## Milestone gates

| Milestone | Implementation and evidence | Open acceptance gates |
| --- | --- | --- |
| M0: baseline/upstream/toolchains | **Substantially complete on this host.** Pinned newer upstream reused; isolated stock/Ox Make and Dune text builds/selftests; historical stock→Ox→stock local archive smoke test; unmodified v2.53.5 fallback tests. | Dedicated stock↔Ox v1 remote cases now pass with exact receiving bytes; an archived reproducible local compiler/archive smoke sequence would strengthen the record. Other platforms and GUIs have separate qualification. |
| M1: pure kernel/spec | **Core implemented and verified.** Checked parser/reader, full/complement hashes, generic registry, exact plans, canonical SDE/SDR, inspector and bounded SIR/0 observations. Kernel/report tests include adversarial fixtures and randomized short inputs. | Independent wire/transcript vectors now pass; coverage-guided fuzzing and broader sustained stress remain open. Inspector reports payload/envelope sizes and full-read cost qualitatively, not instrumented verification read counts. |
| M2-G: general APFS transfer | **Main APFS paths, constrained planner and narrow native receiver integration verified; acceptance incomplete.** Stable basis/stage, source-clone preference, inherited skips, shifted copying, exact EOF and separate interrupted stages remain. Strict APFS results distinguish scoped declines from phased failures. The fake adapter qualifies alignment/tails/maxima/progress and injected generations. Native held-FD observation/borrowed leases now bind ordinary receiver shifted matches to actual descriptors, owner epochs and fresh checks before operations/completion; destination write timestamps are permitted. Intermediate stage-to-normal-temp publication now retains the actual creation parent and witness, performs exclusive held-parent rename, and cleans only its identity-bound leaf. Native handle/publication suites and current Make/Dune builds pass both compilers. | Actual Copy publication fault qualification, regular-file final live-commit/logical-root binding and current scratch integration are qualified. Native scratch reservation/removal is descriptor-relative; initial old-temp cleanup remains pathname-based. Lifecycle invalidation still requires separate evidence without treating UUID/fsid as a mount-incarnation proof. Native sharing/results and other sink/composed-materialization paths remain open. Legacy range EINVAL/ESPIPE/ENOTSOCK still preserve compatibility and need precise backend status; whole-clone boolean wrappers hide errors. No capability cache, new ZFS/ReFS runtime or crash qualification. |
| M2: local DNG path | **Implemented and verified for fixed-layout v0/v1.** Exact output, private original preservation, stale/aliased basis rejection, async cancellation and clone policy paths have fixtures. Sparse application counts bytes returned by writes and syscall attempts. Both TIFF byte orders, unchanged/first/last/disjoint/adjacent/full changes, clipped window boundaries, coalescing and synthetic multi-region application are tested. | Counters measure logical writes, not physical storage effects. Controlled failures at write/verification/property/commit boundaries remain incomplete; clone allocation ordering is manually hardened without OOM fault injection. Exhaustive packet-size and platform boundary matrices are not established. |
| M3: negotiation/fallback | **Implemented and substantially verified.** Both directions, old peers, local-local source-clone bypass, loopback SSH, command/body bounds, reply binding, saturated bidirectional budgets and persistent socket reconnect are tested. RPC scopes retain resources through queued output, settle queued/blocked replies on close, and await active borrowers. Delayed results from a closed session do not escape into the next owner session. | Dedicated mixed stock/OxCaml v1 wire cases now pass. A real heterogeneous source/receiver filesystem setup and explicit RPC-v0 behavior lack dedicated evidence. Current loopback peers share the host/filesystem. These lifecycle fixtures do not replace systematic fault or scheduling stress. |
| M4-V: Adobe option/helpers | **Usable functionality verified; milestone incomplete.** Real SDK controls and receive-gate integration complement synthetic policy, mutation, timeout, process-tree and cancellation tests. Endpoint-local tool configuration is protected against legacy incoming values. Cached 24 MP SDK validation-core scaling is measured at 1/18/36 with five parallel repetitions. | Actual SDK/corpus reruns of the now-qualified synthetic receiving-path matrix, per-algorithm diagnostic detail, representative corpus/full-sync performance and actual SDK qualification of the source-implemented capped multi-thread area-task host remain open. Driver reports an aggregate raw-digest result; durable per-file receipts and stored/computed per-tag digest reporting are not implemented. |
| M4: reporting/coverage | **Lazy current-pair CLI reporting implemented and verified; broader coverage partial.** Explicit `d`/`x` requests show profile, classification, hashes and bounded escaped metadata samples through negotiated SIR/0. Local/remote metadata, opaque/layout changes, unsupported files, renamed eligible files, old peers and ordinary text fallback are tested. Details are one-shot and invalidate on local change/replacement, another row or disconnect. | Independent Lightroom oracle fixtures, representative supported-stratum coverage and eligibility measurements remain absent. GUI reporting and broader one-sided/equal-edit interaction qualification are separate gaps. No archive-base change inference or semantic merge is claimed. Layout-changing profiles are later work; correct fallback already meets the safety requirement. |
| M5: opt-in reconciliation | **Not implemented; retained later milestone.** Exact byte conflicts remain unchanged. | No versioned base-XMP cache, explicit semantic policy, field allowlist/RDF model, deterministic merged artifact, negotiation or merge/recovery tests. The user did not explicitly request automatic merging, but SOL retains this planned optional policy; do not quietly label its milestone complete. |
| M6: OxCaml data path/qualification | **Port and concurrent implementation verified; full qualification incomplete.** Typed jobs, owned duplicates, mutex queue, atomic cancellation, owner completion pump and shared helper permits exist. | Compiler-specific safe boundary work, the broader inherited-FFI inventory, randomized stress, actual RSS/child caps, measured storage scheduling and the complete benchmark matrix remain. Execution-scoped per-filesystem admission is now qualified. A [manual audit of the new primitives](foreign-boundary-audit.md) documents roots, owners, runtime release and remaining limits. TSAN is unavailable in the pinned installed compiler. |

## Required acceptance matrix, matched to existing tests

| SOL gate | Existing evidence | Evidence still missing or narrower than the gate |
| --- | --- | --- |
| 1. Exactness | [semantic/test.ml](../tests/semantic/test.ml), [local_clone.ml](../tests/local_clone.ml), [test_semantic_remote.py](../tests/test_semantic_remote.py): same-layout patches, exact byte comparisons, stale-stage and same-inode no-write rejection, unchanged second sync. Sparse tests cover first/last editable bytes, aligned-window crossings, clipped heads/tails, disjoint/adjacent/full changes in both TIFF byte orders, and two synthetic editable regions with unchanged originals. | Independent multi-region wire/transcript goldens and bounded max-payload vectors now pass both compilers; exhaustive packet/layout combinations and representative corpus strata remain open. DNG intentionally has one region. Source-selected fork/property behavior is tested separately, not every semantic combination. |
| 2. DNG coverage | Both byte orders, classic/BigTIFF, independently ordered CR profiles, successful multiple SubIFDs/strips/tiles/previews/original/opcode combinations, EXIF/GPS/Interop, aliases/unknown/private fallback and opaque trailers; older real SDK-generated JPEG/JXL controls remain separately pinned. | Representative Lightroom/camera strata, modern/private graph support and actual SDK qualification of the new v1 subset. The new >4 GiB controls qualify inspection/read offsets, not full large-file transfer. Accepting these as safe fallback is different from qualifying fast-path coverage. |
| 3. Malformed input | Cycle, duplicate, alias, pointer type, fanout, corruption, truncation and short random-input tests; profile payload declaration and RPC preallocation bounds. | Coverage-guided/structured fuzzing, sanitizer-qualified native execution, sustained time/memory limits and independently constructed multi-region overlap/overflow vectors. XML is opaque in the transfer profile; the SDK separately parses it. |
| 4. Integrity | Whole/complement/payload SHA checks, opaque differences, stale basis, wrong nonce/profile, actual SDK old/new/both/missing/corrupt/zero digest controls. | Same decoded samples with different raw encoding as a differential identity case, algorithm-specific receipt details and real Lightroom oracle controls. |
| 5. Concurrent modification | Worker source mutation, synchronous cancellation, late completion cleanup, immutable clone-basis behavior, validator tree mutation including links/properties, final source/archive fingerprint fence. [report_details.ml](../tests/report_details.ml) checks one-shot observations, changed/replaced local names, followed links, row binding and disconnect invalidation. Reports also check descriptor/pathname stamps before returning observations. StagePublication native tests now cover effective-root/parent/name rebinding, symlinks and replacement sentinels at the intermediate boundary. | A systematic live source/destination path/inode/symlink replacement matrix at each transfer/commit boundary and restored-mtime adversarial cases. Reporting remains observational; the existing uncooperative check-to-rename race remains documented. |
| 6. Failure/recovery | Process-group SIGKILL during generic clone transfer and exact retry; queued/active cancellation; helper crashes/timeouts; failed validation quarantine. [remote_bounds.ml](../tests/remote_bounds.ml) covers queued/blocked output failure, pending reply settlement and closed-session late borrowers. [socket_reconnect.ml](../tests/socket_reconnect.ml) verifies same-PID persistent-server reconnect after admission saturation, with an old-leak negative control. Generic Lwt close tests cover pending I/O settlement, throwing callbacks and descriptor reuse. Intermediate publication tests retain cleanup ownership through one post-rename Sys.Break and close all owned FDs after native cleanup errors. | ENOSPC/EIO and injected failures after clone, mid-write, properties, flush, rename and archive update; crash/restart matrix and archive recovery at each point. No power-loss durability or new fsync/F_FULLFSYNC policy is established. |
| 7. Filesystems/properties | [clone_stage.ml](../tests/clone_stage.ml) and [test_clone_stage.py](../tests/test_clone_stage.py): exclusive creation, readonly source, stable unlinked basis, xattrs/resource fork/ACL clearing, flagged-file decline and prompt FIFO rejection. Clone results are preallocated before native resources; singly linked/distinct-inode guards precede private permission changes. Integration covers hardlink isolation and source mode restoration. [File-observation tests](../tests/file_observation/README.md) independently verify native IDs, flags, links, sizes/nanoseconds, strict UUID parsing, phased errors and held-descriptor replacement/leak boundaries. The 20 handle and 58 publication cases additionally cover actual creation parent, Unicode names, followed/search-only/distinct parents, single-link admission, identity-only cleanup and preparation fallback scope. | Actual separate-volume/remount/reformat tests; sparse/compressed layouts, open-reader integration, case behavior, end-to-end Unicode paths, stashing/backups and all fork transitions. Native non-APFS/new-platform execution is not qualified. Final live-commit/logical-root binding remains separate from the implemented intermediate guard. |
| 8. Compatibility | Stock/Ox Make and fresh Dune builds/selftests, archive smoke evidence, ordinary peer fallback both directions, extension disabled, endpoint-local settings, unchanged archive format. [test_semantic_reports.py](../tests/test_semantic_reports.py) covers old-peer report unavailability and ordinary text-diff fallback while preserving bytes and conflict choices. The second synthetic format uses the same local/remote report path. | Explicit RPC-v0 and broader mixed-compiler matrix beyond the qualified DNG v1 cases; current-source archive round-trip back to baseline after semantic use; GUI/platform guard builds; focused interaction tests for ignores, user merge programs and external copy. |
| 9. Parallelism/resources | [workers/test.ml](../tests/workers/test.ml), [admission/test.ml](../tests/admission/test.ml), local multi-candidate and bidirectional remote tests: actual domains, weighted helper overlap, queue/credit limits, cleanup, source headroom and descriptor stability. | Randomized schedule/cancel stress, one versus multiple physical volumes, measured aggregate parent/child RSS, enforced memory/complete-lifetime descriptor limits and measured physical-storage scheduling. Per-filesystem execution admission is now qualified. Estimated payload credits explicitly exclude parser allocations, directory manifests and SDK memory. |
| 10. Semantic merge | Existing Unison conflicts retained; no semantic merge can silently discard data. | Entire opt-in M5 acceptance set: same/disjoint/conflicting/deletion/Bag/Seq/Alt/qualifier/rendering/unknown/base/policy/partial-commit tests. This is deferred feature work, not existing merge qualification. |
| 11. Generic clone transfer | [test_clone_sync.py](../tests/test_clone_sync.py) exercises ordinary fixed/shifted/duplicate/all-literal/truncated/grown cases, clone off/require, no-op and interruption; local producer fixture exercises receiver-basis comparison directly. [Copy-range](../tests/copy_range/README.md) and [constrained clone-range](../tests/clone_range/README.md) suites qualify prefixes/errors, alignment/tails/maxima, injected binding invalidation and exact independent bytes/sentinels. [Lease tests](../tests/clone_lease/README.md) connect native observations to exact borrowed FDs and owner epochs. The ordinary receiver uses that bridge with bounded copied operations and now publishes its normal temp through StagePublication. | Actual Copy publication/reference coverage passes 86 cases per compiler, with a stock cleanup-removal negative control. Current Copy-adapter coverage passes 9 groups/27 scenarios on stock/Ox, including EIO/ENOSPC and invalidation before/after bounded progress. Native sharing/completed-prefix/indeterminate-error status, true lifecycle detection, broader transaction-family publication and general sink syscall-level accounting remain open. Regular-file final binding now has current native/worker/79-case caller evidence. Local producer tests do not use an actual cross-volume mount. No added physical-sharing or performance claim. |
| 12. Adobe and CPU accounting | Synthetic helper/policy tests; actual SDK qualification and [test_adobe_sync.py](../tests/test_adobe_sync.py); distinct receiver tools/pins; directory consumers; shared actual domains plus weighted synthetic helper; synchronous reap on disconnect; cached 24 MP SDK multi-file CPU/permit scaling. | Actual SDK receiving-path cases described under M4-V; real-corpus controls; actual SDK thread/process/CPU/memory telemetry; multi-thread SDK host; mixed actual Adobe/ExifTool/hash throughput. Optional all-scanned scope is absent. |

## Resource and observability gaps that should not be hidden by passing tests

- `SemanticAdmission` is a bounded transaction-credit system. Its 8× payload
  estimate plus fixed overhead is not an RSS cap. It excludes parser working
  sets, received-directory manifests, unrelated legacy transfers and external
  SDK allocations. `HelperSupervisor` limits CPU reservations, child count,
  queue length, elapsed execution and captured output; it has no child memory
  ceiling. `IoAdmission` now bounds domain/helper execution by ephemeral filesystem device keys, with independent endpoint-local limits. It does not cap ordinary transfer I/O, identify physical devices, or create a cross-process global budget.
- `Fs.clone_stage_status` distinguishes scoped macOS declines from phased
  operational errors and keeps staging private. The legacy option ABI remains.
  The surrounding upstream interfaces still
  suppress clone errors into booleans. `CopyRange` now preserves known
  completed prefixes and distinguishes compatibility declines from operational
  failure; EBADF/EIO/ENOSPC/permission errors and callback/cancellation
  exceptions cannot authorize fallback. Ambiguous legacy native classifications,
  native range sharing/status receipts and reliable lifecycle/final-live-commit
  guards remain M2-G work. `FileObservation` now supplies real macOS held-FD facts;
  borrowed `CloneLease` epochs connect them to `CloneRange` in ordinary receiver
  shifted copying. Its 10 MiB operations use `range = None` and claim copied
  bytes only. No native mount-incarnation identity or reusable capability cache
  follows from UUID/fsid equality. A successful generic copy API does not prove
  block sharing. Intermediate publication now retains four extra steady owned
  FDs per active ordinary receiver clone (effective root, actual stage parent,
  temporary parent and witness); transient preparation/clone descriptors are
  additional. Finalizable ownership and close ordering are implemented, but no
  new global descriptor admission budget follows from that per-context count. Bound local semantic work can hold nine semantic descriptors plus four/five final-publication descriptors and transient probes; the historical eight transfer credits are estimates, not that complete lifetime.
- The measured artifacts under `bench/semantic` contain cached SHA timing,
  CPU/wall, correct result counts and worker peaks. Production application now
  counts logical write bytes and write-call attempts, with exact sparse-write
  fixtures, but these counters are not yet a complete measured transfer
  benchmark. The artifacts do not contain wire bytes, application read counts,
  filesystem write telemetry, stage timings,
  peak RSS or the original/upstream/clone/semantic
  end-to-end comparison required by the benchmark plan. The separate
  [Adobe benchmark](../bench/adobe/README.md) measures cached synthetic
  validation-core throughput, parent/child CPU and budget peaks; it excludes
  synchronization, tree/property manifests, storage telemetry and RSS.
- The new [actual sync runner](../bench/sync/README.md) qualifies thirteen bounded
  rows / thirty-nine CLI invocations on the current stock/Ox 315-input snapshots
  and original 2.53.5. It records full forwarded protocol bytes, outer stage
  timings and individual `wait4` CPU/RSS along with exact outcome/basis/no-op and
  process-settlement checks. For two 2 MiB files, the receiver-clone non-inherited
  model is 16 KiB and semantic successful logical writes are 6 KiB / two attempts.
  Internal read/hash/parse/commit times, aggregate tree RSS and physical writes
  remain unmeasured; one warm startup-heavy sample establishes no speedup or
  worker recommendation. Both same-host endpoints have independent CPU budgets.
  Forced-failure cleanup is qualified; catastrophic owner loss is labeled without
  native-owner reap proof. The broader matrix and real storage/SDK controls remain.
- The [new-boundary manual audit](foreign-boundary-audit.md) enumerates roots,
  runtime release, buffer/descriptor ownership, globals, cancellation and ABI
  for SHA, helper supervision, clone-stage, held-FD observation and intermediate
  publication primitives. It remains a manual
  contract: broader inherited FFI, allocation/native fault injection and
  supported race instrumentation are still open. Tests do not supply a
  compiler-checked domain boundary.

## Next substantive steps

1. **Broaden reporting and DNG qualification.** The bounded, disposable `d`/`x`
   current-pair report path is implemented and preserves exact-byte conflict
   decisions. Extend interaction evidence for one-sided and equal edits,
   disabled-profile behavior and GUI presentation where supported. Add
   independent Lightroom/Adobe oracle fixtures and representative supported
   strata before claiming broader coverage or rendering semantics. Keep
   archived-base inference and semantic reconciliation separate from reports.
2. **Finish filesystem publication and native range contracts.** Typed outcomes,
   strict APFS stage results, the constrained fake backend, native held-FD
   observations, borrowed-lease receiver integration and exclusive held-parent
   intermediate publication are delivered. Production Copy faults, retained
   actual producers and regular-file final `Files.renameLocal` / logical-root /
   follow-target binding are qualified. Native scratch creation/removal now uses
   the retained parent and identity witnesses; its direct and actual caller
   evidence is in the [implementation record](native-scratch-next.md). Address
   initial old-temp cleanup, additional-name families, first-admission limits
   and explicit lifecycle invalidation. Keep leases uncached
   until invalidation is qualified. Refine inherited native range status/effect
   reporting before adding authoritative sharing adapters; retain exact fallback
   and property semantics. ZFS/ReFS readiness is broader than the tested APFS
   caller, and new platform claims still require those platform tests.
3. **Measure the actual product paths and close resource bounds.** Add
   reproducible generic-clone/SDE/Adobe benchmarks with exact-byte verification,
   read/write/wire counters, stage times and parent/child peak memory. Compare
   1/2/4/8/18/36 where useful, tune the implemented per-filesystem execution admission
   and add explicit memory/complete-lifetime descriptor policy from observed working sets. Retain raw measurements and
   distinguish compiler effects from algorithms and concurrency.
4. **Finish validation and interruption qualification.** The synthetic resumed/reused/
   external-copy/merge receive-gate matrix is now qualified. Add its actual SDK/corpus
   controls and deterministic fault points around
   materialization/finalization/commit/archive. Then runtime-qualify the source-implemented, separately gated
   SDK area-task wrapper with explicit native-thread accounting for single-file
   scaling, preserving the known one-thread reference.
5. **Retain later semantic work explicitly.** Broader DNG profiles and opt-in
   three-way reconciliation remain planned. Start them with versioned schemas,
   independent oracle/conformance fixtures and a narrowly specified field
   policy; do not use raw equality to suppress container/rendering conflicts.

JPEG, dynamically loaded/out-of-process format plugins, optional all-scanned
validation, arbitrary metadata relocation and non-byte convergence are distinct
future features. Non-byte convergence is explicitly outside the first
implementation and would require a new archive design. New native ZFS/ReFS
qualification depends on those platforms; the required portable capability
contract and fake-backend tests do not.
