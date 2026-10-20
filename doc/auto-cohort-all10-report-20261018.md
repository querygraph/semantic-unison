# Completed generated worker matrix

All ten stock/OxCaml × 1/2/4/8/auto cohorts passed: 180 rows, 540 CLI calls, 30 warmup and 150 measured rows. Every owning tool exited 0; nested call groups, workers and CPU/IO descriptors closed. The temporary 18-credit series has ended; standing Unison8/Photo8/system2 is restored.

| Compiler | Workers | Ordinary median s | Receiver-clone median s | Semantic median s | Semantic one-worker ratio |
| --- | --- | ---: | ---: | ---: | ---: |
| stock | 1 | 4.930 | 4.875 | 9.013 | 1.000 |
| ox | 1 | 4.909 | 4.860 | 8.984 | 1.000 |
| stock | 2 | 4.667 | 4.683 | 6.084 | 1.481 |
| ox | 2 | 4.695 | 4.769 | 6.136 | 1.464 |
| stock | 4 | 4.243 | 4.201 | 4.641 | 1.942 |
| ox | 4 | 4.128 | 4.076 | 4.623 | 1.943 |
| stock | 8 | 3.942 | 3.925 | 3.992 | 2.258 |
| ox | 8 | 3.921 | 3.870 | 3.921 | 2.291 |
| stock | auto | 3.912 | 3.827 | 3.899 | 2.311 |
| ox | auto | 3.998 | 3.944 | 4.000 | 2.246 |

Each row updates eight generated 32 MiB files over private same-host loopback. Cache state is warm/uncontrolled. All five measured samples are retained; only the declared warmup is omitted from distributions. Ratios compare separate runs and are descriptive, not causal speedup. Five-sample p90 is the maximum and is not a stable population-tail estimate. Auto means configured automatic selection with an eight-worker endpoint ceiling, not an observed OS-thread count.

Semantic medians fall from about 9.0 s at one worker to about 3.9–4.0 s at eight/auto. Stock and OxCaml results are close in this fixture; this does not establish a general compiler advantage. Ordinary and receiver-clone timing remains visible, including unsuccessful elapsed-time optimization.

Source/metadata coordination and uncontrolled OS activity preclude an absolute quiet claim. Client/server CPU and per-process RSS, primary logical reads, returned semantic writes, modeled extents and directional protocol counts remain distinct. Whole-application reads and physical writes are unknown. No SDK/camera/pixel, cross-volume, physical APFS savings or production claim. Larger sizes, additional workloads/topologies and final-candidate integration remain open.

[Machine-readable observations](auto-cohort-all10-report-20261018.json) · [Pinned inputs](auto-cohort-all10-report-input-20261018.json) · [All actual terminals and closure proofs](auto-cohort-all10-actual-closure-20261018.json)
