# Current shared-budget cached SHA observations

Actual2026-10-17 stock/Ox production-object probes, same generated32MiB input,
workers1/2/4/6 within standing Unison8. One warmup and five measured batches
per configuration, six digest jobs/batch. Compiler order reverses each measured
round. This is a finite shared-machine observation, without an absolute quiet claim.

| Workers | Stock MiB/s median (min–max) | Ox MiB/s median (min–max) | Stock / Ox median CPU÷wall |
| ---: | ---: | ---: | ---: |
| 1 | 365.5 (359.6–372.4) | 365.1 (357.9–366.6) | 0.95 / 0.95 |
| 2 | 713.3 (694.1–747.4) | 721.8 (700.7–742.7) | 1.90 / 1.91 |
| 4 | 1096.5 (1021.8–1116.4) | 1107.2 (1062.4–1124.1) | 2.94 / 2.98 |
| 6 | 2128.4 (2104.5–2145.1) | 2127.4 (2051.2–2157.4) | 5.94 / 5.95 |

Six versus one worker gives 5.82× stock and 5.83× Ox median batch throughput in this experiment.
The compilers use the same CommonCrypto SHA backend. Their similar throughput
does not demonstrate an OxCaml-specific optimization or universal speedup.

Six jobs do not evenly fill four workers: ideal equal-duration execution has
a four-job wave followed by two jobs, averaging three busy workers. The observed
~2.94–2.98 CPU÷wall at four workers is consistent with that batch shape; it is
not evidence of sustained four-worker saturation. No samples are excluded or
replaced, and no automatic repeat or revised cohort is authorized.

## What was counted

All48 native batches and288 digests were correct, including warmups. The production
primary-reader observer counted9,663,676,416 delivered bytes (9GiB),147,456 chunks
and288 completed input observations. This covers the primary digest input only;
compiler/source verification, filesystem metadata, diagnostics and output are
outside that counter. Fixture generation writes32MiB once outside timed batches.
No Unison synchronization or network transport was invoked. System-wide network
or physical storage traffic was not sampled; cache residency was not enforced.

The timed native interval covers opening/submitting/reading/hashing and owner
completion. Pool construction, compilation, fixture creation, result checking
and shutdown are outside it. Process CPU includes all native domains/owner
within that interval; it is not physical-core utilization or whole-pipeline CPU.

Process-lifetime peak RSS includes native startup/shutdown. The largest saved
sample was 6,164,480 bytes. Input-open FD samples reached30, while every sample
returned to its12-descriptor baseline (including nine inherited resource FDs).
FD samples can miss transient peaks. These observations do not impose a hard
parent/child-tree RSS, FD or OS-thread ceiling. The16GiB declared IO allowance
is planning accounting, not an instrumented physical limit.

## Ownership and evidence

Actual owningtool69788/terminal8ecd8e/exit0/no running session; worker6983
reaped0 with other group members absent before reaping. The parent audited raw
numeric rows, exact schedule, compiler/object pins and generated executables
under retained EXglobal IO before closing CPU00..07 and the IO descriptor.
Photo release01a14d94-bcdd preceded sealing; no resources or analysis hold remain.

[Sealed observations](../../../tests/qualification/cached-worker-benchmark-actual-20261017.json)
bind all48 numeric samples, raw native output, summaries, actual terminal and
raw stored artifact pins. Source qualification and two64B directed counters are
separate from this actual matrix. Admission4c9d02f3 was consumed once.

This closes the current cached-worker measurement gap only. End-to-end transfer
stage/physical IO interpretation and whole-process resource-limit requirements
remain distinct; neither this report nor historical partial warm512 results
prove the entire SOL goal complete. No SDK, Adobe, Photo/camera original, UI,
production publication or receiving operation occurred.
