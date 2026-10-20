# Opt-in whole-endpoint FD enforcement

The native launcher now has a separate `--unison-endpoint-limits-v1` protocol.
It runs before the Unison endpoint, rather than changing limits in an already
multithreaded Unison process. Build a new private executable with
`tools/helper-limits/build.py`; do not overwrite an installed/pinned limiter or
reuse a consumed execution admission. Existing helper protocol and default
Unison execution are unchanged.

Example (absolute paths and literal arguments, no shell evaluation required):

```text
/absolute/launcher --unison-endpoint-limits-v1 96 0 -- /absolute/unison unison -ui text ...
```

Fields are: descriptor ceiling, requested hard RSS bytes, `--`, absolute
executable, literal argv0, then arguments. Canonical unsigned decimal parsing,
representation/overflow checks and protocol validation apply. Descriptor zero
means no FD limit, but both budgets zero is invalid; positive FD ceilings must
include at least stdin/stdout/stderr. Inherited extra FDs are closed and verified
before lowering both soft and hard `RLIMIT_NOFILE` and reading the limits back.
The fresh process then execs Unison without changing PID or process group.
Because no inherited high FDs survive, a cap of96 bounds that endpoint to at
most96 descriptors, including transport, runtime, legacy paths and semantic
work. Future descendant processes inherit the per-process ceiling. This is not
one96-FD allowance shared across the entire descendant tree. Privileged code
or external administrators are outside the unprivileged hard-cap guarantee.

Use only in a fresh explicitly owned endpoint launch. The launcher deliberately
closes inherited CPU/IO lock copies too; any coordinating owner must keep its
own authoritative descriptions through actual endpoint/descendant settlement.
It is not a replacement for token ownership, per-acquisition reservation,
source/target safety, independent helper closure or the normal transfer lifecycle.
A missing FD needed by a workflow must fail normally; the launcher never retries
without limits or changes a live endpoint's policy. Ordinary invocation remains
available without this optional executable.

## RSS is explicitly unimplemented

The endpoint protocol's second budget denotes **hard RSS**, not address space
or estimated OCaml/SDK allocations. Any positive request exits125 before target
entry with `hard endpoint RSS containment unavailable`. It does not substitute
helper `RLIMIT_AS`, `RLIMIT_RSS`, sampled RSS, callback allocator coverage or
semantic payload credits. Zero explicitly leaves RSS unenforced. No platform's
hard RSS containment is newly qualified by this change. Helper v1 retains its
existing separate address-space field and platform refusal behavior.

A supported future RSS backend still needs whole-lifetime process/tree
containment, descendant/native/OCaml allocation controls, refusal on unavailable
platforms and functional execution under the limit. M6 remains incomplete.

## Current evidence

`tests/qualification/endpoint-fd-enforcement-actual-20261018.json` binds the
actual stock/Ox CLI+selftests behind a native pre-exec oracle. It verifies
soft=hard96, exactly93 additional opens before EMFILE, inability to raise the
hard limit, and then execs the actual Unison binary in the same process. Both
selftests pass; their launcher/endpoint group closes and owner limits remain
unchanged. A positive RSS request never reaches a marker target. This is one
configured per-process FD qualification, not representative corpus throughput,
physical IO, aggregate descendant FD budgeting or RSS enforcement.

The original helper suite also passes with both compilers:13 native supervised
controls each, plus existing malformed requests, inherited high FD cleanup,
close-uncertainty/old-behavior regressions and address-space refusal. All inputs
are generated and all native tools are original fixtures; no SDK, camera,
Lightroom, Photo payload or production publication is invoked.
