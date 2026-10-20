# Final scalar merge case map — 2026-10-19

This closes the named **component-case mapping** for SOL acceptance area10;
it does not close receiving, archive-base authority, or the whole goal.
[Fresh source/artifact binding audit](sol-xmp-final-case-bindings-20261019.json)
rechecked all six recorded stock/Ox rows: 14+9+14+9+27+27 explicit source pins
match current files, and all16 referenced result/closure/stdout/stderr artifacts
match their recorded sizes and hashes. This was a saved-evidence audit, not a
new test execution or proof of the entire dependency graph.

| Required case | Exact test body | Proven behavior / boundary |
| --- | --- | --- |
| Unchanged / one-sided scalar / disjoint fields | `tests/xmp_merge/test.ml:8`–12 | Exact packet output for unchanged, rating-only, label-only, combined rating+label, and identical concurrent output. |
| Conflicting scalar edits | `tests/xmp_merge/test.ml:14`–15 and49–64 | Different ratings/labels refuse; all343 base/left/right rating combinations follow independent three-way truth table. |
| Replica order / convergence | `tests/xmp_merge/test.ml:23`–24,61–62; `tests/dng_reconcile/test.ml:9`–13 | Replica symmetry at scalar and DNG-plan target-digest levels; not a long-running archive convergence test. |
| Delete versus edit | `tests/xmp_merge/test.ml:35`–38 | Removing Label while other side edits Label refuses. This is one explicit delete/edit case, not every deletion combination. |
| Bag / Seq / Alt | `tests/xmp_merge/test.ml:65`–67 | All three nested RDF container forms refuse scalar reconciliation. Compound merging is deliberately unsupported. |
| Qualified values | `tests/xmp_merge/test.ml:41`,68–69 | Language-qualified and rdf:parseType Resource/qualifier values refuse this scalar contract. |
| Rendering edit | `tests/xmp_merge/test.ml:31`–34 | Exposure change combined with descriptive edit refuses; no rendering equivalence or rendering merge claim. |
| Unknown bytes | `tests/xmp_merge/test.ml:20`,27–30 | Newly introduced unsupported field refuses; unchanged opaque subtree preserved exactly and structural opaque change refuses. |
| Encoding / malformed / limits | `tests/xmp_merge/test.ml:13`,16–22,25–26,39–48 | Entity-normalized scalar agreement preserves selected exact encoding; invalid rating/long label/NUL/duplicate/truncated packet and merged packet overflow refuse. |
| Exact DNG materialization | `tests/dng_reconcile/test.ml:12`–18 | Independent target digest, exactly3072 logical bytes/one reported write, materialized target digest. Logical counters do not prove physical writes. |
| Opaque change / stale basis / competing rating | `tests/dng_reconcile/test.ml:19`–23 | Each rejects the plan rather than inventing a merge. |
| Base authority / nonce | `tests/dng_reconcile/test.ml:24`–26 | Peer-only decoded base and invalid nonce refuse. This does not establish durable archive-base authority. |

Recorded real executions are the stock/Ox kernel/observation jobs in
`tests/qualification/current-xmp-kernel-observation-actual-20261018.json`
(actual controller65831/c277e0/0/no session), and two reconciliation jobs in
`tests/qualification/current-dng-reconciliation-actual-20261018.json`
(actual controller5070/c3ff40/0/no session). Reconciliation receipts explicitly
say automaticMergeEnabled=false and archiveBaseAuthorityQualified=false.
Those limits remain; final native receiving merge requires the separate
current SDK merge matrix after authentic fixtures are recovered.

Next source audit: generic clone packet/property/failure cases and DNG
parser/layout coverage. Adobe execution stays at the end per user steering.
