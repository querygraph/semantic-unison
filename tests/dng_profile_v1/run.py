#!/usr/bin/env python3
"""Qualify bounded /1 DNG container grammar using independent synthetic bytes."""
import argparse
from datetime import datetime, timezone
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

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "tests/semantic/conformance"))
from reference import Region, inspect, plan, encode_request, encode_envelope
from fixtures import (Layout, PROFILE, PRIMARY, XMP, XMP_LENGTH, SIZE,
                      valid_fixtures, invalid_fixtures)

MODULES = ("semanticHash", "semanticFile", "formatExtension", "xmpObservation", "xmpMerge",
           "dngSemantic", "dngExtended", "semanticDelta")
INPUTS = tuple("src/" + name + suffix for name in MODULES for suffix in (".mli", ".ml")) + (
    "src/semanticHash_stubs.c", "src/semanticHash_evp.h", "src/semanticFile_stubs.c",
    "tests/semantic/conformance/reference.py", "doc/semantic-delta-v0.md",
    "tests/dng_profile_v1/fixtures.py", "tests/dng_profile_v1/test.ml",
    "tests/dng_profile_v1/fs.c", "tests/dng_profile_v1/run.py",
    "tests/dng_profile_v1/README.md", "tests/dng_profile_v1/SDK-SOURCE-NOTES.md")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def sha_file(path):
    return sha(path.read_bytes())


def replace_once(source, old, new):
    if source.count(old) != 1:
        raise AssertionError("private mutation anchor changed: " + repr(old))
    return source.replace(old, new)


def mutate(source, mode):
    if mode == "fixed":
        return source
    if mode == "wrong-CR-base":
        return replace_once(source,
            "else relative base (number directory (at+layout.value_at) layout.number_width)",
            "else relative (if kind = CameraProfile then 0L else base) "
            "(number directory (at+layout.value_at) layout.number_width)")
    if mode == "missing-CR-protection":
        return replace_once(source,
            "end else if bytes > Int64.of_int layout.inline_width then protect value_offset bytes;",
            "end else if bytes > Int64.of_int layout.inline_width && kind <> CameraProfile "
            "then protect value_offset bytes;")
    if mode == "widened-CR-pointer":
        source = replace_once(source, "| CameraProfile -> camera_profile_tag tag",
                              "| CameraProfile -> camera_profile_tag tag || tag = 34665")
        start, stop = source.index("let camera_profile_type"), source.index("let allowed_tag")
        fragment = replace_once(source[start:stop], "| _ -> false",
                                "| 34665 -> typ = 4\n  | _ -> false")
        return source[:start] + fragment + source[stop:]
    raise AssertionError(mode)


def inventory(directory, sparse_paths):
    result = {}
    for path in sorted(directory.rglob("*")):
        observed = path.lstat()
        if stat.S_ISDIR(observed.st_mode):
            result[str(path.relative_to(directory))] = {"kind": "directory"}
            continue
        entry = {"kind": "regular", "size": observed.st_size,
                 "allocated_bytes": observed.st_blocks * 512,
                 "mode": observed.st_mode, "links": observed.st_nlink}
        if str(path) not in sparse_paths:
            entry["sha256"] = sha_file(path)
        else:
            # These >4GiB holes are inspector-only; never hash the whole file.
            samples = {}
            with path.open("rb") as stream:
                for address in (0, 32, 4096, (1 << 32) + 512):
                    if address < observed.st_size:
                        stream.seek(address)
                        samples[str(address)] = stream.read(min(128, observed.st_size - address)).hex()
            entry["bounded_samples"] = samples
            entry["scope"] = "inspector-only sparse offset; exact size/allocation and bounded known-address bytes, no full-file digest"
        result[str(path.relative_to(directory))] = entry
    return result


