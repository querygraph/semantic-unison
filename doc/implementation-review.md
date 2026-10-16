# Implementation review entry point

For complete continuation state, exact pending request, ownership rules and next
steps, read [OPUS-HANDOFF.md](../OPUS-HANDOFF.md). Keep it updated at material checkpoints.

This branch is unfinished. Use this map to review production changes before
examining the larger historical evidence archive. The pinned upstream base is
`8772d26a2eb77cfd0cb6da81807e81f24f51044c`; current branch work is on
`feat/semantic-dng-oxcaml` in the querygraph fork. No deployment or full-goal
acceptance is implied. Photo owns preview generation/publishing qualification.

| Review area | Main production code | Evidence and remaining scope |
| --- | --- | --- |
| Generic clone and range transfer | `wholeFileClone`, `cloneRange`, `cloneLease`, `copyRange`, native stubs; `copy.ml`/`transfer.ml` integration | Upstream engine reuse, exact receiver basis and fallback. [Property/path audit](clone-property-path-review.md); no APFS physical-write/shared-block claim. |
| Format-neutral proof boundary | `formatExtension`, `formatRecognition`, `semanticFormats`, `semanticDelta`, `semanticHash` | [Normative SDE draft](semantic-delta-v0.md), independent conformance vectors and extension identity checks. Unknown/unsupported layouts retain exact fallback. |
| DNG and descriptive metadata | `dngSemantic`, `dngExtended`, `xmpObservation`, `xmpMerge` | Bounded profiles and conservative fixed-region scalar merge; no universal private-tag closure, growing-packet or general RDF merge claim. |
| Materialization/publication | `semanticFile`, `semanticSync`, `semanticRemote`, `candidateValidation`, `copy.ml`, `files.ml` | Retained source/target witnesses and final verification, fork/property lifecycle. [Acceptance matrix](acceptance-matrix-audit.md) keeps power-loss/platform/fault limits explicit. |
| Optional Adobe checks | `dngValidation`, `dngCandidateValidation`, `candidateValidators`, `helperSupervisor`, `helperLimiter` | Real one-camera receiving and generated receiving/merge controls exist; fake receipts are not SDK raw-digest evidence. No universal camera/pixel validation claim. |
| OxCaml and accounting | `semanticWorkers`, checked interfaces/mailbox, `semanticAdmission`, `semanticRuntime`, `backendResources`, `ioAdmission` | Stock/Ox Make and Dune/selftests; checked worker parity and finite fault controls. Credits are not whole-process RSS/OS-thread/physical-device caps. |

## Current evidence to read first

The follow-up originally changed only `src/supervisedExternal.ml` in production
for opt-in helper settlement diagnostics. It now also adds the isolated
`validationSnapshot` kernel, a typed `SemanticWorkers.snapshot` operation and
checked WholeFileClone/snapshot Make/Dune interfaces, plus private stage
ownership and asynchronous validation composition. These are groundwork for
unchanged-file validation; no enabled all-scanned preference or scan hook exists
yet. Read [the integration plan and current evidence](all-scanned-validation-implementation.md).
Most other follow-up files are qualification/source-owner harnesses and sealed
evidence. The [actual mixed workload](../tests/qualification/mixed-validation-v1-actual-20261017.json)
and [Root independent adoption](../tests/qualification/mixed-validation-v1-root-adoption-20261017.json)
now pass/close two SDK calls, two readonly ExifTool requests and32 shared hash
tasks under Unison8/EXglobal. Four SDK warnings each remain visible. No quiet
scaling, hard whole-process limits, representative corpus or full-goal claim.

- [Current helper-diagnostic Make pair](../tests/qualification/validation-live-collector-build-actual-20261016.json)
  and [Dune pair](../tests/qualification/validation-live-current-dune-actual-20261016.json).
- [Camera SDK receiving V2](../tests/qualification/camera-sdk-receiving-v2-actual-20261016.json):
  stock/Ox receiving candidates, real decode/raw-digest valid, actual closure;
  one copied camera sample only.
- [Synthetic two-file receiving V2](../tests/qualification/concurrent-synthetic-receiving-v2-actual-20261016.json):
  exact production receiving and overlapping original fake-helper lifetimes;
  zero SDK/pixel/semantic inference. Admission consumed and Root independently accepted.
