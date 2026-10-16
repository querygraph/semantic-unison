# Concurrent publication accounting scope

The actual stock/Ox controls hold two declared2GiB validator envelopes and one
source lease at6GiB/64 descriptor credits. These are admission credits, not
allocated SDK workspaces or physical/RSS caps. No helper is invoked.

The gate retains future-source headroom even while a source is active. Four
transaction slots admit all three source/consumer arrival orders; three slots
queue the second consumer when a source is already active. This is an explicit
progress reservation, not a leaked debit. Cancellation removes the waiter and
retiring all owners leaves every ledger at zero.

The frozen synthetic receiving V2 request remains unchanged. Its three-slot
configuration is not evidence of source-first two-validator overlap. Its actual
receiving result must report observed overlap, including false. A future
bidirectional semantic/SDK overlap plan must account for the extra reserved
source slot and its corresponding memory/descriptor headroom.

[Actual order controls](../qualification/concurrent-budget-order-actual-20261016.json)
retain source pins and genuine outer owner/group/token closure on both compilers.