def sparse_fixture(directory, *, little, high_primary):
    layout = Layout(True, little)
    high = (1 << 32) + 512
    primary, xmp = (high, 4096) if high_primary else (32, high)
    name = ("sparse-primary" if high_primary else "sparse-XMP") + ("-le" if little else "-be")
    packet = b"<fixture>high-offset-not-a-photo</fixture>    "
    path = directory / (name + ".bin")
    packet_path = directory / (name + ".packet")
    packet_path.write_bytes(packet)
    header = (b"II" if little else b"MM") + layout.integer(43, 2)
    header += layout.integer(8, 2) + bytes(2) + layout.integer(primary, 8)
    table = layout.integer(2, 8)
    table += layout.integer(700, 2) + layout.integer(1, 2) + layout.integer(len(packet), 8) + layout.integer(xmp, 8)
    table += layout.integer(50706, 2) + layout.integer(1, 2) + layout.integer(4, 8) + b"\x01\0\0\0" + bytes(4)
    table += bytes(8)
    extents = ((0, header), (primary, table), (xmp, packet))
    with path.open("w+b") as stream:
        for address, data in extents:
            stream.seek(address)
            stream.write(data)
        stream.truncate(max(address + len(data) for address, data in extents))
    observed = path.stat()
    assert observed.st_size > (1 << 32)
    assert observed.st_blocks * 512 < 1048576, "high-offset fixture unexpectedly materialized its hole"
    return ["sparse", name, str(path), str(xmp), str(len(packet)), str(packet_path)], {
        "name": name, "path": str(path), "primary_offset": primary, "xmp_offset": xmp,
        "logical_size": observed.st_size, "allocated_bytes": observed.st_blocks * 512,
        "known_extents": [{"offset": address, "length": len(data), "sha256": sha(data)}
                          for address, data in extents],
        "scope": "real /private/tmp APFS sparse file; public inspector and exact packet read only, no proof/full SHA/SDE/apply"}


def make_cases(directory):
    directory.mkdir()
    commands, metadata, fixture_oracles, sparse_records = [], [], [], []

    def add(fields, scope):
        commands.append("\t".join(map(str, fields)))
        metadata.append({"name": fields[1], "operation": fields[0], "scope": scope})

    for fixture in valid_fixtures():
        base = directory / (fixture.name + ".base")
        base.write_bytes(fixture.data)
        add(["inspect", fixture.name, base, XMP, XMP_LENGTH, str(fixture.old_accepts).lower()],
            "direct and wrapper extent, v0 compatibility, source preservation")
        target_bytes = bytearray(fixture.data)
        for address in (XMP + 300, XMP + 4200, XMP + 8240):
            target_bytes[address] ^= 1
        target_bytes = bytes(target_bytes)
        target = directory / (fixture.name + ".target")
        target.write_bytes(target_bytes)
        nonce = bytes(range(32))
        region = (Region(XMP, XMP_LENGTH),)
        before, after = inspect(fixture.data, PROFILE, region), inspect(target_bytes, PROFILE, region)
        request, envelope = directory / (fixture.name + ".sdr"), directory / (fixture.name + ".sde")
        request.write_bytes(encode_request(nonce, before))
        envelope.write_bytes(encode_envelope(plan(nonce, before, after)))
        add(["golden", fixture.name + "-wire", base, target, request, envelope,
             directory / (fixture.name + ".stage")],
            "independent exact SDR/SDE, peer plan, explicit and registry apply, no-op writes, version binding")
        for index, extent in enumerate(fixture.mutable):
            address = extent["offset"] + extent["length"] - 1
            assert not XMP <= address < XMP + XMP_LENGTH
            changed = bytearray(fixture.data)
            changed[address] ^= 1
            opaque = directory / (fixture.name + f".opaque-{index}")
            opaque.write_bytes(changed)
            add(["opaque", fixture.name + "-" + extent["label"], base, opaque],
                "known protected payload or safe inline value changes remain opaque and ineligible")
        changed = fixture.data[:-1] + bytes([fixture.data[-1] ^ 1])
        opaque = directory / (fixture.name + ".opaque-tail")
        opaque.write_bytes(changed)
        add(["opaque", fixture.name + "-unreferenced-tail", base, opaque],
            "complete complement proof protects bytes outside any declared TIFF extent too")
        fixture_oracles.append({"name": fixture.name, "base": str(base),
            "base_sha256": sha(fixture.data), "xmp": {"offset": XMP, "length": XMP_LENGTH},
            "protected_ranges": fixture.protected, "safe_mutable_ranges": fixture.mutable,
            "oracle": "producer placement records, independent of locator output",
            "request_sha256": sha_file(request), "envelope_sha256": sha_file(envelope)})
    for name, data, reason in invalid_fixtures():
        path = directory / (name + ".invalid")
        path.write_bytes(data)
        add(["reject", name, path, reason],
            "bounded unsupported/malformed graph rejection before semantic proof or writes")
    for little in (True, False):
        for high_primary in (False, True):
            fields, record = sparse_fixture(directory, little=little, high_primary=high_primary)
            add(fields, "inspector-only actual sparse >4GiB LargeFile read")
            sparse_records.append(record)
    names = [item["name"] for item in metadata]
    assert len(names) == len(set(names)), "duplicate case identifiers"
    return commands, metadata, fixture_oracles, sparse_records


