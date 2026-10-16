# Final live-file publication native tests

These isolated synthetic tests compile the production `FinalPublication` module
and C translation unit under private syscall wrappers. They use only small
files under `/private/tmp`; they do not invoke Adobe or access Photo catalogs,
previews, production photos, or mounted production caches.

```sh
python3 tests/final_publication/run.py --keep-work --ocamlopt /usr/local/bin/ocamlopt
python3 tests/final_publication/run.py --keep-work --ocamlopt /Users/alexy/.opam/5.2.0+ox/bin/ocamlopt
python3 tests/final_publication/run.py --negative-control --ocamlopt /usr/local/bin/ocamlopt
python3 tests/final_publication/run.py --negative-control --ocamlopt /Users/alexy/.opam/5.2.0+ox/bin/ocamlopt
python3 tests/final_publication/run.py --producer-negative-control --ocamlopt /usr/local/bin/ocamlopt
python3 tests/final_publication/run.py --producer-negative-control --ocamlopt /Users/alexy/.opam/5.2.0+ox/bin/ocamlopt
```

The suite checks absent and expected replacement targets, existing live
hardlinks and symlinks, physical root/directory/parent/name binding, followed
aliases, immutable candidate stat facts, native resource forks and extended
attributes, sibling directory changes, AppleDouble absence policy, namespace
changes, cleanup through captured parents, descriptor ownership and reuse, and
native-success state when pending exceptions or result observations fail.
Actual `._` sidecars select legacy handling before attachment. Operational
sidecar lookup errors are never interpreted as absence.

Quarantine tests distinguish successful native rename followed by injected
unlink failure (the normal candidate name is isolated) from a real
`UF_IMMUTABLE` file, for which APFS forbids both rename and unlink. The latter
reports an explicit error, retains the original candidate, and does not clear
flags. Exclusive collision/replacement tests preserve foreign names. After
publication, neither abort nor quarantine removes a live file.

The negative control removes only the candidate baseline check in the private
copy. It must fail at the assertion that a mutated candidate was published:
an eventual post-rename error is insufficient to protect the old live file.

`producerTest.ml` extends the original 99-case suite with actual retained output
descriptor admission, mutable production and a single fullstat freeze. Same
bytes in a replacement inode are rejected before admission, during production
and after freeze. Planned size/mode/ownership/timestamp/flag/resource-fork/xattr
writes pass before freeze; later writes fail. The producer witness survives
closure and reuse of the caller's original descriptor, and named attachment or
refreezing cannot replace it. Pending exceptions after successful adoption or
freeze preserve native ownership and receipts before runtime reacquisition.

Resume admission opens the held parent's actual normal leaf read-only with
no-follow, nonblocking and close-on-exec flags, before caller hashing. Its
`Admitted_resume` origin is distinct from an actual supplied producer descriptor
and does not certify bytes or new-session creation. A separate matcher binds
prefix-read or append-writer descriptors to that retained object before writes.
Missing or replaced resumes, symlinks, FIFOs, hardlinks, source namespace changes,
volume failures and wrong/reused writer descriptors fail without adopting or
deleting foreign names. Planned AppleDouble family handoff remains before freeze.

The producer negative control reopens the normal name instead of duplicating
the actual output descriptor. The identical-byte replacement control must
detect that false origin immediately. The separate producer receipt preserves
the earlier checkpoint's source pins and records the extended suite's scope;
actual Copy/Files producer handoff requires independent caller evidence.

This is evidence for the native cooperative publication boundary. Caller
RPC/session admission, finalized content/validation binding, backups, archive
advancement, helper settlement, directory transactions, source moves, conflict
retargeting, actual AppleDouble families and other platform implementations
require their own integration evidence. Fresh lookup followed by rename or
unlink is not an atomic inode compare-and-swap against hostile writers. This
does not prove mount incarnation, crash durability or APFS physical write
amplification. Non-macOS availability is false.
