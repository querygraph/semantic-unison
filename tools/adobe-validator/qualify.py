#!/usr/bin/env python3
"""Qualify the real SDK adapter using generated DNGs and negative controls."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import subprocess

parser = argparse.ArgumentParser()
parser.add_argument("--build-dir", type=Path, required=True)
args = parser.parse_args()
build = args.build_dir.resolve()
binary = build / "unison-adobe-validator"
fixtures = build / "fixtures"
fixtures.mkdir(exist_ok=True)

def make_dng(*, digest="both", corrupt_raw=False, corrupt_digest=False, xmp=None):
    raw = b"".join(struct.pack("<H", 500 + (i * 131) % 60000) for i in range(256))
    old = hashlib.md5(raw).digest()
    new = hashlib.md5(hashlib.md5(raw).digest()).digest()
    if corrupt_digest:
        new = bytes([new[0] ^ 1]) + new[1:]
    if corrupt_raw:
        raw = bytes([raw[0] ^ 1]) + raw[1:]
    tags = []
    def tag(code, kind, count, payload):
        tags.append((code, kind, count, payload))
    def shorts(code, *values): tag(code, 3, len(values), struct.pack("<" + "H" * len(values), *values))
    def longs(code, *values): tag(code, 4, len(values), struct.pack("<" + "I" * len(values), *values))
    def rationals(code, *values, signed=False):
        tag(code, 10 if signed else 5, len(values),
            b"".join(struct.pack("<ii" if signed else "<II", n, d) for n, d in values))
    def text(code, value): tag(code, 2, len(value) + 1, value.encode("ascii") + b"\0")
    longs(254, 0)
    longs(256, 16); longs(257, 16)
    shorts(258, 16); shorts(259, 1); shorts(262, 32803)
    text(271, "Unison"); text(272, "Synthetic DNG")
    longs(273, 0); shorts(274, 1); shorts(277, 1)
    longs(278, 16); longs(279, len(raw)); shorts(284, 1)
    shorts(33421, 2, 2); tag(33422, 1, 4, bytes([0, 1, 1, 2]))
    tag(50706, 1, 4, bytes([1, 4, 0, 0])); tag(50707, 1, 4, bytes([1, 1, 0, 0]))
    text(50708, "Unison Synthetic DNG")
    tag(50710, 1, 3, bytes([0, 1, 2])); shorts(50711, 1)
    shorts(50713, 1, 1); rationals(50714, (0, 1)); longs(50717, 65535)
    rationals(50718, (1, 1), (1, 1))
    longs(50719, 0, 0); longs(50720, 16, 16)
    rationals(50721, *[(1 if i in (0, 4, 8) else 0, 1) for i in range(9)], signed=True)
    rationals(50728, (1, 1), (1, 1), (1, 1)); shorts(50778, 21)
    longs(50829, 0, 0, 16, 16)
    if digest in ("old", "both"): tag(50972, 1, 16, old)
    if digest in ("new", "both"): tag(51111, 1, 16, new)
    if digest == "zero": tag(51111, 1, 16, bytes(16))
    if xmp is not None: tag(700, 1, len(xmp), xmp)
    tags.sort()
    extra = bytearray()
    entries = []
    base = 8 + 2 + len(tags) * 12 + 4
    for code, kind, count, payload in tags:
        if len(payload) <= 4:
            value = payload.ljust(4, b"\0")
        else:
            if len(extra) & 1: extra += b"\0"
            value = struct.pack("<I", base + len(extra))
            extra += payload
        entries.append([code, kind, count, value])
    if len(extra) & 1: extra += b"\0"
    raw_offset = base + len(extra)
    for item in entries:
        if item[0] == 273: item[3] = struct.pack("<I", raw_offset)
    return b"II*\0" + struct.pack("<I", 8) + struct.pack("<H", len(tags)) + b"".join(
        struct.pack("<HHI", code, kind, count) + value for code, kind, count, value in entries
    ) + bytes(4) + extra + raw

valid_xmp = b'''<x:xmpmeta xmlns:x="adobe:ns:meta/"><rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"><rdf:Description rdf:about=""/></rdf:RDF></x:xmpmeta>'''
cases = [
    ("valid-both", make_dng(), "valid", True),
    ("valid-old", make_dng(digest="old"), "valid", True),
    ("valid-new", make_dng(digest="new"), "valid", True),
    ("valid-xmp", make_dng(xmp=valid_xmp), "valid", True),
    ("missing-digest", make_dng(digest="none"), "missing", True),
    ("corrupt-raw", make_dng(corrupt_raw=True), "mismatch", False),
    ("corrupt-digest", make_dng(corrupt_digest=True), "mismatch", False),
    ("zero-digest", make_dng(digest="zero"), "mismatch", False),
    ("bad-xmp", make_dng(xmp=valid_xmp.replace(b"</rdf:RDF>", b"</rdf:WRONG>")), None, False),
    ("bad-structure", b"not a DNG file", None, False),
]
source = fixtures / "transcode-source.dng"
source.write_bytes(make_dng())
for codec in ("jpeg", "jxl"):
    target = fixtures / ("valid-" + codec + ".dng")
    writer = subprocess.run([str(build / "fixture-writer"), codec, str(source), str(target)],
                            capture_output=True, text=True, timeout=30)
    if writer.returncode:
        raise RuntimeError(f"{codec} fixture writer failed\n{writer.stdout}\n{writer.stderr}")
    data = target.read_bytes()
    endian = "<" if data[:2] == b"II" else ">"
    offset = struct.unpack_from(endian + "I", data, 4)[0]
    count = struct.unpack_from(endian + "H", data, offset)[0]
    tags = [struct.unpack_from(endian + "HHII", data, offset + 2 + 12 * i)
            for i in range(count)]
    compression = next(value & 65535 for tag, kind, count, value in tags if tag == 259)
    assert compression == {"jpeg": 7, "jxl": 52546}[codec], "writer did not compress raw"
    cases.append(("valid-" + codec, data, "valid", True))
    digest_offset = next(value for tag, kind, count, value in tags
                         if tag in (50972, 51111) and count == 16)
    corrupted = bytearray(data)
    corrupted[digest_offset] ^= 1
    cases.append(("corrupt-" + codec + "-digest", bytes(corrupted), "mismatch", False))
results = []
for name, data, raw_expected, should_pass in cases:
    path = fixtures / (name + ".dng")
    path.write_bytes(data)
    digest = hashlib.sha256(data).hexdigest()
    command = [str(binary), "--unison-dng-validation-v1", "--expected-sha256", digest,
               "--expected-size", str(len(data)), "--threads", "1", "--", str(path)]
    child = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                           text=True, timeout=30)
    (fixtures / (name + ".stderr")).write_text(child.stderr)
    (fixtures / (name + ".receipt")).write_text(child.stdout)
    lines = child.stdout.splitlines()
    if not lines or lines[0] != "UNISON-DNG-VALIDATION 1" or lines[-1] != "END":
        raise RuntimeError(f"{name}: malformed receipt\n{child.stderr}\n{child.stdout}")
    report = dict(line.split(" ", 1) for line in lines[1:-1])
    passed = (child.returncode == 0 and report["structure"] == "valid"
              and report["decode"] == "success" and report["raw-digest"] in ("valid", "missing")
              and report["errors"] == "0")
    assert report["candidate-sha256"] == digest
    assert report["candidate-size"] == str(len(data))
    assert passed == should_pass, f"{name}: wrong verdict {report}\n{child.stderr}"
    if raw_expected is not None:
        assert report["raw-digest"] == raw_expected, f"{name}: {report}\n{child.stderr}"
    # Negative controls must exercise the real exit-zero error-report path.
    if not should_pass:
        assert child.returncode == 0 and int(report["errors"]) > 0, f"{name}: {report}"
    print(f"PASS {name}: exit={child.returncode} raw={report['raw-digest']} errors={report['errors']}")
    results.append({"case": name, "receipt": report, "exit": child.returncode,
                    "sha256": digest, "expected_pass": should_pass})
    if name == "valid-both":
        wrong_threads = command.copy()
        wrong_threads[7] = "2"
        wrong = subprocess.run(wrong_threads, capture_output=True, text=True, timeout=30)
        assert wrong.returncode == 64 and not wrong.stdout, "unqualified threading accepted"

manifest_path = build / "build-manifest.json"
manifest = json.loads(manifest_path.read_text())
assert manifest["executable_sha256"] == hashlib.sha256(binary.read_bytes()).hexdigest()
manifest["qualification"] = "passed synthetic CFA uncompressed/lossless JPEG/JXL and XMP controls; see qualification.json"
manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
(build / "qualification.json").write_text(json.dumps(results, indent=2) + "\n")
print("Qualification passed. No real photographs or Lightroom UI were used.")
