"""Pure scenario recipes for generated benchmark containers, never camera rewriting.

No paths, file IO, compiler or sync dispatch. A future owned fixture consumer must
stream the initial payload, apply recipes, and independently hash final bytes.
"""
from dataclasses import dataclass
import struct

KINDS = ('fixed-xmp', 'growing-xmp', 'metadata-preview', 'metadata-raw', 'metadata-opaque',
         'full-change', 'malformed-ifd', 'unsupported-signature')
MAX_PACKET = 1048576


@dataclass(frozen=True)
class Layout:
    size: int
    packet_bytes: int
    image_offset: int
    image_bytes: int
    preview_offset: int
    preview_bytes: int
    header: bytes
    packet_offset: int = 1024
    packet_count_field: int = 62
    packet_pointer_field: int = 66
    schema: str = 'unison-generated-workload-tiff/1'


@dataclass(frozen=True)
class Write:
    offset: int
    data: bytes
    xor: bool = False


@dataclass(frozen=True)
class Recipe:
    workload: str
    source_size: int
    target_size: int
    writes: tuple[Write, ...]
    expected_transfer: str
    full_xor: bool = False
    scope: str = 'Generated arbitrary encoded payloads only; no Adobe/photo validity'


def layout(size, packet_bytes=8192, preview_bytes=4096):
    if not (type(size) is int and 32768 <= size <= 2147483648
            and type(packet_bytes) is int and 256 <= packet_bytes <= MAX_PACKET
            and type(preview_bytes) is int and 1 <= preview_bytes <= MAX_PACKET):
        raise ValueError('bounded generated layout dimensions required')
    start = (1024 + packet_bytes + 4095) // 4096 * 4096
    preview = size - preview_bytes
    if preview <= start:
        raise ValueError('packet/preview leaves no encoded primary extent')
    header = bytearray(8 + 2 + 6 * 12 + 4)
    struct.pack_into('<2sHIH', header, 0, b'II', 42, 8, 6)
    entries = [(273, 4, 1, start), (279, 4, 1, preview-start),
               (513, 4, 1, preview), (514, 4, 1, preview_bytes),
               (700, 1, packet_bytes, 1024), (50706, 1, 4, 1025)]
    for index, row in enumerate(entries):
        struct.pack_into('<HHII', header, 10 + 12*index, *row)
    return Layout(size, packet_bytes, start, preview-start, preview, preview_bytes, bytes(header))


def packet(count, generation):
    if type(count) is not int or not 256 <= count <= MAX_PACKET or type(generation) is not int or generation not in (1, 2):
        raise ValueError('bounded synthetic packet required')
    value = (b'<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">'
             b'<rdf:Description xmlns:xmp="http://ns.adobe.com/xap/1.0/" '
             b'xmp:Rating="' + str(generation).encode('ascii') + b'"/></rdf:RDF>')
    return value + b' '*(count-len(value))


def initial_writes(value):
    check_layout(value)
    return (Write(0, value.header), Write(value.packet_offset, packet(value.packet_bytes, 1)))


def check_layout(value):
    if type(value) is not Layout or value != layout(value.size, value.packet_bytes, value.preview_bytes):
        raise ValueError('exact generated layout contract required')


def recipe(value, kind, *, growth=1024):
    check_layout(value)
    if kind not in KINDS:
        raise ValueError('unknown generated workload')
    target = value.size
    full_xor = kind == 'full-change'
    if full_xor:
        writes = ()
    elif kind == 'growing-xmp':
        if type(growth) is not int or not 1 <= growth <= MAX_PACKET-value.packet_bytes:
            raise ValueError('bounded positive packet growth required')
        data = packet(value.packet_bytes+growth, 2)
        target += len(data)
        writes = (Write(value.packet_count_field, struct.pack('<I', len(data))),
                  Write(value.packet_pointer_field, struct.pack('<I', value.size)),
                  Write(value.size, data))
    else:
        writes = (Write(value.packet_offset, packet(value.packet_bytes, 2)),)
        if kind == 'malformed-ifd':
            writes += (Write(4, struct.pack('<I', value.size+4096)),)
        elif kind == 'unsupported-signature':
            writes += (Write(0, b'NO'),)
        elif kind != 'fixed-xmp':
            at = {'metadata-preview': value.preview_offset,
                  'metadata-raw': value.image_offset,
                  'metadata-opaque': 256}[kind]
            writes += (Write(at, b'\x01', xor=True),)
    if any(w.offset < 0 or not w.data or w.offset+len(w.data) > target for w in writes):
        raise ValueError('recipe escaped target envelope')
    ordered = sorted(writes, key=lambda w: w.offset)
    if any(a.offset+len(a.data) > b.offset for a, b in zip(ordered, ordered[1:])):
        raise ValueError('overlapping generated mutations')
    return Recipe(kind, value.size, target, writes,
                  'SDE-eligible-fixture' if kind == 'fixed-xmp' else 'exact-fallback-fixture', full_xor=full_xor)
