This fork adds clone-aware exact transfers for ordinary files and DNGs, optional receiving-time Adobe validation, and coordinated stock OCaml/OxCaml workers. DNG interpretation separates encoded pixels, standard metadata and conservatively preserved opaque bytes; nested interpretation can improve incrementally without treating incomplete MakerNotes as a deployment blocker.

The current production successor adds an endpoint-local `semanticcpubudget` ceiling. It does not change the archive or RPC format. Shared launchers account for both endpoints and orchestration; configured budgets are not OS-thread or hard-RSS caps. Semantic behavior and Adobe validation remain opt-in.

Validation now includes:

- Four current stock/Ox Make/Dune builds and selftests, with 329 production-source pins matched.
- Current fixed SDE, range, worker parity/apply, XMP, reconciliation and renewed Runtime composition controls.
- Ten generated 32 MiB stock/OxCaml cohorts at 1/2/4/8/auto workers: 180 rows and 540 CLI calls, all actual parent/group/FD closures. The first 128 MiB stock/one-worker cohort also passed 18 rows and 54 CLI calls.
- Current mixed Adobe/ExifTool/hash probes, actual full receiving on two generated encodings, and unchanged-file all-scanned validation. Ten real SDK calls in these separate batches passed structure/decode/raw-digest checks; padding warnings are retained.

The draft remains incomplete. Larger benchmarks are at an empirical scheduling checkpoint; the prepared remaining matrix is not executed evidence. Final receiving-path/policy/merge mapping, additional workload/topology comparisons and final acceptance review remain open. Historical V6 compatibility results retain their predecessor source scope. No camera-corpus, pixel-equivalence, physical APFS savings, quiet-host scaling, hard-RSS or production activation claim follows.

Review entry points: [current acceptance map](https://github.com/querygraph/unison/blob/integration/sol-consolidated-review/doc/sol-final-acceptance-map-20261019.md), [worker measurements](https://github.com/querygraph/unison/blob/integration/sol-consolidated-review/doc/auto-cohort-all10-report-20261018.md), [first larger checkpoint](https://github.com/querygraph/unison/blob/integration/sol-consolidated-review/doc/larger128-stock1-checkpoint-20261019.md), and [handoff](https://github.com/querygraph/unison/blob/integration/sol-consolidated-review/OPUS-HANDOFF.md).

Fork-only draft review against `querygraph/unison:master`; the remaining qualification work is listed above.
