#!/usr/bin/env python3
"""Exercise real typed domain workers with the production shared CPU budget."""
import argparse
import contextlib
import json
import datetime
import hashlib
from pathlib import Path
import shutil
import subprocess
import struct
import tempfile

parser = argparse.ArgumentParser()
parser.add_argument("--ocamlopt", default="ocamlopt")
parser.add_argument("--build",type=Path,help="Use actual compiled production objects from this snapshot src directory")
parser.add_argument("--identify-only",action="store_true")
parser.add_argument("--shared-parity-only",action="store_true")
parser.add_argument("--shared-mixed-only",action="store_true")
parser.add_argument("--shared-mixed-hash-only",action="store_true")
parser.add_argument("--read-stats-only",action="store_true")
parser.add_argument("--stage-stats-only",action="store_true")
parser.add_argument("--stress-only",action="store_true")
parser.add_argument("--apply-stress-only",action="store_true")
parser.add_argument("--keep-work",action="store_true")
parser.add_argument("--receipt",type=Path)
args = parser.parse_args()
root = Path(__file__).resolve().parents[2]
sources = [
    "src/lwt/lwt.mli", "src/lwt/lwt.ml", "src/lwt/pqueue.mli", "src/lwt/pqueue.ml",
    "src/lwt/generic/lwt_unix_impl.ml", "src/lwt/lwt_unix.mli", "src/lwt/lwt_unix.ml",
    "src/stagePublication_stubs.c", "src/stagePublication.mli", "src/stagePublication.ml",
    "src/ownedClose.mli", "src/ownedClose.ml",
    "src/domainOwner.mli", "src/domainOwner.ml",
    "src/notificationPipe.mli", "src/notificationPipe.ml",
    "src/borrowedWork.mli", "src/borrowedWork.ml",
    "src/helperSupervisor_stubs.c", "src/helperSupervisor.mli", "src/helperSupervisor.ml",
    "src/semanticAdmission.mli", "src/semanticAdmission.ml",
    "src/ioAdmission.mli", "src/ioAdmission.ml",
    "src/semanticHash_stubs.c", "src/semanticHash.mli", "src/semanticHash.ml",
    "src/semanticFile_stubs.c", "src/semanticFile.mli", "src/semanticFile.ml",
    "src/wholeFileClone_stubs.c", "src/wholeFileClone.mli", "src/wholeFileClone.ml",
    "src/validationSnapshot.mli", "src/validationSnapshot.ml",
    "src/componentHash.mli", "src/componentHash.ml",
    "src/formatRecognition.mli", "src/formatRecognition.ml",
    "src/dngRecognition.mli", "src/dngRecognition.ml",
    "src/formatExtension.mli", "src/formatExtension.ml",
    "src/xmpObservation.mli", "src/xmpObservation.ml", "src/xmpMerge.mli", "src/xmpMerge.ml",
    "src/dngSemantic.mli", "src/dngSemantic.ml",
    "src/dngExtended.mli", "src/dngExtended.ml",
    "src/dngLayout.mli", "src/dngLayout.ml",
    "src/dngComponents.mli", "src/dngComponents.ml",
    "src/semanticDelta.mli", "src/semanticDelta.ml",
    "src/semanticMailbox.mli", "src/semanticMailbox.ml", "src/semanticWorkers.mli", "src/semanticWorkers.ml",
    "tests/workers/test.ml",
]
workspace = (contextlib.nullcontext(tempfile.mkdtemp(prefix="unison-workers-"))
             if args.keep_work else tempfile.TemporaryDirectory(prefix="unison-workers-"))
