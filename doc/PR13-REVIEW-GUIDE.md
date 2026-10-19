# Review current Semantic Unison integration

PR13 targets this public fork's `master`, not original upstream. The base is
3957717819e3a64e3030eb02f422338ec1f0b751, which already contains the first merged
semantic/APFS implementation and the public documentation update. This PR is
the subsequent implementation and qualification work, not an assertion that all
features were first added in this diff. It remains a draft.

The production tree is byte-identical to the prior reviewed f6bfd653 snapshot;
recent commits add qualification, owned test drivers and evidence. Reconciling
public master changed only documentation ancestry/links. No production source,
archive/RPC format, frozen runtime plan, Photo state or user payload was changed
by this review refresh. Master itself is unchanged.

There are106 changed production paths (9478 insertions/977 deletions) against
this base. Most of the much larger PR is tests, preserved machine-readable
receipts, plans and reports. Start with the production paths and the directed
reports below, rather than treating every evidence line as application code.
The [exact source inventory](pr13-current-review-scope-20261019.json) fixes group
membership and current blob hashes; it is navigation, not acceptance evidence.

## Review order and invariants

1. Follow ordinary copy/receiver-basis materialization into stage and final
   publication. Check exclusive ownership, source/target epochs, same-offset
   skip versus shifted bytes, error effect classification and conservative
   fallback. Unknown or partially effective operations must not become clean
   declines or authorize destruction of a foreign name.
2. Review descriptor/resource lifetimes before parallelism: close attempts are
   one-shot, uncertainty retains identities/causes, returned-but-undelivered
   work still owns accounting, borrowed descriptors survive. Workers receive
   immutable proofs/messages; legacy RPC/Lwt/archive/UI state stays on its owner.
3. Follow DNG manifests and hashes into SDE application and scalar XMP merge.
   Encoded pixel spans are delineated, not decoded-pixel equivalence. Unknown
   MakerNotes stay opaque/exact; future nested interpretation is versioned and
   incremental. Incomplete private meaning does not itself block safe exact sync.
4. Inspect RPC/archive downgrade, fallback and stale-base handling. Supported
   upstream peers are the target; obsolete RPCv0 was explicitly dropped by the
   user. Capability negotiation never authorizes a missing/changed local base.
5. Inspect optional per-file Adobe selection/publication and all-scanned scope.
   Validation off must not invoke Adobe. Require must reject mismatched/invalid
   receipts even at exit0; warn cannot bypass candidate integrity/inspection
   fences. Missing optional digest differs from unchecked or mismatched digest.
6. Inspect stock/Ox build selection, native-thread/resource declarations and
   platform branches. Cooperative CPU accounting and sampled observations are
   not OS-thread caps, hardRSS or proof of other-platform native behavior.

## Directed evidence

- [Current acceptance map](sol-final-acceptance-map-20261019.md) keeps proved,
  missing and limited scopes separate.
- [Native stage](final-native-stage-result-20261019.md),
  [publication](final-native-publication-result-20261019.md),
  [positional writes](final-positional-write-result-20261019.md) and
  [scratch rollback](final-clone-scratch-result-20261019.md) bind native faults
  and designated guard-removal controls to current sources.
- [Generic clone receiving](final-clone-sync-result-20261019.md),
  [interruption/recovery](final-clone-interruption-result-20261019.md) and
  [archive round trip](final-archive-roundtrip-result-20261019.md) retain actual
  parent/client/server/group/resource closure rather than process-absence guesses.
- [Parser cases](final-parser-case-map-20261019.md),
  [DNG components](final-dng-component-result-20261019.md),
  [XMP decisions/refusals](final-xmp-policy-case-map-20261019.md) and
  [validation findings](final-adobe-finding-policy-case-map-20261019.md) give
  named scopes and distinguish synthetic controls from genuine SDK calls.
- [Three comparison binaries](upstream-baseline-builds-20261019.md) separate
  original stock, genuine selected upstream, and minimally patched upstream Ox.
  Build/selftest success is not a measured compiler speedup.
- [Handoff](../OPUS-HANDOFF.md) records current next work and zero resource holds.

## Open acceptance before the draft can be completed

