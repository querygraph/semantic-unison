# Component RPC final-auditor source successor

The consumed V1 matrix ran all eight probes successfully but its original final
auditor failed on a client/supervisor `cancel_reason` field that the pinned
producers never emitted. The original exit1/result bytes and subsequent narrow
saved-receipt adoption remain unchanged in the main worktree and sealed return.
This branch fixes future auditing; it does not replay or relabel that run.

`producer_schema.py` now defines the exact current client and supervisor cleanup
shapes. `audit.functional` calls it after the existing raw command/group/ledger
binding and independent generated-file SHA readback. The original top-level
fault refusal remains. Normal direct wait, pre-reap group absence, timeout and
hard-kill evidence and actual native-server cancellation/pump proof are required.
The helper does not invent/default missing cancellation fields and is not a
standalone process/group/resource-release authority.

The helper is in the runtime source inventory (343 sources here, previously342).
Missing/changing that dependency refuses the plan. The old source-pinned plan
is deliberately not repinned or made runnable in this successor. No fresh
workspace, admission or transport command is prepared by this change; any
future runtime execution requires its own reviewed immutable plan and grant.

Controls now emit distinct real producer shapes rather than a generic cleanup
dictionary with invented fields. AST checks compare those field sets with the
actual current producer definitions and the supervisor's explicit extra field.
Eight projected actual metadata vectors retain their exact cleanup objects and
historical source/receipt provenance. Historical hashes are compared with the
consumed plan, not relabeled when unrelated current source comments change.
The shared predicate's AST matches the separately adopted saved predicate.

A full simulated eight-case worker runs with nine private disposable resource
FDs, no live canonical IO grant or RPC. Its final functional audit is unmocked:
real-shaped results produce complete=true/zero, while restoring the original
lookup produces the original complete=false/KeyError/one. This is a regression
control, not an actual transport rerun. Existing raw-proxy substitution,
failed-prefix/retained ownership, independent file-readback and cancellation
controls remain in place.

Exact qualification:
`tests/qualification/component-rpc-producer-audit-source-actual-20261017.json`.
Twenty-two coordinator, eight metadata-readback and six saved-audit control
groups passed under standing Unison8. Actual control parents93347/15fd98/0 and
9b669b/0 closed, with all contained groups/token sets closed. The coordinator
suite was rerun only after clarifying historical-vector provenance; the helper,
readback/saved code and343runtime source pins were unchanged. All318C/OCaml
production source bytes match the prior qualified source, so no build rerun is
claimed or needed for this Python-only change. Original main342runtime pins and
all eight actual metadata source records were independently rechecked unchanged.
No SDK/camera/Adobe/media/receiving/performance/production claim follows.
