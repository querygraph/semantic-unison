#!/usr/bin/env python3
"""Direct native APFS scratch-ownership controls in retained private snapshots."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[2]
INPUTS = ("src/copy_stubs.c", "src/fs.ml", "src/fs.mli",
          "tests/clone_scratch/fixture.c", "tests/clone_scratch/test.ml",
          "tests/clone_scratch/run.py", "tests/clone_scratch/README.md")


def digest(data):
    return hashlib.sha256(data).hexdigest()


def replace_once(source, old, new):
    if source.count(old) != 1:
        raise AssertionError("private mutation anchor is no longer unique: " + repr(old))
    return source.replace(old, new)


def mutated(source, mode):
    if mode == "fixed":
        return source
    if mode == "absolute-reservation":
        # Set after inspecting the frozen production implementation. This
        # control restores the actual absolute reservation/removal operations,
        # retaining the remaining descriptor-relative clone engine.
        start = source.index('  phase = "clone_stage: basis reservation";')
        end = source.index('  phase = "clone_stage: reservation close";', start)
        source = source[:start] + """
  char obsolete_scratch[4096];
  if (snprintf(obsolete_scratch, sizeof(obsolete_scratch),
               "%s.basis.XXXXXX.unison.tmp", dst) >= sizeof(obsolete_scratch)) {
    error = ENAMETOOLONG; goto unlocked_done;
  }
  phase = "clone_stage: basis reservation";
  reserve = mkstemps(obsolete_scratch, strlen(".unison.tmp"));
  if (reserve < 0) { error = errno; goto unlocked_done; }
  strcpy(scratch, strrchr(obsolete_scratch, '/') + 1);
  reservation_owned = 1;
  phase = "clone_stage: reservation removal";
  if (unlink(obsolete_scratch)) { error = errno; goto unlocked_done; }
  reservation_owned = 0;