Authentic generated JXL/twelve-state SDK fixture generation and final
three-encoding mixed stock/Ox merge receiving remain unexecuted. The concrete
SDK generator is prepared, but its immediate shared-machine window is not
allocated; Photo is not held during preparation. The remaining prescribed
large/workload/topology and original/upstream performance comparisons, plus the
last requirement-to-evidence joins, remain open. Already saved failures and
partial matrices must stay visible. This guide neither shrinks those
requirements nor marks the goal complete or authorizes a runtime successor.

## Production paths by review area

### Filesystem transfer and native publication (17)

- [`src/copy.ml`](../src/copy.ml)
- [`src/copy.mli`](../src/copy.mli)
- [`src/directoryOwner.ml`](../src/directoryOwner.ml)
- [`src/directoryOwner.mli`](../src/directoryOwner.mli)
- [`src/finalPublication.ml`](../src/finalPublication.ml)
- [`src/finalPublication.mli`](../src/finalPublication.mli)
- [`src/finalPublication_stubs.c`](../src/finalPublication_stubs.c)
- [`src/fs.ml`](../src/fs.ml)
- [`src/fspath.ml`](../src/fspath.ml)
- [`src/fspath.mli`](../src/fspath.mli)
- [`src/os.ml`](../src/os.ml)
- [`src/stagePublication.ml`](../src/stagePublication.ml)
- [`src/stagePublication.mli`](../src/stagePublication.mli)
- [`src/stagePublication_stubs.c`](../src/stagePublication_stubs.c)
- [`src/transfer.ml`](../src/transfer.ml)
- [`src/transfer.mli`](../src/transfer.mli)
- [`src/wholeFileClone.ox.mli.in`](../src/wholeFileClone.ox.mli.in)

### DNG interpretation, semantic ranges and hashes (32)

- [`src/componentHash.ml`](../src/componentHash.ml)
- [`src/componentHash.mli`](../src/componentHash.mli)
- [`src/componentHash.ox.mli.in`](../src/componentHash.ox.mli.in)
- [`src/dngComponents.ml`](../src/dngComponents.ml)
- [`src/dngComponents.mli`](../src/dngComponents.mli)
- [`src/dngComponents.ox.mli.in`](../src/dngComponents.ox.mli.in)
- [`src/dngLayout.ml`](../src/dngLayout.ml)
- [`src/dngLayout.mli`](../src/dngLayout.mli)
- [`src/dngLayout.ox.mli.in`](../src/dngLayout.ox.mli.in)
- [`src/dngSemantic.ml`](../src/dngSemantic.ml)
- [`src/dngSemantic.mli`](../src/dngSemantic.mli)
- [`src/dngSemantic.ox.mli.in`](../src/dngSemantic.ox.mli.in)
- [`src/formatExtension.ml`](../src/formatExtension.ml)
- [`src/formatExtension.mli`](../src/formatExtension.mli)
- [`src/formatExtension.ox.mli.in`](../src/formatExtension.ox.mli.in)
- [`src/semanticDelta.ml`](../src/semanticDelta.ml)
- [`src/semanticDelta.mli`](../src/semanticDelta.mli)
- [`src/semanticDelta.ox.mli.in`](../src/semanticDelta.ox.mli.in)
- [`src/semanticFile.ml`](../src/semanticFile.ml)
- [`src/semanticFile.mli`](../src/semanticFile.mli)
- [`src/semanticFile.ox.mli.in`](../src/semanticFile.ox.mli.in)
- [`src/semanticFile_stubs.c`](../src/semanticFile_stubs.c)
- [`src/semanticFormats.ml`](../src/semanticFormats.ml)
- [`src/semanticFormats.mli`](../src/semanticFormats.mli)
- [`src/semanticFormats.ox.mli.in`](../src/semanticFormats.ox.mli.in)
- [`src/semanticHash.ml`](../src/semanticHash.ml)
- [`src/semanticHash_evp.h`](../src/semanticHash_evp.h)
- [`src/semanticHash_stubs.c`](../src/semanticHash_stubs.c)
- [`src/semanticReport.ml`](../src/semanticReport.ml)
- [`src/semanticReport.mli`](../src/semanticReport.mli)
- [`src/semantic_hash_config.ml`](../src/semantic_hash_config.ml)
- [`src/xmpObservation.ml`](../src/xmpObservation.ml)

### Worker, resource and descriptor ownership (15)

