# Implementation review entry point

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
  task/covered-allocation settlement. The new [shared8 request](shared-sdk-host-request-v1.json)
  is about its new owner/grant integration and experimental2-thread case;
  it is not a missing first-ever functional SDK test. No native admission yet.
- [Frozen warm512 report](../bench/sync/results/warm512-observed-results-v2.md):
  all retained samples, incomplete failed part3, explicit part0/brew/source timing
  disclosures; protocol bytes and logical models are separated from unknown
  physical writes. These are historical warm fixtures, not current-code/camera benchmarks.

The [remaining-work queue](milestone-next-work.md) and twelve-row
[acceptance audit](acceptance-matrix-audit.md) preserve the complete objective.
A current build, source test or narrow SDK result must not silently close a
broader corpus, platform, cancellation, resource or performance requirement.
