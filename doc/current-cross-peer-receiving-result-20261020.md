# Stock↔OxCaml cross-compiler peer: actual result

Builds of the same production source (`8581f357`) interoperate in both
directions over Unison's RPC, which uses OCaml `Marshal`. Both runs completed
on 2026-10-20:

- stock client with an OxCaml server: `current-cross-peer-receiving-stock-20261019-03`;
- OxCaml client with a stock server: `current-cross-peer-receiving-ox-20261019-03`.

Each made 12 calls and 2 fake validator calls. The owner audited every call
while it still held EXglobal IO and CPU00..07, and an independent post-closure
replay (CPU04) matched both owner audits.
[Receipt](../tests/qualification/current-cross-peer-receiving-actual-20261020.json).

| Case | Shown in both directions |
| --- | --- |
| seed-update | A client file and a server file seed across, a one-byte change in a 300 KB file arrives byte-exact by delta, and the third call is "Nothing to do" |
| reverse-deletion | A deletion made on the server side propagates to the client; an anchor file survives |
| conflict-skip | Concurrent edits are skipped, with exit 1 and the exact `(0 items transferred, 1 skipped, 0 failed)` line, and both replicas keep their own bytes |
| properties | With `-xattrs -acl`, a client xattr and ACL reach the server, then the server's xattr change and ACL clearing reach the client |
| dng-receive | A DNG update passes the server's receive gate in one direction and the client's in the other; each validator call names the exact candidate and previous bytes |

The failed predecessor `stock-02` is preserved with `FAILED-RECOVERY-CLOSED.json`.
The client's loopback launcher was told to expect the client binary and refused
the peer server command, a harness error. It was fixed in `c3e011c1` and covered
by a peered invoke test. The plans name builds of one production commit; this
says nothing about peers from different commits or about real SSH.
