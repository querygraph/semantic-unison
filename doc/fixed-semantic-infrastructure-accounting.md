# Fixed semantic infrastructure accounting

The Runtime resource gate now declares its worker notification pipe and fixed
completion buffer before constructing the pool. `SemanticWorkers.fixed_resources`
is two descriptors and 4096 payload bytes; the pump uses that same buffer-size
constant. The single pipe serves all domains, so this allowance does not multiply
with worker count.

`SemanticAdmission.create_with_baseline` takes total capacities and an immutable
fixed baseline. It subtracts the baseline before checking source headroom or
admitting workspace reservations. The baseline remains reserved for the gate's
lifetime, including the lazy period before infrastructure opens and the period
after known pool shutdown. Transaction retirement and cancellation cannot make
it available to another workspace. Known/uncertain pool ownership continues to
use the separately qualified notification/domain ledgers and failed-initializer
latch; this accounting does not authorize close or replacement.

`SemanticAdmission.create` retains its original zero-baseline semantics.
`usage` remains workspace-only, preserving existing consumers and minimum-budget
settings. `accounting` reports baseline, workspace, workspace peaks, combined
reserved/peak costs and total capacity. These are planning credit quantities;
peaks of payload and descriptor credits are independent maxima, not a sampled
joint process state or an OS high-water mark.

Runtime preferences remain **workspace budgets**. For example,
`semanticdescriptorbudget = 32` allows the existing 24-credit consumer plus the
reserved eight-credit source; its explicitly declared infrastructure raises the
combined planning capacity to 34. Likewise the existing 17 MiB buffer setting
has a separate 4096-byte completion-buffer allowance. A default 512-descriptor
workspace budget therefore declares 514 total accounted descriptors, not a
512-FD whole-process limit. Overflow in the combined capacity refuses before
opening the pipe. `SemanticRuntime.resource_accounting` initializes this gate
without constructing domains or opening descriptors. `-debug semantic` also
prints the fixed allowance when the pool starts.

On this Darwin host, a native `/dev/fd` census excluding its own enumerator
observed three descriptors before pool creation, five with the pool open, and
three after known shutdown, on both compilers with 1, 2 and 4 workers. The initial
observation is preserved separately from the implementation qualification.
Current controls also hold a consumer and source simultaneously at the existing
32-credit workspace minimum, start the pool without charging its allowance
again, retire both workspaces, and verify exact FD restoration on shutdown.
Overflow refuses before acquisition; a private Runtime omitting only the fixed
baseline must fail a designated pre-acquisition assertion. Component tests cover
independent capacity, source headroom, cancellation, invalid baseline inputs and
machine-integer edges. Native publication/handoff and retained-borrower
regressions remain separate evidence.

The allowance covers exactly the notification pipe and buffer payload. Domain
runtime descriptors, transport/logging/UI baseline, mailbox/OCaml object metadata,
heap headers, stacks, transient native probes, legacy transfers and external
helpers are excluded. Their complete accounting and aggregate descendant FD/RSS
containment remain open. No RSS bound follows from adding 4096 payload credits.
No camera/SDK/Photo/EXglobal IO or benchmark claim is involved in these controls.
