#!/usr/bin/env python3
"""Compile constrained portable clone-range tests outside the checkout."""
import argparse
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import tempfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ocamlopt", default="ocamlopt")
    args = parser.parse_args()
    compiler = shutil.which(args.ocamlopt)
    if compiler is None:
        parser.error("native compiler unavailable")
    root = Path(__file__).resolve().parents[2]
    sources = ["src/cloneRange.mli", "src/cloneRange.ml", "tests/clone_range/test.ml"]
    environment = os.environ.copy()
    for name in ("OCAMLLIB", "OCAMLPATH", "CAML_LD_LIBRARY_PATH", "OCAMLRUNPARAM"):
        environment.pop(name, None)
    version = subprocess.check_output([compiler, "-version"], env=environment, text=True).strip()
    with tempfile.TemporaryDirectory(prefix="unison-clone-range-") as temporary:
        work = Path(temporary)
        for source in sources:
            data = (root / source).read_bytes()
            (work / Path(source).name).write_bytes(data)
            print("source " + source + " " + hashlib.sha256(data).hexdigest(), flush=True)
        print("Compiler " + version + "; isolated build " + str(work), flush=True)
        for source in ("cloneRange.mli", "cloneRange.ml"):
            subprocess.run([compiler, "-I", "+unix", "-c", source],
                           cwd=work, env=environment, check=True)
        subprocess.run([compiler, "-I", "+unix", "unix.cmxa", "cloneRange.cmx",
                        "test.ml", "-o", "clone-range-test"],
                       cwd=work, env=environment, check=True)
        subprocess.run([str(work / "clone-range-test")],
                       cwd=work, env=environment, check=True, timeout=30)


if __name__ == "__main__":
    main()
