# Checked file component controls

```sh
python3 tests/checked_file/run.py --compiler /usr/local/bin/ocamlopt --receipt /tmp/file-stock.json
python3 tests/checked_file/run.py --compiler ~/.opam/5.2.0+ox/bin/ocamlopt --receipt /tmp/file-ox.json
```

The runner selects exact checked Hash/File templates and their marked native
contracts on OxCaml; stock uses the same ordinary implementation. Four actual
domains open independent synthetic inputs/stages and exercise read/iteration/
hashing/cancellation, borrowed descriptor survival and bounded positional writes.
Independent Python checks full output bytes, unchanged inputs and hashlib hashes.
The POSIX test expects pwrite to preserve cursor, rejects append/read-only flags,
and checks process descriptor parity after domains join. OxCaml additionally
rejects shared reader/writer and mutable chunk-buffer capture. Negative programs
are compiled only and never perform I/O. All staged files live in the retained
private workspace; no Photo/Adobe/Lightroom objects or production originals are
accessed.

C contracts are explicitly manual; kernel descriptor ownership and pending
runtime actions are not proved by the mode annotations. Input/string/FD borrowing
requirements remain. Normal production mode-interface selection is not changed
by this runner. Initial fixture syntax was corrected before execution; an earlier
passing fixture's string-valued cancellation exception was replaced by a dedicated
exception, and final source/receipt pins represent that version.
