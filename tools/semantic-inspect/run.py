#!/usr/bin/env python3
"""Build the read-only inspector in isolation, then pass it the remaining args."""
import argparse
from pathlib import Path
import shutil
import subprocess
import tempfile

parser = argparse.ArgumentParser()
parser.add_argument("--ocamlopt", default="ocamlopt")
args, forwarded = parser.parse_known_args()
if forwarded[:1] == ["--"]:
    forwarded = forwarded[1:]
root = Path(__file__).resolve().parents[2]
modules = ["semanticHash", "semanticFile", "formatExtension", "xmpObservation", "dngSemantic", "semanticDelta"]
with tempfile.TemporaryDirectory(prefix="unison-semantic-inspect-") as temporary:
    build = Path(temporary)
    for name in modules:
        for suffix in (".ml", ".mli"):
            shutil.copyfile(root / "src" / (name + suffix), build / (name + suffix))
    for name in ("semanticHash_stubs.c", "semanticFile_stubs.c"):
        shutil.copyfile(root / "src" / name, build / name)
    shutil.copyfile(root / "tools/semantic-inspect/inspect.ml", build / "inspect.ml")
    command = [args.ocamlopt, "-I", "+unix", "unix.cmxa", "semanticHash_stubs.c",
               "semanticFile_stubs.c"]
    for name in modules:
        command += [name + ".mli", name + ".ml"]
    subprocess.run(command + ["inspect.ml", "-o", "semantic-inspect"], cwd=build, check=True)
    raise SystemExit(subprocess.run([str(build / "semantic-inspect")] + forwarded).returncode)
