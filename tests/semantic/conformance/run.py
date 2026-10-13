#!/usr/bin/env python3
"""Check production codecs against independent bytes in a compiler-local snapshot."""
import argparse
from dataclasses import replace
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True
from reference import (MAX_PAYLOAD, Proof, Region, binds, decode_envelope,
                       decode_request, digest, encode_envelope, encode_request,
                       golden_values, inspect, plan, Invalid)
from vectors import case_manifest, sha, verify_goldens, wire_cases

MODULES = ["semanticHash", "semanticFile", "formatExtension", "xmpObservation", "dngSemantic", "semanticDelta"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ocamlopt", default="ocamlopt")
    parser.add_argument("--report", type=Path)
    parser.add_argument("--negative-control", nargs="?", const="nonce", choices=("nonce", "preservation"),
                        help="privately corrupt nonce binding or preservation hashing and require detection")
    args = parser.parse_args()
    compiler = shutil.which(args.ocamlopt)
    if compiler is None:
        parser.error("native OCaml compiler unavailable")
    root = Path(__file__).resolve().parents[3]
    here = Path(__file__).resolve().parent
    work = Path(tempfile.mkdtemp(prefix="unison-sde-conformance-", dir="/private/tmp"))
    print("Private compiler snapshot:", work, flush=True)
    copied = []
    for name in MODULES:
        for suffix in (".mli", ".ml"):
            copied.append("src/" + name + suffix)
    copied += ["src/semanticHash_stubs.c", "src/semanticFile_stubs.c",
               "doc/semantic-delta-v0.md", "doc/dng-profile-v0.md"]
    copied += [str(path.relative_to(root)) for path in sorted(here.rglob("*"))
               if path.is_file() and "__pycache__" not in path.parts and not path.name.startswith("qualification-")]
    sources = {}
    for relative in copied:
        data = (root / relative).read_bytes()
        target = work / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        sources[relative] = sha(data)
    fixture_root = work / "tests/semantic/conformance"
    # Import-independent expected bytes are checked against the committed
    # goldens, not replaced with whatever the production codec happens to emit.
    verify_goldens(fixture_root / "golden")
    cases = wire_cases()
    pinned_manifest = json.loads((fixture_root / "golden/boundary-manifest.json").read_text())
    assert case_manifest(cases) == pinned_manifest, "deterministic boundary recipes differ from committed pins"
    case_dir = work / "cases"
    case_dir.mkdir()
    commands = []
    command_metadata = []

    def add(fields, scope):
        commands.append("\t".join(map(str, fields)))
        command_metadata.append({"name": fields[1], "mode": fields[0], "scope": scope})

    paths = {}
    for index, (name, kind, data, limit, accepted, error) in enumerate(cases):
        path = case_dir / f"{index:03d}-{name}.{kind}"
        path.write_bytes(data)
        paths[kind, name] = path
        if kind == "sde":
            add(["sde", name, path, limit, "accept" if accepted else "reject", error or "-"],
                "structural decoder and canonical encoder")
        else:
            add(["sdr", name, path, "accept" if accepted else "reject", error or "-"],
                "structural request decoder and canonical encoder")
    for name, profile, regions, nonce, before, after in golden_values():
        golden = fixture_root / "golden"
        base_path, target_path = golden / f"{name}.base", golden / f"{name}.target"
        request_path, envelope_path = golden / f"{name}.sdr", golden / f"{name}.sde"
        region_text = ",".join(f"{r.offset}:{r.length}" for r in regions)
        kind = "dng" if name.startswith("dng-") else "generic"
        add(["golden", name, base_path, target_path, request_path, envelope_path,
             profile.decode(), region_text, kind],
            "local file inspection, preservation transcript, local/claimed-base plan, exact apply and source preservation")
        add(["truncate", name, request_path, envelope_path], "every strict prefix of fixed golden SDE and SDR")
        for length in (0, 31, 33):
            try:
                plan(bytes(length), inspect(before, profile, regions), inspect(after, profile, regions))
                raise AssertionError("reference accepted invalid nonce")
            except Invalid:
                pass
            add(["reject_plan", f"{name}-nonce-length-{length}", base_path, target_path,
                 profile.decode(), region_text, kind, length], "plan/request construction nonce length")
        for label, data in (("growth", after + b"!"),
                            ("opaque-change", after[:8 if kind == "generic" else 255] +
                             bytes([after[8 if kind == "generic" else 255] ^ 1]) +
                             after[(8 if kind == "generic" else 255) + 1:])):
            target = case_dir / f"{name}-{label}.target"
            target.write_bytes(data)
            try:
                plan(nonce, inspect(before, profile, regions), inspect(data, profile, regions))
                raise AssertionError("reference accepted ineligible update")
            except Invalid:
                pass
            add(["reject_plan", f"{name}-{label}", base_path, target, profile.decode(), region_text, kind, 32],
                "same-size exact-layout and opaque-byte preservation contract")
    golden = fixture_root / "golden"
    request_path = golden / "multi.sdr"
    envelope_path = golden / "multi.sde"
    nonce, original_proof = decode_request(request_path.read_bytes())
    original_envelope = decode_envelope(envelope_path.read_bytes())
    add(["bind", "exact-proof", request_path, envelope_path, "true"], "all receiver proof fields")
    for name in ("nonce-zero", "unknown-profile", "wrong-whole-base-proof", "wrong-preservation-proof",
                 "wrong-old-range-proof", "incomplete-local-region-list"):
        response_path = paths["sde", name]
        assert not binds(nonce, original_proof, decode_envelope(response_path.read_bytes()))
        add(["bind", "response-" + name, request_path, response_path, "false"], "changed response field binding")
    request_variants = [
        ("nonce", bytes([nonce[0] ^ 1]) + nonce[1:], original_proof),
        ("profile", nonce, replace(original_proof, profile=b"unregistered.request/0")),
        ("file-size", nonce, replace(original_proof, size=original_proof.size + 1)),
        ("whole-base", nonce, replace(original_proof, whole=digest(b"wrong base"))),
        ("preservation", nonce, replace(original_proof, preserved=digest(b"wrong preservation"))),
        ("region-placement", nonce, replace(original_proof, regions=original_proof.regions[:2] +
                                            (Region(12, 4),) + original_proof.regions[3:])),
        ("region-length", nonce, replace(original_proof, regions=original_proof.regions[:2] +
                                         (Region(11, 3),) + original_proof.regions[3:])),
        ("old-region-hash", nonce, replace(original_proof, old_hashes=(digest(b"wrong old"),) +
                                            original_proof.old_hashes[1:])),
        ("region-count", nonce, replace(original_proof, regions=original_proof.regions[:-1],
                                        old_hashes=original_proof.old_hashes[:-1]))]
    for name, changed_nonce, proof in request_variants:
        assert not binds(changed_nonce, proof, original_envelope)
        path = case_dir / f"bind-request-{name}.sdr"
        path.write_bytes(encode_request(changed_nonce, proof))
        add(["bind", "request-" + name, path, envelope_path, "false"], "changed retained request field binding")
    assert binds(nonce, original_proof, decode_envelope(paths["sde", "wrong-target-digest"].read_bytes()))
    add(["bind", "target-digest-checked-by-materializer", request_path,
         paths["sde", "wrong-target-digest"], "true"], "request binding does not claim the target hash is already verified")
    for name, when in (("unknown-profile", "unregistered"), ("wrong-whole-base-proof", "before_writes"),
                       ("wrong-preservation-proof", "before_writes"), ("wrong-old-range-proof", "before_writes"),
                       ("incomplete-local-region-list", "before_writes"), ("wrong-target-digest", "after_writes")):
        add(["reject_apply", name, golden / "multi.base", paths["sde", name],
             original_proof.profile.decode(), "0:3,3:2,11:4,27:5", "generic", when],
            "local authorization before writes" if when != "after_writes" else "target verification of private output after writes")
    manifest = work / "commands.tsv"
    manifest.write_text("\n".join(commands) + "\n")
    environment = dict(os.environ)
    for variable in ("OCAMLLIB", "OCAMLPATH", "CAML_LD_LIBRARY_PATH", "OCAMLRUNPARAM"):
        environment.pop(variable, None)
    environment["PATH"] = str(Path(compiler).parent) + os.pathsep + environment.get("PATH", "")
    source_dir = work / "src"
    if args.negative_control:
        source = (source_dir / "semanticDelta.ml").read_text()
        if args.negative_control == "nonce":
            source, count = re.subn(r"t\.nonce = nonce && t\.profile = base\.name", "t.profile = base.name", source, count=1)
        else:
            source, count = re.subn(r'feed_string preserved "SDE/0-preserved',
                                   'feed_string preserved "SDE/0-incorrect-preserved', source, count=1)
        assert count == 1, "nonce binding private negative-control anchor changed"
        (source_dir / "semanticDelta.ml").write_text(source)
    compiled_sources = {"src/" + path.name: sha(path.read_bytes()) for path in source_dir.iterdir()
                        if path.is_file() and path.suffix in (".ml", ".mli", ".c")}
    compiler_version = subprocess.check_output([compiler, "-version"], text=True, env=environment).strip()
    with (work / "build.log").open("w") as log:
        command = [compiler, "-I", "+unix", "unix.cmxa", "semanticHash_stubs.c",
                   "semanticFile_stubs.c"]
        for name in MODULES:
            command += [name + ".mli", name + ".ml"]
        result = subprocess.run(command + [str(fixture_root / "test.ml"), "-o", str(work / "conformance-test")],
                                cwd=source_dir, env=environment, stdout=log, stderr=subprocess.STDOUT)
    if result.returncode:
        print((work / "build.log").read_text())
        raise SystemExit(result.returncode)
    result = subprocess.run([str(work / "conformance-test"), str(manifest)], cwd=work,
                            env=environment, capture_output=True, text=True, timeout=90)
    (work / "test.log").write_text(result.stdout + result.stderr)
    print(result.stdout, end="", flush=True)
    print(result.stderr, end="", flush=True)
    if args.negative_control:
        assert result.returncode != 0, "corrupted production negative control unexpectedly passed"
        expected = ("response-nonce-zero: request proof binding mismatch" if args.negative_control == "nonce"
                    else "multi: independently computed whole/region/preserved proof mismatch")
        assert expected in result.stderr, result.stderr
        print("PASS private", args.negative_control, "negative control was detected", flush=True)
    else:
        result.check_returncode()
    counts = re.search(r"CONFORMANCE commands=(\d+) assertions=(\d+)", result.stdout)
    receipt = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "production semantic kernel codecs/proofs in a compiler-matched private snapshot; synthetic bytes only",
        "compiler": compiler, "compiler_version": compiler_version,
        "compiler_binary_sha256": sha(Path(compiler).read_bytes()),
        "private_snapshot": str(work), "build_exit": 0, "test_exit": result.returncode,
        "negative_control": args.negative_control,
        "negative_control_detected": bool(args.negative_control and result.returncode != 0),
        "commands_passed": int(counts.group(1)) if counts else result.stdout.count("PASS "),
        "assertions_passed": int(counts.group(2)) if counts else None,
        "source_sha256": sources,
        "compiled_source_sha256": compiled_sources,
        "current_source_matches_snapshot": all((root / relative).is_file() and
            sha((root / relative).read_bytes()) == expected for relative, expected in sources.items()),
        "build_log_sha256": sha((work / "build.log").read_bytes()),
        "test_log_sha256": sha((work / "test.log").read_bytes()),
        "commands_sha256": sha(manifest.read_bytes()),
        "commands": command_metadata,
        "wire_case_count": len(cases),
        "wire_accepted_count": sum(case[4] for case in cases),
        "wire_rejected_count": sum(not case[4] for case in cases),
        "strict_prefix_rejections": sum(len((golden / f"{name}.{suffix}").read_bytes())
                                        for name in ("multi", "dng-le", "dng-be") for suffix in ("sde", "sdr")),
        "limitations": ["No profile proof from Adobe SDK or personal DNG files", "No RPC allocation/transport lifecycle measurement",
                        "No physical APFS write/allocation or speed claim", "No production renderer, preview/cache/catalog invocation"]}
    output = args.report or work / "receipt.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(receipt, indent=2) + "\n")
    print("Receipt:", output, flush=True)


if __name__ == "__main__":
    main()
