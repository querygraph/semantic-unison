# Optional Adobe policy final case map — 2026-10-19

[Binding audit](sol-validation-policy-final-bindings-20261019.json) rechecked,
percompiler,329production inputs,212linked source inputs,5test inputs,4saved
artifacts and11case logs: all match. Original actual owner59806/68e562/0/no
session remains execution provenance. This audit ran no helpers or Adobe.

| Case in `tests/validation_warning/test.ml` | Proved component behavior |
| --- | --- |
| off | No selected helper invocation; no warning. This test prepares its own expected snapshot; it is not proof that every scan-selection path opens nothing. |
| warn-pass | Successful synthetic receipt permits, no warning. |
| warn-error | Synthetic errors permit with exactly one candidate-specific visible warning after the worker notification pump rearms. |
| require-error | Same finding rejects and does not emit a permissive warning. |
| warn-inspection-error | Candidate inspection EIO rejects before helper invocation; not a warning. |
| warn-mutation | Explicit synthetic helper mutation fails the immutable candidate fence. |
| warn-active-cancel | Active cancellation rejects after helper settlement. |
| warn-before-delivery-cancel | Cancellation after final tool inspection but before notice rejects without a notice. |
| warn-delivery-cancel / warn-delivery-abort | Cancellation or global abort during warning delivery prevents success. |
| warn-printer-error | Warning printer failure prevents success; no silent acceptance. |

The test checks an independently launched sibling hash can complete through the
nested owner-loop warning wait, retained resource/admission accounting during
notice delivery, no remaining helper/worker ledger and actual helper reap.
Synthetic v1 report bytes are not Adobe structure/decode/raw-digest proof.

## Source policy boundaries

`src/dngValidation.ml:148`–189 verifies completed/nontruncated/zero-exit protocol,
exact candidate hash+size and driver build, zeroerrors, validstructure and
successfuldecode. `Mismatch`, `Unsupported`, `Not_checked` rawdigests are findings;
`Missing` may pass structure/decode but remains missing, never rawdigest-valid.
Warn can relax findings; candidate/tool change and cancellation reject regardless.
`src/dngCandidateValidation.ml:170`–202 yields before visible warning, checks
cancellation both before and after delivery, and rejects required findings.

## Actual native scopes already retained

Current full receiving2CLI/4SDK and all-scanned4CLI/4SDK plus mixed2SDK+ExifTool/
hash runs remain valid exact recorded scopes. All-scanned includesoff/noSDK.
These do not establish every receiving policy/path combination. Final SDK merge
receiving uses the new nine-call matrix after authentic three-codec fixtures
are recovered. Native negative rawdigest/corrupt-output cases and explicit
reuse/resume/merge path mapping remain open. Do not replace them with this
synthetic handler-policy proof or claim pixel/corpus equivalence.

Photo bulk IO currently has priority. This source/evidence audit creates no
resource reservation/admission or native dispatch; standing8/8 is unchanged.
