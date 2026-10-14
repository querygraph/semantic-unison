#!/usr/bin/env python3
"""Build the current source (including uncommitted work) outside the checkout."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

parser = argparse.ArgumentParser()
parser.add_argument("--compiler-prefix", required=True, help="absolute directory containing ocaml/ocamlopt")
parser.add_argument("--jobs", type=int, default=min(os.cpu_count() or 1, 8))
parser.add_argument("--selftest", action="store_true")
parser.add_argument("--build-system", choices=("make", "dune"), default="make")
parser.add_argument("--report", type=Path, help="save source/compiler/binary pins and actual outcomes")
args = parser.parse_args()
prefix = Path(args.compiler_prefix).resolve()
if args.jobs < 1 or not (prefix / "ocamlopt").is_file():
    parser.error("positive jobs and a compiler directory with ocamlopt are required")
root = Path(__file__).resolve().parents[1]
work = Path(tempfile.mkdtemp(prefix="unison-build-"))
paths = subprocess.check_output(["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"], cwd=root)
for raw in paths.split(b"\0"):
    if not raw:
        continue
    relative = os.fsdecode(raw)
    source, target = root / relative, work / relative
    if source.is_file():
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
env = dict(os.environ, PATH=str(prefix) + os.pathsep + os.environ.get("PATH", ""))
for key in ("OCAMLLIB", "OCAMLPATH", "CAML_LD_LIBRARY_PATH", "OCAMLRUNPARAM"):
    env.pop(key, None)
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
receipt = {"workspace": str(work), "build_system": args.build_system,
           "complete": False, "selftest_requested": args.selftest,
           "runner_sha256": sha(Path(__file__).resolve()),
           "compiler": str(prefix / "ocamlopt"), "compiler_sha256": sha(prefix / "ocamlopt"),
           "compiler_version": subprocess.check_output([str(prefix / "ocamlopt"), "-version"], env=env, text=True).strip(),
           "source_sha256": {os.fsdecode(raw): sha(work / os.fsdecode(raw))
               for raw in paths.split(b"\0") if raw and (work / os.fsdecode(raw)).is_file()
               and (Path(os.fsdecode(raw)).suffix in (".ml", ".mli", ".c", ".h")
                    or Path(os.fsdecode(raw)).name in ("Makefile", "Makefile.OCaml", "dune", "dune-project")
                    or os.fsdecode(raw).endswith(".ox.mli.in"))},
           "build_exit": None, "selftest_exit": None}
def save_receipt():
    (work / "build-receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    if args.report:
        args.report.write_text(json.dumps(receipt, indent=2) + "\n")
save_receipt()
print("Build snapshot:", work, flush=True)
with (work / "build.log").open("w") as log:
    commands = ([["make", "-C", "src", target, "-j" + str(args.jobs), "NATIVE=true", "TOOL_PREFIX=" + str(prefix) + "/"]
                 for target in ("depend", "tui")] if args.build_system == "make" else
                [["dune", "build", "-j", str(args.jobs), "src/linktext.exe"]])
    receipt["commands"] = commands
    for command in commands:
        result = subprocess.run(command, cwd=work, env=env, stdout=log, stderr=subprocess.STDOUT)
        receipt["build_exit"] = result.returncode
        save_receipt()
        if result.returncode:
            print("\n".join((work / "build.log").read_text().splitlines()[-30:]))
            raise SystemExit(result.returncode)
binary = work / ("src/unison" if args.build_system == "make" else "_build/default/src/linktext.exe")
receipt["binary"] = str(binary)
receipt["binary_sha256"] = sha(binary)
receipt["build_log_sha256"] = sha(work / "build.log")
receipt["complete"] = not args.selftest
save_receipt()
print("Built:", binary, flush=True)
if args.selftest:
    state = work / "selftest-state"
    state.mkdir()
    with (work / "selftest.log").open("w") as log:
        result = subprocess.run([str(binary), "-ui", "text", "-selftest"],
                                cwd=work, env=dict(env, UNISON=str(state)), stdout=log,
                                stderr=subprocess.STDOUT, timeout=600)
    print("Selftest exit:", result.returncode, "log:", work / "selftest.log", flush=True)
    receipt["selftest_exit"] = result.returncode
    receipt["selftest_log_sha256"] = sha(work / "selftest.log")
    receipt["complete"] = result.returncode == 0
    save_receipt()
    raise SystemExit(result.returncode)
