#!/usr/bin/env python3
"""Compile and test copy-range outcomes in an isolated directory."""
import argparse
from pathlib import Path
import shutil
import subprocess
import tempfile

parser = argparse.ArgumentParser()
parser.add_argument("--ocamlopt", default="ocamlopt")
args = parser.parse_args()
root = Path(__file__).resolve().parents[2]
with tempfile.TemporaryDirectory(prefix="unison-copy-range-") as temporary:
    work = Path(temporary)
    for source in ("src/copyRange.mli", "src/copyRange.ml", "tests/copy_range/test.ml"):
        shutil.copyfile(root / source, work / Path(source).name)
    for source in ("copyRange.mli", "copyRange.ml"):
        subprocess.run([args.ocamlopt, "-I", "+unix", "-c", source], cwd=work, check=True)
    subprocess.run([args.ocamlopt, "-I", "+unix", "unix.cmxa", "copyRange.cmx",
                    "test.ml", "-o", "copy-range-test"], cwd=work, check=True)
    subprocess.run([str(work / "copy-range-test")], cwd=work, check=True, timeout=10)
