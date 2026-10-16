# Shared-eight SDK sampled OS observations

Actual V2 owner39043/ef80c4/exit0/no session closed. Twelve SDK calls and62
probe children settled, with62 available samples and no missing sample records.
Unison00..07 and EXglobal closed. This separately admitted run is consumed once.

| Codec | Backend | Requested | Samples | Sampled threads min–max | Largest sampled RSS bytes |
| --- | --- | ---: | ---: | ---: | ---: |
| uncompressed | reference | 1 | 3 | 1–1 | 53190656 |
| uncompressed | experimental | 1 | 3 | 1–1 | 54341632 |
| uncompressed | experimental | 2 | 3 | 1–1 | 53346304 |
| uncompressed | experimental | 6 | 2 | 1–1 | 50987008 |
| jpeg | reference | 1 | 4 | 1–1 | 53051392 |
| jpeg | experimental | 1 | 4 | 1–1 | 53358592 |
| jpeg | experimental | 2 | 3 | 1–2 | 56070144 |
| jpeg | experimental | 6 | 2 | 1–6 | 43032576 |
| jxl | reference | 1 | 13 | 1–1 | 114302976 |
| jxl | experimental | 1 | 13 | 1–1 | 119595008 |
| jxl | experimental | 2 | 8 | 1–2 | 120934400 |
| jxl | experimental | 6 | 4 | 1–6 | 153579520 |

JPEG/JXL experimental2/6 calls include actual OS observations of2/6 threads.
The short uncompressed calls were sampled only at one thread; sampling does
not establish their maximum fanout. RSS values are sample maxima, never actual
peaks or hard caps. No process-tree total, calibrated CPU utilization, pixel
equivalence, camera corpus, production endpoint or throughput claim follows.

Probe overhead is included in elapsed work. Each configuration ran once in a
fixed order on retained generated inputs; this is not a scaling benchmark.

[Machine-readable report](sdk-shared-host-v2-observations-20261016.json) is
reproduced by the exact command in the [analysis receipt](../tests/qualification/sdk-observation-report-actual-20261016.json).
The generator independently reruns the SDK/probe record audit but does not
replay SDK calls or prove outer closure. [Actual closure](../tests/qualification/sdk-shared-host-v2-actual-20261016.json)
separately pins the actual parent terminal, raw results and CPU/IO closure.
