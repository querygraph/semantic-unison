# Semantic merge (SOL row 10) — case map, 2026-10-19

Read-only mapping of existing tests and actual receipts; nothing was rerun for
this map. Production head is now `10c5d159`; evidence below marked *pre-fix*
pins earlier production hashes (see
[production delta impact](production-delta-10c5d159-impact-20261019.md)).

## Evidence sources

| Key | Receipt | Actual | Pins |
| --- | --- | --- | --- |
| K | `tests/qualification/current-xmp-kernel-observation-actual-20261018.json` | PASS_CLOSED, controller 65831 7dcb8a→c277e0, exit 0 | pre-fix; rebound by `final-xmp-case-binding-20261019.json` (audit 9cb39c/0, metadata only) |
| R | `tests/qualification/current-dng-reconciliation-actual-20261018.json` | PASS_CLOSED, 5070 d4fe44→c3ff40, exit 0; records `automaticMergeEnabled: false`, `archiveBaseAuthorityQualified: false` | pre-fix |
| D | `tests/dng_merge/qualification.json` (built-in DNG merge CLI, stock+Ox budgeted receipts) | `passed`, 2026-10-14 | older production pins |
| S | `tests/qualification/current-sdk-merge-native-actual-20261019.json` | PASS_ACTUAL_CLOSED, session 61260 2d7fab→3d8747, exit 0; postclosure `current-sdk-merge-saved-audit-actual-20261019.json` | pre-fix |
| N | `tests/qualification/current-named-receiving-actual-20261019.json` | PASS_ACTUAL_CLOSED stock+Ox `-04` | `10c5d159` |

## Concern map

| Concern | Tests | Evidence | Scope / limits |
| --- | --- | --- | --- |
| Same-scalar conflict | `tests/xmp_merge/test.ml` Rating 2 vs 3, Label Red vs Green; 343-triple Rating truth table ("rating truth-table conflict decision"); `tests/dng_reconcile/test.ml` "competing rating accepted"; D `competing` | K, R, D (rejected as designed) | Rating fully tabulated; Label one conflict case |
| One-sided / disjoint change | `test.ml` `ok` cases; D `disjoint`; S disjoint Rating/Label | K; D converged; S target exact on both replicas for uncompressed/JPEG/JPEG XL | generated DNGs; 4 SDK warnings per report retained |
| Delete vs change | `test.ml` `remove_label`; D `deleted-field` | K; D rejected | one delete/edit case, not every deletion combination |
| rdf:Bag / Seq / Alt | `test.ml` loop over `["Bag";"Seq";"Alt"]` | K (+4 RDF conflicts) | refusal only; no general RDF merge |
| Language alternatives | `test.ml` `xml:lang="en"`; Alt loop | K | refusal only |
| Qualifiers | `test.ml` `rdf:parseType="Resource"` + `xmp:Qualifier` | K | refusal only |
| Rendering fields | `test.ml` `crs:Exposure2012` ("rendering group admitted") | K | one field; no rendering-equivalence or rendering-merge claim |
| Unknown / opaque / compound | `test.ml` `xmp:Unknown`, opaque `urn:opaque` kept, structural change refused; dng_reconcile "opaque edit accepted"; D `unknown-field`, `opaque-payload` | K, R, D (rejected) | unchanged opaque subtree kept byte-exact; meanings stay opaque |
| Missing / mismatched base | dng_reconcile "stale live basis accepted", "peer-only base accepted", "invalid nonce accepted"; D `missing-base`, `stale-base`; `tests/merge_io_errors/probe.ml`; `semantic_base_cache` missing-base | R; D; merge_io_errors (2026-10-14) | durable archive-base authority explicitly NOT qualified; missing bases decline unless a verified backup exists |
| Convergence / idempotence | `test.ml` replica-symmetry checks; dng_reconcile "replica order target differs"; D `disjoint`/`swapped` converged ×3; S no-op | K, R, D, S (no-op: identical bytes and eight-field identities, zero helpers, all three codecs) | merge→no-op only; no long-running multi-sync convergence |
| Receiving the merged output | S 3 codecs × seed/merge/no-op with required SDK validation; N `merge-pass-pass`, `merge-error-pass`, `merge-pass-error`, `merge-pass-wrong-receipt`; D `first-receiver-reject`, `second-receiver-reject` | S (pre-fix); N at `10c5d159` | S: no negative/warn/resume. N: fixture merge program, not the XMP semantic merge, no SDK |

## Gaps

1. The built-in semantic DNG/XMP merge has not run end to end on the
   `10c5d159` binary. N exercises the changed merge commit path only with a
   fixture merge program; D and S predate the fix. Re-running the D matrix (and
   ideally S) on the current builds is the concrete closure.
2. Bag/Seq/Alt/qualifier/language cases are kernel-level refusals only; no
   CLI/receiving-level run.
3. One rendering field and one delete/edit combination only.
4. Durable archive-base authority remains unqualified by design.
5. No real-SDK receiving run of a refused conflicting merge (S covers disjoint
   merges only); no multi-sync convergence run.

Unsupported compound and rendering merges refuse in every mapped case; none is
guessed.
