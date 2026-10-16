# Frozen warm512 observed results

This is a descriptive report of retained samples, not a completed six-part benchmark. No sample was removed, replaced or rerun.

Update wall time in seconds; each configuration uses four512MiB generated files.

| Compiler | Workers | Mode | Measured rows | Median | Min–max | Protocol bytes | Non-inherited byte model | Partition |
| --- | ---: | --- | ---: | ---: | --- | ---: | ---: | --- |
| stock | 1 | ordinary | 5 | 37.423 | 37.390–37.767 | 806012 | 2147483648 | 0 complete |
| stock | 1 | receiver-clone | 5 | 36.700 | 36.610–36.820 | 806013 | 131072 | 0 complete |
| stock | 1 | semantic | 5 | 69.659 | 69.320–70.214 | 51861 | 12288 | 0 complete |
| stock | 6 | ordinary | 5 | 37.027 | 36.974–37.249 | 806012 | 2147483648 | 1 complete |
| stock | 6 | receiver-clone | 5 | 36.344 | 36.316–36.413 | 806013 | 131072 | 1 complete |
| stock | 6 | semantic | 5 | 34.209 | 34.170–34.793 | 51861 | 12288 | 1 complete |
| stock | 8 | ordinary | 5 | 37.028 | 36.986–37.114 | 806012 | 2147483648 | 2 complete |
| stock | 8 | receiver-clone | 5 | 36.299 | 36.255–36.387 | 806013 | 131072 | 2 complete |
| stock | 8 | semantic | 5 | 34.232 | 34.171–34.284 | 51861 | 12288 | 2 complete |
| ox | 1 | ordinary | 5 | 37.353 | 36.218–39.219 | 806012 | 2147483648 | 3 FAILED/INCOMPLETE |
| ox | 1 | receiver-clone | 4 | 36.980 | 35.437–38.345 | 806013 | 131072 | 3 FAILED/INCOMPLETE |
| ox | 1 | semantic | 4 | 71.046 | 70.474–72.021 | 51861 | 12288 | 3 FAILED/INCOMPLETE |
| ox | 6 | ordinary | 5 | 36.490 | 36.438–36.613 | 806012 | 2147483648 | 4 complete |
| ox | 6 | receiver-clone | 5 | 35.854 | 35.845–36.523 | 806013 | 131072 | 4 complete |
| ox | 6 | semantic | 5 | 35.019 | 34.937–35.041 | 51861 | 12288 | 4 complete |
| ox | 8 | ordinary | 5 | 36.346 | 36.278–36.450 | 806012 | 2147483648 | 5 complete |
| ox | 8 | receiver-clone | 5 | 35.664 | 35.586–35.691 | 806013 | 131072 | 5 complete |
| ox | 8 | semantic | 5 | 34.684 | 34.635–34.718 | 51861 | 12288 | 5 complete |

Limitations:

- Part3 failed after16completedrows/49actualCLI; remaining rows absent, not zero or imputed.
- Part0 static objdump overlap definitely affected zero-based row5 and possibly row4 boundary; impact/carryover unknown. Mandatory e311d5f6 addendum retained.
- Part3 user brew/neomutt make and source review disclosure; part5 bounded source-edit disclosures retained. No absolute quiet or timing-clean cohort claim.
- Four512MiB generated files; warm/uncontrolled caches, loopback protocol on one APFS host. No cold/network/physical IO savings, RSS hard-cap or camera throughput inference.
- Protocol counters are forwarded application protocol bytes, not network packets; materialization models are not physical storage writes. Semantic write counts are successful returned logical writes, not attempted or physical amplification.
- Medians use all retained measured update rows, including partial partition rows; warmups retained in original input, not measured statistics.
- Frozen historical source, not current-code performance. Per-process wait4 values are not summed into tree RSS/CPU.

The machine-readable companion pins all six input reports and the mandatory part0 timing addendum. Resource closure is established by the separately retained owner/aggregate acceptance receipts, not by these timing statistics.
