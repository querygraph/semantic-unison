#!/usr/bin/env python3
"""Build and run semantic kernel tests outside the checkout, using synthetic data."""
import argparse
import hashlib
import pathlib
import shutil
import json
import struct
import subprocess
import tempfile

parser = argparse.ArgumentParser()
parser.add_argument("--ocamlopt", default="ocamlopt")
args = parser.parse_args()
root = pathlib.Path(__file__).resolve().parents[2]
modules = ["semanticHash", "semanticFile", "formatExtension", "dngSemantic", "semanticDelta"]
with tempfile.TemporaryDirectory(prefix="unison-semantic-") as tmp:
    build = pathlib.Path(tmp)
    for name in modules:
        for suffix in (".ml", ".mli"):
            shutil.copyfile(root / "src" / (name + suffix), build / (name + suffix))
    shutil.copyfile(root / "tests/semantic/test.ml", build / "test.ml")
    shutil.copyfile(root / "src/semanticHash_stubs.c", build / "semanticHash_stubs.c")
    # Exercise SHA-256 padding boundaries and multi-buffer reads against hashlib.
    for length in (0, 1, 55, 56, 63, 64, 65, 119, 120, 127, 128, 65535, 65536, 65537, 1048576):
        data = bytes((i * 113 + 29) % 256 for i in range(length))
        (build / f"vector-{length}").write_bytes(data)
        (build / f"vector-{length}.sha256").write_text(hashlib.sha256(data).hexdigest())
    command = [args.ocamlopt, "-I", "+unix", "unix.cmxa", "semanticHash_stubs.c"]
    for name in modules:
        command += [name + ".mli", name + ".ml"]
    subprocess.run(command + ["test.ml", "-o", "semantic-test"], cwd=build, check=True)
    subprocess.run([str(build / "semantic-test")], cwd=build, check=True)
    shutil.copyfile(root / "tools/semantic-inspect/inspect.ml", build / "inspect.ml")
    subprocess.run([args.ocamlopt, "-I", "+unix", "unix.cmxa", "semanticHash_stubs.o"] +
                   [name + ".cmx" for name in modules] + ["inspect.ml", "-o", "semantic-inspect"],
                   cwd=build, check=True)
    header = (b"II" + struct.pack("<HIH", 42, 8, 2) +
              struct.pack("<HHII", 700, 1, 16, 38) +
              struct.pack("<HHI", 50706, 1, 4) + b"\x01\x04\0\0" + struct.pack("<I", 0))
    original = header + b"metadata packet!" + b"opaque payload bytes"
    before, after = build / "before.dng", build / "after.dng"
    before.write_bytes(original)
    for contents, classification in (
            (original, "exact_bytes"),
            (original.replace(b"packet!", b"PACKET!"), "editable_metadata"),
            (original[:-1] + b"!", "other_bytes"),
            (original + b"!", "other_bytes"),
            (b"unsupported", "unavailable")):
        after.write_bytes(contents)
        report = json.loads(subprocess.check_output(
            [str(build / "semantic-inspect"), "--base", str(before), str(after)]))
        assert report["classification"] == classification, report
        assert before.read_bytes() == original and after.read_bytes() == contents
        if classification == "editable_metadata":
            assert report["metadata_payload_bytes"] == 16 and report["patch_eligible"]
            assert report["target"]["sha256"] == hashlib.sha256(contents).hexdigest()
    print("Read-only inspection: exact/metadata/opaque/growth/unsupported reports passed.")
