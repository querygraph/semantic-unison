#!/usr/bin/env python3
"""Advisory extension semantics through actual CLI/workers/local and RPC paths.
No SDK, native preview, real photo or archive-conflict policy changes involved.
"""
from pathlib import Path
import runpy
import struct
import sys

ROOT = Path(__file__).resolve().parent
exercise = runpy.run_path(str(ROOT / 'test_semantic_reports.py'))['exercise']


def fixture(rating=b'1', exposure=b'0', opaque=b'A', nested=b'one', invalid=False):
    packet = (b'<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" '
              b'xmlns:xmp="http://ns.adobe.com/xap/1.0/" '
              b'xmlns:crs="http://ns.adobe.com/camera-raw-settings/1.0/" '
              b'xmlns:custom="urn:unison:test">'
              b'<rdf:Description rdf:about="" xmp:Rating="' + rating + b'" '
              b'crs:Exposure2012="' + exposure + b'">'
              b'<crs:Mask><rdf:Seq><rdf:li>' + nested + b'</rdf:li></rdf:Seq></crs:Mask>'
              b'<custom:State>opaque</custom:State></rdf:Description></rdf:RDF>')
    if invalid:
        packet = b'<!DOCTYPE rdf:RDF SYSTEM "file:///unqualified">' + packet
    packet = packet.ljust(1024, b' ')
    data = bytearray(2 * 1024 * 1024)
    struct.pack_into('<2sHIH', data, 0, b'II', 42, 8, 4)
    for i, entry in enumerate(((273, 4, 1, 4096), (279, 4, 1, 1024),
                               (700, 1, len(packet), 1024), (50706, 1, 4, 1025))):
        struct.pack_into('<HHII', data, 10 + i * 12, *entry)
    data[1024:1024 + len(packet)] = packet
    data[4096:5120] = b'R' * 1024
    data[-1:] = opaque
    return bytes(data)


def main():
    binary = str(Path(sys.argv[1]).resolve())
    metadata = 'Classification: editable metadata differs; all bytes outside those regions match.'
    schema = 'Extension interpretation: dng-xmp-property-encoding-v0'
    for remote in (False, True):
        exercise(binary, binary, 'rating.dng', fixture(), fixture(rating=b'2'), fixture(rating=b'3'),
                 classification=metadata, remote=remote,
                 expected_meaning=(schema, 'descriptive metadata:', 'Rating encoding/context changed'))
        exercise(binary, binary, 'rendering.dng', fixture(), fixture(exposure=b'1'), fixture(exposure=b'2'),
                 classification=metadata, remote=remote,
                 expected_meaning=(schema, 'rendering metadata:', 'Exposure2012 encoding/context changed'))
        exercise(binary, binary, 'nested.dng', fixture(), fixture(nested=b'two'), fixture(nested=b'six'),
                 classification=metadata, remote=remote,
                 expected_meaning=(schema, 'Mask encoding/context changed'))
        exercise(binary, binary, 'protected.dng', fixture(), fixture(rating=b'2', opaque=b'Z'), fixture(rating=b'3'),
                 classification='Classification: other bytes or the editable-region layout differ.', remote=remote,
                 expected_meaning=(schema, 'Rating encoding/context changed'))
        exercise(binary, binary, 'bad-xmp.dng', fixture(invalid=True), fixture(rating=b'2', invalid=True),
                 fixture(rating=b'3', invalid=True), classification=metadata, remote=remote,
                 expected_meaning=('Extension interpretation unavailable:',))
    if len(sys.argv) > 2:
        old = str(Path(sys.argv[2]).resolve())
        # Previous implementation supports byte SIR0, but has no property SIR1.
        exercise(binary, old, 'sir0-peer.dng', fixture(), fixture(rating=b'2'), fixture(rating=b'3'),
                 classification=metadata, remote=True)
    print('Extension meanings: actual local/remote namespace roles and nested masks; byte authority/conflicts unchanged')


if __name__ == '__main__':
    main()
