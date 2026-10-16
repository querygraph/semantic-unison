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
