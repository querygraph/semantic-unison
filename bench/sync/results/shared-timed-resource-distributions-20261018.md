# Saved repeated-matrix resource distributions

This supplement interprets the existing consumed 32 MiB cohort, not the latest
production candidate. No synchronization, camera read or benchmark was repeated.
The original 108 rows and all five measured samples per configuration remain;
18 warmups are excluded only from distributions.

Directional forwarded protocol bytes, delivered primary-reader bytes, returned
semantic write bytes, inherited clone extents, modeled output extents and
unknown application-read/physical-write fields now have separate distributions.
No transport/CPU/phase sums or model-to-syscall conversion is performed.

Stock one-worker measured medians:

| Mode | Client→server B | Server→client B | Primary reads B | Returned semantic writes B | Non-inherited extent model B | Physical writes |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Ordinary | 27,917 | 76,566 | unknown | unknown | 67,108,864 | unknown |
| Receiver clone | 27,918 | 76,566 | unknown | unknown | 16,384 | unknown |
| Semantic | 27,977 | 3,077 | 201,327,048 | 6,144 | 6,144 | unknown |

Returned writes and modeled extents have different scopes. The model cannot
prove physical APFS allocation or storage traffic. Ordinary sync already sends
deltas; destination cloning does not imply equivalent network savings. Earlier
wall distributions show semantic updates slower on this warm generated dataset,
so no general speedup follows from its smaller returned write count.

[All 18 distributions](shared-timed-resource-distributions-20261018.json) include
stock/Ox workers1/2/3. [Actual metadata controls](../../../tests/qualification/timed-resource-distributions-actual-20261018.json)
passed four directed controls, source-bound saved Darwin interpretation and both
CPU4/group closures. Original recovery/exit137 remains historical; this report
does not turn it into normal owner exit or original-worker wait4. No quiet-host,
current-source timing, full 1/2/4/8/auto coverage, hard RSS or full SOL claim.
