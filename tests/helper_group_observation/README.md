# Retained helper-group observation primitive

The [qualification](qualification.json) records actual Intel macOS observations
with stock/Ox native and bytecode entry points, four private query-failure
controls per compiler, 38 ordinary helper groups per compiler and fresh full
Make/selftests. No SDK, Photo or Lightroom invocation occurred. The new binding
and observation functions are **not activated by production HelperSupervisor**.

```sh
python3 tests/helper_group_observation/run.py \
  --ocamlopt /absolute/compiler/bin/ocamlopt \
  --report /private/tmp/fresh-group-observation.json
```

This compiles original finite fake-child fixtures. It creates and cleans only
its own process groups. Coordinate compiler/core credits before running it.
Native calls and kernel queries are not hard-deadline guarantees; this is not a
fuzz/sanitizer campaign or owner-SIGKILL recovery test.

## Binding and native contracts

`unsn_helper_group_owner_create` preallocates an opaque, nonserializable native
binding. `unsn_helper_spawn_group_owned` uses exactly the default native spawn
engine and attributes, assigning its successful child/group identity before
returning the PID without another ML allocation. It cannot reuse a successfully
bound or retired owner. The existing default entry point is unchanged in ABI and
uses the same original native body. No process creation/credential behavior is
changed to fit a test supervisor.

`unsn_helper_retained_group_others` requires that binding, the same owner process
and its unreaped terminal direct child. It checks `waitid(WNOWAIT)` before and
after a bounded 64-record kernel query. Success counts other members, including
reported zombies. Unsupported non-macOS/contained backends return -1; query,
partial-buffer, malformed-row, duplicate-leader and child-ownership failures
raise instead of certifying zero. No signal, reap, FD acquisition or callback
occurs in this observer. Runtime stays held; stack storage is fixed.

A zero is a past group observation while the child PID was still retained, not a
surviving capability or authorization to signal later. The caller must retire
the binding **before every reap**, retain the actual native child owner through
errors, and prohibit other reapers/group escape. The binding has no resource-
owning finalizer: abandoning it does not clean up a child. Fatal owner loss and
hostile group/credential changes remain outside this contract. Fresh ownership
must never be inferred by replaying an old returned PID.

The first unbound prototype actually failed because `getpgid` rejects this Mac's
zombie leader. The successful design authenticates group assignment at spawn;
it does not convert that failure into an empty result. Apple's
[process-query implementation](https://github.com/apple-oss-distributions/xnu/blob/main/bsd/kern/kern_sysctl.c)
selects process groups and iterates live and zombie process lists. That source
also warns these queries are SPI. Current-host tests, not a promise of future
macOS ABI or general platform support, qualify the implementation; unsupported
or failed queries must remain unknown in any future caller.

Tests cover retained-zero/repeated observations without reaping, actual wait
status, running/unspawned/retired/reused owner refusal, GC movement and rejected
serialization, lost-child refusal after an external reap, and a live descendant
followed by observed absence before the retained leader is reaped. Private C
wrappers inject ENOMEM, bad returned length, wrong live-group identity and
duplicate leaders; each refuses zero and retains the exact child for cleanup.

Production integration, observation on exceptional teardown, diagnostic protocol
binding and the actual SDK-gated receiving pilot remain separate next gates.
