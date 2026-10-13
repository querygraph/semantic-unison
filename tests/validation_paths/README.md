# Synthetic receiving-path validation qualification

This suite launches actual Unison CLI client/server processes from an existing
private build. The server runs through a local exec transport; no SSH server or
Adobe installation is involved. Every input, helper, profile, staging file and
archive lives under one disposable `/private/tmp/unison-validation-paths-*`
directory. The inputs intentionally are synthetic bytes with a `.dng` suffix,
not photographic files or claims of a valid RAW format.

Run a compiler-matched snapshot built with `tests/build_snapshot.py`:

```sh
python3 tests/validation_paths/run.py --unison /absolute/build/src/unison \
  --keep-work --receipt /private/tmp/validation-paths-result.json
```

With the filesystem execution-admission implementation, add `--volume-jobs 1`.
All pre/post hashing and helper execution must still finish at a one-job limit;
wrapping an entire validation inside that same gate would deadlock nested hash
work. The limit applies independently to each endpoint.

The 21 cases observe publication and exact bytes rather than calling the core
hook directly:

- A synthetic external producer durably writes a complete or partial stage,
  then waits. The test kills only its own producer PID and Unison process
  group. A fresh run reaches the real completed-staging or verified-prefix
  branch, confirmed by its diagnostic and the same device/inode. The partial
  prefix exceeds the existing 1 MiB threshold. Both branches invoke the
  receiver's validator on the full source bytes. An exit-zero `errors 1`
  receipt rejects publication, removes the rejected stage, and requires a
  fresh validated retry.
- A real configured external copy command produces the candidate. Its exact
  output pathname is the validator's candidate. `require`, `warn`, and `off`
  have their documented behavior, while helper mutation rejects even under
  `warn`. No unfinished or rejected stage becomes the live file.
- Unison's fingerprint hint backend copies a retained exact donor to a new
  name, confirmed by `Shortcut: copied ... from local file ...`. The donor
  stays unchanged; pass, require rejection/retry and warning all invoke the
  receiving gate. This deliberately qualifies **moved-file content reuse**,
  not a rename-only move (which is outside received validation scope).
- A configured merge command creates one deterministic exact result from
  two actual changed inputs. Each receiving endpoint uses its own pinned
  driver. First-receiver rejection preserves both old inputs and prevents the
  second invocation. Second-receiver rejection, including a mismatched
  receipt, preserves that receiver's old input after the first commit. The
  next run still reports a merge conflict, recaptures the actual partially
  committed inputs, regenerates the result and validates both fresh receivers.
  This is the existing configured Unison merge lifecycle, not an XMP semantic
  auto-merge or a distributed atomic commit.
- A hanging synthetic child times out under `require` and `warn`. Its PID is
  gone before the CLI returns; each policy preserves or publishes the live
  bytes as selected, then a fresh validated update makes progress. An actual
  SIGINT during an active client-side reverse-receive helper rejects under
  both policies, reaps the child, preserves old receiver bytes, discards the
  cancelled stage and permits a fresh validated retry. This does not qualify
  forwarding a client-only SIGINT to a remote receiving server.
- Six directory candidates use delayed helpers and atomic `O_APPEND`
  start/end records. At two CPU permits and one filesystem execution credit,
  observed helper overlap must be exactly one. This detects a bypassed helper
  execution wrapper even when the CLI still reports the requested preference.
  Client CLI and server endpoint profile both set the requested local limit;
  each receiving endpoint's actual runtime diagnostic is checked.

The driver checks the exact v1 argv allowlist, expected full hash/size, one
thread, private staging pathname and endpoint-local build identity. Before
returning it logs the live destination bytes so the test can prove that
invocation preceded publication. Every successful/recovered case ends with a
no-op sync: unchanged file bytes/inodes and no extra helper calls.

The JSON result names the binary/test hashes, per-case results and retained
work directory. Logs and endpoint driver records remain there with
`--keep-work`. Process crash fixtures do not establish crash-durable
publication. These tests qualify core invocation/publication contracts only;
real Adobe structure/decode/digest behavior and a real-corpus matrix require
separately authorized SDK qualification. They do not read or write Photo
catalogs, previews, production photos, or mounted photo volumes.
