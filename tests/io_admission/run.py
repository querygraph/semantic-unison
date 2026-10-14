#!/usr/bin/env python3
"""Qualify I/O scheduling in private builds, including a fairness negative control."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ocamlopt", default="ocamlopt")
    parser.add_argument("--keep", action="store_true")
    parser.add_argument("--receipt", type=Path)
    parser.add_argument("--skip-negative-control", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    sources = [
        "src/lwt/lwt.mli", "src/lwt/lwt.ml", "src/lwt/pqueue.mli", "src/lwt/pqueue.ml",
        "src/lwt/generic/lwt_unix_impl.ml", "src/lwt/lwt_unix.mli", "src/lwt/lwt_unix.ml",
        "src/borrowedWork.mli", "src/borrowedWork.ml",
        "src/helperSupervisor_stubs.c", "src/helperSupervisor.mli", "src/helperSupervisor.ml",
        "src/ioAdmission.mli", "src/ioAdmission.ml",
    ]
    pinned = sources + ["tests/io_admission/test.ml", "tests/io_admission/run.py"]
    build = Path(tempfile.mkdtemp(prefix="unison-io-admission-"))
    receipt = {
        "schema": "unison-io-admission-qualification/0",
        "scope": "Owner-loop scheduling, native held-FD device accounting and Adobe-free CPU interop; no physical storage benchmark or SDK/Photo invocation.",
        "ocamlopt": str(Path(shutil.which(args.ocamlopt) or args.ocamlopt).resolve()),
        "compiler_version": subprocess.check_output([args.ocamlopt, "-version"], text=True).strip(),
        "build_directory": str(build),
        "source_sha256": {source: sha256(root / source) for source in pinned},
        "runs": [],
    }
    try:
        for source in sources + ["tests/io_admission/test.ml"]:
            shutil.copyfile(root / source, build / Path(source).name)
        objects = [Path(source).stem + (".o" if source.endswith(".c") else ".cmx")
                   for source in sources if source.endswith((".ml", ".c"))]

        def qualify(label):
            for source in sources:
                subprocess.run([args.ocamlopt, "-I", "+unix", "-c", Path(source).name],
                               cwd=build, check=True)
            executable = build / f"io-admission-{label}"
            subprocess.run([args.ocamlopt, "-I", "+unix", "unix.cmxa", *objects,
                            "test.ml", "-o", executable.name], cwd=build, check=True)
            result = subprocess.run([str(executable)], cwd=build, text=True,
                                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=30)
            log = build / f"{label}.log"
            log.write_text(result.stdout)
            receipt["runs"].append({
                "label": label, "exit_code": result.returncode,
                "binary": str(executable), "binary_sha256": sha256(executable),
                "log": str(log), "log_sha256": sha256(log), "output": result.stdout,
            })
            print(result.stdout, end="", flush=True)
            return result

        result = qualify("current")
        if result.returncode != 0:
            raise RuntimeError("current I/O admission suite failed")
        if not args.skip_negative_control:
            source = build / "ioAdmission.ml"
            text = source.read_text()
            before = "if not t.scheduled && not (conflicts blocked devices) && fits t devices then"
            after = "if not t.scheduled && fits t devices then"
            if text.count(before) != 1:
                raise RuntimeError("fairness negative-control anchor changed")
            source.write_text(text.replace(before, after))
            result = qualify("conflict-fifo-removed")
            if result.returncode == 0 or "conflicting request bypassed older multi-device waiter" not in result.stdout:
                raise RuntimeError("fairness negative control was not detected by the intended assertion")
            receipt["runs"][-1]["expected_rejection"] = True
            receipt["runs"][-1]["mutation"] = "Remove older conflicting-request barrier from immediate admission only."
        receipt["passed"] = True
        receipt["current_sources_still_match"] = all(
            sha256(root / source) == digest for source, digest in receipt["source_sha256"].items())
        if not receipt["current_sources_still_match"]:
            raise RuntimeError("source changed during qualification")
        if args.receipt:
            args.receipt.write_text(json.dumps(receipt, indent=2) + "\n")
        print(f"Qualified I/O admission; build {build}; compiler {receipt['compiler_version']}")
    finally:
        if not args.keep:
            shutil.rmtree(build)


if __name__ == "__main__":
    main()
