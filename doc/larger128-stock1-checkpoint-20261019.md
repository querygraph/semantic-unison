# First 128 MiB cohort checkpoint

Stock OCaml / one worker / four128MiB generated files passed18rows54CLI. Actual owning session52223 returned3c264e/exit0/no session; worker97794 was reaped0 with other group members absent, CPU8/EXglobal closed and source pins unchanged. No SDK or Photo access.

| Mode | Median update s | Measured rows |
| --- | ---: | ---: |
| ordinary | 11.267 | 5 |
| receiver-clone | 9.801 | 5 |
| semantic | 18.824 | 5 |

The final RESULT file timestamp was653.10seconds after parentSTART; the sum of54monotonic CLI outcome walls was425.48seconds. Neither is a complete hardwall/whole-application IO measurement. The later terminal transcription was706.10seconds afterSTART and includes polling/sealing latency. About11minutes is an appropriate observed-duration description.

The corpus doubles the earlier32MiB×8 corpus but halves the number of files; the approximately2.09 semantic-update ratio is descriptive and does not isolate one causal factor. PhotoCPU8 source preparation and uncontrolled OS activity were allowed. All five measured samples stay; no outlier exclusion or replacement.

A simple byte-scaled full30cohort projection is roughly23hours, with preliminary18–30hour planning uncertainty. This is not a runtime guarantee or a request for continuous quiet ownership. The empirical checkpoint has been reached; further payload starts await the scheduling review already raised by Photo. No new18ACTIVE grant exists. Independent source/design work continues.

The selected semantic path returned12,288logical write bytes and modeled the same
non-inherited output extents; the ordinary extent model is536,870,912bytes and
receiver-clone model65,536bytes. These are different accounting quantities,
not whole-application or physical writes. Selected primary-reader bytes were
1,610,613,648; total application reads remain unknown. Server→client protocol
median was299,245bytes ordinary/receiver-clone versus4,802semantic; this is one
direction, not total network traffic, and generated compressibility matters.
Semantic mode did perform the selected optimization despite slower one-worker
wall time; no elapsed-time win is claimed.

[Saved observations](larger128-stock1-saved-report-20261019.json) are INCOMPLETE_MATRIX: only1of10cohorts at this size, not completion of the30cohort series. [Actual terminal and closure](../tests/qualification/larger128-stock1-actual-20261019.json).