def execute(argv, directory, env, log, timeout=120):
    started = time.monotonic()
    with log.open("w") as stream:
        result = subprocess.run(argv, cwd=directory, env=env,
                                stdout=stream, stderr=subprocess.STDOUT, timeout=timeout)
    output = log.read_text()
    if result.returncode:
        print(output[-12000:], end="", flush=True)
    elif output.strip():
        print(output.strip().splitlines()[-1], flush=True)
    return {"argv": argv, "cwd": str(directory), "exit_code": result.returncode,
            "elapsed_seconds": time.monotonic() - started,
            "log": str(log), "log_sha256": sha_file(log)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ocamlopt", required=True)
    parser.add_argument("--receipt", type=Path)
    parser.add_argument("--keep-work", action="store_true")
    parser.add_argument("--fixed-only", action="store_true")
    args = parser.parse_args()
    if sys.platform != "darwin":
        parser.error("this qualification currently requires macOS APFS; no other platform runtime claim")
    compiler = shutil.which(args.ocamlopt)
    if not compiler:
        parser.error("native compiler unavailable")
    env = os.environ.copy()
    for key in ("OCAMLLIB", "OCAMLPATH", "CAML_LD_LIBRARY_PATH", "OCAMLRUNPARAM"):
        env.pop(key, None)
    env["PATH"] = str(Path(compiler).parent) + os.pathsep + env.get("PATH", "")
    original = {relative: (ROOT / relative).read_bytes() for relative in INPUTS}
    work = Path(tempfile.mkdtemp(prefix="unison-dng-profile-v1-", dir="/private/tmp"))
    print("Private synthetic artifacts", work, flush=True)
    for relative, data in original.items():
        path = work / "sources" / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    commands, metadata, oracles, sparse = make_cases(work / "fixtures")
    command_path = work / "commands.tsv"
    command_path.write_text("\n".join(commands) + "\n")
    oracle_path = work / "fixture-oracles.json"
    oracle_path.write_text(json.dumps(oracles, indent=2) + "\n")
    version = subprocess.check_output([compiler, "-version"], text=True, env=env).strip()
    config = subprocess.check_output([compiler, "-config"], text=True, env=env)
    record = {"schema": "unison-dng-profile-v1-direct-qualification/1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "compiler": compiler, "compiler_version": version, "compiler_sha256": sha_file(Path(compiler)),
        "compiler_config": config, "platform": sys.platform,
        "source_sha256": {relative: sha(data) for relative, data in original.items()},
        "artifact_directory": str(work), "retained": args.keep_work, "runs": [],
        "commands_sha256": sha_file(command_path), "commands": metadata,
        "fixture_oracles_sha256": sha_file(oracle_path), "sparse_inspector_only": sparse,
        "scope": "real public DNG /1 locator and semantic kernel in private compiler snapshots; independent synthetic containers/placement/wire bytes; no valid photo, decoded pixels, rendering, SDK validation, physical clone or speed claim",
        "limitations": ["No Adobe SDK linking/invocation or Photo/Lightroom/catalog/cache/production file access",
            "Large sparse cases inspect and read exact packets only; never full-file hash or transfer",
            "Rejection is bounded by finite small fixtures, cancellation-check budget and timeout; no whole-process RSS claim",
            "Private mutations demonstrate specific graph guards; no production hook or public test switch"]}
    modes = ("fixed",) if args.fixed_only else ("fixed", "wrong-CR-base", "missing-CR-protection", "widened-CR-pointer")
    for mode in modes:
        build = work / mode
        build.mkdir()
        for relative, data in original.items():
            if relative.startswith("src/"):
                (build / Path(relative).name).write_bytes(data)
        (build / "dngSemantic.ml").write_text(mutate(original["src/dngSemantic.ml"].decode(), mode))
        for name in ("test.ml", "fs.c"):
            (build / name).write_bytes(original["tests/dng_profile_v1/" + name])
        argv = [compiler, "-I", "+unix", "unix.cmxa", "semanticHash_stubs.c", "semanticFile_stubs.c", "fs.c"]
        for module in MODULES:
            argv += [module + ".mli", module + ".ml"]
        argv += ["test.ml", "-o", str(build / "dng-profile-test")]
        built = execute(argv, build, env, build / "build.log")
        if built["exit_code"]:
            raise AssertionError("DNG /1 compiler snapshot failed")
        selected = commands
        expected = None
        if mode != "fixed":
            designated = {"wrong-CR-base": "classic-le-crL",
                "missing-CR-protection": "big-le-cr-value-alias-XMP",
                "widened-CR-pointer": "big-le-cr-exif-pointer-unsupported"}[mode]
            selected = [command for command in commands if command.split("\t")[1] == designated]
            assert len(selected) == 1
            expected = {"wrong-CR-base": designated + ": XMP aliases protected extent",
                "missing-CR-protection": designated + ": malformed or unsupported container was admitted",
                "widened-CR-pointer": designated + ": malformed or unsupported container was admitted"}[mode]
        selected_path = build / "commands.tsv"
        selected_path.write_text("\n".join(selected) + "\n")
        run = execute([str(build / "dng-profile-test"), str(selected_path), str(work / "fixtures")],
                      build, env, build / "test.log")
        rendered = (build / "test.log").read_text()
        if mode == "fixed":
            if run["exit_code"]:
                raise AssertionError("DNG /1 synthetic production controls failed")
            count = re.search(r"All (\d+) DNG /1 cases passed; (\d+) assertions; maximum cancellation checks (\d+)", rendered)
            assert count and "Filesystem apfs" in rendered
            run.update(cases=int(count[1]), assertions=int(count[2]), maximum_cancellation_checks=int(count[3]))
        else:
            if run["exit_code"] != 2 or expected not in rendered:
                raise AssertionError("private mutation missed its designated actual defect")
            run["detected_assertion"] = expected
        compiled = {path.name: sha_file(path) for path in sorted(build.iterdir()) if path.is_file()}
        record["runs"].append({"mode": mode, "compile": built, "test": run,
                              "compiled_files_sha256": compiled})
    record["current_sources_match_snapshot"] = all((ROOT / relative).read_bytes() == data
                                                    for relative, data in original.items())
    assert record["current_sources_match_snapshot"], "qualification source changed while building"
    manifest_path = work / "artifact-manifest.json"
    manifest_path.write_text(json.dumps(inventory(work, {item["path"] for item in sparse}), indent=2) + "\n")
    record["artifact_manifest"] = str(manifest_path)
    record["artifact_manifest_sha256"] = sha_file(manifest_path)
    record["terminal"] = "passed"
    output = args.receipt or work / "receipt.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(record, indent=2) + "\n")
    print("Qualification receipt", output, flush=True)
    if not args.keep_work:
        shutil.rmtree(work)


if __name__ == "__main__":
    main()
