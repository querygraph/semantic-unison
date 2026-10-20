# Larger cohorts: full 128 and 512 MiB matrices

All 20 cohorts passed: stock and OxCaml, each with worker selections
1/2/4/8/auto, at 128 MiB×4 and at 512 MiB×4. The 1- and 2-worker cohorts ran
on the standard 8 CPU tokens ([shared8 report](auto-cohort-larger-shared8-report-20261020.md)).
The 4, 8 and auto cohorts borrowed all 18 tokens while Photo was paused. Each
owner exited 0 and closed every worker, group, CPU token and the EXglobal
descriptor. Each size is a `FULL_GENERATED_MATRIX` of 180 rows and 540 CLI
calls ([128](auto-cohort-larger128-all10-report-20261020.json),
[512](auto-cohort-larger512-all10-report-20261020.json); manifests in the
matching `-report-input-` files).

Median update wall seconds over five measured rows:

| MiB | Mode | stock 1 / 2 / 4 / 8 / auto | OxCaml 1 / 2 / 4 / 8 / auto |
| --- | --- | --- | --- |
| 512 | ordinary | 36.5 / 36.4 / 38.2 / 36.6 / 36.4 | 36.9 / 36.6 / 36.5 / 36.3 / 36.2 |
| 512 | receiver-clone | 35.9 / 36.2 / 37.6 / 35.9 / 35.7 | 38.5 / 36.1 / 36.6 / 35.5 / 35.5 |
| 512 | semantic | 69.1 / 46.4 / 35.9 / 34.8 / 34.5 | 69.3 / 51.2 / 35.5 / 34.3 / 34.4 |
| 128 | ordinary | 11.3 / 9.5 / 16.4 / 16.2 / 11.8 | 9.6 / 9.4 / 16.3 / 11.9 / 9.7 |
| 128 | receiver-clone | 9.8 / 9.3 / 16.2 / 16.0 / 11.6 | 9.5 / 9.2 / 16.3 / 11.7 / 9.5 |
| 128 | semantic | 18.8 / 11.9 / 16.6 / 16.5 / 9.2 | 18.0 / 11.8 / 14.6 / 11.0 / 9.2 |

## Reading

At 512 MiB, semantic sync improves from one worker (69 s) to two (46–51 s)
and reaches about 35 s at four workers or more. That equals the
ordinary and receiver-clone times, so semantic verification is fully hidden
behind the transfer from four workers on. Auto lands on that floor too.
Ordinary and receiver-clone do not depend on the worker count. Stock and
OxCaml agree within a few percent at four workers and more.

At 128 MiB, the stock 4 and 8 cohorts and the OxCaml 4 cohort are slower in
every mode, including ordinary (about 16 s against 9.5 s). Ordinary transfers
do not use semantic workers, so the slowdown points to host activity during
those runs, not to worker scaling. Those three cells are uncontrolled-host
outliers and support no claim. Auto (9.2 s semantic) is the best 128 MiB result
for both compilers.

These are descriptive figures from separate runs on a warm, uncontrolled
same-host loopback. They are not causal scaling, quiet-host timing, CPU hard-cap
or physical APFS claims. 2048 MiB is deferred: per-call limits now scale with
size, and those cohorts will run after Photo's run, on the 1- and 2-worker
selections only unless an 18-token borrow is approved again.
