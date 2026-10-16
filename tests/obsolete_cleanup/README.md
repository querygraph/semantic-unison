These controls qualify obsolete regular staging-leaf cleanup through an
already prepared `FinalPublication` binding. All roots, bytes and state are
private synthetic fixtures. No Adobe/Lightroom, catalog, preview, production
volume, payload decoder or performance benchmark is used.

`run.py` compiles the exact production ML/native source. The C fixture includes
the byte-identical translation unit under private syscall wrappers. Ordinary
calls delegate to the real macOS operations; explicit controls replace a leaf
or parent after its first stat, inject unlink EIO, or reuse a descriptor after
a failing close. Twenty-two cases / 83 assertions cover ordinary/absent/scratch
leaves, mode-000 cleanup, hardlink/symlink/directory/FIFO preservation, sidecars,
wrong parent/live names, actual case aliases, equivalent working-directory
aliases, invalid paths, rebound roots/parents, producer/closed states and
operational errors. The snapshot is a full no-follow stat witness, not a held
payload FD. Directory bindings are held. Lookup/unlink remains cooperative,
without atomic namespace compare-and-swap or hostile inode-ABA protection.

`caller.py` requires a compiler-matched complete Make snapshot and recompiles
Copy plus its native-code dependents. Its private hook introduces an old stage
after producer admission, then either continues normally or rebinds the
receiver root and installs independent replacement inventory. Actual ordinary
CLI copying must delete the admitted obsolete stage and publish exact bytes;
rebinding must preserve the original and replacement stage/live bytes and
reject. A private pathname-cleanup negative must actually remove the wrong
replacement stage. It is one regressed Copy participant in the current graph,
not an old complete Unison binary. Cloning and semantic transfer are disabled
in these three controls; their contract is generic receiving cleanup.

Both compilers also run the existing actual Files/CLI publication matrix,
including semantic transfers, retained resumes, sidecars, backups, directories,
conflicts and both old-peer directions. The runner's private source seams now
follow the current optional `clone_owned` argument and sized source-clone hook;
its behavioral assertions remain unchanged.

Example commands:

```sh
python3 tests/obsolete_cleanup/run.py --ocamlopt /absolute/ocamlopt \
  --receipt /private/path/native.json
python3 tests/obsolete_cleanup/caller.py --build /private/path/build \
  --ocamlopt /absolute/ocamlopt --receipt /private/path/caller.json
```

The aggregate receipt records source/compiler/build/command/artifact pins and
the failed metadata-open prototype. Current cleanup does not open/read/chmod
the obsolete payload: permission to unlink comes from the held parent. Legacy
unbound cleanup, directories and auxiliary families remain separate work;
unexpected nonregular or multiply linked leaves are preserved and rejected.
No independent-agent review or physical sharing/speedup/durability claim is
made by this root-owned qualification.
