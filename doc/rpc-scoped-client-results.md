# Scoped decoded client results

`Remote.registerBoundedServerCmdWithResultScope` adds a client continuation to
bounded RPC registration. The server and wire codecs are unchanged. The caller
passes its actual asynchronous consumer of the decoded result, instead of
receiving an unowned decoded value from the RPC API.

An independent endpoint-local lane reserves a slot before decoding, then admits
selected builtin allocation and collection charges incrementally before their
allocations. Defaults are 256 MiB, 1,048,576 elements and 256 owners; owner count
has a maximum of 65,536. Admission refuses without waiting. Per-command bounded
codec limits also apply. Request and result allowances are independent.

The explicit decoded value root and charges survive until the returned consumer
promise actually settles. Connection close does not revoke that ownership.
Known decode/consumer failure releases the partial debit. Recognized ownership
uncertainty, including classifier failure, retains the value root and debit
rather than translating uncertainty into ordinary cleanup. Raw reply bytes also
remain owned through the consumer in this scoped path.

The consumer must not return the decoded value, store it globally, or launch
independent work retaining it without another owned lifetime. Parsing/copying
into an observation or plan creates separate objects; their budgets and lifetime
remain the responsibility of the existing semantic transaction/report model.
User conversion allocations, general result escape tracking, legacy client APIs,
custom stream workspaces, retained stream errors, outbound bytes and full heap/RSS
are not covered by this lane.

The four semantic bounded commands now use this API: plan application retains
its encoded reply through asynchronous materialization/publication, while
inspection/component replies retain their encoded string through validation and
conversion. This does not newly qualify the converted report/plan lifetime.

Directed stock/Ox controls passed for actual pipe reply handoff, paused consumer,
disconnect, slot/byte/element refusal, partial-debit cleanup, endpoint policy and
uncertain value retention. Five deliberate mutants must fail at their designated
witnesses. All four stock/Ox Make/Dune builds and selftests passed, with all580 recorded
inputs/compiler/executable hashes matching. The complete grouped regression union
passed24 designated negatives/compiler. [Actual evidence](../tests/qualification/rpc-scoped-client-results-actual-20261018.json)
preserves earlier focused runs and the fixture-order failure/correction. No new transport, SDK,
Photo payload, production or full-SOL acceptance follows from these controls.
