#!/usr/bin/env python3
"""Qualify actual receiving-companion warning delivery on private synthetic data."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
PARENT = "31980e3d286f5b7a408613faf7a983dc37d1f017"
CASES = ("warn-error", "warn-pass", "require-error", "off", "warn-inspection-error",
         "warn-mutation", "warn-active-cancel", "warn-before-delivery-cancel",
         "warn-delivery-cancel", "warn-delivery-abort", "warn-printer-error")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def once(source, anchor, replacement):
    if source.count(anchor) != 1:
        raise RuntimeError("private observation anchor must occur exactly once: " + anchor)
    return source.replace(anchor, replacement)


def objects(makefile, name):
    match = re.search(r"^" + name + r" = (.*?)(?=\n\n)", makefile, re.M | re.S)
    if match is None:
        raise RuntimeError("complete Make module graph unavailable: " + name)
    return (match.group(1).replace("\\\n", " ").replace("$(SYSTEM)", "generic")
            .replace("$(WINOBJS)", "").replace("$(WINCOBJS)", "")
            .replace("$(OBJ_EXT)", ".o").replace(".cmo", ".cmx").split())


def instrument_worker(source):
    source = once(source, "let dispatch t =\n", "let dispatch t =\n"
                  "  Probe.enter_dispatch ();\n"
                  "  Fun.protect ~finally:Probe.leave_dispatch (fun () ->\n")
    source = once(source, "  !first_error\nlet rec pump", "  !first_error)\nlet rec pump")
    return once(source, "  (match observer_error with\n", "  Probe.rearmed ();\n"
                "  (match observer_error with\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build", type=Path, required=True)
    parser.add_argument("--ocamlopt", required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--freeze", type=Path)
    parser.add_argument("--keep-work", action="store_true", help="artifacts are always retained")
    parser.add_argument("--fixed-only", action="store_true")
    parser.add_argument("--negative-only", action="store_true")
    parser.add_argument("--skip-cli", action="store_true")
    args = parser.parse_args()
    if args.fixed_only and args.negative_only:
        parser.error("select one participant mode")
    build = args.build.resolve() / "src"
    compiler = Path(shutil.which(args.ocamlopt) or args.ocamlopt).resolve()
    makefile = (build / "Makefile.OCaml").read_text()
    all_modules = objects(makefile, "OCAMLOBJS")
    # Runtime now follows the validator registry in the real link graph.
    modules = all_modules[:max(all_modules.index("dngCandidateValidation.cmx"),
                              all_modules.index("semanticRuntime.cmx")) + 1]
    native = objects(makefile, "COBJS")
    graph = list(dict.fromkeys(
        [str(Path(module).with_suffix(ext)) for module in modules for ext in (".ml", ".mli", ".ox.mli.in")
         if (build / Path(module).with_suffix(ext)).exists()] +
        [str(Path(obj).with_suffix(".c")) for obj in native] +
        ["Makefile.OCaml", "semantic_mode_filter.ml", "ubase/util.mli", "ubase/trace.mli"]))
    for name in modules + native + [str(Path(m).with_suffix(".cmi")) for m in modules]:
        if not (build / name).is_file():
            raise RuntimeError("complete compiler-matched native graph required: " + name)
    frozen = json.loads(args.freeze.read_text()) if args.freeze else None
    freeze_pins = frozen.get("sources_sha256", frozen.get("sources", {})) if frozen else {}
    if frozen and not freeze_pins:
        raise RuntimeError("freeze has no source SHA-256 map")
    source_pins, generated = {}, {}
    for name in graph:
        path = build / name
        if not path.is_file():
            raise RuntimeError("snapshot graph source missing: " + name)
        if name == "ubase/projectInfo.ml":
            generated[name] = sha(path)
            continue
        workspace = ROOT / "src" / name
        if workspace.is_file():
            if sha(path) != sha(workspace):
                raise RuntimeError("workspace/snapshot graph differs: " + name)
            if frozen and "src/" + name in freeze_pins and sha(path) != freeze_pins["src/" + name]:
                raise RuntimeError("snapshot graph differs from declared freeze: " + name)
            source_pins[name] = sha(path)
        else:
            if name != "ubase/projectInfo.ml":
                raise RuntimeError("unclassified generated graph input: " + name)
            generated[name] = sha(path)
    fixtures = ("run.py", "test.ml", "probe.ml", "helper.ml", "README.md")
    work = Path(tempfile.mkdtemp(prefix="unison-validation-warning-", dir="/private/tmp"))
    environment = os.environ.copy()
    for name in ("OCAMLLIB", "OCAMLPATH", "CAML_LD_LIBRARY_PATH", "OCAMLRUNPARAM"):
        environment.pop(name, None)
    receipt = {"schema": "unison-receiving-validation-warning/0", "success": False,
        "scope": "Actual DngCandidateValidation.select and full compiler-matched legacy-Lwt/core graph; synthetic helper and files; private worker-dispatch observations.",
        "work": str(work), "retained": True, "build_snapshot": str(build.parent),
        "compiler": {"path": str(compiler), "sha256": sha(compiler)},
        "source_pins": source_pins, "generated_snapshot_sources": generated,
        "test_pins": {name: sha(HERE / name) for name in fixtures},
        "input_object_pins": {name: sha(build / name) for name in modules + native},
        "commands": [], "runs": [], "Photo_or_Adobe_access": False,
        "native_UI_execution": False, "performance_claim": False,
        "limits": ["Synthetic protocol receipts do not establish Adobe structural/decode/digest fidelity.",
                   "Standalone controls invoke the actual selected DNG handler directly; receiving selection/publication is exercised separately by complete loopback CLI controls.",
                   "Remote warning behavior is established for actual local exec transport, not SSH networking or native GTK/Cocoa UI.",
                   "Resource ledger settlement is checked; no whole-process FD/RSS ceiling is claimed."]}
    if args.freeze:
        receipt["freeze"] = {"path": str(args.freeze.resolve()), "sha256": sha(args.freeze)}

    def command(argv, directory, label, *, allow_failure=False, env_extra=None, timeout=30):
        log = directory / (label + ".log")
        try:
            result = subprocess.run([str(value) for value in argv], cwd=directory,
                env=dict(environment, **(env_extra or {})), stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, text=True, timeout=timeout)
            log.write_text(result.stdout)
            entry = {"argv": [str(value) for value in argv], "cwd": str(directory),
                "exit": result.returncode, "task_env": env_extra or {},
                "log": str(log), "log_sha256": sha(log)}
            receipt["commands"].append(entry)
            if result.returncode and not allow_failure:
                print(result.stdout, flush=True)
                result.check_returncode()
            return result, entry
        except subprocess.TimeoutExpired as error:
            output = error.stdout or ""
            if isinstance(output, bytes):
                output = output.decode(errors="replace")
            log.write_text(output)
            receipt["commands"].append({"argv": [str(v) for v in argv], "cwd": str(directory),
                "timeout": timeout, "task_env": env_extra or {}, "log": str(log), "log_sha256": sha(log)})
            raise

    try:
        receipt["compiler"]["version"] = command([compiler, "-version"], work, "compiler-version")[0].stdout.strip()
        frozen_dir = work / "frozen-inputs"
        frozen_dir.mkdir()
        for name in graph:
            target = frozen_dir / "src" / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(build / name, target)
        for name in fixtures:
            shutil.copyfile(HERE / name, frozen_dir / name)
        if args.freeze:
            shutil.copyfile(args.freeze, frozen_dir / "SOURCE-FREEZE.json")
        command([compiler, "-I", "+unix", "-I", build, "unix.cmxa",
                 build / "semanticHash.cmx", "helper.ml", build / "semanticHash_stubs.o",
                 "-o", "helper"], frozen_dir, "link-helper")
        helper = frozen_dir / "helper"
        modes = ["fixed"] if args.fixed_only else ["parent-log", "removed-yield"] if args.negative_only else ["parent-log", "removed-yield", "fixed"]
        for mode in modes:
            directory = work / mode
            directory.mkdir()
            # Copy the whole selected linked graph and native inputs, not an
            # ad-hoc module subset with foreign .cmx optimization assumptions.
            copy_names = set(graph + modules + native)
            copy_names.update(str(Path(m).with_suffix(ext)) for m in modules for ext in (".cmi", ".o"))
            for name in sorted(copy_names):
                target = directory / name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(build / name, target)
            shutil.copyfile(frozen_dir / "probe.ml", directory / "probe.ml")
            shutil.copyfile(frozen_dir / "test.ml", directory / "validationWarningTest.ml")
            worker = directory / "semanticWorkers.ml"
            worker.write_text(instrument_worker(worker.read_text()))
            participant = directory / "dngCandidateValidation.ml"
            if mode == "parent-log":
                data = subprocess.check_output(["git", "show", PARENT + ":src/dngCandidateValidation.ml"], cwd=ROOT)
                participant.write_bytes(data)
                receipt["parent_negative"] = {"commit": PARENT, "participant": "src/dngCandidateValidation.ml",
                    "sha256": sha(participant), "scope": "Exact parent companion only; all other modules are current, with common private worker observations. Not a complete parent binary."}
            if mode == "removed-yield":
                participant.write_text(once(participant.read_text(),
                    "BorrowedWork.bind (fun () -> Lwt_unix.yield ()) (fun () ->",
                    "BorrowedWork.bind (fun () -> return ()) (fun () ->"))
                receipt["removed_yield_negative"] = {"participant_sha256": sha(participant),
                    "scope": "Private mutation replaces only the warning's yielded promise with an already-resolved promise; warning/cancellation behavior otherwise current."}
            receipt.setdefault("private_participant_pins", {})[mode] = {
                "semanticWorkers.ml": sha(worker), "dngCandidateValidation.ml": sha(participant)}
            includes = [directory, directory / "ubase", directory / "system", directory / "system/generic",
                        directory / "lwt", directory / "lwt/generic"]
            flags = [arg for path in includes for arg in ("-I", str(path))] + ["-I", "+unix", "-I", "+str"]
            command([compiler, *flags, "-c", "probe.ml"], directory, "compile-probe")
            # The observed worker implementation's imports change. Recompile
            # every native dependent through the actual DNG companion.
            for obj in modules[modules.index("semanticWorkers.cmx"):]:
                stem = Path(obj).with_suffix("")
                mode_flags = []
                if stem.name in ("semanticWorkers", "semanticFormats"):
                    mode_flags = ["-pp", str(build / "semantic_mode_filter") + " " +
                                  receipt["compiler"]["version"]]
                interface = stem.with_suffix(".mli")
                if (directory / interface).exists():
                    command([compiler, *flags, *mode_flags, "-c", interface], directory, "compile-" + str(interface).replace("/", "-"))
                source = stem.with_suffix(".ml")
                command([compiler, *flags, *mode_flags, "-c", source], directory, "compile-" + str(source).replace("/", "-"))
            binary = directory / "warning-test"
            command([compiler, *flags, "unix.cmxa", "str.cmxa", "probe.cmx", *modules,
                "validationWarningTest.ml", *native, "-o", binary], directory, "link")
            for case in CASES if mode == "fixed" else ("warn-error",):
                files = directory / case
                files.mkdir()
                argv = [binary, case, helper] + ([] if mode == "fixed" else ["negative"])
                result, entry = command(argv, files, "test", allow_failure=mode != "fixed",
                    env_extra={"UNISON": str(files / "state")})
                if mode != "fixed":
                    designated = "DESIGNATED " + ("allowed validation finding never reached visible warning channel"
                        if mode == "parent-log" else "warning delivered inside unrearmed worker dispatch")
                    if result.returncode != 2 or designated not in result.stdout:
                        raise RuntimeError("designated warning negative did not fail exact independent oracle: " + mode)
                receipt["runs"].append({"mode": mode, "case": case, "execution": entry,
                    "designated_negative_detected": mode != "fixed"})
                print(result.stdout.strip().splitlines()[-1], flush=True)
        if not args.skip_cli and not args.negative_only:
            cli_binary = build / "unison"
            receipt["cli_binary"] = {"path": str(cli_binary), "sha256": sha(cli_binary)}
            for policy in ("warn", "require", "off"):
                directory = work / ("loopback-" + policy)
                directory.mkdir()
                left, right, client_state, server_state = [directory / name for name in
                    ("left", "right", "client-state", "server-state")]
                for path in (left, right, client_state, server_state):
                    path.mkdir()
                drivers = {}
                for endpoint in ("client", "server"):
                    driver = directory / (endpoint + "-helper")
                    shutil.copyfile(helper, driver)
                    driver.chmod(0o700)
                    Path(str(driver) + ".control").write_text("error")
                    drivers[endpoint] = driver
                def settings(endpoint):
                    driver = drivers[endpoint]
                    return {"adobevalidator": str(driver), "adobevalidatorhash": sha(driver),
                        "adobevalidatorbuild": "validation-warning-synthetic-1", "adobevalidatorthreads": "1",
                        "adobevalidatetimeout": "10", "semanticvolumejobs": "1"}
                (server_state / "endpoint.prf").write_text("".join(
                    key + " = " + value + "\n" for key, value in settings("server").items()))
                launcher = directory / "loopback.py"
                launcher.write_text("#!/usr/bin/python3\nimport os,sys\na=sys.argv[1:]\n"
                    "i=a.index(" + repr(str(cli_binary)) + ")\n"
                    "os.environ['UNISON']=" + repr(str(server_state)) + "\n"
                    "os.execv(a[i],a[i:])\n")
                launcher.chmod(0o700)
                data = b"SYNTHETIC-LOOPBACK-WARNING\x00" + b"q" * 8192
                (left / "image.dng").write_bytes(data)
                argv = [cli_binary, left, "ssh://localhost/" + str(right), "-sshcmd", launcher,
                    "-servercmd", cli_binary, "-batch", "-auto", "-silent", "-log=false",
                    "-fastcheck", "false", "-clone", "off", "-semanticdng=false",
                    "-semanticworkers", "1", "-maxthreads", "1", "-adobevalidate", policy]
                argv += [value for key, value in settings("client").items() for value in ("-" + key, value)]
                result, entry = command(argv, directory, "receive", allow_failure=True,
                    env_extra={"UNISON": str(client_state)}, timeout=45)
                success = policy != "require"
                if (result.returncode == 0) != success:
                    raise RuntimeError("loopback warning policy outcome differs: " + result.stdout)
                warnings = result.stdout.count("Adobe DNG validation warning")
                if warnings != (1 if policy == "warn" else 0):
                    raise RuntimeError("actual remote warning lost/duplicated under silent/log=false: " + result.stdout)
                counts = {endpoint: len(Path(str(driver) + ".calls").read_text().splitlines())
                    if Path(str(driver) + ".calls").exists() else 0 for endpoint, driver in drivers.items()}
                if counts != {"client": 0, "server": 0 if policy == "off" else 1}:
                    raise RuntimeError("loopback receiving endpoint/helper call mismatch: " + repr(counts))
                call_records = []
                if policy != "off":
                    fields = Path(str(drivers["server"]) + ".calls").read_text().strip().split("\t")
                    stage = Path(fields[4])
                    if fields[2] != hashlib.sha256(data).hexdigest() or fields[3] != str(len(data)) or \
                            not stage.is_absolute() or not stage.is_relative_to(right) or stage == right / "image.dng":
                        raise RuntimeError("receiving helper did not independently observe exact private staged bytes")
                    call_records.append({"pid": int(fields[0]), "mode": fields[1], "actual_sha256": fields[2],
                        "actual_size": int(fields[3]), "candidate": str(stage)})
                target = right / "image.dng"
                if success and target.read_bytes() != data or not success and target.exists():
                    raise RuntimeError("actual receiving publication differs from selected warning policy")
                if any(path.name == "unison.log" for path in directory.rglob("*")):
                    raise RuntimeError("logging-disabled control wrote a logfile")
                receipt["runs"].append({"mode": "complete-cli", "case": "loopback-" + policy,
                    "execution": entry, "warnings": warnings, "helper_calls": counts,
                    "independent_helper_records": call_records, "published": success})
                print("PASS loopback-" + policy + " warning_calls=" + str(warnings), flush=True)
        receipt["workspace_sources_still_match"] = all(sha(ROOT / "src" / name) == pin for name, pin in source_pins.items())
        receipt["snapshot_sources_still_match"] = all(sha(build / name) == pin for name, pin in source_pins.items())
        receipt["test_sources_still_match"] = all(sha(HERE / name) == pin for name, pin in receipt["test_pins"].items())
        if not all(receipt[key] for key in ("workspace_sources_still_match", "snapshot_sources_still_match", "test_sources_still_match")):
            raise RuntimeError("production or fixture source changed during warning qualification")
        receipt["success"] = True
    finally:
        receipt["artifacts"] = {str(path.relative_to(work)): {"path": str(path), "bytes": path.stat().st_size, "sha256": sha(path)}
            for path in sorted(work.rglob("*")) if path.is_file()}
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        args.receipt.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
        print("Receipt " + str(args.receipt), flush=True)
        print("Retained artifacts " + str(work), flush=True)


if __name__ == "__main__":
    try:
        main()
    except BaseException as error:
        # A graph/freeze preflight can fail before an artifact owner exists.
        # Preserve that failed trial too, without replacing a richer receipt.
        if "--receipt" in sys.argv:
            target = Path(sys.argv[sys.argv.index("--receipt") + 1])
            if not target.exists():
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(json.dumps({"schema": "unison-receiving-validation-warning/0",
                    "success": False, "stage": "preflight", "argv": sys.argv,
                    "error": repr(error), "Photo_or_Adobe_access": False,
                    "native_UI_execution": False,
                    "test_pins": {name: sha(HERE / name) for name in
                        ("run.py", "test.ml", "probe.ml", "helper.ml", "README.md")}},
                    indent=2) + "\n")
        raise
