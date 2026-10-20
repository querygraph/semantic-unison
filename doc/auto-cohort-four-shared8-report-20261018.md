# Shared8 worker cohorts: four completed runs

Stock and OxCaml each passed the separate one-worker and two-worker cohorts.
All four actual owning tools exited0; all workers/call groups and CPU8/EXglobal
descriptors closed. Total:72rows/216CLI,12warmups+60measured rows.
The six4/8/auto cohorts are unstarted. This is not a completed SOL matrix.

| Compiler | Workers | Mode | Median update s | Descriptive one-worker wall ratio |
| --- | ---: | --- | ---: | ---: |
| stock | 1 | ordinary | 4.930 | 1.000 |
| stock | 1 | receiver-clone | 4.875 | 1.000 |
| stock | 1 | semantic | 9.013 | 1.000 |
| ox | 1 | ordinary | 4.909 | 1.000 |
| ox | 1 | receiver-clone | 4.860 | 1.000 |
| ox | 1 | semantic | 8.984 | 1.000 |
| stock | 2 | ordinary | 4.667 | 1.056 |
| stock | 2 | receiver-clone | 4.683 | 1.041 |
| stock | 2 | semantic | 6.084 | 1.481 |
| ox | 2 | ordinary | 4.695 | 1.046 |
| ox | 2 | receiver-clone | 4.769 | 1.019 |
| ox | 2 | semantic | 6.136 | 1.464 |

The corpus is eight32MiB generated files per row, warm/uncontrolled cache,
same-host private loopback. All five measured samples per configuration remain.
Ratios are descriptive across separate runs, not causal scaling or OS-thread
proof. Source/metadata coordination and uncontrolled OS activity prevent an
absolute quiet-timing claim. No physical APFS savings, SDK/camera/pixel or
production qualification is inferred.

[All72saved observations](auto-cohort-four-shared8-report-20261018.json) separate
directional protocol counts, client/server CPU/RSS, primary reads, returned
semantic writes and modeled non-inherited output extents. Missing application
reads/physical writes remain unknown. Raw inputs remain pinned and unchanged.

[Allfour actual terminals and closure proofs](auto-cohort-four-shared8-actual-closure-20261018.json)
remain distinct from this saved-only report. No runtime or resource release
was performed by reporting.
