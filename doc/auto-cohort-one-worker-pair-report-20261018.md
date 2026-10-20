# Current one-worker pair: partial benchmark report

Actual stock and OxCaml one-worker cohorts each passed18rows/54CLI, with one
warmup and five measured samples in each of three modes. Both owning tools
exited0, with all call/worker groups and Unison8/EXglobal descriptors closed.
The other eight cohorts are unstarted; this is not a completed worker matrix.

| Compiler | Mode | Median update s | Client→server B | Server→client B | Returned semantic writes B | Non-inherited extent model B |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| stock | ordinary | 4.930 | 87052 | 302214 | unknown | 268435456 |
| stock | receiver-clone | 4.875 | 87053 | 302214 | unknown | 65536 |
| stock | semantic | 9.013 | 87052 | 8255 | 24576 | 24576 |
| ox | ordinary | 4.909 | 87052 | 302214 | unknown | 268435456 |
| ox | receiver-clone | 4.860 | 87053 | 302214 | unknown | 65536 |
| ox | semantic | 8.984 | 87052 | 8255 | 24576 | 24576 |

Generated corpus: eight32MiB files per row, warm/uncontrolled cache,
same-host private loopback transport. All five measured samples remain; the
nearest-rank p90 with five samples is only the maximum. No absolute quiet-host
claim: source/report metadata inspection and coordination occurred during runs.

Semantic updates reduced the recorded reverse-direction protocol bytes and
returned logical writes, but took longer than ordinary or receiver-clone updates
in this one-worker dataset. Extent models are not measured write syscalls.
Application-wide reads and physical storage writes remain unknown. There is
no whole-tree RSS/FD, camera, SDK, pixel, corpus or production claim.

[All36saved observations and six distributions](auto-cohort-one-worker-pair-report-20261018.json)
retain compiler separation, directional protocol counts, per-endpoint CPU/RSS,
known writes/models and missing values. Raw result bytes remain authenticated
in the input manifest. Metadata reporting executed no transport or tool binary.

[Stock actual closure](../tests/qualification/auto-cohort-stock1-actual-20261018.json)
and [OxCaml actual closure](../tests/qualification/auto-cohort-ox1-actual-20261018.json)
retain the owning-tool terminals separately from nested process/FD evidence.