""" + source[end:]
        return source
    if mode == "missing-reservation-guard":
        # Production retains the witness even with this identity check removed.
        # Native replacement is triggered from fstatat before the guarded
        # comparison, so removing its comparison exposes a real wrong unlink.
        return replace_once(source,
            "  if (!S_ISREG(named.st_mode) || !S_ISREG(after.st_mode) ||\n"
            "      before.st_dev != after.st_dev || before.st_ino != after.st_ino ||\n"
            "      named.st_dev != before.st_dev || named.st_ino != before.st_ino ||\n"
            "      (single_link && (named.st_nlink != 1 || after.st_nlink != 1))) {",
            "  if (witness != reserve_fd &&\n"
            "      (!S_ISREG(named.st_mode) || !S_ISREG(after.st_mode) ||\n"
            "       before.st_dev != after.st_dev || before.st_ino != after.st_ino ||\n"
            "       named.st_dev != before.st_dev || named.st_ino != before.st_ino ||\n"
            "       (single_link && (named.st_nlink != 1 || after.st_nlink != 1)))) {")
    raise AssertionError(mode)


def run(args, *, cwd, env, log, timeout=90):
    started = time.monotonic()
    with log.open("w") as output:
        result = subprocess.run(args, cwd=cwd, env=env, stdout=output,
                                stderr=subprocess.STDOUT, timeout=timeout)
    elapsed = time.monotonic() - started
    data = log.read_bytes()
    rendered = data.decode(errors="replace")
    if result.returncode:
        print(rendered, end="", flush=True)
    elif rendered.strip():
        print(rendered.strip().splitlines()[-1], flush=True)
    return {"argv": list(args), "cwd": str(cwd), "exit_code": result.returncode,
            "elapsed_seconds": elapsed, "log": str(log), "log_sha256": digest(data)}


def inventory(root):
    result = {}
    for path in sorted(root.rglob("*")):
        observed = path.lstat()
        entry = {"mode": observed.st_mode, "device": observed.st_dev,
                 "inode": observed.st_ino, "links": observed.st_nlink,
                 "bytes": observed.st_size}
        if stat.S_ISREG(observed.st_mode):
            entry["sha256"] = digest(path.read_bytes())
            entry["kind"] = "regular"
        elif stat.S_ISLNK(observed.st_mode):
            entry["kind"] = "symlink"; entry["target"] = os.readlink(path)
        elif stat.S_ISDIR(observed.st_mode):
            entry["kind"] = "directory"
        else:
            entry["kind"] = "other"
        result[str(path.relative_to(root))] = entry
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ocamlopt", required=True)
    parser.add_argument("--receipt", type=Path)
    parser.add_argument("--fixed-only", action="store_true", help="development focus; not final qualification")
    parser.add_argument("--case", default="all", help="development focus; not final qualification")
    args = parser.parse_args()
    if sys.platform != "darwin":
        print("SKIP: direct native controls require macOS/APFS")
        return
    compiler = shutil.which(args.ocamlopt)
    if compiler is None:
        parser.error("native compiler unavailable")
    env = os.environ.copy()
    for name in ("OCAMLLIB", "OCAMLPATH", "CAML_LD_LIBRARY_PATH", "OCAMLRUNPARAM"):
        env.pop(name, None)
    version = subprocess.check_output([compiler, "-version"], env=env, text=True).strip()
    compiler_config = subprocess.check_output([compiler, "-config"], env=env, text=True)
    native_compiler = subprocess.check_output(["/usr/bin/xcrun", "--find", "clang"], env=env, text=True).strip()
    native_version = subprocess.check_output([native_compiler, "--version"], env=env, text=True)
    original = {name: (ROOT / name).read_bytes() for name in INPUTS}
    source = original["src/copy_stubs.c"].decode()
    native = source.split("static value unsn_clone_stage_impl(", 1)[1]
    before = native.split("char *src = strdup", 1)[0]
    assert "caml_alloc_tuple(keep_parent ? 3 : 2)" in before
    assert "caml_process_pending_actions();" in before
    assert native.count("caml_enter_blocking_section_no_pending();") == 1
    assert "unsn_stage_close" in source and "unsn_stage_remove_owned" in source
    work = Path(tempfile.mkdtemp(prefix="unison-clone-scratch-", dir="/private/tmp"))
    print("Retained artifacts", work, "Compiler", version, flush=True)
    receipt = {"schema": "unison-native-clone-scratch-qualification/1",
               "compiler": compiler, "compiler_version": version,
               "compiler_sha256": digest(Path(compiler).read_bytes()),
               "compiler_config": compiler_config,
               "native_compiler": native_compiler,
               "native_compiler_sha256": digest(Path(native_compiler).read_bytes()),
               "native_compiler_version": native_version,
               "build_environment": {key: env.get(key) for key in ("SDKROOT", "MACOSX_DEPLOYMENT_TARGET", "CC", "CFLAGS")},
               "sources": {name: digest(data) for name, data in original.items()},
               "artifacts": str(work), "runs": [], "source_guards": "result preallocation/pending dispatch/no-pending release; not allocation-fault or native-deadline proof",
               "scope": "synthetic disposable local APFS files only; no Photo, catalog, SDK, Lightroom or production volume access"}
    ml = original["src/fs.ml"].decode().split("type clone_stage_decline =", 1)[1].split("(****)", 1)[0]
    mli = original["src/fs.mli"].decode().split("type clone_stage_decline =", 1)[1]
    modes = ("fixed",) if args.fixed_only else ("fixed", "absolute-reservation", "missing-reservation-guard")
    for mode in modes:
        build = work / mode; build.mkdir()
        (build / "copy_stubs.c").write_text(mutated(source, mode))
        (build / "fspath.ml").write_text("type t = string\n")
        (build / "fs.ml").write_text("let path (p : Fspath.t) = p\ntype clone_stage_decline =" + ml)
        (build / "fs.mli").write_text("type clone_stage_decline =" + mli)
        for name in ("fixture.c", "test.ml"):
            (build / name).write_bytes(original["tests/clone_scratch/" + name])
        commands = []
        for name in ("fspath.ml", "fs.mli", "fs.ml", "fixture.c"):
            command = [compiler, "-I", "+unix", "-ccopt", "-Wall", "-ccopt", "-Wextra", "-c", name]
            checked = run(command, cwd=build, env=env, log=build / (name + ".compile.log"))
            commands.append(checked)
            if checked["exit_code"]:
                raise AssertionError("private native compilation failed")
        command = [compiler, "-I", "+unix", "unix.cmxa", "fspath.cmx", "fs.cmx", "fixture.o",
                   "test.ml", "-o", "scratch-test"]
        checked = run(command, cwd=build, env=env, log=build / "link.log")
        commands.append(checked)
        if checked["exit_code"]:
            raise AssertionError("private native link failed")
        executions = []
        for api in ("all",) if mode == "fixed" else ("legacy", "strict", "handles"):
            files = build / ("files-" + api); files.mkdir()
            case = args.case if mode == "fixed" else ("held-parent-rebind" if mode == "absolute-reservation" else "reservation-replacement")
            command = [str(build / "scratch-test"), str(files), case]
            if api != "all":
                command.append(api)
            checked = run(command, cwd=build, env=env, log=build / ("run-" + api + ".log"), timeout=90)
            expected = 0 if mode == "fixed" else 2
            if checked["exit_code"] != expected:
                raise AssertionError(mode + ": unexpected terminal exit " + str(checked["exit_code"]))
            log = Path(checked["log"]).read_text()
            if mode == "fixed":
                match = re.search(r"All (\d+) clone-scratch cases passed; (\d+) assertions", log)
                if not match:
                    raise AssertionError("native fixture did not complete")
                checked["cases"] = int(match[1]); checked["assertions"] = int(match[2])
                assert "Filesystem apfs" in log
                checked["filesystem"] = "apfs"
            else:
                expected_message = "held-parent-rebind" if mode == "absolute-reservation" else "reservation-replacement"
                failure_message = "reservation escaped held parent" if mode == "absolute-reservation" else "reservation-replacement: unexpected success"
                if expected_message not in log or failure_message not in log or "Fatal error: exception" not in log:
                    raise AssertionError("negative failed outside designated assertion")
                checked["detected_defect"] = expected_message
                checked["detected_assertion"] = failure_message
                checked["abi"] = api
            executions.append(checked)
            artifact_manifest = files / "inventory.json"
            artifact_manifest.write_text(json.dumps(inventory(files), indent=2) + "\n")
            checked["native_artifact_manifest"] = str(artifact_manifest)
            checked["native_artifact_manifest_sha256"] = digest(artifact_manifest.read_bytes())
        receipt["runs"].append({"mode": mode, "commands": commands, "execution": executions[0],
                                "additional_executions": executions[1:],
                                "production_copy_sha256": digest((build / "copy_stubs.c").read_bytes()),
                                "binary": str(build / "scratch-test"),
                                "binary_sha256": digest((build / "scratch-test").read_bytes())})
    receipt["terminal"] = "passed"
    destination = args.receipt or work / "qualification.json"
    destination.write_text(json.dumps(receipt, indent=2) + "\n")
    print("Qualification receipt", destination, flush=True)


if __name__ == "__main__":
    main()
