# Production OxCaml component contracts

Make and Dune now compile SemanticHash, SemanticFile and SemanticMailbox against
their qualified checked interfaces when the configured compiler version contains
`+ox`. Stock OCaml receives the original source bytes and ordinary interfaces.
The subsequent extension/counter integration now compiles the complete
SemanticWorkers closure through Safe.spawn; see
[the current boundary](checked-semantic-worker.md). Native contracts and wider
resource/performance qualification remain separate.

The build-only `semantic_mode_filter` accepts only the qualified component filenames, now including
extension/recognition, built-in inspectors, observations, delta execution, the
worker and its owner registration wrapper. Checked interfaces must equal the ordinary interface
plus their exact qualified annotations, including the mailbox payload mode.
Hash and File implementations require exactly three and two native contract
markers respectively. Unexpected modules, changed templates, marker counts or
mailbox declarations fail before producing preprocessed source. Source reads
are bounded to1MiB. No unsafe cast or alert suppression is introduced.
Native portability still relies on the reviewed C ownership/borrowing contracts.

Make uses the full configured byte compiler version from make_tools, rather than
the interpreter used to generate configuration. A make_tools change regenerates
existing Makefile.cfg. Explicit component rules apply the selector to both
interface and implementation compilation. The helper is omitted from the Unison
link and removed by clean. Dune uses a separate build-only executable and its
[per-module action preprocessor](https://dune.readthedocs.io/en/stable/reference/preprocessing-spec.html),
with [the compiler version variable](https://dune.readthedocs.io/en/stable/concepts/variables.html)
and explicit template dependencies. No project language version bump is needed.
Windows and other make implementations have not been runtime-qualified here.

Four fresh builds and CLI selftests pass: Make and Dune, each with stock5.5.1 and
OxCaml5.2.0+ox. Tests link the actual build artifacts without replacing interfaces:
immutable mailbox jobs execute private File/Hash operations inside Safe.spawn on
OxCaml, while a shared reference payload fails compilation. Stock exercises the
same runtime behavior with ordinary spawn. Each actual selector passes18 controls.
A simulated old Make configuration regenerates correctly and preserves all320
existing compiled object/interface files. Both final Make executables pass21
synthetic receive/publication controls each; mixed-compiler JPEG receiving passes
six controls. Negotiated DNG receiving also passes, including24 bidirectional
exact-file transactions and stable cleanup/retry. Earlier same-component builds also pass14 shared-helper controls
per compiler. The pinned receipt distinguishes these exact build identities.

This is no proof of renderer fidelity, Adobe validation, resource ceilings,
throughput improvement or complete M6. Qualification used private synthetic
files and invoked no Adobe/Lightroom or production photo/cache operation.

The subsequent [production worker integration](checked-semantic-worker.md)
now compiles the complete worker closure with Safe.spawn on OxCaml, including
checked extension execution and atomic counters. Earlier component receipts
remain historical; full native/resource/performance M6 requirements stay open.
