# Finite resource-admission faults

Run each compiler against private instrumented sources:

```sh
python3 tests/admission_faults/run.py --ocamlopt /absolute/compiler/ocamlopt --keep-work
```

Seventeen positive groups exercise caller-owned reservations, cancellation,
allocation failures at selected grant/retire/scheduling seams, and deferred
workspace settlement. Four private regressions remove the unregister or
scheduling recovery, restore an allocating grant, or restore an allocating
retirement. Each must fail its designated assertion. Use `--negative-control`
with `unregister`, `schedule`, `allocating-grant`, or `allocating-retire`.

The sealed `qualification-20261013.json` also binds the ordinary 26-group
admission suite and the 106-group registry suite with its two historical
regressions on stock OCaml and OxCaml. Registry compatibility seams do not prove
native resource ownership. Retained commands, sources, objects, binaries and
logs distinguish positive runs from expected failing controls.

These are logical resource-ledger and selected finite-fault checks. They do not
measure native descriptor peaks or RSS, force persistent allocator exhaustion,
or establish universal recovery. Native lifecycle tests are separate under
`../resource_lifetime/`. No Adobe or Photo operations occur.

The seventeenth group queues two consumers behind two held owners, then frees
both slots before the deferred pump runs. The first grant's raw reply observer
throws; its granted state must remain visible, the second ready owner must still
be granted, and the first observer exception must propagate unchanged. The
previous production dispatcher fails the ready-sibling assertion. This is an
owner-loop progress check, not proof of native process or descriptor settlement.
