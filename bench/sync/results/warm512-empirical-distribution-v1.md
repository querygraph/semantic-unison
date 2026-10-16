# Frozen warm512 empirical distributions

Historical observations only. All measured values are retained; there are no new executions, exclusions or replacements.

Each list is sorted update seconds; bracketed numbers are zero-based rows in the pinned raw partition file. Four or five values cannot establish a population tail.

| Compiler | Workers | Mode | Retained measured values (seconds [row]) | Partition |
| --- | ---: | --- | --- | --- |
| stock | 1 | ordinary | 37.389574 [15], 37.399166 [3], 37.422669 [14], 37.519459 [9], 37.767426 [8] | 0 complete |
| stock | 1 | receiver-clone | 36.609746 [16], 36.623862 [7], 36.699721 [4], 36.789700 [10], 36.819855 [13] | 0 complete |
| stock | 1 | semantic | 69.319973 [17], 69.570086 [5], 69.658790 [6], 69.895453 [12], 70.214309 [11] | 0 complete |
| stock | 6 | ordinary | 36.974262 [3], 36.994778 [9], 37.027367 [15], 37.044302 [14], 37.249223 [8] | 1 complete |
| stock | 6 | receiver-clone | 36.315989 [13], 36.332497 [16], 36.344291 [4], 36.376430 [10], 36.412840 [7] | 1 complete |
| stock | 6 | semantic | 34.169850 [11], 34.183235 [5], 34.208992 [6], 34.271795 [12], 34.792508 [17] | 1 complete |
| stock | 8 | ordinary | 36.986188 [15], 37.027338 [14], 37.028454 [8], 37.081624 [3], 37.113856 [9] | 2 complete |
| stock | 8 | receiver-clone | 36.254562 [16], 36.293481 [7], 36.298736 [10], 36.314703 [13], 36.386514 [4] | 2 complete |
| stock | 8 | semantic | 34.171085 [5], 34.209208 [11], 34.231766 [12], 34.255088 [6], 34.284338 [17] | 2 complete |
| ox | 1 | ordinary | 36.217968 [3], 37.328110 [9], 37.352867 [14], 37.395861 [8], 39.219091 [15] | 3 FAILED/PARTIAL |
| ox | 1 | receiver-clone | 35.437171 [4], 36.893967 [10], 37.066169 [13], 38.344712 [7] | 3 FAILED/PARTIAL |
| ox | 1 | semantic | 70.473914 [5], 71.015801 [12], 71.075775 [11], 72.020588 [6] | 3 FAILED/PARTIAL |
| ox | 6 | ordinary | 36.437759 [14], 36.461119 [8], 36.489635 [9], 36.544132 [15], 36.612591 [3] | 4 complete |
| ox | 6 | receiver-clone | 35.844528 [4], 35.853555 [10], 35.853919 [7], 35.951659 [16], 36.522743 [13] | 4 complete |
| ox | 6 | semantic | 34.936953 [11], 34.975004 [6], 35.018746 [12], 35.021455 [17], 35.041281 [5] | 4 complete |
| ox | 8 | ordinary | 36.278159 [8], 36.338985 [9], 36.346190 [15], 36.377042 [14], 36.450079 [3] | 5 complete |
| ox | 8 | receiver-clone | 35.586432 [16], 35.657330 [7], 35.663625 [13], 35.683557 [4], 35.690981 [10] | 5 complete |
| ox | 8 | semantic | 34.634873 [17], 34.645381 [5], 34.683983 [11], 34.688312 [6], 34.717934 [12] | 5 complete |

Interpretation:

- Each point is one observed measured update and its zero-based source row; warmups remain in raw input.
- Only four or five measured values per configuration. Empirical ranks are not population-tail estimates or confidence bounds.
- Observed maximum is the slowest retained sample, not a predicted worst case. No interpolated/extrapolated p95 or p99.
- Failed part3 is partial and all observed values remain. No replacement/exclusion or complete-six-part claim.

Timing and measurement limitations:

- Part3 failed after16completedrows/49actualCLI; remaining rows absent, not zero or imputed.
- Part0 static objdump overlap definitely affected zero-based row5 and possibly row4 boundary; impact/carryover unknown. Mandatory e311d5f6 addendum retained.
- Part3 user brew/neomutt make and source review disclosure; part5 bounded source-edit disclosures retained. No absolute quiet or timing-clean cohort claim.
- Four512MiB generated files; warm/uncontrolled caches, loopback protocol on one APFS host. No cold/network/physical IO savings, RSS hard-cap or camera throughput inference.
- Protocol counters are forwarded application protocol bytes, not network packets; materialization models are not physical storage writes. Semantic write counts are successful returned logical writes, not attempted or physical amplification.
- Medians use all retained measured update rows, including partial partition rows; warmups retained in original input, not measured statistics.
- Frozen historical source, not current-code performance. Per-process wait4 values are not summed into tree RSS/CPU.
