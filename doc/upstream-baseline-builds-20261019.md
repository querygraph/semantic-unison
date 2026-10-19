# Three pinned comparison baselines

The original375 source now builds unchanged with stock OCaml5.2.0, using the
same installed stock compiler as the retained genuine8772 build. The minimal
8772 OxCaml build passes with ten eta expansions in four files. None of these
three binaries contains this fork's semantic/APFS/worker implementation.

| Artifact | Source | Compiler | Binary SHA256 prefix | Evidence |
| --- | --- | --- | --- | --- |
| Original | 375ea3ad2cace8584c508ef463332066d85e1d4e, unchanged | stock5.2.0 | 1713490bee5f70c0 | New build/selftest owner12764/8177fa/0 |
| Selected upstream | 8772d26a2eb77cfd0cb6da81807e81f24f51044c, unchanged | stock5.2.0 | 5886a3b15e15b23b | Retained genuine build/selftest receipt |
| Minimal upstream Ox | same8772 plus versioned compatibility patch | 5.2.0+ox | 481c640cba954d926 | New build/selftest owner97618/60b3b0/0 |

[Artifact binding](../tests/qualification/three-baseline-artifact-binding-20261019.json)
records full hashes, source archives, actual direct-child records and compiler
pins. The independent audit089fef/0 reparsed all five original and seven Ox
child settlements, compared182/187 archived source/build files respectively,
and compared187 genuine-upstream files. Git archive commit comments and exact
source hashes are checked; the four Ox modifications match their pinned
base/result hashes. The historical genuine build keeps its original proof
scope; this audit does not invent a new historical child ledger.

All new compiler calls used serial Make jobs, existing Unison00..07 tokens,
private source/build/archive state and no EXglobal/Photo/Adobe operation.
All children settled and CPU grants closed. Fresh CPU reacquisition also
passed. Neither build duration nor successful selftests establishes a compiler
speedup, filesystem speedup or benchmark result.

The first Ox wrapper refused its capture configuration before child creation;
its idle owner was independently recovered (137, not normal success). The
next build failed on Features.mem's exposed local argument mode, with all six
children and CPU credits closed. Those failures remain preserved in the
minimal-Ox receipt. The successor added only that missing eta expansion and
passed; it did not suppress compiler alerts or change runtime semantics.

The original baseline's former OCaml5.5.1 artifact is absent. This new5.2.0
artifact is a distinct qualification; historical5.5.1 receipts remain unchanged.
The original archive contains182 checked source/build files; selected8772 has187.

Next use these exact binaries in a matched generated-input baseline comparison,
with source/binary epochs, explicit parameters and per-call settlement. A real
bulk-IO or quiet timing window must be coordinated separately. The existing
larger-size workload matrix, final SDK three-codec merge receiving and broader
platform scopes remain separate requirements.
