# Shared8 larger cohorts: 128 and 512 MiB complete, 2048 MiB stopped

All eight one- and two-worker cohorts at 128 MiB×4 and 512 MiB×4 passed on
stock and OxCaml. Each owning tool exited 0 and closed every worker, call group,
CPU8 and EXglobal descriptor. Each cohort has 18 rows and 54 CLI calls: one
warm-up and five measured rows per mode. The first 2048 MiB×2 cohort (stock,
one worker) stopped in its warm-up; the remaining three 2048 cohorts were not
started. The 4/8/auto selections belong to the separate temporary18 series, so
each per-size report is `INCOMPLETE_MATRIX` by design.

Median update wall seconds, with client / server CPU seconds:

| MiB×files | Compiler | Workers | ordinary | receiver-clone | semantic |
| --- | --- | ---: | ---: | ---: | ---: |
| 128×4 | stock | 1 | 11.27 (4.26/7.87) | 9.80 (3.79/6.75) | 18.82 (4.78/14.81) |
| 128×4 | ox | 1 | 9.64 (3.64/6.72) | 9.47 (3.63/6.56) | 18.03 (4.60/14.18) |
| 128×4 | stock | 2 | 9.50 (3.58/6.63) | 9.34 (3.57/6.46) | 11.89 (4.55/14.07) |
| 128×4 | ox | 2 | 9.38 (3.54/6.56) | 9.21 (3.55/6.37) | 11.76 (4.52/13.95) |
| 512×4 | stock | 1 | 36.53 (13.89/26.13) | 35.87 (13.88/25.46) | 69.09 (17.66/55.01) |
| 512×4 | ox | 1 | 36.85 (13.89/26.35) | 38.54 (15.37/27.41) | 69.30 (17.69/55.14) |
| 512×4 | stock | 2 | 36.44 (13.85/26.08) | 36.20 (13.99/25.68) | 46.44 (18.00/56.14) |
| 512×4 | ox | 2 | 36.56 (13.95/26.15) | 36.11 (13.93/25.65) | 51.23 (20.01/61.81) |

At both sizes the semantic mode is the only one that gains from a second worker
(128 MiB: 1.5–1.6×, 512 MiB: 1.35–1.5×). Ordinary and receiver-clone stay flat
because they are bound by transfer, not by CPU. Stock and OxCaml are within a
few percent of each other everywhere, except the 512 MiB two-worker semantic row
(46.4 s against 51.2 s). The rows come from separate runs on a warm, uncontrolled
same-host loopback. These are descriptive figures, not causal scaling, quiet-host
timings or physical APFS savings.

## 2048 MiB stop

The 2048 MiB stock one-worker cohort exited 1 after 1071 s, closed and
unretained. The ordinary (78.5 s) and receiver-clone (125.2 s) warm-ups passed.
The semantic warm-up moves 4 GiB per call through one CPU permit and hit the
cohort's fixed 180 s per-call native client deadline. At that point the server
had spent 56 s verifying one file and 23 s hashing the next. Unison handled the
cancellation as designed:

- the item reported `Failed [image-0001.dng]: Semantic inspection cancelled`;
- the server exited 0;
- groups were reaped, and tokens and the IO barrier were closed;
- source pins were unchanged.

No product fault is indicated. The limit comes from `bench/sync/auto_cohort.py`
(`timeout_seconds=180.0` for every larger workload). The frozen plans also
declare a 7200 s owner observation, and a full 2048 cohort at these per-call
times would not fit in it. 2048 MiB therefore needs successor plans with size-scaled
per-call and observation limits; those runs are deferred to the end of the
pipeline. The temporary18 series runs at 128 and 512 MiB only.

## Evidence

- Reports (saved-only, `runtime_invoked: false`; every row index retained):
  [128](auto-cohort-larger128-shared8-report-20261020.json),
  [512](auto-cohort-larger512-shared8-report-20261020.json),
  [2048 failed prefix](auto-cohort-larger2048-shared8-report-20261020.json).
  Their manifests are the matching `-report-input-` files.
- Plans: `unison-cpu-ceiling-20261018/doc/auto-cohort-qualification-larger-{128,512,2048}-v1-20261019`.
  Admissions were local: Photo is paused by user direction, and the user authorized everything.
- The 128 MiB stock one-worker cohort is the earlier
  `larger128-stock1-actual-20261019.json` run (52223/3c264e/0); this series
  added the other seven, plus the 2048 stop.
