#!/usr/bin/env python3
"""Synthetic, exact-byte end-to-end Unison sync measurements, without Adobe."""
import argparse
from contextlib import ExitStack
import datetime
import hashlib
import json
import os
from pathlib import Path
import platform
import plistlib
import re
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
import zlib

from fixtures import create, edit, equal_files, sha256, validate_dimensions
from workloads import KINDS as WORKLOADS, layout as workload_layout, recipe as workload_recipe
from workload_fixtures import create as create_workload, edit as edit_workload
import partitions
import artifact_pins
import properties as property_controls
from invocation_journal import Journal
from measure import CapturedStream, run
from ownership import OwnedGroup
from read_stats import parse as primary_reader_counters
from phase_stats import parse as semantic_phase_counters
from worker_config import WORKER_CHOICES, parse_workers, endpoint_bound, worker_options

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
MODES = ("ordinary", "receiver-clone", "semantic", "source-clone")
SDE = re.compile(
    r"Remote semantic clone wrote (\d+) logical metadata bytes in (\d+) write calls "
    r"\((\d+) payload bytes; (\d+)-byte comparison windows; ([^)]+)\)")
PRESERVED = re.compile(r"(?<!Local )Receiver clone preserved (\d+) logical bytes")


def selected_property_flags():
    # Uarg.Bool does not consume a separate "true" argument. Inline values
    # work for BOOL, BOOLDEF and INT and cannot become anonymous roots.
    return ['-rsrc=true', '-xattrs=true', '-perms=0o777']


def executable(value):
    path = Path(value).expanduser().resolve()
    if not path.is_file() or not os.access(path, os.X_OK):
        raise argparse.ArgumentTypeError("executable unavailable: " + str(path))
    return path


def pairs(items, parser):
    values = {}
    for item in items:
        label, separator, path = item.partition("=")
        if not separator or not label or not label.replace("-", "").replace("_", "").isalnum():
            parser.error("use unique LABEL=/absolute/path/to/executable")
        if label in values:
            parser.error("duplicate executable label")
        values[label] = executable(path)
    return values


def binary_info(path):
    result = {"path": str(path), "sha256": sha256(path),
            "version": subprocess.check_output([str(path), "-version"], text=True).strip(),
            "build_log_sha256": sha256(path.parent.parent / "build.log")
            if (path.parent.parent / "build.log").is_file() else None}
    snapshot = path.parent.parent
    result["snapshot_source_manifest"] = None
    if path.parent.name == "src" and (snapshot / "src/Makefile").is_file():
        inputs = [item for item in (snapshot / "src").rglob("*")
                  if item.is_file() and (item.suffix in (".ml", ".mli", ".c", ".h") or item.name.endswith(".ox.mli.in"))]
        inputs += [snapshot / relative for relative in
                   ("src/Makefile", "src/Makefile.OCaml", "dune-project", "INSTALL.md")
                   if (snapshot / relative).is_file()]
        result["snapshot_source_manifest"] = {
            str(item.relative_to(snapshot)): sha256(item) for item in sorted(inputs)}
        # Associate this historical binary with its qualified source receipt,
        # never with the possibly changing checkout used to launch this runner.
        known = ROOT / "tests/qualification/semantic-observation-20261013.json"
        if known.is_file():
            proof = json.loads(known.read_text())
            # Read the actual selected snapshot bytes for the previously
            # enumerated package inputs plus any newly added source files.
            # The old receipt supplies path coverage, not current digests.
            package_names = set(proof.get("source_manifest", {}))
            package_names.update(str(item.relative_to(snapshot)) for item in inputs
                                 if item.name != "projectInfo.ml")
            result["snapshot_package_manifest"] = {
                name: sha256(snapshot / name) for name in sorted(package_names)
                if (snapshot / name).is_file()}
            if any(record["binary_sha256"] == result["sha256"] for record in proof.get("make", {}).values()):
                for name, digest in proof["source_manifest"].items():
                    assert sha256(snapshot / name) == digest, "qualified binary snapshot source changed"
                result["qualified_snapshot"] = {"receipt": str(known), "receipt_sha256": sha256(known),
                    "production_inputs_verified": len(proof["source_manifest"]),
                    "source_manifest": proof["source_manifest"]}
        current = ROOT / "tests/checked_worker/qualification.json"
        if current.is_file():
            proof=json.loads(current.read_text())
            if any(record["binarySha256"]==result["sha256"] for record in proof.get("makeBuilds",{}).values()):
                manifest=proof["frozenFinalMakeInputs"]
                for name,digest in manifest.items():
                    assert sha256(snapshot/name)==digest,"checked build source changed"
                result["qualified_snapshot"]={"receipt":str(current),"receipt_sha256":sha256(current),
                    "production_inputs_verified":len(manifest),"source_manifest":manifest,
                    "scope":"actual checked worker build; native/resource/performance limits remain separate"}
    return result


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".new")
    with temporary.open('w') as stream:
        stream.write(json.dumps(value, indent=2) + "\n")
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(path)
    directory = os.open(path.parent, os.O_RDONLY)
    try:
        os.fsync(directory)
    finally:
        os.close(directory)


