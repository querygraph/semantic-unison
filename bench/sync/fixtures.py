"""Deterministic, non-photographic classic TIFF/DNG-shaped benchmark inputs."""
import hashlib
from pathlib import Path
import random
import struct


def validate_dimensions(file_mib, files, packet_bytes):
    if not (type(file_mib) is int and type(files) is int and type(packet_bytes) is int
            and 1 <= file_mib <= 2048 and 1 <= files <= 256
            and 256 <= packet_bytes <= 1048576):
        raise ValueError('fixture dimensions exceed declared bounds')
    size = file_mib * 1048576
    if size * files > 8 * 1024 ** 3 or packet_bytes + 8192 >= size:
        raise ValueError('fixture working set exceeds8GiB or packet does not fit')
    # The largest admitted file and its protected byte count fit classic TIFF's
    # unsigned32-bit fields. This is argument admission, not large-file proof.
    return size


def packet(size, generation):
    value = (b'<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">'
             b'<rdf:Description rdf:about="" xmlns:xmp="http://ns.adobe.com/xap/1.0/" '
             b'xmp:Rating="' + str(generation).encode("ascii") + b'"/></rdf:RDF>')
    if len(value) > size:
        raise ValueError("packet too small")
    return value + b" " * (size - len(value))


def create(path, size, packet_size, index, *, layout_only=False):
    """Write one reproducible incompressible payload, without a large Python copy."""
    if type(layout_only) is not bool:
        raise ValueError("typed layout-only fixture flag required")
    rng = random.Random(0x51DE0000 + index)
    with Path(path).open("wb") as stream:
        remaining = size
        while remaining:
            amount = min(1048576, remaining)
            stream.write(rng.randbytes(amount))
            remaining -= amount
    xmp_offset = 1024
    image_offset = (xmp_offset + packet_size + 4095) // 4096 * 4096
    if image_offset >= size:
        raise ValueError("packet leaves no protected image payload")
    # This is a transfer/parser fixture, not a claim of Adobe-valid image pixels.
    count = 6 if layout_only else 4
    header = bytearray(8 + 2 + count * 12 + 4)
    struct.pack_into("<2sHIH", header, 0, b"II", 42, 8, count)
    entries = [(273, 4, 1, image_offset), (279, 4, 1, size - image_offset),
               (700, 1, packet_size, xmp_offset), (50706, 1, 4, 1025)]
    if layout_only:
        # Both private forms deliberately contain offsets into changed XMP.
        # They are preserved exactly, not interpreted as safe metadata pointers.
        entries += [(50740, 1, 128, 256), (65000, 13, 1, xmp_offset)]
    for number, entry in enumerate(entries):
        struct.pack_into("<HHII", header, 10 + number * 12, *entry)
    with Path(path).open("r+b") as stream:
        stream.write(header)
        if layout_only:
            stream.seek(256)
            stream.write(struct.pack('<I', xmp_offset))
        stream.seek(xmp_offset)
        stream.write(packet(packet_size, 1))
    return {"name": Path(path).name, "size_bytes": size, "packet_offset": xmp_offset,
            "packet_bytes": packet_size, "protected_image_offset": image_offset,
            "before_sha256": sha256(path), "seed": 0x51DE0000 + index,
            "layout_only": layout_only,
            "opaque_private_extent": [256, 128] if layout_only else None,
            "opaque_xmp_references": [256, 10+5*12+8] if layout_only else []}


def edit(path, metadata):
    with Path(path).open("r+b") as stream:
        stream.seek(metadata["packet_offset"])
        stream.write(packet(metadata["packet_bytes"], 2))
    return sha256(path)


def sha256(path):
    result = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1048576), b""):
            result.update(block)
    return result.hexdigest()


def equal_files(first, second):
    with Path(first).open("rb") as a, Path(second).open("rb") as b:
        while True:
            left, right = a.read(1048576), b.read(1048576)
            if left != right:
                return False
            if not left:
                return True
