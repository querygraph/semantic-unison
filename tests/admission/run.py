#!/usr/bin/env python3
"""Test owner-loop resource admission outside the source checkout."""
import argparse
from pathlib import Path
import shutil
import subprocess
import tempfile

parser = argparse.ArgumentParser()
parser.add_argument("--ocamlopt", default="ocamlopt")
args = parser.parse_args()
root = Path(__file__).resolve().parents[2]
sources = [
    "src/lwt/lwt.mli", "src/lwt/lwt.ml", "src/lwt/pqueue.mli", "src/lwt/pqueue.ml",
    "src/lwt/generic/lwt_unix_impl.ml", "src/lwt/lwt_unix.mli", "src/lwt/lwt_unix.ml",
    "src/borrowedWork.mli", "src/borrowedWork.ml",
    "src/helperSupervisor_stubs.c", "src/helperSupervisor.mli", "src/helperSupervisor.ml",
    "src/semanticAdmission.mli", "src/semanticAdmission.ml",
]
with tempfile.TemporaryDirectory(prefix="unison-admission-") as tmp:
    build = Path(tmp)
    for source in sources + ["tests/admission/test.ml"]:
        shutil.copyfile(root / source, build / Path(source).name)
    for source in sources:
        subprocess.run([args.ocamlopt, "-I", "+unix", "-c", Path(source).name],
                       cwd=build, check=True)
    objects = [Path(s).stem + (".o" if s.endswith(".c") else ".cmx")
               for s in sources if s.endswith((".ml", ".c"))]
    subprocess.run([args.ocamlopt, "-I", "+unix", "unix.cmxa", *objects,
                    "test.ml", "-o", "admission-test"], cwd=build, check=True)
    subprocess.run([str(build / "admission-test")], cwd=build, check=True, timeout=30)