def diagnostic_text(outcome):
    # Streams are separate observations: never fuse an unterminated stdout tail
    # with a stderr/server record, or manufacture a record across two streams.
    return "\n".join(outcome[name] for name in ('stdout','stderr','supervisor_output'))


def internal_counters(log, mode, files, size, *, primary_reads=False, phase_timings=False, expect_semantic=True):
    if type(expect_semantic) is not bool:
        raise ValueError("typed semantic expectation required")
    semantic = [tuple(int(value) for value in match[:4]) + (match[4],)
                for match in SDE.findall(log)]
    preserved = [int(value) for value in PRESERVED.findall(log)]
    clone_started = log.count("Using immutable receiver clone basis")
    source_clones = log.count("Local source clone completed before semantic planning")
    if semantic:
        logical_writes = sum(match[0] for match in semantic)
        model = logical_writes
        model_basis = "production SemanticDelta successful returned logical write bytes"
    elif preserved:
        logical_writes = None
        model = files * size - sum(preserved)
        model_basis = "complete output extents minus same-offset inherited clone bytes"
    elif source_clones == files:
        logical_writes = None
        model = 0
        model_basis = "whole source clone selected; no user data rewrite measured"
    else:
        logical_writes = None
        model = files * size
        model_basis = "full output extent; syscall/physical-write accounting unavailable"
    if mode == "semantic" and expect_semantic and (len(semantic) != files or preserved or clone_started or source_clones):
        raise AssertionError("semantic mode failed to select exactly one SDE update per file")
    if mode == "semantic" and not expect_semantic and (semantic or source_clones
            or clone_started != len(preserved) or clone_started > files):
        raise AssertionError("fallback workload has inconsistent semantic/receiver path evidence")
    if mode == "receiver-clone" and (len(preserved) != files or clone_started != files or semantic or source_clones):
        raise AssertionError("receiver-clone mode did not qualify every receiver basis")
    if mode in ("ordinary", "reference") and (semantic or clone_started or source_clones or preserved):
        raise AssertionError("ordinary/reference unexpectedly selected new clone/semantic mode")
    if mode == "source-clone" and (source_clones != files or semantic or preserved or clone_started):
        raise AssertionError("same-volume local source cloning was not selected")
    if not 0 <= model <= files * size:
        raise AssertionError("logical output model outside expected size")
    return {"semantic_updates": len(semantic), "expected_semantic_update": mode == "semantic" and expect_semantic, "receiver_clone_starts": clone_started,
            "receiver_clone_completed": len(preserved), "source_clone_completed": source_clones,
            "same_offset_inherited_bytes": sum(preserved),
            "semantic_logical_write_bytes": logical_writes,
            "semantic_write_attempts": sum(match[1] for match in semantic) if semantic else None,
            "semantic_payload_bytes": sum(match[2] for match in semantic) if semantic else None,
            "semantic_comparison_windows": sorted({match[3] for match in semantic}),
            "semantic_profiles": sorted({match[4] for match in semantic}),
            "materialization_non_inherited_logical_bytes_model": model,
            "materialization_model_basis": model_basis,
            "receiver_clone_declines": log.count("Receiver clone declined:"),
            "semantic_fallback_events": log.count("Remote semantic fallback:"),
            "primary_reader_reads": primary_reader_counters(log, required=mode == "semantic" and expect_semantic)
              if primary_reads else None,
            "semantic_phase_observations": semantic_phase_counters(log, required_workers=mode == "semantic" and expect_semantic)
              if phase_timings else None,
            "application_read_bytes": None, "hash_parse_verify_commit_seconds": None,
            "physical_storage_write_bytes": None, "queue_descriptor_peaks": None}


