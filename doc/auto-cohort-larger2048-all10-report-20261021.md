# 2048 MiB × 2 cohorts: full matrix

All ten 2048 MiB × 2 cohorts passed on 2026-10-20/21: stock and OxCaml, each
with worker selections 1/2/4/8/auto. They ran from the v2 successor plans
(`auto-cohort-qualification-larger-2048-v2-20261020`), whose limits now scale
with size: 900 s per CLI call and a 28 800 s owner observation. The binaries
are the current `-05` builds of production `8581f357`.

- **Owners:** each exited 0, was not retained, and closed every worker, group,
  CPU token and the EXglobal descriptor. All 180 rows (540 CLI calls) are exact
  in result, basis and no-op.
- **CPU tokens:** the 1- and 2-worker cohorts used the standard 8 tokens. The
  4/8/auto cohorts used all 18 under the user's explicit "you can use all
  CPUs" ([authorization](temporary18-larger2048-authorization-20261020.json)),
  before Photo's run.
- **Report:** a saved-only `FULL_GENERATED_MATRIX`
  ([report](auto-cohort-larger2048-all10-report-20261021.json),
  [manifest](auto-cohort-larger2048-all10-report-input-20261021.json)).
- **Duration:** each cohort took 69–78 minutes.

Median update wall seconds, with client / server CPU seconds:

| Workers | stock ordinary | stock semantic | OxCaml ordinary | OxCaml semantic |
| ---: | ---: | ---: | ---: | ---: |
| 1 | 74.9 (28.3/54.0) | 142.3 (36.0/113.6) | 75.8 (28.8/54.5) | 144.6 (36.9/115.4) |
| 2 | 71.7 (27.3/51.5) | 91.8 (35.7/111.4) | 72.2 (27.4/51.9) | 91.3 (35.5/110.5) |
| 4 | 74.7 (28.5/53.7) | 94.3 (36.5/113.9) | 74.5 (28.4/53.4) | 94.8 (36.7/114.3) |
| 8 | 75.7 (28.8/54.4) | 93.3 (36.0/112.3) | 73.3 (27.9/52.6) | 93.9 (36.1/113.7) |
| auto | 73.6 (28.0/52.9) | 93.3 (36.1/112.8) | 76.0 (28.9/54.6) | 96.5 (37.4/116.7) |

Receiver-clone tracks ordinary within 1–3 s in every cohort; all values are in
the report.

## Reading

Semantic sync gains 1.55–1.58× from a second worker, and nothing more after
that: 4, 8 and auto all land at 93–97 s. Each row carries only two files, so at
most two semantic jobs can run at once. That is why 512 MiB × 4 kept improving
up to four workers and this workload stops at two. At two workers and more,
semantic stays about 20 s above ordinary. The two 2 GiB verifications overlap
each other but not all of the transfer, and server CPU rises by about 60 s.
Auto chooses well: it matches the best fixed selection on both compilers.
Stock and OxCaml agree within 2% at every selection.

The earlier shared8 stop (180 s per-call deadline in the semantic warm-up) does
not recur. The v2 semantic warm-ups finished in about 144 s at one worker, so the
first stop was most likely a cold-cache first run. The new limit leaves wide
margin either way.

These figures come from separate runs on a warm, uncontrolled same-host
loopback; Lightroom Classic was quitting around the start. They are
descriptive, not causal scaling, quiet-host timing or physical APFS claims.
