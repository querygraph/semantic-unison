# SDK receiving comparison

Functional status: PASSED; complete: True. No new native executions.

| Compiler | Endpoint workers | Measured samples | Median seconds | Range seconds |
| --- | ---: | ---: | ---: | --- |
| stock | 1 | 5 | 3.384026 | 3.373181–3.470242 |
| stock | 3 | 5 | 2.503401 | 2.494228–2.516853 |
| ox | 1 | 5 | 3.364461 | 3.355103–3.373581 |
| ox | 3 | 5 | 2.476375 | 2.460561–2.587454 |

Observed median ratios (worker1 / worker3):

- stock: 1.3518
- ox: 1.3586

Limitations:

- Warm generated-input end-to-end receiving validation includes hashing, transport, staging, helper startup and SDK; not isolated SDK decode throughput.
- One warmup/five measured repetitions per configuration; observed median ratios are descriptive, not confidence bounds or causal SDK speedup.
- All verified measured cases retain their exact row indexes and order. Failed calls remain in attempted rows and raw pinned input, never imputed as zero.
- Incomplete results have no comparative ratio. CPU8 reservations and source limits are not whole-process RSS/OSthread/physical IO caps.
- No coldcache, representative camera corpus, semantic eligibility, pixel equivalence or production qualification. Source activity and scheduling disclosures must accompany actual results.
- This receipt audit does not prove owning-tool terminal, fresh payload hashes or global resource release; those require separate actual owner/parent acceptance.
