#!/usr/bin/env python3
"""Qualify actual positional-write admission, native attempt and apply loops."""
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
MODULES = ("semanticHash", "semanticFile", "formatExtension", "xmpObservation", "xmpMerge", "semanticDelta")
INPUTS = tuple("src/" + name + suffix for name in MODULES for suffix in (".mli", ".ml")) + (
    "src/semanticHash_stubs.c", "src/semanticFile_stubs.c",
    "tests/positional_write/fixture.c", "tests/positional_write/test.ml",
    "tests/positional_write/run.py", "tests/positional_write/README.md")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def replace_once(source, old, new):
    if source.count(old) != 1:
        raise AssertionError("private mutation source anchor changed: " + repr(old))
    return source.replace(old, new)


def mutate(source, mode):
    operation = "ssize_t written = pwrite(fd, buffer, (size_t)count, native_offset);"
    if mode == "fixed":
        return source
    if mode == "seek-write":
        return replace_once(source, operation,
            "ssize_t written = lseek(fd, native_offset, SEEK_SET) < 0 ? -1 :\n"
            "    write(fd, buffer, (size_t)count);")
    if mode == "missing-append-guard":
        return replace_once(source, "else if (flags & O_APPEND) error = EINVAL;",
                            "else if (0) error = EINVAL;")
    if mode == "heap-pointer":
        source = replace_once(source,
            "if (count) memcpy(buffer, String_val(data) + first, (size_t)count);",
            "if (count) memcpy(buffer, String_val(data) + first, (size_t)count);\n"
            "  const void *borrowed_pointer = String_val(data) + first;")
        return replace_once(source, operation,
            "ssize_t written = pwrite(fd, borrowed_pointer, (size_t)count, native_offset);")
    if mode == "forward-bad-progress":
        return replace_once(source,
            "if (written < -1 || written > count || (written == -1 && !error))",
            "if (written == -1 && !error)")
    if mode == "forced-ml-backend":
        return replace_once(source, "CAMLreturn(Val_true);", "CAMLreturn(Val_false);")
    raise AssertionError(mode)


def execute(command, *, work, env, log, timeout=90):
    start = time.monotonic()
    with log.open("w") as stream:
        result = subprocess.run(command, cwd=work, env=env, stdout=stream,
                                stderr=subprocess.STDOUT, timeout=timeout)
    rendered = log.read_text()
    if result.returncode:
        print(rendered, end="", flush=True)
    elif rendered.strip():
        print(rendered.strip().splitlines()[-1], flush=True)
    return {"argv": command, "cwd": str(work), "exit_code": result.returncode,
            "elapsed_seconds": time.monotonic() - start,
            "log": str(log), "log_sha256": sha(log)}


