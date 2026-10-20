# Many-small worker comparison

Generated 1,024 × 32 KiB inputs, 512 B XMP edits, five measured samples after one warmup per configuration. Both endpoints use the listed compiler. The two serial cohorts ran at different times on an uncontrolled warm host; ratios are descriptive, not isolated scaling or compiler effects.

| Compiler | Mode | Worker1 client median (s) | Worker3 client median (s) | Ratio 1/3 |
| --- | --- | ---: | ---: | ---: |
| ox | ordinary | 7.0133 | 6.6916 | 1.048 |
| ox | receiver-clone | 8.4809 | 8.1621 | 1.039 |
| ox | semantic | 8.5171 | 6.7739 | 1.257 |
| stock | ordinary | 6.9057 | 6.5330 | 1.057 |
| stock | receiver-clone | 8.5973 | 8.1694 | 1.052 |
| stock | semantic | 8.5739 | 7.0087 | 1.223 |

All 72 sample owners/216 CLI calls completed normally. Raw samples, pair timings, per-process CPU/RSS and protocol counters are retained in the individual JSON reports. Every target/no-op identity was checked before deliberate generated cleanup.

Ordinary transfer remains fastest here. Clone/SDE logical materialization models are 1 MiB/512 KiB versus 32 MiB ordinary, not physical write counts. Unmeasured application reads, descriptor/queue peaks and separate processing-stage times remain unknown. No SDK/camera/pixel/cold-cache/physical-network or production claim.
