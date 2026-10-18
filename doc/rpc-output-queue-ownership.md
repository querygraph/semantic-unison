# Selected output queue ownership

Normal/idle dump payloads share endpoint-local `rpcoutputbudget` (512MiB),
`rpcoutputparts` (65,536 slice elements) and `rpcoutputslots` (256 owners).
Urgent dumps have independent `rpcurgentoutputbytes` (65,536 bytes),
`rpcurgentoutputparts` (2,048) and `rpcurgentoutputslots` (256). Slot maxima are
65,536. An empty message still needs an owner; empty slices count as elements.

Measurement validates ranges and selected logical bytes/parts without waiting.
A final authoritative admission rechecks the current policy/counters after all
owner/callback preparation. No allocation/yield separates a successful final
check from counter installation. A lost admission race does not poison existing
queued work. A scheduler/setup failure after reservation fails queued work rather
than leaving an unavailable queue with no active action.

Queued callbacks capture an owner, not the original payload list. The list is
cleared and credits released after that owner's actual consumer settles, even
when an immediate `performOutput` return promise is still draining an unrelated
later action. Removed queued entries release on their known failure; an active
consumer cannot be released by queue/connection failure before it settles.
Recognized uncertainty, including a throwing classifier, retains the exact
payload root and selected charges in prepared state. Producers must await their
returned send operation before reusing mutable backing buffers.

These budgets cover dump payload logical bytes, element count and owner count.
They do not cover allocation before serialization/queuing, caller aliases,
aliased Bigarray backing capacity, connection buffers, generic scheduler/token
baselines, every heap object or RSS. Separate urgent capacity prevents bulk
admission from consuming it; it does not promise progress through a blocked
socket or permit interleaving bytes inside an atomic protocol frame.

Original stock/Ox controls exercise normal/idle sharing, urgent independence,
queued drop versus active borrower, exact bytes/empty-element costs, a real
nested owner between measurement and reservation, actual own-action settlement
versus unrelated draining, endpoint isolation and typed/classifier uncertainty.
A non-inlined returning fixture factory prevents the caller's compiler-created
local roots from being confused with a queue-retained payload; the weak-root
assertion remains enabled on both compilers. Nine counterfactuals remove the
specified policy/lifetime protections; whole-policy omissions remove both
measurement and authoritative guards, while recheck-only has its own race case.
No synchronization/SDK/Photo payload run or overall goal completion is implied.
All four current stock/Ox Make/Dune builds and selftests passed; all583 recorded
inputs/compiler/executable hashes match. The final grouped suite passed48
designated negatives per compiler. [Actual evidence](../tests/qualification/rpc-output-queue-owners-actual-20261018.json)
preserves earlier syntax/liveness fixture failures, the non-inline factory
correction, dual-guard policy counterexamples and all final closures.
