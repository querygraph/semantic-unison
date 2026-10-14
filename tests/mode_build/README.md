# Actual production mode exports

`probe.py --compiler OCAMLOPT --build SNAPSHOT [--dune] --receipt FILE` links
actual compiled Hash/File/Mailbox objects and interfaces from a Make or Dune
snapshot. It performs private file hashing through an immutable mailbox job.
OxCaml uses Safe.spawn and must also reject a shared mutable reference payload;
stock exercises runtime parity through ordinary spawn. No checked interface is
substituted by this runner.

`filter.py --help` describes the selector harness. Its18 controls verify exact
stock passthrough, exact checked output and rejection with zero output bytes.
[Qualification](qualification.json) records the actual artifacts and related
build/configuration/receive tests. Native C contracts remain manually audited;
the complete production worker is not yet compiler-checked.
