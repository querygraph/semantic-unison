#!/usr/bin/env python3
"""Build the current source (including uncommitted work) outside the checkout."""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

parser = argparse.ArgumentParser()
parser.add_argument("--compiler-prefix", required=True, help="absolute directory containing ocaml/ocamlopt")
parser.add_argument("--jobs", type=int, default=min(os.cpu_count() or 1, 8))
parser.add_argument("--selftest", action="store_true")
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
print("Build snapshot:", work, flush=True)
with (work / "build.log").open("w") as log:
    for target in ("depend", "tui"):
        command = ["make", "-C", "src", target, "-j" + str(args.jobs), "NATIVE=true", "TOOL_PREFIX=" + str(prefix) + "/"]
        result = subprocess.run(command, cwd=work, env=env, stdout=log, stderr=subprocess.STDOUT)
        if result.returncode:
            print("\n".join((work / "build.log").read_text().splitlines()[-30:]))
            raise SystemExit(result.returncode)
print("Built:", work / "src/unison", flush=True)
if args.selftest:
    state = work / "selftest-state"
    state.mkdir()
    with (work / "selftest.log").open("w") as log:
        result = subprocess.run([str(work / "src/unison"), "-ui", "text", "-selftest"],
                                cwd=work, env=dict(env, UNISON=str(state)), stdout=log,
                                stderr=subprocess.STDOUT, timeout=600)
    print("Selftest exit:", result.returncode, "log:", work / "selftest.log", flush=True)
    raise SystemExit(result.returncode)
