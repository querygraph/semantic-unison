#!/usr/bin/env python3
"""Compile isolated production modules with the vendored Lwt; leave no build files."""
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
    "src/lwt/lwt.mli", "src/lwt/lwt.ml",
    "src/lwt/pqueue.mli", "src/lwt/pqueue.ml",
    "src/lwt/generic/lwt_unix_impl.ml",
    "src/lwt/lwt_unix.mli", "src/lwt/lwt_unix.ml",
    "src/borrowedWork.mli", "src/borrowedWork.ml",
    "src/helperSupervisor.mli", "src/helperSupervisor.ml",
    "src/dngValidation.mli", "src/dngValidation.ml",
    "src/helperSupervisor_stubs.c",
    "tests/helpers/synthetic_helper.ml", "tests/helpers/helper_tests.ml",
    "tests/helpers/exit_guard.ml",
]
with tempfile.TemporaryDirectory(prefix="unison-helper-tests-") as temp:
    build = Path(temp)
    for source in sources:
        shutil.copy2(root / source, build / Path(source).name)
    def run(*command):
        subprocess.run(command, cwd=build, check=True)
    for source in sources:
        if "tests/helpers/" not in source:
            run(args.ocamlopt, "-I", "+unix", "-c", Path(source).name)
    run(args.ocamlopt, "-I", "+unix", "unix.cmxa", "synthetic_helper.ml", "-o", "synthetic_helper")
    run(args.ocamlopt, "-I", "+unix", "unix.cmxa", "lwt.cmx", "pqueue.cmx",
        "lwt_unix_impl.cmx", "lwt_unix.cmx", "helperSupervisor_stubs.o",
        "borrowedWork.cmx",
        "helperSupervisor.cmx", "exit_guard.ml", "-o", "exit_guard")
    run(args.ocamlopt, "-I", "+unix", "unix.cmxa", "lwt.cmx", "pqueue.cmx",
        "lwt_unix_impl.cmx", "lwt_unix.cmx", "helperSupervisor_stubs.o",
        "borrowedWork.cmx",
        "helperSupervisor.cmx", "dngValidation.cmx", "helper_tests.ml", "-o", "helper_tests")
    run(str(build / "helper_tests"), str(build / "synthetic_helper"))