- [Prior actual capped-host scope review](../tests/qualification/sdk-prior-host-scope-review-20261016.json):
  twelve historical native calls on the same planned tool/input SHA pins already
  passed reference versus experimental1/6/18 validation parity and reported
  task/covered-allocation settlement. Subsequent shared-owner V1 and observed V2
  runs also completed; neither is a pending first-ever SDK test or reusable grant.
- [Frozen warm512 report](../bench/sync/results/warm512-observed-results-v2.md):
  all retained samples, incomplete failed part3, explicit part0/brew/source timing
  disclosures; protocol bytes and logical models are separated from unknown
  physical writes. These are historical warm fixtures, not current-code/camera benchmarks.

The [remaining-work queue](milestone-next-work.md) and twelve-row
[acceptance audit](acceptance-matrix-audit.md) preserve the complete objective.
A current build, source test or narrow SDK result must not silently close a
broader corpus, platform, cancellation, resource or performance requirement.

Earlier native resource-owner evidence: [shared-eight SDK host V1](../tests/qualification/sdk-shared-host-v1-actual-20261016.json)
passed12 serial reference/experimental calls with independent direct-child and
worker/group settlement, unchanged source pins and closed CPU/IO ownership.
This is shared-owner/inherited-descriptor functional evidence, not OS resource
limits, pixel equivalence or a speedup result.


Latest [shared SDK host V2 actual result](../tests/qualification/sdk-shared-host-v2-actual-20261016.json)
adds twelve real SDK calls plus62 independently audited OS-probe children;
actual39043/ef80c4/exit0, worker43646 reaped0, all CPU/EXglobal ownership closed.
The [reproducible observation report](../bench/sdk-shared-host-v2-observations-20261016.md)
contains bounded process samples (including observed2/6 OS threads on JPEG/JXL),
not peaks, whole-tree limits, calibrated CPU units or speedup qualification.
Its admission735810e6 is consumed and cannot authorize further native work.

The [multi-file receiving V1 request](sdk-multifile-receiving-request-v1.json)
was subsequently admitted and [actually passed](../tests/qualification/sdk-multifile-receiving-v1-actual-20261016.json):
two stock/Ox receiving seeds, each with two generated DNG candidates and two
qualified single-thread SDK helpers. Actual23264/2004ad/exit0/allgroups/FDs
closed; raw digests valid/decode success/errors0/warnings4. Positive known-live
lifetimes are observed, not SDK compute overlap or throughput qualification.
The preparation request remains immutable; admission7b320b51 is consumed once.
The full goal remains incomplete, including representative semantic eligibility,
required failure/platform scope and the remaining benchmark/resource evidence.

## Current source checkpoint — internal unchanged-file validation

The new `CandidateValidation.unchanged_file` entry is implemented and qualified
against current stock/Ox Make objects. It remains INTERNAL: no all-scanned
preference, negotiated capability, scan traversal, or production activation yet.
`SemanticWorkers.recognize` performs bounded recognition without the existing
Identify operation's whole-file fingerprint. Off opens nothing; a generated
nonmatch larger than the snapshot budget reads only four recognition bytes and
skips hashing/copying/validation. A matched file obeys the snapshot byte budget;
validators receive only its private snapshot. Success, rejection, private
mutation, cancellation, and retained-uncertainty controls passed for both
compilers. The canonical staging Fspath is passed in; this entry never changes
process CWD. The worker Identify fingerprint behavior remains covered.

Actual control owner ec7bac/session38387 -> terminal4df709/exit0/no session;
three controllers/twelve compile-or-test child calls reaped0, groups settled,
Unison00..07 released. Evidence:
`tests/qualification/unchanged-validation-entry-actual-20261017.json`.
Current Make build005 stock and Ox succeeded; stock's original parent handle
85221 was missing on continuation, so its parent terminal is NOT reconstructed
from SHARED-CLOSED. Ox actual47362/ce238f/0/no session. Build004 preceded the
CWD correction and is historical. The stage-work harness now pins itself;
older harness receipts are not retroactively described as self-pinned.
All fixtures generated/private; no SDK, Photo payload, new native sharing,
all-scanned activation, or general legacy FD-fault qualification follows.

Next: exact scan-selected work coverage, private endpoint staging initialization,
followed-link/path policy, scope/capability negotiation and default/no-op tests.
Do not expose all-scanned based only on this internal entry.

User steering: exiftool-rs is being extended separately for dng-compare. Revisit
reuse here after that work is ready; do not install, switch validators, or add
an exiftool-rs dependency now. Existing source review remains historical.
