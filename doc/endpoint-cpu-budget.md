# Endpoint CPU ceiling for automatic semantic workers

`semanticcpubudget` is an optional endpoint-local ceiling on the shared semantic
worker/helper CPU permit owner. Zero preserves existing behavior. A positive
value caps both automatic (`semanticworkers = 0`) and explicit worker selection:

```text
semanticworkers = 0
semanticcpubudget = 3
```

This selects at most three semantic/helper CPU permits for that endpoint,
using fewer if automatic CPU discovery reports fewer. A same-machine two-endpoint
run can therefore assign three to each endpoint and retain two owner credits
inside the standing Unison8 grant. Setting a ceiling does not acquire those
machine-wide credits; the dispatcher/launching owner still owns the canonical
tokens through actual settlement. Photo8 remains independent.

The effective budget is `min(selected semanticworkers budget, positive ceiling)`.
The worker pool also respects its recommended domain count. Helpers reserve
against the same supervisor, including their declared internal native threads;
a weight greater than the effective ceiling refuses. Existing queue, descriptor,
workspace and filesystem admission remains independent. Changing an already
created supervisor's effective budget requires a process restart. Changing raw
preferences while retaining the same effective budget reuses the existing owner.

This controls covered CPU permits, not kernel threads, process CPU enforcement,
RSS or unrelated ordinary transfers. An external tool with an incorrect thread
declaration remains outside that accounting guarantee. The default is unchanged;
no old peer is sent an unsupported flag, and archives/SDE/RPC encodings do not
change. A new flag should be configured only on endpoints that implement it.

Original fixed controls recompile the actual runtime against compiler-matched
production dependency objects. They cover unchanged defaults, auto/explicit
ceilings, invalid preferences, full-budget permit settlement, over-budget refusal,
worker/helper owner identity, worker-pool shutdown and restart/same-effective
behavior. A private mutation ignoring only the ceiling must fail the exact
budget oracle before starting a pool. The initial fixture failed because it did
not evaluate a failed Lwt promise; that closed attempt is preserved. This is not
SDK execution, physical IO, performance or an aggregate hard-limit qualification.

[Actual qualification](../tests/qualification/endpoint-cpu-budget-actual-20261018.json)
now records both compiler control sets and four full Make/Dune builds/self-tests.
All586recorded input pins match per build; all groups and CPU grants closed.
The separate completed V6 runs remain bound to their immutable predecessor;
this source successor neither relabels nor repeats them.