class InvocationFailure(RuntimeError):
    def __init__(self, outcome):
        self.outcome = outcome
        super().__init__("sync invocation failed: " + json.dumps(outcome))


def measure_invocation(command, environment, timeout, proxy_script, use_proxy=True,
                       strict_group_settlement=False):
    """Own both groups through cancellation, cleanup and exact leader reap."""
    start = time.monotonic()
    supervisor = capture = None
    measured = None
    settled = None
    fault = None
    try:
        if use_proxy:
            supervisor = OwnedGroup([sys.executable, str(proxy_script)],
                strict_group_settlement=strict_group_settlement, env=environment,
                stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            capture = CapturedStream(supervisor.process.stdout)
            deadline = time.monotonic() + 5
            socket_path = Path(environment["UNISON_SYNC_BENCH_SOCKET"])
            while not socket_path.exists():
                if supervisor.terminal() or time.monotonic() >= deadline:
                    raise RuntimeError("loopback supervisor failed to listen")
                time.sleep(0.005)
        measured = run(command, environment, timeout, strict_group_settlement=strict_group_settlement)
        if measured["returncode"] or measured["timed_out"] or measured["capture_truncated"]:
            fault = "native client failed, timed out or exceeded captured output limit"
    except BaseException as error:
        fault = repr(error)
        # A settled direct client may have been interrupted before run()
        # returned. Keep its real receipt rather than replacing it with only
        # the exception text. Missing evidence stays missing.
        measured = getattr(error, "owned_process_outcome", None)
    finally:
        if supervisor is not None:
            settled, _ = supervisor.finish(timeout=0 if fault else 5, cancel_reason=fault)
        captured = capture.finish() if capture else {"bytes": 0, "truncated": False, "text": ""}
    outcome = measured if measured is not None else {"command": command, "client_fault": fault}
    outcome["native_client_lifetime_seconds"] = outcome.get("wall_seconds")
    outcome["wall_seconds"] = time.monotonic() - start
    outcome["supervisor_cleanup"] = settled
    outcome["supervisor_output"] = captured["text"]
    outcome["supervisor_capture_bytes"] = captured["bytes"]
    outcome["supervisor_capture_truncated"] = captured["truncated"]
    receipt_path = Path(environment["UNISON_SYNC_BENCH_PROXY_RECEIPT"])
    outcome["proxy"] = json.loads(receipt_path.read_text()) if receipt_path.is_file() else None
    if use_proxy:
        proxy = outcome["proxy"]
        if (not proxy or proxy["fault"] or proxy["server_returncode"] or proxy["pump_errors"] or
                not proxy["input_pump_joined"] or not proxy["server_cleanup"]["reaped"] or
                not settled["reaped"] or settled["returncode"] or settled["cancel_reason"] or
                captured["truncated"]):
            fault = fault or "loopback native/supervisor outcome is unqualified"
    if fault:
        outcome["fault"] = fault
        raise InvocationFailure(outcome)
    return outcome


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", action="append", default=[], metavar="LABEL=BINARY")
    parser.add_argument("--reference", action="append", default=[], metavar="LABEL=BINARY",
                        help="unmodified original/upstream binary; no new preferences")
    parser.add_argument("--compiler", action="append", default=[], metavar="LABEL=OCAMLOPT")
    parser.add_argument("--modes", default="ordinary,receiver-clone,semantic")
    parser.add_argument("--workers", default="1", help="comma-separated selections, including auto with an explicit endpoint budget")
    parser.add_argument("--endpoint-cpu-budget", type=int,
                        help="explicit semanticcpubudget ceiling1..36 on each current endpoint; required for auto")
    parser.add_argument("--partition", type=int,
                        help="one explicit0..5 stock/Ox worker partition; never starts other parts")
    parser.add_argument("--loopback-cpu-credits",type=int,
                        help="Bound the sum of configured semantic/helper CPU budgets across same-host endpoints; not an OS CPU cap")
    parser.add_argument("--orchestration-cpu-credits", type=int, default=0,
                        help="Additional owner/hash/transport credits inside the loopback bound; not OS isolation")
    parser.add_argument("--file-mib", type=int, default=32)
    parser.add_argument("--files", type=int, default=2)
    parser.add_argument("--packet-bytes", type=int, default=8192)
    parser.add_argument("--workload", choices=WORKLOADS, default="fixed-xmp",
                        help="versioned generated workload; nonfixed cases expect exact fallback, not SDE success")
    parser.add_argument("--warmups", type=int, default=1)
    parser.add_argument("--repetitions", type=int, default=5)
    parser.add_argument("--timeout", type=float, default=180)
    parser.add_argument("--qualification", action="store_true",
                        help="fixed finite smoke: two 2 MiB files, workers 1/2, no warmup, one sample")
    parser.add_argument("--shared-qualification", action="store_true",
                        help="finite shared smoke: two 2 MiB files, workers1/2, six to eight credits including two owner credits")
    parser.add_argument("--layout-only-controls", action="store_true",
                        help="finite generated opaque-private exact-layout receiving matrix")
    parser.add_argument("--property-removal-controls", action="store_true",
                        help="Darwin shared functional fixtures: old fork/xattr removal and retained readers")
    parser.add_argument("--prepare-only", action="store_true", help="metadata/arguments only; no sync")
    parser.add_argument("--measure-primary-reads", action="store_true",
                        help="opt-in worker primary-reader counters; not total application/disk reads")
    parser.add_argument("--measure-semantic-phases", action="store_true",
                        help="opt-in inclusive worker/native-publication observations, not total commit time")
    parser.add_argument("--background-note", default="ordinary host activity uncontrolled")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--expected-binary-sha256", action="append", default=[],
                        help="optional exact label=SHA256 set, verified before any executable call")
    parser.add_argument("--expected-compiler-sha256", action="append", default=[],
                        help="optional exact compiler label=SHA256 set, verified before version calls")
    args = parser.parse_args()
    binaries, references = pairs(args.binary, parser), pairs(args.reference, parser)
    compilers = pairs(args.compiler, parser)
    if not binaries and not references:
        parser.error("at least one --binary or --reference required")
    if binaries.keys() & references.keys() or not compilers.keys() <= binaries.keys():
        parser.error("reference/current labels must differ; compiler labels must match current binaries")
    modes = args.modes.split(",")
    try:
        workers = parse_workers(args.workers)
    except ValueError as error:
        parser.error(str(error))
    if args.qualification and args.shared_qualification:
        parser.error("choose one qualification profile")
    finite_qualification = args.qualification or args.shared_qualification
    if args.workload != "fixed-xmp" and (finite_qualification or args.partition is not None
            or args.layout_only_controls or args.property_removal_controls):
        parser.error("new workloads require a separate explicit matrix, not frozen qualification/partition controls")
    if ('auto' in workers or args.endpoint_cpu_budget is not None) and (finite_qualification or args.partition is not None):
        parser.error("automatic/ceiling selections require a separate versioned matrix, not fixed qualification or legacy partitions")
    if args.endpoint_cpu_budget is not None and (references or args.loopback_cpu_credits is None):
        parser.error("endpoint CPU budget requires current endpoints and explicit loopback credits")
    if finite_qualification:
        args.file_mib, args.files, args.warmups, args.repetitions = 2, 2, 0, 1
        workers = [1, 2, 3] if args.shared_qualification else [1, 2]
    if args.layout_only_controls and (not args.shared_qualification or args.property_removal_controls):
        parser.error("layout-only controls require a separate finite shared qualification matrix")
    if args.property_removal_controls and (not args.shared_qualification or platform.system() != "Darwin"):
        parser.error("property-removal controls require the Darwin shared qualification matrix")
    if args.shared_qualification and (args.loopback_cpu_credits != 8 or args.orchestration_cpu_credits != 2):
        parser.error("shared qualification requires eight credits including two owner credits")
    try:
        worker_bounds = [endpoint_bound(value, args.endpoint_cpu_budget) for value in workers]
    except ValueError as error:
        parser.error(str(error))
    if not modes or any(mode not in MODES for mode in modes) or len(set(modes)) != len(modes):
        parser.error("invalid/duplicate mode")
    endpoint_count=2 if any(mode!="source-clone" for mode in modes) else 1
    if not 0 <= args.orchestration_cpu_credits <= 18:
        parser.error("orchestration credits must be0..18")
    if args.orchestration_cpu_credits and args.loopback_cpu_credits is None:
        parser.error("orchestration credits require an explicit loopback CPU bound")
    if args.loopback_cpu_credits is not None:
        if references:parser.error("reference CPU budgets cannot be qualified by the loopback credit bound")
        if (args.loopback_cpu_credits<=0 or
                endpoint_count*max(worker_bounds)+args.orchestration_cpu_credits>args.loopback_cpu_credits):
            parser.error("endpoint plus orchestration CPU credits exceed loopback budget")
    if not (args.warmups >= 0 and 1 <= args.repetitions <= 50 and args.timeout > 0):
        parser.error("fixture/count bounds exceeded")
    try:
        size = validate_dimensions(args.file_mib, args.files, args.packet_bytes)
        largest_fixture_size = size
        if args.workload != "fixed-xmp":
            changed = workload_recipe(workload_layout(size, args.packet_bytes), args.workload)
            largest_fixture_size = max(size, changed.target_size)
            if changed.target_size * args.files > 8*1024**3:
                raise ValueError("grown generated working set exceeds8GiB")
    except ValueError as error:
        parser.error(str(error))
    if not finite_qualification and (args.warmups < 1 or args.repetitions < 5):
        parser.error("performance run requires at least one warmup and five measured repetitions")
    configurations = [(label, mode, worker) for label in binaries for mode in modes for worker in workers]
    configurations += [(label, "reference", None) for label in references]
    if args.partition is not None:
        if finite_qualification:
            parser.error("performance partitions cannot use qualification counts")
        if modes != list(partitions.MODES) or workers != list(partitions.WORKERS):
            parser.error("partition mode/worker order must match the canonical matrix")
        try:
            configurations = partitions.select(configurations, args.partition)
        except ValueError as error:
            parser.error(str(error))
    environment = os.environ.copy()
    for key in ("OCAMLLIB", "OCAMLPATH", "CAML_LD_LIBRARY_PATH", "OCAMLRUNPARAM"):
        environment.pop(key, None)
    try:
        admitted_binary_pins = artifact_pins.verify({**binaries, **references},
                                                   artifact_pins.parse(args.expected_binary_sha256))
        admitted_compiler_pins = artifact_pins.verify(compilers,
                                                     artifact_pins.parse(args.expected_compiler_sha256))
    except (ValueError, OSError) as error:
        parser.error(str(error))
    metadata = {label: binary_info(path) for label, path in {**binaries, **references}.items()}
    host = {"system": platform.system(), "release": platform.release(),
            "machine": platform.machine(), "logical_cpus": os.cpu_count()}
    if platform.system() == "Darwin":
        for key in ("hw.physicalcpu", "hw.memsize"):
            query = subprocess.run(["sysctl", "-n", key], capture_output=True, text=True)
            host[key] = int(query.stdout) if query.returncode == 0 else None
    scripts = {path.name: sha256(path) for path in HERE.glob("*.py")}
    result = {"schema": "unison-synthetic-sync/0", "complete": False,
              "purpose": ("finite shared-harness qualification" if args.shared_qualification else
                          "finite harness qualification" if args.qualification else "warm-cache performance"),
              "created_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
              "repository_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
              "runner_sha256": scripts, "host": host, "binaries": metadata,
              "admitted_binary_sha256": admitted_binary_pins,
              "admitted_compiler_sha256": admitted_compiler_pins,
              "compilers": {label: {"path": str(path),
                    "version": subprocess.check_output([str(path), "-version"], text=True).strip(),
                    "configuration": subprocess.check_output([str(path), "-config"], text=True)}
                    for label, path in compilers.items()},
              "parameters": {"modes": modes, "workers": workers, "file_mib": args.file_mib,
                    "files": args.files, "packet_bytes": args.packet_bytes, "workload": args.workload,
                    "maximum_source_or_target_file_bytes": largest_fixture_size,
                    "warmups": args.warmups, "repetitions": args.repetitions,
                    "timeout_seconds": args.timeout, "background_note": args.background_note,
                    "measure_primary_reads": args.measure_primary_reads,
                    "measure_semantic_phases": args.measure_semantic_phases,
                    "property_removal_controls": args.property_removal_controls,
                    "layout_only_controls": args.layout_only_controls,
                    "loopback_cpu_credit_bound":args.loopback_cpu_credits,
                    "maximum_configured_endpoint_credit_sum":endpoint_count*max(worker_bounds),
                    "orchestration_cpu_credits":args.orchestration_cpu_credits,
                    "maximum_declared_cpu_credit_sum":endpoint_count*max(worker_bounds)+args.orchestration_cpu_credits},
              "cache_state": "warm/uncontrolled: fixture generation, seed sync and independent hashing precede every update; no cache flush",
              "transport": "same-host Python loopback SSH replacement through private Unix socket and raw pipes; no encryption or physical network",
              "rss_units": "bytes on Darwin; KiB on Linux; native OS units elsewhere",
              "resource_scope": "per-process wait4 receipts; CPU may include reaped descendants; never sum overlapping main/server reports; maxrss is not aggregate tree RSS",
              "unmeasured": ["application read bytes", "complete hash/parse/verify/commit accounting (optional inclusive traces are partial)",
                    "aggregate process-tree peak RSS", "descriptor/queue peaks", "physical storage writes",
                    "range/extent sharing", "cross-volume or non-APFS behavior", "cold cache",
                    "real SSH/network behavior", "Adobe validation or photographic rendering"],
              "samples": [], "summary": []}
    if args.endpoint_cpu_budget is not None:
        result['parameters']['endpoint_cpu_budget_ceiling'] = args.endpoint_cpu_budget
        result['parameters']['endpoint_cpu_permit_upper_bounds'] = [
            dict(selection=selection, upper_bound=bound) for selection, bound in zip(workers, worker_bounds)]
        result['parameters']['automatic_cpu_scope'] = (
            'auto is semanticworkers=0 with explicit semanticcpubudget; these are conservative '
            'permit upper bounds, not measured domain/OS-thread counts or a machine token grant')
    if args.partition is not None:
        result['partition'] = partitions.specification(args.partition)
    save(args.output, result)
    if args.prepare_only:
        result["preparation_complete"] = True
        save(args.output, result)
        print("Prepared metadata only; no sync or measurement executed.")
        return
    with tempfile.TemporaryDirectory(prefix="unison-sync-bench-", dir="/private/tmp") as temporary, ExitStack() as reader_owners:
        work = Path(temporary)
        capacity=os.statvfs(work)
        available=capacity.f_bavail*capacity.f_frsize
        required=4*largest_fixture_size*args.files+64*1048576
        if args.property_removal_controls:
            required += size * args.files * len(configurations)
        result["fixture_capacity"]={"available_bytes_before_run":available,
            "required_bytes":required,"model":"four largest source/target corpus extents plus64MiB headroom, one row at a time; not APFS allocation proof"}
        if available<required:raise RuntimeError("insufficient private fixture capacity")
        for name in ("proxy.py", "measure.py", "launcher.py", "ownership.py"):
            shutil.copy2(HERE / name, work / name)
        (work / "launcher.py").chmod(0o700)
        result["temporary_directory"] = str(work)
        result["filesystem"] = {"source_device": work.stat().st_dev,
                                "receiver_device": work.stat().st_dev}
        if platform.system() == "Darwin":
            volume_path = work
            # diskutil accepts mount points, but not every directory beneath
            # the Data volume's firmlinks. Probe only this synthetic fixture's
            # own device, never a Photo volume or payload.
            for candidate in (Path("/System/Volumes/Data"), Path("/")):
                if candidate.is_dir() and candidate.stat().st_dev == work.stat().st_dev:
                    volume_path = candidate
                    break
            query = subprocess.run(["diskutil", "info", "-plist", str(volume_path)], capture_output=True)
            if query.returncode == 0:
                volume = plistlib.loads(query.stdout)
                result["filesystem"].update({key: volume.get(key) for key in
                    ("FilesystemType", "DeviceIdentifier", "VolumeUUID", "TotalSize", "Internal")})
        save(args.output, result)

        journal = Journal(result, lambda: save(args.output, result))

        def invoke(label, binary, mode, worker, directory, stage):
            assert sha256(binary) == metadata[label]["sha256"], "binary changed"
            flags = ["-debug", "copy", "-debug", "semantic"] if mode != "reference" else []
            if args.measure_primary_reads and mode != "reference":
                flags += ["-debug", "semantic-reads"]
            if args.measure_semantic_phases and mode != "reference":
                flags += ["-debug", "semantic-timings"]
            if worker is not None:
                flags += ["-clone", "off" if mode == "ordinary" else "auto",
                          *worker_options(worker, args.endpoint_cpu_budget)]
                if mode == "semantic":
                    flags += ["-semanticdng"]
            if args.property_removal_controls:
                flags += selected_property_flags()
            command = [str(binary), str(directory / "left")]
            receipt_path = directory / (stage + "-proxy.json")
            socket_path = directory / (stage + ".sock")
            env = dict(environment, UNISON=str(directory / "state"),
                       UNISON_SYNC_BENCH_BINARY=str(binary),
                       UNISON_SYNC_BENCH_SERVER_FLAGS=json.dumps(flags),
                       UNISON_SYNC_BENCH_PROXY_RECEIPT=str(receipt_path),
                       UNISON_SYNC_BENCH_SOCKET=str(socket_path),
                       UNISON_SYNC_BENCH_DEADLINE_SECONDS=str(args.timeout + 5))
            if mode == "source-clone":
                command += [str(directory / "right")]
            else:
                command += ["ssh://localhost/" + str(directory / "right"),
                            "-sshcmd", str(work / "launcher.py"), "-servercmd", str(binary)]
            command += ["-batch", "-auto", "-fastcheck", "false", "-times", *flags]
            journal.begin({'label': label, 'mode': mode, 'workers': worker,
                           'directory': str(directory), 'stage': stage}, command)
            try:
                outcome = measure_invocation(command, env, args.timeout, work / "proxy.py",
                                          use_proxy=mode != "source-clone",
                                          # Every benchmark call owns its groups, including timed runs
                                          # which deliberately do not set shared_qualification.
                                          strict_group_settlement=True)
            except InvocationFailure as error:
                result["failed_invocation"] = error.outcome
                journal.finish(error.outcome)
                raise
            journal.finish(outcome)
            return outcome

        try:
            for phase, count in (("warmup", args.warmups), ("measured", args.repetitions)):
                for repetition in range(1, count + 1):
                    order = configurations if repetition % 2 else list(reversed(configurations))
                    for number, (label, mode, worker) in enumerate(order):
                        for name, digest in scripts.items():
                            assert sha256(HERE / name) == digest, "runner changed during run"
                        directory = work / f"{phase}-{repetition}-{number}"
                        for name in ("left", "right", "state", "basis"):
                            (directory / name).mkdir(parents=True)
                        start = time.monotonic()
                        fixtures = [(create(directory / "left" / f"image-{index:04d}.dng", size,
                                           args.packet_bytes, index, layout_only=args.layout_only_controls)
                                     if args.workload == "fixed-xmp" else
                                     create_workload(directory / "left" / f"image-{index:04d}.dng", size,
                                                     args.packet_bytes, index)) for index in range(args.files)]
                        if args.property_removal_controls:
                            for item in fixtures:
                                property_controls.initialise(directory / "left" / item["name"])
                        preparation_seconds = time.monotonic() - start
                        binary = binaries.get(label, references.get(label))
                        seed = invoke(label, binary, mode, worker, directory, "seed")
                        old_readers = {}
                        for item in fixtures:
                            name = item["name"]
                            assert sha256(directory / "right" / name) == item["before_sha256"]
                            os.link(directory / "right" / name, directory / "basis" / name)
                            if args.property_removal_controls:
                                handle = reader_owners.enter_context((directory / "right" / name).open('rb'))
                                observed = property_controls.old_reader_snapshot(handle.fileno())
                                assert observed['sha256'] == item['before_sha256']
                                old_readers[name] = (handle, observed)
                            item["expected_after_sha256"] = (edit(directory / "left" / name, item)
                                if args.workload == "fixed-xmp" else
                                edit_workload(directory / "left" / name, item, args.workload))
                            if item["expected_after_sha256"] == item["before_sha256"]:
                                raise AssertionError("declared change workload unexpectedly produced a no-op")
                            if args.property_removal_controls:
                                property_controls.remove_source(directory / "left" / name)
                        sample = {"label": label, "mode": mode, "workers": worker,
                                  "phase": phase, "repetition": repetition,
                                  "fixture_preparation_seconds": preparation_seconds,
                                  "fixtures": fixtures, "seed_sync": seed}
                        result["samples"].append(sample)
                        save(args.output, result)
                        measured = invoke(label, binary, mode, worker, directory, "update")
                        sample["update_sync"] = measured
                        log = diagnostic_text(measured)
                        sample["counters"] = internal_counters(log, mode, args.files, fixtures[0].get("after_size_bytes", size),
                            expect_semantic=args.workload == "fixed-xmp",
                            primary_reads=args.measure_primary_reads and mode != "reference",
                            phase_timings=args.measure_semantic_phases and mode != "reference")
                        if args.layout_only_controls and mode=="semantic":
                            assert sample['counters']['semantic_profiles']==['org.firstpair.dng-layout/0'], \
                                "opaque private fixture did not select exact layout-only profile"
                        verification_start = time.monotonic()
                        inodes = {}
                        selected_property_epochs = {}
                        for item in fixtures:
                            name = item["name"]
                            for replica in ("left", "right"):
                                assert sha256(directory / replica / name) == item["expected_after_sha256"]
                            assert equal_files(directory / "left" / name, directory / "right" / name)
                            assert sha256(directory / "basis" / name) == item["before_sha256"]
                            inodes[name] = (directory / "right" / name).stat().st_ino
                            if args.property_removal_controls:
                                property_controls.verify_removed(directory / "left" / name)
                                selected_property_epochs[name] = property_controls.noop_snapshot(directory / "right" / name)
                                handle, observed = old_readers[name]
                                assert property_controls.old_reader_snapshot(handle.fileno()) == observed
                        sample["verification_seconds"] = time.monotonic() - verification_start
                        sample["noop_sync"] = invoke(label, binary, mode, worker, directory, "noop")
                        for item in fixtures:
                            name = item["name"]
                            assert (directory / "right" / name).stat().st_ino == inodes[name]
                            assert sha256(directory / "right" / name) == item["expected_after_sha256"]
                            assert sha256(directory / "basis" / name) == item["before_sha256"]
                        if args.property_removal_controls:
                            for item in fixtures:
                                name = item['name']
                                assert property_controls.noop_snapshot(directory / "right" / name) == selected_property_epochs[name]
                                handle, observed = old_readers[name]
                                assert property_controls.old_reader_snapshot(handle.fileno()) == observed
                            sample.update(source_selected_properties_removed=True,
                                          retained_old_readers_preserved=True, noop_properties_preserved=True,
                                          old_reader_snapshots={name:value[1] for name,value in old_readers.items()},
                                          noop_property_epochs=selected_property_epochs)
                        expected_names = {item["name"] for item in fixtures}
                        assert {path.name for path in (directory / "right").iterdir()} == expected_names
                        assert {path.name for path in (directory / "left").iterdir()} == expected_names
                        sample["exact_result_and_unchanged_basis"] = True
                        sample["noop_preserved_receiver_inode"] = True
                        sample["staging_cleaned"] = True
                        if "fixture_compressibility_probe" not in result:
                            with (directory / "left" / fixtures[0]["name"]).open("rb") as stream:
                                probe=stream.read(1048576)
                            result["fixture_compressibility_probe"] = {
                                "bytes": len(probe), "zlib_level": 6,
                                "compressed_bytes": len(zlib.compress(probe, 6)),
                                "scope": "first MiB of first fixture only; generation mostly seeded pseudorandom bytes"}
                        cleanup_start=time.monotonic()
                        shutil.rmtree(directory)
                        sample["fixture_cleanup_seconds"]=time.monotonic()-cleanup_start
                        sample["private_fixture_removed"]=not directory.exists()
                        assert sample["private_fixture_removed"]
                        save(args.output, result)
                        print(f"{phase} {repetition} {label}/{mode} workers={worker}: "
                              f"{measured['wall_seconds']:.3f}s, exact result/basis/no-op", flush=True)
            for label, mode, worker in configurations:
                samples = [sample for sample in result["samples"]
                    if (sample["label"], sample["mode"], sample["workers"], sample["phase"]) ==
                       (label, mode, worker, "measured")]
                values = [sample["update_sync"]["wall_seconds"] for sample in samples]
                result["summary"].append({"label": label, "mode": mode, "workers": worker,
                    "samples": len(values), "wall_seconds": {"median": statistics.median(values),
                    "minimum": min(values), "maximum": max(values)},
                    "all_results_exact": all(sample["exact_result_and_unchanged_basis"] for sample in samples)})
            result["complete"] = True
            save(args.output, result)
        except BaseException as error:
            result["failure"] = repr(error)
            save(args.output, result)
            raise


if __name__ == "__main__":
    main()
