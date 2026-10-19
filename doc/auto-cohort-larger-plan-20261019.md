# Larger generated workload successor

The completed ten 32 MiB cohorts and their exact declarations remain preserved.
The successor adds three explicit workload pairs: 128 MiB × 4 files, 512 MiB × 4,
and 2048 MiB × 2. Each has stock/Ox × 1/2/4/8/auto, three transfer modes, one
warmup and five measured rows per mode. Total planned: 30 cohorts, 540 rows,
1620 CLI calls. None is executed by freezing the plans.

A v1 nested cohort remains exactly the original32×8 contract. A v2 nested
cohort carries typed dimensions from the three-pair allowlist. The existing
plan/2 envelope authenticates its precise nested declaration. Limits and full
launch arguments derive from that declaration. Dimensions, limits or argv
cannot be swapped independently; mixed sizes cannot form one completed report.
Each report contains one workload; original raw samples and failed prefixes stay.

Larger owners observe up to7200s and each CLI up to180s. These are observation
intervals, not a global hard deadline: unknown owner/child/group/descriptor state
retains ownership beyond the interval. No automatic retry, replacement or broad
aggregate kill. The declared4TiB logical IO allowance per cohort is conservative,
uninstrumented planning, not a physical read/write cap. Each workload corpus is
at most4GiB and the runner verifies/removes its disposable fixture after each
row; filesystem/VM/OS overhead is not hard-capped by that model. Metadata df
observed529GiB free before preparation, not reserved space or a future guarantee.

Endpoint1/2 cohorts fit standing Unison8; endpoint4/8/auto need separately
coordinated temporary18 and exact fresh admissions. The earlier six-cohort18
coordination is consumed and cannot authorize these. IO uses the same existing
EXglobal pool. Each request is one-use with a unique workspace, exact current
source/build/tool pins and independently collected actual parent terminal.

Original disposable controls passed46tests under canonicalUnison4; their one
Python child was reaped0 with empty group and all outer tokens closed. Saved
legacy revalidation also accepted all180 original rows without runtime work.
These controls do not qualify actual larger workload execution or CPU hard caps.
No production source or compiled binary changed in this harness successor.

[Prepared series](auto-cohort-larger-series-prepared-20261019.json) ·
[Controls](../tests/qualification/auto-cohort-larger-controls-actual-20261019.json)

This covers the larger fixed-layout generated loopback matrix when actually
executed. Other prescribed workload shapes, original/upstream comparisons and
available storage/network/platform evidence still require the final SOL audit.
