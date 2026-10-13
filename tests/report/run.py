#!/usr/bin/env python3
"""Build bounded advisory report tests in a private directory."""
import argparse
from pathlib import Path
import shutil
import subprocess
import tempfile

parser = argparse.ArgumentParser()
parser.add_argument("--ocamlopt", default="ocamlopt")
args = parser.parse_args()
root = Path(__file__).resolve().parents[2]
modules = ["semanticHash", "semanticFile", "formatExtension", "xmpObservation", "dngSemantic",
           "semanticDelta", "semanticReport"]
with tempfile.TemporaryDirectory(prefix="unison-report-") as tmp:
    build = Path(tmp)
    for name in modules:
        for suffix in (".ml", ".mli"):
            shutil.copyfile(root / "src" / (name + suffix), build / (name + suffix))
    for name in ("semanticHash_stubs.c", "semanticFile_stubs.c"):
        shutil.copyfile(root / "src" / name, build / name)
    fixtures = (root / "tests/semantic/test.ml").read_text().split("let () =", 1)[0]
    (build / "test.ml").write_text(fixtures + (root / "tests/report/test.ml").read_text())
    command = [args.ocamlopt, "-I", "+unix", "unix.cmxa", "semanticHash_stubs.c",
               "semanticFile_stubs.c"]
    for name in modules:
        command += [name + ".mli", name + ".ml"]
    subprocess.run(command + ["test.ml", "-o", "report-test"], cwd=build, check=True)
    subprocess.run([str(build / "report-test")], cwd=build, check=True, timeout=30)
