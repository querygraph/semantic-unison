#!/usr/bin/env python3
"""Link real SemanticRuntime/preferences from a compiler-matched private Make build."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--build", type=Path, required=True)
    parser.add_argument("--ocamlopt", required=True)
    parser.add_argument("--keep", action="store_true")
    parser.add_argument("--receipt", type=Path)
    parser.add_argument("--skip-negative-control", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    build = args.build.resolve() / "src"
    if not (build / "semanticRuntime.cmx").is_file():
        raise RuntimeError("an isolated complete native Make snapshot is required")
    makefile = (build / "Makefile.OCaml").read_text()

    def objects(name):
        match = re.search(r"^" + name + r" = (.*?)(?=\n\n)", makefile, re.M | re.S)
        if match is None:
            raise RuntimeError(f"Make object declaration missing: {name}")
        value = match.group(1).replace("\\\n", " ").replace("$(SYSTEM)", "generic")
        value = value.replace("$(WINOBJS)", "").replace("$(WINCOBJS)", "")
        return value.replace("$(OBJ_EXT)", ".o").replace(".cmo", ".cmx").split()

    modules = objects("OCAMLOBJS")
    modules = modules[:modules.index("semanticRuntime.cmx") + 1]
    native = objects("COBJS")
    pins = ["src/ioAdmission.ml", "src/ioAdmission.mli", "src/semanticRuntime.ml",
            "src/semanticRuntime.mli", "src/semanticWorkers.ml", "src/semanticMailbox.mli", "src/semanticMailbox.ml", "src/semanticWorkers.mli",
            "src/ubase/prefs.ml", "src/ubase/prefs.mli", "src/semanticFormats.ml",
            "tests/io_admission/runtime.ml", "tests/io_admission/runtime_run.py"]
    for source in pins:
        if source.startswith("src/") and sha256(root / source) != sha256(build / source[4:]):
            raise RuntimeError(f"snapshot source differs from checkout: {source}")
    work = Path(tempfile.mkdtemp(prefix="unison-io-runtime-"))
    receipt = {
        "schema": "unison-actual-io-runtime-qualification/0",
        "scope": "Actual linked endpoint preference and held-candidate lifecycle; synthetic files only, no helper/Adobe/Photo invocation or storage benchmark.",
        "compiler": str(Path(shutil.which(args.ocamlopt) or args.ocamlopt).resolve()),
        "compiler_version": subprocess.check_output([args.ocamlopt, "-version"], text=True).strip(),
        "build_snapshot": str(build.parent), "artifact_directory": str(work),
        "source_sha256": {source: sha256(root / source) for source in pins},
        "linked_objects_sha256": {source: sha256(build / source) for source in modules + native},
        "runs": [],
    }
    includes = [work, build, build / "ubase", build / "system", build / "system/generic",
                build / "lwt", build / "lwt/generic"]
    flags = [flag for path in includes for flag in ("-I", str(path))] + ["-I", "+unix", "-I", "+str"]
    source = work / "runtime.ml"
    shutil.copyfile(root / "tests/io_admission/runtime.ml", source)
    module_paths = [str(build / module) for module in modules]

    def link(label, override=None):
        paths = module_paths if override is None else module_paths[:-1] + [str(override)]
        binary = work / label
        subprocess.run([args.ocamlopt, *flags, "unix.cmxa", "str.cmxa", *paths,
                        str(source), *(str(build / obj) for obj in native), "-o", str(binary)],
                       cwd=work, check=True)
        return binary

    def execute(binary, scenario, *, injected=False, negative=False):
        directory = work / (binary.name + "-" + scenario)
        directory.mkdir()
        env = dict(os.environ, UNISON=str(directory / "state"), UNISON_IO_RUNTIME_CASE=scenario)
        if injected:
            env["UNISON_IO_ALLOCATE_FAIL"] = "1"
        else:
            env.pop("UNISON_IO_ALLOCATE_FAIL", None)
        arguments = [str(binary)] + (["-semanticvolumejobs", "2"] if scenario == "cli" else [])
        result = subprocess.run(arguments, cwd=directory, env=env, text=True,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=20)
        log = directory / "result.log"
        log.write_text(result.stdout)
        record = {"scenario": scenario, "binary": str(binary), "binary_sha256": sha256(binary),
                  "exit_code": result.returncode, "log": str(log), "log_sha256": sha256(log),
                  "output": result.stdout}
        if negative:
            if result.returncode == 0 or "first ownership-closure allocation leaked candidate descriptor" not in result.stdout:
                raise RuntimeError("removed-ownership-guard negative control was not detected by intended assertion")
            record["expected_rejection"] = True
        elif result.returncode != 0:
            print(result.stdout, end="", flush=True)
            raise RuntimeError(f"actual runtime scenario failed: {scenario}")
        receipt["runs"].append(record)
        print(result.stdout, end="", flush=True)

    try:
        binary = link("runtime-current")
        for scenario in ["default", "endpoint", "cli", "negative", "candidate"]:
            execute(binary, scenario)
        # Recompile only a PRIVATE copy of SemanticRuntime with unchanged MLI.
        # This does not load or execute any proprietary code.
        runtime_source = (build / "semanticRuntime.ml").read_text()
        before = "  try\n    let close () = if !owned then begin"
        after = ("  try\n    if Sys.getenv_opt \"UNISON_IO_ALLOCATE_FAIL\" = Some \"1\" then raise Out_of_memory;\n"
                 "    let close () = if !owned then begin")
        if runtime_source.count(before) != 1:
            raise RuntimeError("private allocation-injection anchor changed")
        private_ml = work / "semanticRuntime.ml"
        shutil.copyfile(build / "semanticRuntime.mli", work / "semanticRuntime.mli")
        subprocess.run([args.ocamlopt, *flags, "-c", "semanticRuntime.mli"], cwd=work, check=True)
        injected = runtime_source.replace(before, after)

        def private_runtime(text, label):
            private_ml.write_text(text)
            receipt.setdefault("private_mutations", {})[label] = sha256(private_ml)
            subprocess.run([args.ocamlopt, *flags, "-c", "semanticRuntime.ml"], cwd=work, check=True)
            return link(label, work / "semanticRuntime.cmx")

        fault_binary = private_runtime(injected, "runtime-allocation-injection")
        execute(fault_binary, "fault", injected=True)
        if not args.skip_negative_control:
            guard = ("    if !owned then begin owned := false;\n"
                     "      try Unix.close fd with Unix.Unix_error _ -> () end;\n"
                     "    raise e")
            if injected.count(guard) != 1:
                raise RuntimeError("private ownership-guard removal anchor changed")
            negative = private_runtime(injected.replace(guard, "    raise e"), "runtime-ownership-guard-removed")
            execute(negative, "fault", injected=True, negative=True)
        receipt["passed"] = True
        receipt["current_sources_still_match"] = all(
            sha256(root / source) == digest for source, digest in receipt["source_sha256"].items())
        if not receipt["current_sources_still_match"]:
            raise RuntimeError("source changed during runtime qualification")
        if args.receipt:
            args.receipt.write_text(json.dumps(receipt, indent=2) + "\n")
        print(f"Qualified actual endpoint/runtime lifecycle; artifacts {work}")
    finally:
        if not args.keep:
            shutil.rmtree(work)


if __name__ == "__main__":
    main()
