# Frozen warm512 observed results

This is a descriptive report of retained samples, not a completed six-part benchmark. No sample was removed, replaced or rerun.

Update wall time in seconds; each configuration uses four512MiB generated files.

| Compiler | Workers | Mode | Measured rows | Median | Min–max | Partition |
| --- | ---: | --- | ---: | ---: | --- | --- |
| stock | 1 | ordinary | 5 | 37.423 | 37.390–37.767 | 0 complete |
| stock | 1 | receiver-clone | 5 | 36.700 | 36.610–36.820 | 0 complete |
| stock | 1 | semantic | 5 | 69.659 | 69.320–70.214 | 0 complete |
| stock | 6 | ordinary | 5 | 37.027 | 36.974–37.249 | 1 complete |
| stock | 6 | receiver-clone | 5 | 36.344 | 36.316–36.413 | 1 complete |
| stock | 6 | semantic | 5 | 34.209 | 34.170–34.793 | 1 complete |
| stock | 8 | ordinary | 5 | 37.028 | 36.986–37.114 | 2 complete |
| stock | 8 | receiver-clone | 5 | 36.299 | 36.255–36.387 | 2 complete |
| stock | 8 | semantic | 5 | 34.232 | 34.171–34.284 | 2 complete |
| ox | 1 | ordinary | 5 | 37.353 | 36.218–39.219 | 3 FAILED/INCOMPLETE |
| ox | 1 | receiver-clone | 4 | 36.980 | 35.437–38.345 | 3 FAILED/INCOMPLETE |
| ox | 1 | semantic | 4 | 71.046 | 70.474–72.021 | 3 FAILED/INCOMPLETE |
| ox | 6 | ordinary | 5 | 36.490 | 36.438–36.613 | 4 complete |
| ox | 6 | receiver-clone | 5 | 35.854 | 35.845–36.523 | 4 complete |
| ox | 6 | semantic | 5 | 35.019 | 34.937–35.041 | 4 complete |
| ox | 8 | ordinary | 5 | 36.346 | 36.278–36.450 | 5 complete |
| ox | 8 | receiver-clone | 5 | 35.664 | 35.586–35.691 | 5 complete |
| ox | 8 | semantic | 5 | 34.684 | 34.635–34.718 | 5 complete |

Limitations:

- Part3 failed after16completedrows/49actualCLI; remaining rows absent, not zero or imputed.
- Part0 static objdump overlap definitely affected zero-based row5 and possibly row4 boundary; impact/carryover unknown. Mandatory e311d5f6 addendum retained.
- Part3 user brew/neomutt make and source review disclosure; part5 bounded source-edit disclosures retained. No absolute quiet or timing-clean cohort claim.
- Four512MiB generated files; warm/uncontrolled caches, loopback protocol on one APFS host. No cold/network/physical IO savings, RSS hard-cap or camera throughput inference.
- Medians use all retained measured update rows, including partial partition rows; warmups retained in original input, not measured statistics.
- Frozen historical source, not current-code performance. Per-process wait4 values are not summed into tree RSS/CPU.

The machine-readable companion pins all six input reports and the mandatory part0 timing addendum. Resource closure is established by the separately retained owner/aggregate acceptance receipts, not by these timing statistics.