def inventory(directory):
    entries = {}
    for path in sorted(directory.rglob("*")):
        observed = path.lstat()
        entry = {"device":observed.st_dev,"inode":observed.st_ino,
                 "mode":observed.st_mode,"links":observed.st_nlink,
                 "size":observed.st_size,"mtime_ns":observed.st_mtime_ns,
                 "ctime_ns":observed.st_ctime_ns}
        if stat.S_ISREG(observed.st_mode):
            entry["kind"] = "regular"
            if observed.st_size <= 1048576:
                entry["sha256"] = sha(path)
            else:
                # The >2GiB sparse offset control never hashes its whole hole.
                fd = os.open(path,os.O_RDONLY)
                try:
                    samples = {}
                    for address in (0,max(0,observed.st_size-64)):
                        os.lseek(fd,address,os.SEEK_SET)
                        samples[str(address)] = os.read(fd,64).hex()
                finally:
                    os.close(fd)
                entry["bounded_samples"] = samples
                entry["scope"] = "large synthetic sparse file: exact size/inode plus bounded endpoint samples; not whole-file digest"
        elif stat.S_ISLNK(observed.st_mode):
            entry["kind"] = "symlink"; entry["target"] = os.readlink(path)
        elif stat.S_ISDIR(observed.st_mode):
            entry["kind"] = "directory"
        entries[str(path.relative_to(directory))] = entry
    return entries


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ocamlopt", required=True)
    parser.add_argument("--receipt", type=Path)
    parser.add_argument("--fixed-only", action="store_true")
    parser.add_argument("--case", default="all")
    args = parser.parse_args()
    if sys.platform != "darwin":
        parser.error("this fixture currently requires macOS; production POSIX code and Windows fallback have separate platform scope")
    compiler = shutil.which(args.ocamlopt)
    if compiler is None:
        parser.error("native compiler unavailable")
    env = os.environ.copy()
    for name in ("OCAMLLIB", "OCAMLPATH", "CAML_LD_LIBRARY_PATH", "OCAMLRUNPARAM"):
        env.pop(name, None)
    version = subprocess.check_output([compiler, "-version"], env=env, text=True).strip()
    config = subprocess.check_output([compiler, "-config"], env=env, text=True)
    native_compiler = subprocess.check_output(["/usr/bin/xcrun", "--find", "clang"], env=env, text=True).strip()
    native_version = subprocess.check_output([native_compiler, "--version"], env=env, text=True)
    library = Path(subprocess.check_output([compiler, "-where"], env=env, text=True).strip())
    original = {name: (ROOT / name).read_bytes() for name in INPUTS}
    source = original["src/semanticFile_stubs.c"].decode()
    body = source.split("CAMLprim value unison_semantic_pwrite(", 1)[1]
    released = body.split("caml_enter_blocking_section_no_pending();", 1)[1].split("caml_acquire_runtime_system();", 1)[0]
    for forbidden in ("String_val", "Int64_val", "Long_val", "caml_alloc", "caml_unix_error", "caml_invalid_argument", "caml_callback"):
        if forbidden in released:
            raise AssertionError("OCaml heap/runtime operation while released: " + forbidden)
    assert "unsigned char buffer[UNISON_SEMANTIC_WRITE_MAX]" in body
    assert body.index("memcpy(buffer, String_val(data)") < body.index("caml_enter_blocking_section_no_pending();")
    work = Path(tempfile.mkdtemp(prefix="unison-positional-write-", dir="/private/tmp"))
    print("Retained private artifacts", work, "Compiler", version, flush=True)
    receipt = {"schema": "unison-positional-write-direct-qualification/1",
        "compiler": compiler, "compiler_version": version, "compiler_sha256": sha(Path(compiler)),
        "compiler_config": config, "platform": sys.platform,
        "native_compiler":native_compiler, "native_compiler_sha256":sha(Path(native_compiler)),
        "native_compiler_version":native_version,
        "build_environment":{key:env.get(key) for key in ("SDKROOT","MACOSX_DEPLOYMENT_TARGET","CC","CFLAGS")},
        "sources": {name: hashlib.sha256(data).hexdigest() for name,data in original.items()},
        "artifacts": str(work), "runs": [],
        "source_guards": "bounded native stack copy before runtime release; no OCaml heap/runtime use in released body",
        "counter_scope": "fcntl/fstat through new native admission stub only; excludes existing ML/Unix proof queries",
        "scope": "synthetic disposable files only; no Photo, Adobe, Lightroom, catalog/cache/publisher or production volume access"}
    test = original["tests/positional_write/test.ml"].decode()
    if "val with_async_exns" in (library / "sys.mli").read_text():
        test = test.replace("let with_async_exns f = f ()",
                            "let with_async_exns = Sys.with_async_exns")
    modes = ("fixed",) if args.fixed_only else ("fixed", "forward-bad-progress", "forced-ml-backend", "seek-write", "missing-append-guard", "heap-pointer")
    for mode in modes:
        build = work / mode; build.mkdir()
        for name in INPUTS:
            if name.startswith("src/"):
                (build / Path(name).name).write_bytes(original[name])
        (build / "semanticFile_stubs.c").write_text(mutate(source, mode))
        (build / "fixture.c").write_bytes(original["tests/positional_write/fixture.c"])
        (build / "test.ml").write_text(test)
        commands = []
        for name in ("semanticHash_stubs.c", "fixture.c"):
            command = [compiler, "-I", "+unix", "-ccopt", "-Wall", "-ccopt", "-Wextra", "-c", name]
            result = execute(command, work=build, env=env, log=build / (name + ".compile.log"))
            commands.append(result)
            if result["exit_code"]:
                raise AssertionError("native fixture failed compilation")
        for name in MODULES:
            for suffix in (".mli", ".ml"):
                command = [compiler, "-I", "+unix", "-c", name + suffix]
                result = execute(command, work=build, env=env, log=build / (name + suffix + ".compile.log"))
                commands.append(result)
                if result["exit_code"]:
                    raise AssertionError("actual production module failed compilation")
        command = [compiler, "-I", "+unix", "unix.cmxa", "semanticHash_stubs.o", "fixture.o",
                   *[name + ".cmx" for name in MODULES], "test.ml", "-o", "positional-test"]
        result = execute(command, work=build, env=env, log=build / "link.log")
        commands.append(result)
        if result["exit_code"]:
            raise AssertionError("native fixture failed link")
        cases = [args.case] if mode == "fixed" else {
            "forward-bad-progress":["ml-overcount","ml-negative"],
            "forced-ml-backend":["fallback-interior-and-bounds","fallback-materialize","fallback-unchanged"],
            "seek-write":["direct-offset"],
            "missing-append-guard":["append-rejected","loop-unchanged-append-rejected"],
            "heap-pointer":["snapshot-copy"]}[mode]
        executions = []
        for case in cases:
            files = build / ("files-" + case); files.mkdir()
            command = [str(build / "positional-test"), str(files), case]
            result = execute(command, work=build, env=env, log=build / (case + ".run.log"))
            executions.append(result)
            rendered = Path(result["log"]).read_text()
            if mode in ("fixed", "forward-bad-progress", "forced-ml-backend"):
                if result["exit_code"]:
                    raise AssertionError("direct native/production-loop controls failed")
                match = re.search(r"All (\d+) positional-write cases passed; (\d+) assertions", rendered)
                if not match:
                    raise AssertionError("native controls did not finish")
                result["cases"] = int(match[1]); result["assertions"] = int(match[2])
                if mode == "forward-bad-progress":
                    result["scope"] = "unchanged production ML guard; private native count validation bypassed to inject impossible progress"
                elif mode == "forced-ml-backend":
                    result["scope"] = "production ML seek/write branch on POSIX host through privately forced false native preparation; not Windows ABI/runtime qualification"
            else:
                expected = {
                    "direct-offset":"positional write changed caller offset",
                    "append-rejected":"append writer was admitted",
                    "loop-unchanged-append-rejected":"expected Invalid argument at semantic writer flags",
                    "snapshot-copy":"released write used borrowed heap pointer"}[case]
                if result["exit_code"] != 2 or expected not in rendered:
                    raise AssertionError("private negative missed its designated actual defect")
                result["detected_assertion"] = expected
            manifest = build / (case + ".inventory.json")
            manifest.write_text(json.dumps(inventory(files),indent=2) + "\n")
            result["native_artifact_manifest"] = str(manifest)
            result["native_artifact_manifest_sha256"] = sha(manifest)
        pins = {}
        for path in sorted(build.iterdir()):
            if path.is_file() and path.suffix in (".c",".ml",".mli",".o",".cmx"):
                pins[path.name] = sha(path)
        receipt["runs"].append({"mode":mode, "commands":commands, "executions":executions,
            "build_files":pins, "binary":str(build / "positional-test"),
            "binary_sha256":sha(build / "positional-test")})
    receipt["terminal"] = "passed"
    target = args.receipt or work / "qualification.json"
    target.write_text(json.dumps(receipt,indent=2) + "\n")
    print("Qualification receipt", target, flush=True)


if __name__ == "__main__":
    main()
