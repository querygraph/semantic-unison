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
parser.add_argument("--skip-conformance", action="store_true",
                    help="run only the original kernel/inspection fixtures")
args = parser.parse_args()
root = pathlib.Path(__file__).resolve().parents[2]
modules = ["semanticHash", "semanticFile", "formatExtension", "xmpObservation", "xmpMerge", "dngSemantic", "dngExtended", "semanticDelta"]
with tempfile.TemporaryDirectory(prefix="unison-semantic-") as tmp:
    build = pathlib.Path(tmp)
    for name in modules:
        for suffix in (".ml", ".mli"):
            shutil.copyfile(root / "src" / (name + suffix), build / (name + suffix))
    shutil.copyfile(root / "tests/semantic/test.ml", build / "test.ml")
    for name in ("semanticHash_stubs.c", "semanticFile_stubs.c"):
        shutil.copyfile(root / "src" / name, build / name)
    # Exercise SHA-256 padding boundaries and multi-buffer reads against hashlib.
    for length in (0, 1, 55, 56, 63, 64, 65, 119, 120, 127, 128, 65535, 65536, 65537, 1048576):
        data = bytes((i * 113 + 29) % 256 for i in range(length))
        (build / f"vector-{length}").write_bytes(data)
        (build / f"vector-{length}.sha256").write_text(hashlib.sha256(data).hexdigest())
    command = [args.ocamlopt, "-I", "+unix", "unix.cmxa", "semanticHash_stubs.c",
               "semanticFile_stubs.c"]
    for name in modules:
        command += [name + ".mli", name + ".ml"]
    subprocess.run(command + ["test.ml", "-o", "semantic-test"], cwd=build, check=True)
    subprocess.run([str(build / "semantic-test")], cwd=build, check=True)
    shutil.copyfile(root / "tools/semantic-inspect/inspect.ml", build / "inspect.ml")
    subprocess.run([args.ocamlopt, "-I", "+unix", "unix.cmxa", "semanticHash_stubs.o",
                    "semanticFile_stubs.o"] +
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
    # An independent BigTIFF byte fixture exercises the explicit developer
    # profile without changing its backward-compatible default v0 selection.
    big_header = (b"II" + struct.pack("<HHHQ", 43, 8, 0, 16) + struct.pack("<Q", 2) +
                  struct.pack("<HHQQ", 700, 1, 16, 72) +
                  struct.pack("<HHQ", 50706, 1, 4) + b"\x01\x04\0\0\0\0\0\0" +
                  struct.pack("<Q", 0))
    big_original = big_header + b"metadata packet!" + b"opaque payload bytes"
    before.write_bytes(big_original)
    after.write_bytes(big_original.replace(b"packet!", b"PACKET!"))
    for profile, classification in (("org.firstpair.dng-xmp/0", "unavailable"),
                                    ("org.firstpair.dng-xmp/1", "editable_metadata")):
        report = json.loads(subprocess.check_output(
            [str(build / "semantic-inspect"), "--profile", profile,
             "--base", str(before), str(after)]))
        assert report["classification"] == classification, report
        if classification == "editable_metadata":
            assert report["target"]["profile"] == profile and report["metadata_payload_bytes"] == 16
            assert report["target"]["sha256"] == hashlib.sha256(after.read_bytes()).hexdigest()
        assert before.read_bytes() == big_original
    print("Read-only inspection: explicit v1 BigTIFF and unchanged v0 fallback passed.")
if not args.skip_conformance:
    import sys
    subprocess.run([sys.executable, str(root / "tests/semantic/conformance/run.py"),
                    "--ocamlopt", args.ocamlopt], check=True)
