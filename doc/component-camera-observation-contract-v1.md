# Advisory camera component observation contract

This is source preparation, not a payload admission. The manual entrypoint is
`INSPECT_COMPONENTS=1 ... tests/manual.py inspect-file`. Its default strict-profile
mode remains unchanged. An explicitly admitted IO invocation must bind:

- `inspector_contract.mode`: `components`;
- absolute `build_receipt`, its SHA256, and its recorded `binary_sha256`;
- absolute `input` and exact `input_identity` fields dev, inode, mode, nlink,
  uid, size, mtime_ns and ctime_ns;
- the exact runner argv, all dispatcher/helper sources and all26 inspector kernel
  source files through the admission's `execution_source_sha256` map.

The dispatcher checks metadata before acquisition and immediately before launch.
It acquires the existing global IO barrier then Unison00..07. The worker hashes
its pinned binary and validates current kernel sources before launching it. No
build, SDK, renderer, receiving clone, original recopy or source write is part of
this operation. A single component observation still reads the whole input for
its whole-file and component hashes; it is not an IO-saving claim.

After the owned process group is settled, the dispatcher samples the same eight
input fields without opening the payload. Missing, replaced, modified or invalid
input is a functional failure (exit3) recorded in SHARED-CLOSED, after known
process and FD settlement. An lstat failure opens no FD and does not invent
uncertain descriptor ownership. Actual CPU/IO close uncertainty continues through
the existing retained-ownership path. Actual owning-tool terminal must still be
collected separately from worker/group markers.

A fresh immutable request must choose the exact retained Unison-owned clone,
current successful inspector receipt, private absent output directory, deadline,
and declared read/log budgets. It must pin the executable runner, interpreter,
all sources and prior fixture evidence. It needs separate explicit Photo IO
coordination before payload launch. Older consumed camera/SDK grants do not apply.

Current qualification covers ten metadata-only contract controls. It does not
qualify the composed dispatcher path, actual camera classification, semantic
eligibility, decoded pixels, IO savings or receiving authority. Next: disposable
composed dispatcher success/changed-input controls, then freeze the one-input
request. Preserve all unknown/private bytes exactly and report role hashes as
advisory; incomplete MakerNote meaning is not a deployment blocker.
