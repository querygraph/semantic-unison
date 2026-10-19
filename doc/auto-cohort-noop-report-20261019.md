# Saved warm no-change observations — 2026-10-19

No synchronization was rerun. This report extracts the already completed no-op
call after each verified fixed-XMP update in the ten32MiB cohorts: two generated
files,30warmups and150measured no-op calls. Each saved call has exact-output/
unchanged-basis/no-op-inode fences and saved client/server/supervisor settlement.
The reproducible reader rehashed all20saved plan/result pins, retaining all180
raw no-op samples. Original full results/owners remain unchanged.

This covers that finite **warm no-change** workload, not cold startup, arbitrary
file counts, upstream performance, or whole SOL completion. These are modified
stock/Ox configurations; preference labels do not mean a clone/SDE update ran
during a no-change scan. No speedup or causal compiler advantage is established.

| Compiler | Worker selection | Mode | n | Median s | Min s | Max s |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| ox | 1 | ordinary | 5 | 0.738687 | 0.731794 | 0.747790 |
| ox | 1 | receiver-clone | 5 | 0.743368 | 0.726330 | 0.748303 |
| ox | 1 | semantic | 5 | 0.745360 | 0.736237 | 0.749661 |
| ox | 2 | ordinary | 5 | 0.746323 | 0.739608 | 0.760316 |
| ox | 2 | receiver-clone | 5 | 0.744410 | 0.743684 | 0.750162 |
| ox | 2 | semantic | 5 | 0.751336 | 0.743518 | 0.754161 |
| ox | 4 | ordinary | 5 | 0.737531 | 0.733181 | 0.746721 |
| ox | 4 | receiver-clone | 5 | 0.737493 | 0.725063 | 0.746926 |
| ox | 4 | semantic | 5 | 0.733706 | 0.728251 | 0.741517 |
| ox | 8 | ordinary | 5 | 0.737825 | 0.732045 | 0.746658 |
| ox | 8 | receiver-clone | 5 | 0.739643 | 0.736754 | 0.747269 |
| ox | 8 | semantic | 5 | 0.742790 | 0.732364 | 0.747568 |
| ox | auto | ordinary | 5 | 0.764503 | 0.747407 | 0.771512 |
| ox | auto | receiver-clone | 5 | 0.763887 | 0.754166 | 0.784763 |
| ox | auto | semantic | 5 | 0.768268 | 0.760777 | 0.779426 |
| stock | 1 | ordinary | 5 | 0.743412 | 0.732191 | 0.759981 |
| stock | 1 | receiver-clone | 5 | 0.743715 | 0.731297 | 0.759441 |
| stock | 1 | semantic | 5 | 0.742883 | 0.737663 | 0.752690 |
| stock | 2 | ordinary | 5 | 0.748996 | 0.744367 | 0.756731 |
| stock | 2 | receiver-clone | 5 | 0.744246 | 0.740007 | 0.753488 |
| stock | 2 | semantic | 5 | 0.741840 | 0.735025 | 0.755333 |
| stock | 4 | ordinary | 5 | 0.749743 | 0.737928 | 0.753504 |
| stock | 4 | receiver-clone | 5 | 0.746583 | 0.741360 | 0.756111 |
| stock | 4 | semantic | 5 | 0.745818 | 0.739660 | 0.751580 |
| stock | 8 | ordinary | 5 | 0.749449 | 0.743050 | 0.786397 |
| stock | 8 | receiver-clone | 5 | 0.751326 | 0.746381 | 0.760641 |
| stock | 8 | semantic | 5 | 0.752279 | 0.746769 | 0.762301 |
| stock | auto | ordinary | 5 | 0.734285 | 0.726044 | 0.744543 |
| stock | auto | receiver-clone | 5 | 0.729883 | 0.718619 | 0.749688 |
| stock | auto | semantic | 5 | 0.734818 | 0.722284 | 0.742321 |

Invocation wall includes client and loopback supervisor settlement. Native
client lifetime remains separate in every raw sample. Auto means configured
auto with endpoint ceiling8, not observed physical-core/OS-thread use. All rows
have five measured samples; the maximum describes these five, not a qualified
population tail. No quiet-window, cold-cache, physicalIO, bytes-transferred or
process-tree peak claim. Preserve background disclosures in the pinned originals.

[Machine-readable observations](auto-cohort-noop-report-20261019.json) contain
exact root/input pins. To reproduce into an absent owned output, use the pinned
Python with `bench/sync/noop_report.py --saved-report PATH
--saved-report-sha256 SHA --closure-index PATH --closure-index-sha256 SHA
--output UNUSED.json`; all paths/hashes are in that JSON. This reads saved
metadata only; it does not grant payload IO or infer a historical parent exit.

Actual saved-only analysis e73a07/exit0/no session: five original refusal/
distribution controls and the real pinned-input CLI closed, both childgroups
reaped0/absent and CPU4closed; noEXglobal/Unison/SDK/Photo.
