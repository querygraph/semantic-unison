#!/usr/bin/env python3
"""Exercise generic descriptor close and reuse in an isolated native build."""
import argparse
from pathlib import Path
import shutil
import subprocess
import tempfile

parser = argparse.ArgumentParser()
parser.add_argument("--ocamlopt", default="ocamlopt")
parser.add_argument("--implementation", type=Path, help="optional generic implementation for a negative control")
args = parser.parse_args()
root = Path(__file__).resolve().parents[2]
sources = [
    "src/lwt/lwt.mli", "src/lwt/lwt.ml", "src/lwt/pqueue.mli", "src/lwt/pqueue.ml",
    "src/lwt/generic/lwt_unix_impl.ml", "src/lwt/lwt_unix.mli", "src/lwt/lwt_unix.ml",
]
with tempfile.TemporaryDirectory(prefix="unison-lwt-close-") as temporary:
    build = Path(temporary)
    for source in sources + ["tests/lwt_close/test.ml"]:
        actual = args.implementation if args.implementation and source.endswith("/lwt_unix_impl.ml") else root / source
        shutil.copyfile(actual, build / Path(source).name)
    for source in sources:
        subprocess.run([args.ocamlopt, "-I", "+unix", "-c", Path(source).name], cwd=build, check=True)
    objects = [Path(source).stem + ".cmx" for source in sources if source.endswith(".ml")]
    subprocess.run([args.ocamlopt, "-I", "+unix", "unix.cmxa", *objects,
                    "test.ml", "-o", "lwt-close-test"], cwd=build, check=True)
    subprocess.run([str(build / "lwt-close-test")], cwd=build, check=True, timeout=15)
