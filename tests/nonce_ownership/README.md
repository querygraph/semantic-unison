# Exact nonce-function descriptor ownership

Run the exact extracted production function with private module aliases:

```sh
python3 tests/nonce_ownership/run.py --ocamlopt /absolute/compiler/ocamlopt --keep-work
```

Thirteen positive groups use actual random-device descriptors and synthetic
sentinels. They cover pre-open allocation faults, interrupted and short reads,
EOF, primary-error preservation, and close errors after the descriptor has
already been consumed. A same-integer replacement sentinel verifies that
cleanup attempts the owned close once and preserves the reused descriptor.

Two private regressions must fail their designated checks. Select
`--negative-control original-constructor` to restore the pinned old function,
or `--negative-control unchecked-close` to remove the close ownership flag.
Negative-only teardown closes the intentionally leaked/replaced resources.
The sealed `qualification-20261013.json` binds stock OCaml and OxCaml commands,
exact function extraction, copied and instrumented sources, binaries and logs.

This qualifies the extracted nonce function, not the whole remote protocol.
The close-error model consumes the descriptor before raising; it does not
qualify an operating system that refuses to close it. No Adobe or Photo
operations occur.
