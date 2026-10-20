# Many-small shared-host measurements

Warm generated corpus;1,024×32KiB files,512B XMP packets. One warmup and five measured samples per configuration. Both endpoints use the named current compiler. No cache flush or quiet-host guarantee.

| Compiler | Mode | Client median(s) | Observed range(s) | Pair median(s) |
| --- | --- | ---: | ---: | ---: |
| ox | ordinary | 7.0133 | 6.9386–7.1884 | 7.2114 |
| ox | receiver-clone | 8.4809 | 8.4537–8.5945 | 8.6776 |
| ox | semantic | 8.5171 | 8.4979–8.6816 | 8.7105 |
| stock | ordinary | 6.9057 | 6.8861–6.9937 | 7.0941 |
| stock | receiver-clone | 8.5973 | 8.4593–8.6894 | 8.7873 |
| stock | semantic | 8.5739 | 8.5252–8.6896 | 8.7635 |

Ordinary transfer is faster in this dataset. Receiver clones and SDE reduce the logical materialization model, but do not deliver a wall-time win here. Do not infer isolated compiler gains from these small, shared-host samples.

Client time is spawn-to-terminal-observed. Pair time also includes proxy startup and evidence persistence. Per-process wait4 CPU/RSS and protocol-byte observations are retained in JSON. Proxy CPU may include its reaped native server; do not sum overlapping resource observations or call them simultaneous tree peaks/hard caps.

All outputs and no-op identities were verified before generated payload cleanup; raw samples and peer proofs remain. Protocol counts exclude launcher control headers and are not physical-network traffic. Logical materialization models are not physical writes. No SDK/photo/pixel/cold-cache/cross-volume/physical-network/scaling claim. Five observations give a descriptive range, not a reliable population-tail guarantee.
