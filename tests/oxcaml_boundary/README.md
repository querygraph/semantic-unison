# Installed OxCaml boundary probes

```sh
python3 tests/oxcaml_boundary/probe.py \
  --compiler ~/.opam/5.2.0+ox/bin/ocamlopt \
  --worker-build /absolute/path/to/retained/flat/worker/build \
  --receipt /tmp/ox-boundary.json
```

Use a compiler-matched build from tests/workers/run.py. The probe copies it to
an isolated tree, verifies matching current production/Lwt sources, compiles
the unchanged production worker and its one-line Safe.spawn substitution, then
checks an actually executed portable atomic control and two rejected mutable
reference controls. Production Safe.spawn substitution must fail; a passing
probe does not mean the production boundary is safe. Sources, objects, compiler,
installed interfaces and logs are pinned in qualification.json. No unsafe cast
or ignored compiler error is used to make the replacement compile.

The first preparatory copy accidentally matched the fixture test.ml against
Unison's unrelated production test.ml. That source-identity guard stopped before
compiler/runtime probes. Fixture test artifacts are now excluded from imports;
only production dependency sources/interfaces are matched. All five actual
probes then reached their expected terminal results.
