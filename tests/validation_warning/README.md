These controls invoke the actual `DngCandidateValidation.select` handler with
logging disabled and a captured `Util.warnPrinter`. They use synthetic bytes
and an independently compiled protocol fixture. No Adobe SDK, codec, photograph,
catalog, preview, live volume or native UI is used.

The runner requires a complete compiler-matched isolated Make snapshot. It
checks snapshot/workspace linked-source equality, records source/native-object
pins, and recompiles the privately observed worker plus every dependent through
the DNG companion. The actual legacy Lwt, Runtime, CPU/I/O/resource admission,
stable hash workers and supervised child lifecycle remain in use.

Private observations bracket actual worker dispatch and record notification-pump
rearming. After the final tool hash, the fixture launches a real sibling hash.
The warning printer models remote synchronous forwarding by running the owner
loop until that sibling settles. Delivery must occur outside dispatch, after
the pump rearms, while the candidate's resource workspace remains retained.
The assertions do not substitute a fabricated worker response or manually pump
the notification channel. The protocol child deliberately returns SDK-style
`errors 1` with exit zero; it does not claim image validation.

Controls cover exactly one visible warning, ordinary validation success,
require rejection, off/no helper, candidate inspection EIO, helper mutation,
active-child cancellation, cancellation before delivery, cancellation/global
abort during delivery, and a throwing warning printer. All actual helpers must
be independently observed reaped before the companion returns, and all worker,
helper, CPU/I/O/resource ledgers settle afterward.

The parent negative restores only the exact companion source from commit
`31980e3d286f5b7a408613faf7a983dc37d1f017`. It is a current dependency graph
with one parent participant, not a full parent binary. A second private negative
replaces only the warning's yielded promise with an already-resolved promise.
Both retain identical worker observations and must fail distinct exact oracles.

Separate controls run the complete supplied CLI through its actual local exec
client/server transport. A server-side synthetic receiving error under `warn`
must reach the client's warning output exactly once with `-silent -log=false`,
then publish exact bytes. Require rejects and off runs without a helper. These
controls qualify remote warning forwarding and receiving behavior, not SSH
networking, Cocoa/GTK visibility or a distributed atomic commit.

Run stock and OxCaml sequentially after the root-owned source freeze/build gate:

```sh
python3 tests/validation_warning/run.py --build /private/path/complete-snapshot \
  --ocamlopt /absolute/compiler/bin/ocamlopt \
  --freeze /private/path/SOURCE-FREEZE.json --receipt /private/path/warnings.json
```

Artifacts always remain in the private temporary directory. Receipts include
failed trials, exact compiler/compile/link/test commands, object and binary pins,
original/private source pins, log pins, and precise negative provenance.
`--fixed-only`, `--negative-only`, and `--skip-cli` permit focused reruns.
Estimated workspace credits are temporal ownership checks, not an RSS/FD cap.
The separate `mac_route.py` source-extraction controls establish a narrow handler
route; they do not execute native Cocoa UI or promise persistent visibility.
