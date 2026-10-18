# Pending RPC waiter admission

`rpcpendingreplyslots` is an endpoint-local positive limit (default 256, maximum
65536). The owner loop refuses without waiting before marshaling another request
when full, then checks again immediately before adding its waiter. A duplicate
message ID is rejected without replacing the original promise or reply limit.

Response handoff, connection failure and known request failure remove the entry
through the existing settlement paths. A handed-off raw reply can remain owned
independently after the pending entry is removed. The limit does not account for
returned client-value lifetime, outgoing buffers, retained error values or RSS.
Those remain separate resource requirements.

Directed controls cover full-registry preflight, insertion, duplicate preservation,
disconnect settlement, reply/body lifetime separation and endpoint preference
isolation. Three deliberate mutations must fail at designated witnesses. Stock and Ox Make/Dune builds and selftests passed with all recorded source,
compiler and executable hashes verified. The grouped suite covers19 designated
negative participants per compiler. [Actual evidence](../tests/qualification/rpc-pending-reply-slots-actual-20261018.json)
preserves fixture failures and the incomplete60s Ox attempt; no transport, SDK or
Photo payload was used.
