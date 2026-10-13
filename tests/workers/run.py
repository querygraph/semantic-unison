#!/usr/bin/env python3
"""Exercise real typed domain workers with the production shared CPU budget."""
import argparse
from pathlib import Path
import shutil
import subprocess
import struct
import tempfile

parser = argparse.ArgumentParser()
parser.add_argument("--ocamlopt", default="ocamlopt")
args = parser.parse_args()
root = Path(__file__).resolve().parents[2]
sources = [
    "src/lwt/lwt.mli", "src/lwt/lwt.ml", "src/lwt/pqueue.mli", "src/lwt/pqueue.ml",
    "src/lwt/generic/lwt_unix_impl.ml", "src/lwt/lwt_unix.mli", "src/lwt/lwt_unix.ml",
    "src/helperSupervisor_stubs.c", "src/helperSupervisor.mli", "src/helperSupervisor.ml",
    "src/semanticAdmission.mli", "src/semanticAdmission.ml",
    "src/ioAdmission.mli", "src/ioAdmission.ml",
    "src/semanticHash_stubs.c", "src/semanticHash.mli", "src/semanticHash.ml",
    "src/semanticFile_stubs.c", "src/semanticFile.mli", "src/semanticFile.ml",
    "src/formatExtension.mli", "src/formatExtension.ml",
    "src/xmpObservation.mli", "src/xmpObservation.ml",
    "src/dngSemantic.mli", "src/dngSemantic.ml",
    "src/dngExtended.mli", "src/dngExtended.ml",
    "src/semanticDelta.mli", "src/semanticDelta.ml",
    "src/semanticWorkers.mli", "src/semanticWorkers.ml",
    "tests/workers/test.ml",
]
with tempfile.TemporaryDirectory(prefix="unison-workers-") as tmp:
    build = Path(tmp)
    for source in sources:
        shutil.copyfile(root / source, build / Path(source).name)
    for source in sources[:-1]:
        subprocess.run([args.ocamlopt, "-I", "+unix", "-c", Path(source).name],
                       cwd=build, check=True)
    objects = [Path(s).stem + (".o" if s.endswith(".c") else ".cmx")
               for s in sources[:-1] if s.endswith((".ml", ".c"))]
    subprocess.run([args.ocamlopt, "-I", "+unix", "unix.cmxa", *objects,
                    "test.ml", "-o", "worker-test"], cwd=build, check=True)
    packet = b"<x>one</x>      "
    dng = bytearray(8192)
    struct.pack_into("<2sHIH", dng, 0, b"II", 42, 8, 4)
    for i, entry in enumerate([(273, 4, 1, 4096), (279, 4, 1, 1024),
                               (700, 1, len(packet), 1024), (50706, 1, 4, 1025)]):
        struct.pack_into("<HHII", dng, 10 + i * 12, *entry)
    dng[1024:1024 + len(packet)] = packet
    dng[4096:5120] = b"R" * 1024
    (build / "fixture.dng").write_bytes(dng)
    (build / "stage.dng").write_bytes(dng)
    target = bytearray(dng)
    target[1024:1024 + len(packet)] = b"<x>two</x>      "
    (build / "target.dng").write_bytes(target)
    # BigTIFF with an independently big-endian classic CR profile. These
    # synthetic bytes qualify structural proofs, not SDK-valid image pixels.
    extended = bytearray(2 * 1024 * 1024)
    struct.pack_into("<2sHHHQ", extended, 0, b"II", 43, 8, 0, 16)
    entries = [(273, 16, 1, 4096), (279, 16, 1, 1024),
               (700, 1, len(packet), 1024), (50706, 1, 4, 1025),
               (50933, 16, 1, 2048)]
    struct.pack_into("<Q", extended, 16, len(entries))
    for i, entry in enumerate(entries):
        struct.pack_into("<HHQQ", extended, 24 + i * 20, *entry)
    struct.pack_into(">2sHIH", extended, 2048, b"MM", 0x4352, 8, 1)
    struct.pack_into(">HHII", extended, 2058, 50936, 2, 16, 64)
    extended[2112:2128] = b"profile value!  "
    extended[1024:1024 + len(packet)] = packet
    extended[4096:5120] = b"R" * 1024
    (build / "extended-base.dng").write_bytes(extended)
    extended[1024:1024 + len(packet)] = b"<x>two</x>      "
    (build / "extended-target.dng").write_bytes(extended)
    with (build / "large.dng").open("wb") as out:
        out.write(dng)
        out.truncate(1073741824)
    with (build / "large-stage.dng").open("wb") as out:
        out.write(dng)
        out.truncate(1073741824)
    subprocess.run([str(build / "worker-test")], cwd=build, check=True, timeout=120)
