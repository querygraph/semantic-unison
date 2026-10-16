# Exact DNG reconciliation plan controls

```sh
python3 tests/dng_reconcile/run.py --compiler /usr/local/bin/ocamlopt --receipt /tmp/dng-reconcile-stock.json
python3 tests/dng_reconcile/run.py --compiler ~/.opam/5.2.0+ox/bin/ocamlopt --receipt /tmp/dng-reconcile-ox.json
```

Compile current production source through the real mode selector. OxCaml runs
inside Safe.spawn. Private2MiB fixtures independently encode the expected merged
Rating/Label target. Darwin uses an actual clonefile staging substrate; elsewhere
ordinary private copying is explicitly labelled. Byte-for-byte output equality
and unchanged inputs are checked externally. No file is published or relabelled.

The [scope](../../doc/dng-three-way-materialization.md) and pinned qualification
distinguish packet/target construction from trusted archive-base capture,
reconciliation selection and two-replica publication, which remain open.
