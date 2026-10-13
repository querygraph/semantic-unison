#!/usr/bin/env python3
"""Compile actual SDK adapter only; execute an Adobe-free synthetic scheduler.

No SDK driver, fixture writer, Adobe library, Lightroom, or photograph is run.
"""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import tempfile

parser = argparse.ArgumentParser()
parser.add_argument("--sdk-root", type=Path)
parser.add_argument("--dependency-build-dir", type=Path,
                    help="existing build's generated JXL headers, read only")
parser.add_argument("--output-dir", type=Path)
args = parser.parse_args()
repo = Path(__file__).resolve().parents[2]
adapter = repo / "tools/adobe-validator"
out = args.output_dir or Path(tempfile.mkdtemp(prefix="unison-area-source-"))
out = out.resolve()
out.mkdir(parents=True, exist_ok=True)
records = []

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def run(command, name, expected=0):
    completed = subprocess.run([str(x) for x in command], stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT, text=True, timeout=45)
    log = out / (name + ".log")
    log.write_text(completed.stdout)
    records.append({"name": name, "command": [str(x) for x in command],
                    "exit": completed.returncode, "expected_exit": expected,
                    "log": str(log), "log_sha256": sha(log)})
    if completed.returncode != expected:
        raise RuntimeError(name + " failed: " + completed.stdout[-8000:])
    return completed.stdout

sources = [adapter / p for p in ("driver.cpp", "build.py", "area_scheduler.h", "area_task_host.h")]
sources += [adapter / p for p in ("README.md", "AREA-TASK-SOURCE-REVIEW.md")]
sources += [Path(__file__).resolve(), Path(__file__).with_name("test.cpp")]
sources += [Path(__file__).with_name("README.md")]
try:
    # Parse build instructions without executing their SDK build operations.
    compile((adapter / "build.py").read_text(), str(adapter / "build.py"), "exec")
    common = ["clang++", "-std=c++17", "-pthread", "-Wall", "-Wextra", "-Werror", "-I", adapter]
    synthetic = out / "synthetic-area-scheduler"
    run([*common, "-O2", Path(__file__).with_name("test.cpp"), "-o", synthetic], "synthetic-compile")
    result = run([synthetic], "synthetic-run")
    # A separate sanitizer executable still contains only original Unison code.
    sanitized = out / "synthetic-area-scheduler-sanitized"
    run([*common, "-O1", "-g", "-fsanitize=address,undefined", "-fno-omit-frame-pointer",
         Path(__file__).with_name("test.cpp"), "-o", sanitized], "synthetic-sanitizer-compile")
    run([sanitized], "synthetic-sanitizer-run")
    negative = out / "negative-include"
    negative.mkdir(exist_ok=True)
    original = (adapter / "area_scheduler.h").read_text()
    needle = "return execution_depth ? 1 : requested;"
    assert original.count(needle) == 1
    (negative / "area_scheduler.h").write_text(original.replace(needle, "return requested;"))
    negative_binary = out / "synthetic-negative-uncapped-nesting"
    run([*common[:1], "-std=c++17", "-pthread", "-O2", "-I", negative,
         Path(__file__).with_name("test.cpp"), "-o", negative_binary], "negative-compile")
    negative_result = run([negative_binary], "negative-run", expected=1)
    assert "Start nested codec allowance" in negative_result

    sdk_inputs = {}
    if args.sdk_root:
        if not args.dependency_build_dir:
            parser.error("--sdk-root compile check requires --dependency-build-dir")
        sdk = args.sdk_root.resolve()
        dep = args.dependency_build_dir.resolve()
        if "1.7.1 2724" not in (sdk / "DNG_ReadMe.txt").read_text():
            raise RuntimeError("requires actual SDK 1.7.1 build 2724")
        xmp = sdk / "xmp/toolkit"
        includes = [sdk / "dng_sdk/source", sdk / "libjpeg", xmp, xmp / "public/include",
                    xmp / "third-party/expat/public/lib", xmp / "XMPCore/resource/mac",
                    sdk / "libjxl/libjxl/lib/include", dep / "jxl/lib/include",
                    sdk / "libjxl/client_projects/include"]
        flags = ["-O2", "-DNDEBUG=1", "-DMAC_ENV=1", "-DXMP_StaticBuild=1", "-DXMP_64=1",
                 "-DENABLE_CPP_DOM_MODEL=0", "-DXML_STATIC=1", "-DHAVE_EXPAT_CONFIG_H=1",
                 "-DqDNGValidate=1", "-DqDNGValidateTarget=1", "-DqDNGReportErrors=1",
                 "-DqDNGXMPFiles=0", "-DqDNGXMPDocOps=0", "-DqDNGUseLibJPEG=1",
                 "-DqMacOS=1", "-DqWinOS=0", "-DqDNGUseStdInt=1", "-DMacintosh=1",
                 "-std=c++17", "-funsigned-char", "-fno-common", "-Wall", "-Wextra"]
        flags += [part for p in includes for part in ("-I", str(p))]
        for mode in ("single", "area-unqualified"):
            extra = ["-DUNISON_EXPERIMENTAL_AREA_TASK_HOST=1"] if mode != "single" else []
            run(["clang++", *flags, *extra, "-c", adapter / "driver.cpp",
                 "-o", out / ("driver-" + mode + ".o")], "sdk-headers-compile-" + mode)
        for name in ("dng_host.h", "dng_host.cpp", "dng_area_task.h", "dng_area_task.cpp",
                     "dng_abort_sniffer.h", "dng_abort_sniffer.cpp", "dng_jxl.cpp",
                     "dng_read_image.cpp", "dng_sdk_limits.h", "dng_tile_iterator.cpp"):
            path = sdk / "dng_sdk/source" / name
            sdk_inputs[str(path)] = sha(path)
        runner = sdk / "libjxl/libjxl/lib/threads/resizable_parallel_runner.cc"
        sdk_inputs[str(runner)] = sha(runner)
    manifest = {"status": "passed source compilation and Adobe-free synthetic controls",
                "scope": "source-only; no SDK loading/linking/execution, codec execution, Photo access or benchmarks",
                "sdk_runtime_qualified": False, "multithread_production_enabled": False,
                "platform": platform.platform(), "output_directory": str(out),
                "source_sha256": {str(p.relative_to(repo)): sha(p) for p in sources},
                "sdk_inputs_sha256": sdk_inputs, "records": records,
                "retained_artifacts_sha256": {str(p): sha(p) for p in out.iterdir()
                    if p.is_file() and p.name != "SOURCE-QUALIFICATION.json"},
                "synthetic_result": result.strip()}
    (out / "SOURCE-QUALIFICATION.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))
except Exception:
    (out / "FAILED-RECORDS.json").write_text(json.dumps(records, indent=2) + "\n")
    raise
