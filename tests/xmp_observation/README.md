The production `XmpObservation` module reads an in-memory UTF-8 XMP packet. It
extracts namespace-qualified Description attributes and direct child properties,
then hashes each exact value/element encoding together with its complete in-scope
namespace context. Camera Raw fields are labeled as potential presentation
changes; this observation does not interpret Adobe edits, resolve AI dependencies,
prove rendering equivalence, or change synchronization/conflict decisions.

Run the synthetic suite in a private compiler-matched directory:

```sh
python3 tests/xmp_observation/run.py --ocamlopt /usr/local/bin/ocamlopt
python3 tests/xmp_observation/run.py --ocamlopt /Users/alexy/.opam/5.2.0+ox/bin/ocamlopt
```

The runner compiles only the production reader and SHA-256 module plus the focused
fixture. Python `hashlib` independently generates exact transcript digest vectors.
The OCaml suite covers aliases and scoped/default rebinding, inherited bindings
around identical nested mask bytes, nested data changes, attributes and full child
spans, classification, duplicate expanded properties, multiple RDF subjects,
unsupported declarations/entities/encodings, malformed/truncated XML, UTF-8,
inclusive and overflowing bounds, every truncation prefix of a structured packet,
and deterministic malformed-byte fuzz. A separate batch of synthetic XML token
mutations is checked against Python's independent ElementTree parser: any packet
admitted by the bounded reader must also be well-formed XML there. Valid XML can
still be outside the documented XMP subset. Optional `--receipt FILE` records compiler
version, exact input source hashes, process result, and the independent vectors.

Three private source mutations demonstrate that the tests reject loss of namespace
context, loss of child subtree encoding, and acceptance of duplicate expanded
properties:

```sh
python3 tests/xmp_observation/run.py --negative-control namespace
python3 tests/xmp_observation/run.py --negative-control subtree
python3 tests/xmp_observation/run.py --negative-control duplicate
```

The final isolated qualification is recorded in `qualification-20261013.json`:
968 focused checks and 1029 independent XML mutation checks passed under both
stock OCaml 5.5.1 and OxCaml 5.2.0+ox. All three private negative controls were
rejected under both compilers. The receipt embeds source pins and exact process
results. Independent review corrections distinguish anonymous RDF subjects from
explicit empty `rdf:about` subjects and reject unsupported structural XML
attributes rather than flattening them into metadata properties.

Only synthetic in-memory packets are inspected. No Adobe invocation, catalog,
Photo cache, image payload, or source photo is accessed. The precise supported
subset, resource bounds, excluded structural fields, and digest transcript are
documented in `src/xmpObservation.mli`.
