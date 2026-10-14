# Receiving validation tree limits

Optional endpoint-local preferences bound the structure of each receiving
validation manifest:

```text
validationtreeentries = 100000
validationtreepathbytes = 16777216
```

Each defaults to zero, preserving unlimited legacy enumeration. Negative values
reject when receiving validation runs. Limits apply separately to the before and
after snapshots of a finalized candidate, including its root, directories,
symlinks, hidden entries, auxiliary names and temporary-looking names. The entry
counter includes discovered but not yet inspected children. Path accounting adds
each relative path's bytes, including its parent prefix and separator. The root
uses its actual private staging name, so changing that name changes the count.

The directory reader checks global cancellation before each read. It charges a
discovered child before appending its name or constructing its Path object.
Limit/cancellation failure closes the native directory handle. A limit error is
an operational receiving error under both `require` and `warn`; no helper runs
if the initial snapshot fails. If a helper adds a hidden entry that exceeds the
limit in the final snapshot, ordinary failure handling rejects publication and
discards private staging. Live destinations and source inputs remain untouched.

These are structural limits, not heap/RSS limits or complete directory memory
admission. Properties, symlink target strings, allocator overhead, source-side
archives and SDK heaps are not path bytes. The manifest still occupies memory
until its validators settle; two manifests may coexist during final comparison.
Global manifest resource reservations and pre-creation directory admission
remain separate work. Existing shared CPU/I/O/helper admission remains in force.
These limit settings and implementation code are not accepted from a peer; the receiving
endpoint's local preferences are authoritative.

[Qualification](../tests/validation_tree_limits/qualification.json) records
stock/Ox actual-object arithmetic checks, seven actual receiving cases and a
controlled native-directory cancellation probe. A private negative removes only
the per-read cancellation check and fails the same designated oracle. The
probe does not establish interruptible filesystem syscalls or a wall-clock
cancellation deadline. All fixtures are private synthetic data; no Photo,
Adobe runtime or Lightroom operation is involved.
