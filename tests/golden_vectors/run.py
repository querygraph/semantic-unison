#!/usr/bin/env python3
"""Build gen.ml against Unison's semantic kernel and tiffgraph, write golden
vectors (bytes + vectors.json) to out/. Stock OCaml (default switch)."""
import pathlib, shutil, subprocess, sys, tempfile
HERE = pathlib.Path(__file__).resolve().parent
SRC = HERE.parent.parent / 'src'
TIFFGRAPH = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else pathlib.Path.home() / 'src/tiffgraph')
MODULES = ("semanticHash", "semanticFile", "formatExtension", "xmpObservation", "xmpMerge",
           "dngSemantic", "dngExtended", "semanticDelta")
test = (TIFFGRAPH / 'test/test_tiffgraph.ml').read_text()
start, stop = test.index('(* ---- A small TIFF writer'), test.index('(* ---- Readers')
out = HERE / 'out'
shutil.rmtree(out, ignore_errors=True); out.mkdir()
with tempfile.TemporaryDirectory(prefix='golden-') as td:
    b = pathlib.Path(td)
    for name in ('semanticHash_stubs.c', 'semanticHash_evp.h', 'semanticFile_stubs.c'):
        shutil.copy(SRC / name, b)
    for m in MODULES:
        for s in ('.mli', '.ml'):
            shutil.copy(SRC / (m + s), b)
    shutil.copy(TIFFGRAPH / 'lib/tiffgraph.ml', b)
    shutil.copy(TIFFGRAPH / 'lib/tiffgraph.mli.in', b / 'tiffgraph.mli')
    (b / 'builder.ml').write_text(test[start:stop])
    shutil.copy(HERE / 'gen.ml', b)
    argv = ['opam', 'exec', '--switch=default', '--', 'ocamlfind', 'ocamlopt', '-package', 'unix', '-linkpkg',
            'semanticHash_stubs.c', 'semanticFile_stubs.c', 'tiffgraph.mli', 'tiffgraph.ml']
    for m in MODULES:
        argv += [m + '.mli', m + '.ml']
    argv += ['builder.ml', 'gen.ml', '-o', 'gen']
    subprocess.run(argv, cwd=b, check=True)
    r = subprocess.run([str(b / 'gen'), str(out)], check=True, capture_output=True, text=True)
    (out / 'vectors.json').write_text(r.stdout)
print(r.stdout)