with workspace as tmp:
    build = Path(tmp)
    for source in sources:
        shutil.copyfile(root / source, build / Path(source).name)
    version=subprocess.check_output([args.ocamlopt,"-version"],text=True).strip()
    if '+ox' in version:
        participant=build/'test.ml';text=participant.read_text()
        assert text.count('Domain.spawn (* TEST_HASH_SPAWN *)')==1
        participant.write_text(text.replace('Domain.spawn (* TEST_HASH_SPAWN *)','Domain.Safe.spawn'))
    linked_pins = {}
    if args.build:
        for source in sources[:-1]:
            # --build names the actual src directory; retain compiler-matched
            # object/interface artifacts without rewriting checked signatures.
            actual=args.build / source.removeprefix("src/")
            if source.endswith((".ml", ".mli", ".c")):
                assert actual.read_bytes()==(root/source).read_bytes(),source
            extensions = (".cmi", ".cmx", ".o") if source.endswith(".ml") else ((".cmi",) if source.endswith(".mli") else (".o",))
            for extension in extensions:
                artifact=actual.with_suffix(extension)
                shutil.copyfile(artifact,build/artifact.name)
                linked_pins[str(artifact)]=hashlib.sha256(artifact.read_bytes()).hexdigest()
    else:
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
    observed=bytearray(dng)
    observation_packet=(b'<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" '
            b'xmlns:xmp="http://ns.adobe.com/xap/1.0/"><rdf:Description '
            b'xmp:Rating="3"/></rdf:RDF>')
    struct.pack_into("<I",observed,38,len(observation_packet))
    observed[1024:1024+len(observation_packet)]=observation_packet
    (build/"observed.dng").write_bytes(observed)
    for name,rating,label in [("merge-base.dng","1","Blue"),("merge-left.dng","2","Blue"),("merge-right.dng","1","Gold"),("merge-target.dng","2","Gold")]:
        merge_packet=(f'<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" xmlns:xmp="http://ns.adobe.com/xap/1.0/"><rdf:Description rdf:about="" xmp:Rating="{rating}" xmp:Label="{label}"/></rdf:RDF>').encode()
        data=bytearray(dng);struct.pack_into("<I",data,38,1024)
        data[1024:2048]=merge_packet+b" "*(1024-len(merge_packet));(build/name).write_bytes(data)
    target = bytearray(dng)
    target[1024:1024 + len(packet)] = b"<x>two</x>      "
    (build / "target.dng").write_bytes(target)
    recognition_only=bytearray(dng)
    struct.pack_into("<H",recognition_only,34,65000)
    (build/"recognition-only.bin").write_bytes(recognition_only)
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
    probe=b"SYN1"+bytes((i*71+19)%256 for i in range(262144-4))
    (build/"identify-probe.bin").write_bytes(probe)
    (build/"identify-probe.sha256").write_text(hashlib.sha256(probe).hexdigest()+"\n")
    if not (args.stage_stats_only or args.apply_stress_only or args.shared_parity_only):
        with (build / "large.dng").open("wb") as out:
            out.write(dng)
            out.truncate(1073741824)
        with (build / "large-stage.dng").open("wb") as out:
            out.write(dng)
            out.truncate(1073741824)
    command=[str(build / "worker-test")]
    if args.identify_only: command.append("--identify-only")
    if args.shared_parity_only: command.append("--shared-parity-only")
    if args.shared_mixed_only: command.append("--shared-mixed-only")
    if args.shared_mixed_hash_only: command.append("--shared-mixed-hash-only")
    if args.read_stats_only: command.append("--read-stats-only")
    if args.stage_stats_only: command.append("--stage-stats-only")
    if args.stress_only: command.append("--stress-only")
    if args.apply_stress_only: command.append("--apply-stress-only")
    result=subprocess.run(command,cwd=build,text=True,capture_output=True,timeout=120)
    (build/"test.log").write_text(result.stdout+result.stderr)
    print(result.stdout,end="")
    print(result.stderr,end="")
    receipt=dict(schema="unison-worker-scheduling/1",utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                 compiler=args.ocamlopt,compiler_version=subprocess.check_output([args.ocamlopt,"-version"],text=True).strip(),
                 workspace=str(build),retained=args.keep_work,actual_production_build=str(args.build) if args.build else None,linked_object_pins=linked_pins,shared_parity_only=args.shared_parity_only,stress_only=args.stress_only,apply_stress_only=args.apply_stress_only,read_stats_only=args.read_stats_only,exit=result.returncode,
                 source_pins={s:hashlib.sha256((root/s).read_bytes()).hexdigest() for s in sources+["tests/workers/run.py"]},
                 binary_sha256=hashlib.sha256((build/"worker-test").read_bytes()).hexdigest(),
                 log_sha256=hashlib.sha256((build/"test.log").read_bytes()).hexdigest(),
                 summary=[line for line in result.stdout.splitlines() if line.startswith("PASS seeded")])
    receipt['stage_stats_only']=args.stage_stats_only
    receipt['shared_mixed_only']=args.shared_mixed_only
    receipt['shared_mixed_hash_only']=args.shared_mixed_hash_only
    (build/"receipt.json").write_text(json.dumps(receipt,indent=2)+"\n")
    if args.receipt: args.receipt.write_text(json.dumps(receipt,indent=2)+"\n")
    result.check_returncode()