- [`src/domainOwner.ml`](../src/domainOwner.ml)
- [`src/domainOwner.mli`](../src/domainOwner.mli)
- [`src/notificationPipe.ml`](../src/notificationPipe.ml)
- [`src/notificationPipe.mli`](../src/notificationPipe.mli)
- [`src/ownedClose.ml`](../src/ownedClose.ml)
- [`src/ownedClose.mli`](../src/ownedClose.mli)
- [`src/ownedClose.ox.mli.in`](../src/ownedClose.ox.mli.in)
- [`src/retainedOwnership.ml`](../src/retainedOwnership.ml)
- [`src/retainedOwnership.mli`](../src/retainedOwnership.mli)
- [`src/semanticAdmission.ml`](../src/semanticAdmission.ml)
- [`src/semanticAdmission.mli`](../src/semanticAdmission.mli)
- [`src/semanticRuntime.ml`](../src/semanticRuntime.ml)
- [`src/semanticRuntime.mli`](../src/semanticRuntime.mli)
- [`src/semanticWorkers.ml`](../src/semanticWorkers.ml)
- [`src/semanticWorkers.mli`](../src/semanticWorkers.mli)

### RPC, archive, scan and reconciliation integration (14)

- [`src/files.ml`](../src/files.ml)
- [`src/remote.ml`](../src/remote.ml)
- [`src/remote.mli`](../src/remote.mli)
- [`src/semanticMergeCache.ml`](../src/semanticMergeCache.ml)
- [`src/semanticMergeCache.mli`](../src/semanticMergeCache.mli)
- [`src/semanticRemote.ml`](../src/semanticRemote.ml)
- [`src/semanticRemote.mli`](../src/semanticRemote.mli)
- [`src/semanticSync.ml`](../src/semanticSync.ml)
- [`src/semanticSync.mli`](../src/semanticSync.mli)
- [`src/ubase/umarshal.ml`](../src/ubase/umarshal.ml)
- [`src/ubase/umarshal.mli`](../src/ubase/umarshal.mli)
- [`src/uicommon.ml`](../src/uicommon.ml)
- [`src/update.ml`](../src/update.ml)
- [`src/update.mli`](../src/update.mli)

### Optional receiving validation (20)

- [`src/candidateValidation.ml`](../src/candidateValidation.ml)
- [`src/candidateValidation.mli`](../src/candidateValidation.mli)
- [`src/candidateValidator.ml`](../src/candidateValidator.ml)
- [`src/candidateValidator.mli`](../src/candidateValidator.mli)
- [`src/dngCandidateValidation.ml`](../src/dngCandidateValidation.ml)
- [`src/dngCandidateValidation.mli`](../src/dngCandidateValidation.mli)
- [`src/supervisedExternal.ml`](../src/supervisedExternal.ml)
- [`src/validationDescriptor.ml`](../src/validationDescriptor.ml)
- [`src/validationDescriptor.mli`](../src/validationDescriptor.mli)
- [`src/validationPaths.ml`](../src/validationPaths.ml)
- [`src/validationPaths.mli`](../src/validationPaths.mli)
- [`src/validationScanWork.ml`](../src/validationScanWork.ml)
- [`src/validationScanWork.mli`](../src/validationScanWork.mli)
- [`src/validationSnapshot.ml`](../src/validationSnapshot.ml)
- [`src/validationSnapshot.mli`](../src/validationSnapshot.mli)
- [`src/validationSnapshot.ox.mli.in`](../src/validationSnapshot.ox.mli.in)
- [`src/validationStage.ml`](../src/validationStage.ml)
- [`src/validationStage.mli`](../src/validationStage.mli)
- [`src/validationStageWork.ml`](../src/validationStageWork.ml)
- [`src/validationStageWork.mli`](../src/validationStageWork.mli)

### Build and platform boundaries (8)

- [`src/Makefile.OCaml`](../src/Makefile.OCaml)
- [`src/dune`](../src/dune)
- [`src/fsmonitor/windows/Makefile`](../src/fsmonitor/windows/Makefile)
- [`src/make_tools.ml`](../src/make_tools.ml)
- [`src/semantic_mode_filter.ml`](../src/semantic_mode_filter.ml)
- [`src/system/system_generic.ml`](../src/system/system_generic.ml)
- [`src/system/system_intf.ml`](../src/system/system_intf.ml)
- [`src/system/system_win.ml`](../src/system/system_win.ml)

