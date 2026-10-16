# Bounded receiving-helper live spans

`DngCandidateValidation` enables a constant-size collector only as an observer
when `-debug validation-live` is selected. The collector retains first/last
nonterminal samples, child PID, count and a validity bit, not a sample history.
Count saturates at65536 and overflow invalidates evidence. Invalid/reversed
clock values or a PID change also invalidate it. After supervised execution
settles, one diagnostic line binds the summary to owner PID, returned child PID,
candidate SHA/size and `monotonic-seconds-v0` clock semantics.

A single sample or a valid summary does not prove overlap. Consumers need at
least two samples per helper and positive intersection of conservative live
spans from the same retained endpoint/process clock domain. First/last samples
bound known nonterminal lifetime; terminal-observation latency must not enlarge
that span. PID reuse, cross-host clocks and mixed invocations must be refused.
This does not establish CPU execution, SDK decode overlap, speedup or settlement.
Existing CLI/helper/group/pump/FD proofs remain independently mandatory.

`run.py --compiler /absolute/ocamlopt --report /fresh/result.json` compiles the
exact production collector prefix on stock/Ox and tests bounds, PID/time/child
binding and invalid summaries. It does not run the receiving companion. Full
CLI builds check integration separately; actual trace emission/parsing and
fake-helper receiving controls precede any real SDK concurrency request.

The [strict record parser controls](../qualification/validation-live-record-controls-actual-20261016.json)
add11 finite groups for malformed/excessive records, typed PID/digest/size/endpoint
binding, invalid/insufficient spans, exponent limits and conservative conversion
to nanosecond bounds. `live_records.bound` contracts both ends by representation
margin and inward integer rounding. It never proves settlement or SDK activity.
Synthetic protocol records do not establish actual receiving emission.

[Actual companion controls](../qualification/validation-live-companion-actual-20261016.json)
now link current compiler-matched production objects and exercise four cases
per compiler: passing synthetic receipt, exit-zero/errors1 rejection, tracing
disabled, and validation off. The strict parser binds emitted live spans and
group observations to the actual component/helper PIDs and candidate SHA/size.
All component exits, helper direct reaps, group0 observations and outer CPU
closures pass. This is component emission, not full receiving sync or SDK concurrency.
The runner copies its ML control into its private workspace before compiling.

The [parallel companion successor](../qualification/validation-live-parallel-companion-actual-20261016.json)
adds a fifth case: two distinct tiny candidates invoke synthetic validators under
one two-permit supervisor. Each emits its own PID/digest/size-bound live and group
records, and contracted known-nonterminal spans overlap on stock/Ox. All direct
helpers are reaped and group/permit counters close. The four prior cases remain
passing. This is not full CLI receiving, SDK concurrency or throughput evidence.
