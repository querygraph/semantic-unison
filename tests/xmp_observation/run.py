#!/usr/bin/env python3
"""Compile and exercise the production bounded XMP reader in a private directory."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import random
import struct
import subprocess
import tempfile
import xml.etree.ElementTree as ET


def transcript(kind, bindings, encoding):
    """Independent Python definition of the documented v1 byte transcript."""
    field = lambda value: struct.pack(">I", len(value)) + value
    items = sorted((prefix.encode(), uri.encode()) for prefix, uri in bindings.items())
    value = b"Unison-XMP-observation\0v1\0" + kind.encode() + struct.pack(">I", len(items))
    value += b"".join(field(prefix) + field(uri) for prefix, uri in items)
    return hashlib.sha256(value + field(encoding.encode())).hexdigest()


def differential_packets():
    rdf = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
    crs = "http://ns.adobe.com/camera-raw-settings/1.0/"
    start = f'<r:RDF xmlns:r="{rdf}" xmlns:crs="{crs}"><r:Description r:about=""'
    attribute = (start + ' crs:Exposure2012="1&amp;2"/></r:RDF>').encode()
    child = (start + '><crs:MaskGroup xmlns:m="urn:mask"><m:Mask q="x">'
             '<!--note--><![CDATA[AI<data>]]></m:Mask></crs:MaskGroup></r:Description></r:RDF>').encode()
    envelope = b'<x:xmpmeta xmlns:x="adobe:ns:meta/" x:xmptk="test">' + child + b'</x:xmpmeta>'
    packet = b'\xef\xbb\xbf<?xml version="1.0" encoding="UTF-8"?><?xpacket begin=""?>' + envelope + b'<?xpacket end="w"?>'
    xml_inside = (start + '><crs:MaskGroup xml:base="urn:inside"><Value xml:lang="en"/>'
                  '</crs:MaskGroup></r:Description></r:RDF>').encode()
    seeds = [attribute, child, envelope, packet, xml_inside]
    tokens = [b'<', b'>', b'/', b'"', b"'", b'&', b';', b':', b' ', b'\t', b'\x00',
              b'<!--', b'-->', b'<![CDATA[', b']]>', b'<?xpacket?>',
              b'xmlns:p="urn:p"', b'<p:Mask/>', b'r:about=""']
    rng = random.Random(0x584D5031)
    packets = list(seeds)
    for _ in range(1024):
        seed = rng.choice(seeds)
        at = rng.randrange(len(seed) + 1)
        operation = rng.randrange(4)
        if operation == 0:
            candidate = seed[:at] + seed[at + rng.randrange(1, 5):]
        elif operation == 1:
            candidate = seed[:at] + rng.choice(tokens) + seed[at:]
        elif operation == 2:
            candidate = seed[:at] + rng.choice(tokens) + seed[at + rng.randrange(1, 5):]
        else:
            candidate = seed[:at] + seed[:at] + seed[at:]
        packets.append(candidate)
    return packets


def differential_check(compiler, work, environment):
    subprocess.run([compiler, "semanticHash_stubs.o", "semanticHash.cmx", "xmpObservation.cmx",
                    "probe.ml", "-o", "xmp-probe"], cwd=work, env=environment, check=True)
    packets = differential_packets()
    result = subprocess.run([str(work / "xmp-probe")], cwd=work, env=environment,
                            input="".join(packet.hex() + "\n" for packet in packets),
                            capture_output=True, text=True, check=True, timeout=60)
    lines = result.stdout.splitlines()
    assert len(lines) == len(packets)
    accepted = 0
    invalid = 0
    for index, (packet, decision) in enumerate(zip(packets, lines)):
        assert decision in ("OK", "ERROR")
        try:
            ET.fromstring(packet)
        except (ET.ParseError, ValueError):
            invalid += 1
            assert decision == "ERROR", f"reader accepted malformed XML mutation {index}: {packet!r}"
        if decision == "OK":
            accepted += 1
    assert accepted >= 5 and invalid > 0
    print(f"PASS: {len(packets)} independent ElementTree XML mutation checks "
          f"({accepted} admitted, {invalid} malformed)", flush=True)
    return {"cases": len(packets), "admitted": accepted, "xml_malformed": invalid}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ocamlopt", default="ocamlopt")
    parser.add_argument("--receipt", type=Path)
    parser.add_argument("--fixed-only", action="store_true", help="skip generated XML mutation campaign")
    parser.add_argument("--baseline-revision", help="one exact local Git40-hex source baseline")
    parser.add_argument("--negative-control", choices=("namespace", "subtree", "duplicate"))
    args = parser.parse_args()
    compiler = shutil.which(args.ocamlopt)
    if compiler is None:
        parser.error("native compiler unavailable")
    root = Path(__file__).resolve().parents[2]
    environment = os.environ.copy()
    for variable in ("OCAMLLIB", "OCAMLPATH", "CAML_LD_LIBRARY_PATH", "OCAMLRUNPARAM"):
        environment.pop(variable, None)
    inputs = ["src/semanticHash.ml", "src/semanticHash.mli", "src/semanticHash_stubs.c", "src/semanticHash_evp.h",
              "src/xmpObservation.ml", "src/xmpObservation.mli",
              "tests/xmp_observation/test.ml", "tests/xmp_observation/probe.ml",
              "tests/xmp_observation/run.py"]
    pins = {name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in inputs}
    with tempfile.TemporaryDirectory(prefix="unison-xmp-observation-", dir="/private/tmp") as tmp:
        work = Path(tmp)
        for name in inputs[:-1]:
            shutil.copyfile(root / name, work / Path(name).name)
        if args.baseline_revision:
            import re
            if not re.fullmatch('[0-9a-f]{40}',args.baseline_revision) or args.negative_control:
                parser.error('one exact Git revision and no combined source mutation required')
            baseline=subprocess.check_output(['git','show',args.baseline_revision+':src/xmpObservation.ml'],
                                             cwd=root,timeout=10)
            if len(baseline)>1048576:parser.error('bounded baseline source required')
            (work/'xmpObservation.ml').write_bytes(baseline)
            pins['src/xmpObservation.ml']=hashlib.sha256(baseline).hexdigest()
        ns = {
            "xml": "http://www.w3.org/XML/1998/namespace",
            "r": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
            "crs": "http://ns.adobe.com/camera-raw-settings/1.0/",
        }
        expected = {
            "attribute": transcript("A", ns, "1&amp;2&#x20;3"),
            "element": transcript("E", ns, '<crs:Exposure2012 a="q">1&amp;2<!--x--><![CDATA[<z>]]></crs:Exposure2012>'),
            "nested": transcript("E", dict(ns, mask="urn:mask:first"),
                                 "<crs:MaskGroup><mask:Mask>AI</mask:Mask></crs:MaskGroup>"),
            "self_closing": transcript("E", ns, "<crs:Exposure2012/>"),
        }
        long_uri='urn:'+'x'*480
        def names(n):return ' '.join('p:a'+str(i)+'="v"' for i in range(n))
        long_children='<crs:MaskGroup>'+''.join('<Value '+names(256)+'/>' for _ in range(63))+\
                      '<Value '+names(252)+'/></crs:MaskGroup>'
        expected['long_names']=transcript('E',dict(ns,p=long_uri),long_children)
        (work / "expected.ml").write_text("".join(
            f'let {name} = "{digest}"\n' for name, digest in expected.items()))
        if args.negative_control:
            source = (work / "xmpObservation.ml").read_text()
            if args.negative_control == "namespace":
                old = "let bindings = List.sort (fun (left, _) (right, _) -> String.compare left right) namespaces in"
                new = "let bindings = [] in"
            elif args.negative_control == "subtree":
                old = "property.namespaces 'E' property.first property.last)"
                new = "property.namespaces 'E' property.first property.first)"
            else:
                old = 'if Hashtbl.mem names name then fail "duplicate expanded XMP property";'
                new = "if false then fail \"duplicate expanded XMP property\";"
            assert source.count(old) == 1
            (work / "xmpObservation.ml").write_text(source.replace(old, new))
        version = subprocess.check_output([compiler, "-version"], text=True,
                                          env=environment).strip()
        command = [compiler, "semanticHash_stubs.c", "semanticHash.mli", "semanticHash.ml",
                   "xmpObservation.mli", "xmpObservation.ml", "expected.ml", "test.ml",
                   "-o", "xmp-test"]
        subprocess.run(command, cwd=work, env=environment, check=True)
        test_argv=[str(work / "xmp-test")]+(['--fixed-only'] if args.fixed_only else [])
        result = subprocess.run(test_argv, cwd=work, env=environment,
                                capture_output=True, text=True, timeout=60)
        print(result.stdout, end="", flush=True)
        print(result.stderr, end="", flush=True)
        if args.negative_control:
            assert result.returncode != 0, "negative control unexpectedly passed"
            markers = {
                "namespace": "attribute digest matches independent Python transcript",
                "subtree": "entire element digest matches independent Python transcript",
                "duplicate": "duplicate child expanded property",
            }
            assert markers[args.negative_control] in result.stderr
            print(f"PASS: {args.negative_control} negative control rejected", flush=True)
        else:
            result.check_returncode()
        differential = None if args.negative_control or args.fixed_only else differential_check(compiler, work, environment)
        receipt = {
            "observed_at_utc": datetime.now(timezone.utc).isoformat(),
            "compiler": compiler, "version": version, "source_sha256": pins,
            "tested_xmp_sha256": hashlib.sha256((work / "xmpObservation.ml").read_bytes()).hexdigest(),
            "compile_command": command,
            "negative_control": args.negative_control, "exit_code": result.returncode,
            "fixed_only": args.fixed_only, "baseline_revision": args.baseline_revision,
            "test_argv": test_argv, "random_byte_cases": 0 if args.fixed_only else 512,
            "stdout": result.stdout, "stderr": result.stderr,
            "independent_python_digest_vectors": expected,
            "independent_elementtree_xml_mutations": differential,
            "scope": "Synthetic in-memory XMP packets only; no Adobe, Photo, file payload, or production cache access.",
        }
        if args.receipt:
            args.receipt.write_text(json.dumps(receipt, indent=2) + "\n")
        print("Compiler", version, flush=True)


if __name__ == "__main__":
    main()
