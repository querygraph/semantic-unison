# Bounded self-task footprint observation

`probe.py` compiles an original disposable C program and runs a baseline and a
self-limit observation, sequentially. The only addressed Mach task is
`mach_task_self()`; there is no other PID/task argument, administrator action,
production integration or persistent configuration. Each child can touch at
most32 MiB. The self-limit case requests16 MiB and stops without allocation if
the call rejects. Raw task-info samples are observations, never peaks or an RSS
containment receipt. A rejected request is recorded, not retried without it.

Current host result (2026-10-18): the baseline completed32 MiB of touched memory;
`task_set_phys_footprint_limit` returned8 (`KERN_NO_ACCESS` in the pinned installed
SDK header), and that child exited before the bounded allocation. Both children
returned0 and the containing owner/group closed. This does not prove the reason
for the access refusal, availability on another platform, entitlements that
would enable it, inheritance, a process-tree bound or equivalence of physical
footprint and resident memory.

The production endpoint launcher continues refusing every positive hard RSS
request before exec. This observation supplies no reason to change that policy.
A future supported containment implementation still needs actual over-limit
behavior, native and OCaml/descendant controls, functional execution below the
limit and whole-lifetime settlement. No camera, Adobe, SDK, Photo or production
payload is used.
