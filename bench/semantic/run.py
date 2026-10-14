#!/usr/bin/env python3
"""Cached-file SHA worker microbenchmark; never builds in the source checkout."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import statistics
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
SOURCES = [
    "src/lwt/lwt.mli", "src/lwt/lwt.ml", "src/lwt/pqueue.mli", "src/lwt/pqueue.ml",
    "src/lwt/generic/lwt_unix_impl.ml", "src/lwt/lwt_unix.mli", "src/lwt/lwt_unix.ml",
    "src/borrowedWork.mli", "src/borrowedWork.ml",
    "src/helperSupervisor_stubs.c", "src/helperSupervisor.mli", "src/helperSupervisor.ml",
    "src/ioAdmission.mli", "src/ioAdmission.ml",
    "src/semanticHash_stubs.c", "src/semanticHash.mli", "src/semanticHash.ml",
    "src/semanticFile_stubs.c", "src/semanticFile.mli", "src/semanticFile.ml",
    "src/formatRecognition.mli", "src/formatRecognition.ml",
    "src/formatExtension.mli", "src/formatExtension.ml",
    "src/xmpObservation.mli", "src/xmpObservation.ml",
    "src/dngSemantic.mli", "src/dngSemantic.ml",
    "src/semanticDelta.mli", "src/semanticDelta.ml",
    "src/semanticWorkers.mli", "src/semanticWorkers.ml",
    "bench/semantic/clock_stubs.c", "bench/semantic/hash_bench.ml",
]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--compiler", action="append", required=True, metavar="LABEL=OCAMLOPT")
    parser.add_argument("--workers", default="1,2,4,8,36")
    parser.add_argument("--file-mib", type=int, choices=(32, 64), default=64)
    parser.add_argument("--jobs", type=int, default=72)
    parser.add_argument("--repetitions", type=int, default=5)
    parser.add_argument("--warmups", type=int, default=1)
    parser.add_argument("--build-only", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    workers = [int(n) for n in args.workers.split(",")]
    if not workers or min(workers) < 1 or min(args.jobs, args.repetitions, args.warmups) < 1:
        parser.error("all counts must be positive")
    compilers = {}
    for item in args.compiler:
        label, compiler = item.split("=", 1)
        if not label or label in compilers or not label.replace("-", "").replace("_", "").isalnum():
            parser.error("compiler labels must be unique alphanumeric identifiers")
        resolved = shutil.which(compiler)
        if resolved is None:
            parser.error("compiler executable unavailable")
        compilers[label] = str(Path(resolved).absolute())
    env = os.environ.copy()
    for name in ("OCAMLLIB", "OCAMLPATH", "CAML_LD_LIBRARY_PATH", "OCAMLRUNPARAM"):
        env.pop(name, None)
    source_bytes = {name: (ROOT / name).read_bytes() for name in SOURCES}
    result = {
        "schema": "unison-cached-sha-workers-v1",
        "complete": False,
        "created_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "host": {"system": platform.system(), "release": platform.release(),
                 "machine": platform.machine(), "logical_cpus": os.cpu_count()},
        "parameters": {"file_mib": args.file_mib, "jobs": args.jobs, "workers": workers,
                       "warmups_per_configuration": args.warmups, "measured_repetitions": args.repetitions},
        "clock": {"wall": "CLOCK_MONOTONIC", "cpu": "CLOCK_PROCESS_CPUTIME_ID"},
        "hash_backend": "CommonCrypto" if platform.system() == "Darwin" else "portable OCaml",
        "scope": "Cached synthetic file, complete worker digest path; not production sync or Adobe validation.",
        "compiler_flags": ["-I", "+unix"],
        "source_sha256": {name: hashlib.sha256(data).hexdigest() for name, data in source_bytes.items()},
        "compilers": {}, "samples": [], "summary": [],
    }
    if platform.system() == "Darwin":
        for key in ("hw.physicalcpu", "hw.memsize"):
            query = subprocess.run(["sysctl", "-n", key], text=True, capture_output=True)
            result["host"][key] = int(query.stdout) if query.returncode == 0 else None
    with tempfile.TemporaryDirectory(prefix="unison-sha-bench-") as temporary:
        tmp = Path(temporary)
        binaries = {}
        for label, compiler in compilers.items():
            build = tmp / label
            build.mkdir()
            for name, data in source_bytes.items():
                (build / Path(name).name).write_bytes(data)
            result["compilers"][label] = {
                "version": subprocess.check_output([compiler, "-version"], env=env, text=True).strip(),
                "executable_sha256": hashlib.sha256(Path(compiler).read_bytes()).hexdigest(),
            }
            with (build / "build.log").open("w+") as log:
                commands = [[compiler, "-I", "+unix", "-c", Path(name).name] for name in SOURCES[:-1]]
                objects = [Path(name).stem + (".o" if name.endswith(".c") else ".cmx")
                           for name in SOURCES[:-1] if name.endswith((".ml", ".c"))]
                commands.append([compiler, "-I", "+unix", "unix.cmxa", *objects,
                                 "hash_bench.ml", "-o", "hash-bench"])
                try:
                    for command in commands:
                        subprocess.run(command, cwd=build, env=env, stdout=log, stderr=log, check=True)
                except subprocess.CalledProcessError:
                    log.seek(0)
                    print(log.read())
                    raise
            binaries[label] = build / "hash-bench"
            print(f"Built {label} ({result['compilers'][label]['version']})", flush=True)
        if args.build_only:
            print("Build-only check passed; no benchmark measurements taken.")
            return
        # One small file, independently checked by hashlib, reused for every job.
        block = bytes((i * 71 + 19) & 255 for i in range(65536))
        digest = hashlib.sha256()
        fixture = tmp / "synthetic.bin"
        with fixture.open("wb") as out:
            for _ in range(args.file_mib * 16):
                out.write(block)
                digest.update(block)
        result["fixture_sha256"] = digest.hexdigest()
        schedule = [(label, n) for n in workers for label in compilers]
        # Warm every configuration. Alternate forward/reverse configuration order
        # across measured rounds; all runs are serial, never overlapping compilers.
        for phase, rounds in (("warmup", args.warmups), ("measured", args.repetitions)):
            for repetition in range(rounds):
                order = schedule if repetition % 2 == 0 else list(reversed(schedule))
                for label, n in order:
                    output = subprocess.check_output([
                        str(binaries[label]), str(fixture), digest.hexdigest(),
                        str(args.file_mib * 1048576), str(n), str(args.jobs)],
                        cwd=tmp, env=env, text=True, timeout=600)
                    sample = json.loads(output)
                    sample.update(compiler=label, workers=n, phase=phase, repetition=repetition + 1)
                    sample["throughput_mib_per_second"] = args.file_mib * args.jobs / sample["wall_seconds"]
                    sample["effective_cpu_cores"] = sample["process_cpu_seconds"] / sample["wall_seconds"]
                    result["samples"].append(sample)
                    print(f"{phase} {repetition + 1}: {label} workers={n} "
                          f"{sample['throughput_mib_per_second']:.1f} MiB/s "
                          f"CPU/wall={sample['effective_cpu_cores']:.2f}", flush=True)
                    args.output.parent.mkdir(parents=True, exist_ok=True)
                    args.output.write_text(json.dumps(result, indent=2) + "\n")
        for label, n in schedule:
            samples = [s for s in result["samples"] if s["compiler"] == label and
                       s["workers"] == n and s["phase"] == "measured"]
            summary = {"compiler": label, "workers": n}
            for key in ("wall_seconds", "process_cpu_seconds", "throughput_mib_per_second", "effective_cpu_cores"):
                values = [s[key] for s in samples]
                summary[key] = {"median": statistics.median(values), "min": min(values), "max": max(values)}
            summary["all_digests_correct"] = all(s["correct_digests"] == args.jobs for s in samples)
            summary["peak_active_workers"] = max(s["peak_active_workers"] for s in samples)
            result["summary"].append(summary)
        result["complete"] = True
        args.output.write_text(json.dumps(result, indent=2) + "\n")


if __name__ == "__main__":
    main()
