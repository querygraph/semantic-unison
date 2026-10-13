"""Independent serialized format claims, never Adobe-valid pixel fixtures."""
import struct


def container(*, big=False, little=True, profile=False, xmp=True,
              private=False, future=False, invalid_version_type=False):
    """A bounded DNGVersion claim in IFD0, separate from patch eligibility."""
    order = "little" if little else "big"
    integer = lambda value, width: value.to_bytes(width, order)
    data = bytearray(65536)
    inline, entry_size, number_width, count_width = (8, 20, 8, 8) if big else (4, 12, 4, 2)
    header = (b"II" if little else b"MM") + integer(43 if big else 42, 2)
    header += integer(8, 2) + bytes(2) + integer(32, 8) if big else integer(32, 4)
    data[:len(header)] = header
    fields = [(256, 4, 1, integer(128, 4), None),
              (273, 16 if big else 4, 1, integer(8192, number_width), None),
              (279, 16 if big else 4, 1, integer(1024, number_width), None),
              (50706, 7 if invalid_version_type else 1, 4,
               bytes([9, 8, 0, 0]) if future else b"\x01\x07\0\0", None)]
    if xmp:
        fields.append((700, 1, 16, b"<x>metadata</x> ", 512))
    if private:
        fields.append((65000, 4, 1, integer(512, 4), None))
    if profile:
        fields.append((50933, 16 if big else 4, 1, integer(32768, number_width), None))
        profile_order = "big" if little else "little"
        profile_integer = lambda value, width: value.to_bytes(width, profile_order)
        data[32768:32776] = ((b"MM" if little else b"II") +
                            profile_integer(0x4352, 2) + profile_integer(8, 4))
        name = b"synthetic-profile\0"
        table = (profile_integer(2, 2) + profile_integer(50936, 2) + profile_integer(2, 2) +
                 profile_integer(len(name), 4) + profile_integer(64, 4) +
                 profile_integer(50941, 2) + profile_integer(4, 2) +
                 profile_integer(1, 4) + profile_integer(0, 4) + bytes(4))
        data[32776:32776 + len(table)] = table
        data[32832:32832 + len(name)] = name
    fields.sort()
    table = bytearray(integer(len(fields), count_width))
    for tag, typ, count, value, address in fields:
        assert len(value) == count * {1: 1, 4: 4, 7: 1, 16: 8}[typ]
        table += integer(tag, 2) + integer(typ, 2) + integer(count, number_width)
        if len(value) <= inline:
            table += value + bytes(inline - len(value))
        else:
            assert address is not None
            table += integer(address, number_width)
            data[address:address + len(value)] = value
    table += bytes(number_width)
    assert len(table) == count_width + entry_size * len(fields) + number_width
    data[32:32 + len(table)] = table
    data[8192:9216] = bytes((29 + 113 * i) & 255 for i in range(1024))
    data[-1] = 0xA7
    return bytes(data)


def different(data, label):
    """Change an opaque trailing byte while preserving the IFD0 format claim."""
    return data + b"\n" + label.encode("ascii")


def unrelated_tiff():
    data = bytearray(container())
    # Change the one IFD0 DNGVersion tag to DNGBackwardVersion; keep a complete,
    # valid TIFF layout and XMP so magic/XMP/name alone cannot select DNG.
    for at in range(34, 34 + 12 * 5, 12):
        if int.from_bytes(data[at:at + 2], "little") == 50706:
            data[at:at + 2] = (50707).to_bytes(2, "little")
            break
    else:
        raise AssertionError("fixture DNGVersion slot missing")
    return bytes(data)


def unrelated_jpeg():
    """JPEG marker envelope with a TIFF/DNG claim only inside an APP segment."""
    payload = b"Exif\0\0" + container()[:128]
    return b"\xff\xd8\xff\xe1" + struct.pack(">H", len(payload) + 2) + payload + b"\xff\xd9"


def indeterminate_tiff():
    # A genuine TIFF prefix with an impossible primary address must not be
    # converted from Indeterminate into Not_matched on a renamed file.
    return b"II" + struct.pack("<HI", 42, 65536) + bytes(24)


def fixtures():
    for big in (False, True):
        for little in (True, False):
            label = ("big" if big else "classic") + ("-le" if little else "-be")
            yield label, container(big=big, little=little)
            yield label + "-opposite-CR", container(big=big, little=little, profile=True)
    yield "no-XMP", container(xmp=False)
    yield "private-pointer", container(private=True)
    yield "future-version", container(future=True)
    yield "malformed-version-type", container(invalid_version_type=True)
    yield "indeterminate-TIFF", indeterminate_tiff()
