# Scalar three-way packet kernel

```sh
python3 tests/xmp_merge/run.py --compiler /usr/local/bin/ocamlopt --receipt /tmp/xmp-merge-stock.json
python3 tests/xmp_merge/run.py --compiler ~/.opam/5.2.0+ox/bin/ocamlopt --receipt /tmp/xmp-merge-ox.json
```

The production selector compiles the real hash/observation/merge source. Both
compilers run25 exact-byte/conflict controls; OxCaml also links and executes a
checked-spawn control. This tests the [packet policy](../../doc/xmp-three-way-policy-v0.md),
not an archive base, automatic file merge or publication. The qualification
retains exact inputs, binaries/logs and broader parser/build regression evidence.
