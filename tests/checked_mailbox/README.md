# Bounded checked mailbox tests

```sh
python3 tests/checked_mailbox/run.py --compiler /usr/local/bin/ocamlopt --receipt /tmp/mailbox-stock.json
python3 tests/checked_mailbox/run.py --compiler ~/.opam/5.2.0+ox/bin/ocamlopt --receipt /tmp/mailbox-ox.json
```

Both compile the unchanged src/semanticMailbox.ml. OxCaml uses the tracked
mode-checked interface template; the runner verifies it differs from the stock
interface only in its portable exports/type contract. Stock substitutes ordinary
Domain.spawn in the test, while OxCaml actually type-checks Safe.spawn. Neither
build suppresses alerts or uses unsafe mode casts.

Runtime cases cover capacity1..65536 admission bounds, full/empty distinctions,
FIFO through front/back reversal, idempotent close, rejection after close,
drain-after-close, producer/close racing, and six2000-message concurrent batches.
Messages carry immutable string/ID/descriptor fields and a cancellation atom.
Outputs must contain each ID exactly once with the expected checksum/cancelled
state and all queues drained. Two OxCaml negative controls reject access to a
shared reference or bytes payload. These descriptor values are not opened,
read, written or closed by the test; no kernel ownership proof is claimed.

The retained qualification is component-only; production workers do not yet
use this mailbox or its checked interface. CAS retry scheduling is not a worker
notification strategy, machine-wide resource bound, or performance benchmark.
Initial compiler inference failures and earlier positive runs are retained in
private work trees; final receipts pin the exact current sources/interfaces.
