# Strict native range results

`Fs.copy_file_status` is an additive native API used by production
`Copy.copyFileRange`. The old `Fs.copy_file` and its C implementation retain
their compatibility behavior. `CopyRange.run` also retains its legacy injected
step contract; production uses `run_native` and the checked native decoder.

The strict result describes backend, phase, reported contiguous byte prefix,
mapped Unix error, original native error code, destination effects and decline
scope. Successful generic copying leaves block sharing unreported. A capability
or a filesystem name does not establish sharing, support for another file pair,
or a mount incarnation; no capability cache is introduced.

| Result | Caller behavior |
| --- | --- |
| Progress | Count within the requested step, notify once, continue bounded chunks |
| Scoped decline with no effect or known prefix | Copy only the remaining suffix |
| Native failure | Retain any reported prefix for accounting, fail/discard the candidate |
| Indeterminate effects, contradictory fields, invalid/zero progress | Fail; never retry by copying |

Only specific backend/phase/error combinations can express a decline:
platform absence; native ENOSYS, EXDEV or EOPNOTSUPP; or Windows no-effect
volume/flag/alignment probes. EINVAL, EBADF, ESPIPE, ENOTSOCK and historical
unknown-error conventions cannot authorize fallback. Thrown Unix exceptions
are terminal. Cancellation and progress callbacks remain outside native-error
classification and propagate unchanged.

Requests use at most 10 MiB per step. Reported prefixes advance exact source
offsets and are notified once, including a prefix followed by a terminal error.
The ordinary local-copy fallback now receives `requested - completed`, rather
than requesting the original length again and relying on EOF. It reconciles
the output channel with its FD before suffix copying and flushes buffered data
before final cursor reconciliation. Shifted receiver-basis copying retains its
lease/planner, independent basis and exact requested span.

## Native boundary

The internal eight-field tuple is
`status, completed, backend, phase, Unix.error option, mutation, decline_scope,
native_code:int64`. Rooted parameters stay live; scalar/handle values are copied
before releasing the runtime. Native errno/GetLastError is captured before
cursor checks or reacquisition. Descriptor borrowing requires valid exclusive
lifetimes; the API does not acquire an immutable content snapshot. POSIX
preflight rejects invalid spans, aliased/nonregular descriptors, inaccessible
modes and append output before mutation. Source stability and normal final
fingerprint/publication guards remain necessary.

The macOS backend validates the request/descriptors and returns an explicit
no-effect platform decline: this API supplies no native APFS range sharing.
Whole-file private basis/stage cloning continues to supply APFS reuse; ordinary
buffered suffix copying remains available.

Linux reuses copy_file_range and sendfile, but the latter is attempted only
after verified no-effect ENOSYS/EXDEV/EOPNOTSUPP. EBADF is not hidden by a second
attempt. FreeBSD uses copy_file_range. Solaris retains a native partial-error
prefix and its error rather than converting it into successful completion.
Unreported effects or inconsistent cursors fail the candidate.

The source-implemented Windows path checks volume probes and exact nonzero
cluster alignment before changing sparse state or EOF. Extent length is the
exact request, never rounded up by another cluster. Microsoft's
[extent contract](https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-fsa/4623bf0a-ab5f-4ab6-9c03-b8372c7aa06b)
requires aligned offsets and byte count. Generic writers may also have append
rights: the source checks read/write data rights via synchronous
[NtQueryObject](https://learn.microsoft.com/en-us/windows/win32/api/winternl/nf-winternl-ntqueryobject),
rejects append-only handles, and requires the caller to avoid append-mode
wrappers. Rights alone do not prove wrapper semantics.

Each Windows IOCTL owns one transient manual-reset event and settles reported
pending I/O before releasing stack buffers, closing the event and reacquiring
the runtime. Immediate completion preserves synchronous returned-byte counts.
Successful duplication followed by event/cursor failure retains its completed
prefix but fails with indeterminate effects. Sparse/EOF preparation failures
also remain terminal. Raw Windows DWORD/NTSTATUS bits use Int64 separately from
the mapped Unix error; they are opaque and must not be interpreted by numeric
range. OS waits and cleanup after failed event close are not qualified here.

## Qualification and limits

Both compilers pass sixteen strict typed-result groups, thirteen actual macOS
ABI groups and fourteen complete production-caller groups. Three private
negative controls detect mutation-guard removal, original-length suffix copying
and missing channel reconciliation. Independent byte sentinels, write counts,
FD/channel positions and a following literal establish the selected range
behavior. See [native controls](../tests/native_copy_range/README.md),
[component receipt](../tests/native_copy_range/qualification-20261013.json) and
[integration receipt](../tests/qualification/native-copy-range-integration-20261013.json).

Linux/FreeBSD/Solaris/Windows branches are source-reviewed, with no new native
runtime qualification or representative filesystem performance. Windows mode,
pending-I/O/error/cleanup matrices, native sharing and future ZFS/ReFS adapters
need their own platform evidence. No physical APFS savings, whole-process
FD/RSS ceiling, filesystem deadlines or crash durability is established.
Tests use disposable synthetic files and Adobe-free helpers; no Photo or
Lightroom/cache/volume operation is involved.
