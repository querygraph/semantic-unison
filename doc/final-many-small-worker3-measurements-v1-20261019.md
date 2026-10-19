# Many-small shared-host measurements

Warm generated corpus: 1,024 × 32 KiB files, 512 B XMP packets. One warmup and five measured samples per configuration. Both endpoints use the named current compiler. No cache flush or quiet-host guarantee.

| Compiler | Workers per endpoint | Mode | Client median (s) | Observed range (s) | Pair median (s) |
| --- | ---: | --- | ---: | ---: | ---: |
| ox | 3 | ordinary | 6.6916 | 6.5639–6.7024 | 6.8909 |
| ox | 3 | receiver-clone | 8.1621 | 8.1180–8.2446 | 8.3547 |
| ox | 3 | semantic | 6.7739 | 6.7423–7.0940 | 6.9680 |
| stock | 3 | ordinary | 6.5330 | 6.4702–6.5975 | 6.7269 |
| stock | 3 | receiver-clone | 8.1694 | 8.1388–8.1892 | 8.3605 |
| stock | 3 | semantic | 7.0087 | 6.9316–7.1521 | 7.2021 |

Ordinary transfer is faster in this dataset. Receiver clones and SDE reduce the logical materialization model, but do not deliver a wall-time win here. Do not infer isolated compiler gains from these small, shared-host samples.

Client time is spawn-to-terminal-observed. Pair time also includes proxy startup and evidence persistence. Per-process wait4 CPU/RSS and protocol-byte observations are retained in JSON. Proxy CPU may include its reaped native server; do not sum overlapping resource observations or call them simultaneous tree peaks/hard caps.

Application read bytes, peak live descriptors, peak queue depth and separate hash/parse/verify/commit timings were not instrumented by this cohort. These remain unknown, rather than inferred from file sizes or process samples.

All outputs and no-op identities were verified before generated payload cleanup; raw samples and peer proofs remain. Protocol counts exclude launcher control headers and are not physical-network traffic. Logical materialization models are not physical writes. No SDK/photo/pixel/cold-cache/cross-volume/physical-network/scaling claim. Five observations give a descriptive range, not a reliable population-tail guarantee.
