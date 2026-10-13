"""Independent synthetic container recipes, not a TIFF parser or pixel oracle.

Every protected range below comes from the fixture producer's placement record.
No production locator is used to discover these ranges or expected wire bytes.
"""
from dataclasses import dataclass
import struct

PROFILE = b"org.firstpair.dng-xmp/1"
SIZE = 98304
XMP = 32768
XMP_LENGTH = 8257
PRIMARY = 32
CR_BASE = 16384
WIDTH = {1: 1, 2: 1, 3: 2, 4: 4, 5: 8, 6: 1, 7: 1,
         8: 2, 9: 4, 10: 8, 11: 4, 12: 8, 13: 4,
         16: 8, 17: 8, 18: 8}


@dataclass(frozen=True)
class Layout:
    big: bool
    little: bool

    @property
    def order(self):
        return "<" if self.little else ">"

    @property
    def count_width(self):
        return 8 if self.big else 2

    @property
    def entry_size(self):
        return 20 if self.big else 12

    @property
    def number_width(self):
        return 8 if self.big else 4

    @property
    def inline_width(self):
        return self.number_width

    @property
    def value_at(self):
        return 12 if self.big else 8

    def integer(self, number, width):
        return number.to_bytes(width, "little" if self.little else "big")

    def integers(self, numbers, width):
        return b"".join(self.integer(number, width) for number in numbers)


@dataclass
class Fixture:
    name: str
    data: bytes
    layout: Layout
    entries: dict
    directories: dict
    protected: list
    mutable: list
    old_accepts: bool
    xmp_offset: int = XMP
    xmp_length: int = XMP_LENGTH

    def changed(self, name, address, payload):
        data = bytearray(self.data)
        data[address:address + len(payload)] = payload
        return name, bytes(data)

    def field(self, directory, tag, field, value):
        at, layout, _ = self.entries[directory, tag]
        displacement, width = {"tag": (0, 2), "type": (2, 2),
                               "count": (4, layout.number_width),
                               "value": (layout.value_at, layout.number_width)}[field]
        return at + displacement, layout.integer(value, width)


class Producer:
    def __init__(self, layout):
        self.layout = layout
        self.data = bytearray(SIZE)
        self.entries = {}
        self.directories = {}
        self.protected = []
        self.mutable = []

    def put(self, address, data):
        assert 0 <= address <= SIZE and len(data) <= SIZE - address
        self.data[address:address + len(data)] = data

    def protect(self, name, address, length, *, mutable=False):
        assert length > 0
        self.protected.append({"label": name, "offset": address, "length": length})
        if mutable:
            self.mutable.append({"label": name, "offset": address, "length": length})

    def header(self):
        layout = self.layout
        header = (b"II" if layout.little else b"MM") + layout.integer(43 if layout.big else 42, 2)
        header += (layout.integer(8, 2) + bytes(2) + layout.integer(PRIMARY, 8)
                   if layout.big else layout.integer(PRIMARY, 4))
        self.put(0, header)
        self.protect("outer-header", 0, len(header))

    def directory(self, name, address, fields, *, layout=None, base=0, next_offset=0):
        layout = layout or self.layout
        fields = sorted(fields, key=lambda field: field[0])
        table = bytearray(layout.integer(len(fields), layout.count_width))
        for index, (tag, typ, count, value, relative_address, mutable) in enumerate(fields):
            assert len(value) == WIDTH[typ] * count
            at = address + layout.count_width + index * layout.entry_size
            self.entries[name, tag] = (at, layout, relative_address)
            table += layout.integer(tag, 2) + layout.integer(typ, 2)
            table += layout.integer(count, layout.number_width)
            if len(value) <= layout.inline_width:
                table += value + bytes(layout.inline_width - len(value))
                if mutable:
                    self.mutable.append({"label": name + "-inline-" + str(tag),
                                         "offset": at + layout.value_at, "length": len(value)})
            else:
                assert relative_address is not None
                table += layout.integer(relative_address, layout.number_width)
                actual = base + relative_address
                self.put(actual, value)
                if tag != 700:
                    self.protect(name + "-value-" + str(tag), actual, len(value), mutable=mutable)
        next_at = address + len(table)
        table += layout.integer(next_offset, layout.number_width)
        self.put(address, table)
        self.directories[name] = {"offset": address, "length": len(table),
                                  "next_offset_at": next_at, "layout": layout,
                                  "base": base, "count": len(fields)}
        self.protect(name + "-directory", address, len(table))

    def image_payload(self, name, address, length):
        self.put(address, bytes((address + 97 * i + 29) & 255 for i in range(length)))
        self.protect(name, address, length, mutable=True)


def field(tag, typ, data, address=None, mutable=False):
    assert len(data) % WIDTH[typ] == 0
    return tag, typ, len(data) // WIDTH[typ], data, address, mutable


def make_fixture(*, big, little, camera_orders=(), graph=True, pointer_type=None,
                 extent_type=None, profile_type=None, version=7, full_profile=False):
    """A layout fixture with arbitrary opaque payloads, not a valid photograph."""
    layout = Layout(big, little)
    producer = Producer(layout)
    producer.header()
    pointer_type = pointer_type or (18 if big else 13)
    extent_type = extent_type or (16 if big else 4)
    profile_type = profile_type or (16 if big else 4)
    pointer_width, extent_width, profile_width = WIDTH[pointer_type], WIDTH[extent_type], WIDTH[profile_type]
    image_base = 12288 if extent_type == 3 else 81920
    packet = (b'<x:xmpmeta xmlns:x="adobe:ns:meta/" xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" '
              b'xmlns:dc="http://purl.org/dc/elements/1.1/"><rdf:RDF><rdf:Description dc:format="image/dng"/>'
              b'</rdf:RDF></x:xmpmeta>')
    packet = packet + b" " * (XMP_LENGTH - len(packet))
    main = [field(700, 1, packet, XMP),
            field(50706, 1, bytes([1, version, 0, 0])),
            field(256, 4, layout.integer(128, 4), mutable=True),
            field(258, 3, layout.integers([16, 16, 16, 16], 2), 5632, mutable=True),
            field(270, 2, b"fixture-only-description\0", 5888, mutable=True),
            field(274, 3, layout.integer(1, 2), mutable=True),
            field(273, extent_type, layout.integers([image_base, image_base + 320], extent_width), 4096),
            field(279, extent_type, layout.integers([128, 96], extent_width), 4352),
            field(513, 4, layout.integer(82560, 4)), field(514, 4, layout.integer(80, 4)),
            field(50828, 7, b"opaque-original-raw-file-data!" * 2, 6144, mutable=True),
            field(51008, 7, bytes(range(32)), 6400, mutable=True),
            field(51009, 7, bytes(range(32, 64)), 6656, mutable=True),
            field(51022, 7, bytes(range(64, 96)), 6912, mutable=True),
            field(34675, 7, b"opaque-profile-not-pixel-valid" * 2, 7168, mutable=True)]
    if big:
        main.append(field(255, 17, layout.integer((1 << 64) - 1, 8)))
        main.append(field(257, 16, layout.integer(5120, 8), mutable=True))
    if graph:
        main.append(field(330, pointer_type, layout.integers([1024, 1536], pointer_width), 4608))
        main.append(field(34665, pointer_type, layout.integer(2048, pointer_width)))
        main.append(field(34853, pointer_type, layout.integer(2560, pointer_width)))
        producer.directory("sub-strips", 1024, [
            field(254, 4, layout.integer(0, 4)),
            field(273, extent_type, layout.integers([image_base + 1024, image_base + 1280], extent_width), 4864),
            field(279, extent_type, layout.integers([64, 112], extent_width), 5120)])
        producer.directory("sub-tiles", 1536, [
            field(254, 4, layout.integer(1, 4)),
            field(324, extent_type, layout.integers([image_base + 1600, image_base + 1920], extent_width), 5376),
            field(325, extent_type, layout.integers([96, 80], extent_width), 5504)])
        producer.directory("exif", 2048, [field(36864, 7, b"0231"),
            field(40965, pointer_type, layout.integer(2816, pointer_width))])
        producer.directory("gps", 2560, [field(0, 1, b"\x02\x03\0\0"),
            field(2, 5, layout.integers([1, 1, 2, 1, 3, 1], 4), 7424, mutable=True)])
        producer.directory("interop", 2816, [field(1, 2, b"R98\0"),
            field(2, 7, b"0100")])
        for name, address, length in (("sub-strip-0", image_base + 1024, 64), ("sub-strip-1", image_base + 1280, 112),
                                      ("sub-tile-0", image_base + 1600, 96), ("sub-tile-1", image_base + 1920, 80)):
            producer.image_payload(name, address, length)
    for name, address, length in (("main-strip-0", image_base, 128), ("main-strip-1", image_base + 320, 96),
                                  ("jpeg-preview", 82560, 80)):
        producer.image_payload(name, address, length)
    if camera_orders:
        camera_bases = [CR_BASE + 8192 * index for index in range(len(camera_orders))]
        main.append(field(50933, profile_type, layout.integers(camera_bases, profile_width), 7680))
        for index, (base, camera_little) in enumerate(zip(camera_bases, camera_orders)):
            camera = Layout(False, camera_little)
            header = (b"II" if camera_little else b"MM") + camera.integer(0x4352, 2) + camera.integer(8, 4)
            producer.put(base, header)
            producer.protect("cr" + str(index) + "-header", base, 8)
            # Deliberately make the relative value32768 equal absolute XMP32768.
            # Correct relative addressing protects base+32768; treating the
            # slot as an absolute pointer aliases XMP and rejects this valid case.
            fields = [field(50936, 2, b"independent-camera-profile\0", 32768, mutable=True),
                      field(50932, 2, b"profile-calibration-signature\0", 33024, mutable=True),
                      field(50941, 4, camera.integer(0, 4), mutable=True),
                      field(50778, 3, camera.integer(21, 2), mutable=True),
                      field(50721, 10, camera.integers([1, 1, 2, 1, 3, 1], 4), 33280, mutable=True),
                      field(50940, 11, struct.pack(camera.order + "ffff", 0, 0, 1, 1), 33536, mutable=True),
                      field(50964, 10, camera.integers([1, 1, 2, 1, 3, 1], 4), 33792, mutable=True)]
            if full_profile:
                fields += [
                    field(50708, 2, b"synthetic-model-restriction\0", 34048, mutable=True),
                    field(50722, 10, camera.integers([1, 1, 2, 1, 3, 1], 4), 34304, mutable=True),
                    field(50725, 10, camera.integers([1, 1, 2, 1, 3, 1], 4), 34560, mutable=True),
                    field(50726, 10, camera.integers([1, 1, 2, 1, 3, 1], 4), 34816, mutable=True),
                    field(50779, 3, camera.integer(23, 2), mutable=True),
                    field(50937, 4, camera.integers([1, 2, 1], 4), 35072, mutable=True),
                    field(50938, 11, struct.pack(camera.order + "ffffff", 0, 0, 1, 0, 0, 1), 35328, mutable=True),
                    field(50939, 11, struct.pack(camera.order + "ffffff", 0, 0, 1, 0, 0, 1), 35584, mutable=True),
                    field(50942, 2, b"fixture-only-copyright\0", 35840, mutable=True),
                    field(50965, 10, camera.integers([1, 1, 2, 1, 3, 1], 4), 36096, mutable=True),
                    field(50981, 4, camera.integers([1, 2, 1], 4), 36352, mutable=True),
                    field(50982, 11, struct.pack(camera.order + "ffffff", 0, 0, 1, 0, 0, 1), 36608, mutable=True),
                    field(51107, 4, camera.integer(0, 4), mutable=True),
                    field(51108, 4, camera.integer(0, 4), mutable=True),
                    field(51109, 10, camera.integers([0, 1], 4), 36864, mutable=True),
                    field(51110, 4, camera.integer(0, 4), mutable=True)]
            producer.directory("cr" + str(index), base + 8, fields, layout=camera, base=base)
    producer.directory("main", PRIMARY, main)
    producer.put(SIZE - 1, b"\xa7")
    name = ("big" if big else "classic") + ("-le" if little else "-be")
    name += "-cr" + "".join("L" if order else "B" for order in camera_orders)
    if full_profile:
        name += "-full-profile"
    result = Fixture(name, bytes(producer.data), layout, producer.entries,
                     producer.directories, producer.protected, producer.mutable,
                     not big and not camera_orders)
    # Check the producer's own placement invariant, without parsing output.
    for extent in result.protected:
        start, stop = extent["offset"], extent["offset"] + extent["length"]
        assert stop <= len(result.data)
        assert stop <= XMP or start >= XMP + XMP_LENGTH, extent
    return result


def valid_fixtures():
    for big in (False, True):
        for little in (True, False):
            yield make_fixture(big=big, little=little)
            for camera_little in (True, False):
                yield make_fixture(big=big, little=little, camera_orders=(camera_little,))
            yield make_fixture(big=big, little=little, camera_orders=(True, False))
    # Different width encodings may still carry the same graph values.
    for pointer_type, extent_type, profile_type in ((4, 4, 4), (13, 3, 4), (16, 16, 16)):
        fixture = make_fixture(big=True, little=True, camera_orders=(False,),
                               pointer_type=pointer_type, extent_type=extent_type,
                               profile_type=profile_type)
        fixture.name += f"-types{pointer_type}-{extent_type}-{profile_type}"
        yield fixture
    fixture = make_fixture(big=True, little=False, camera_orders=(True,), version=0)
    fixture.name += "-version1.0"
    yield fixture
    # Exercise the whole finite baseline tag/type grammar independently of
    # any claim that matrix dimensions or LUT pixels are Adobe-valid.
    for big, little in ((False, True), (True, False)):
        full = make_fixture(big=big, little=little, camera_orders=(not little,), full_profile=True)
        yield full
        for count in (0, 1):
            data = bytearray(full.data)
            for tag, component, value in ((50937, "count", count),
                                          (50941, "count", 0), (51109, "count", 0)):
                address, payload = full.field("cr0", tag, component, value)
                data[address:address + len(payload)] = payload
            protected = [extent for extent in full.protected
                         if extent["label"] not in ("cr0-value-50937", "cr0-value-51109")]
            mutable = [dict(extent, label=("unreferenced-" + extent["label"]
                       if extent["label"] in ("cr0-value-50937", "cr0-value-51109") else extent["label"]))
                       for extent in full.mutable]
            yield Fixture(full.name + "-declared-dims-" + str(count), bytes(data),
                          full.layout, full.entries, full.directories, protected,
                          mutable, full.old_accepts)
        address, payload = full.field("cr0", 51109, "type", 5)
        yield Fixture(full.name + "-unsigned-rational", full.changed("unused", address, payload)[1],
                      full.layout, full.entries, full.directories, full.protected,
                      full.mutable, full.old_accepts)
    yield work_fixture(253)


def work_fixture(children):
    """One primary + children + CR header + CR IFD = children+3 visits."""
    layout = Layout(True, True)
    producer = Producer(layout)
    producer.header()
    for index in range(children):
        producer.directory("empty-" + str(index), 8192 + index * 32, [])
    profile = Layout(False, False)
    producer.put(CR_BASE, b"MM" + profile.integer(0x4352, 2) + profile.integer(8, 4))
    producer.protect("cr0-header", CR_BASE, 8)
    producer.directory("cr0", CR_BASE + 8, [
        field(50936, 2, b"bounded-work-profile\0", 32768, mutable=True)], layout=profile, base=CR_BASE)
    packet = b"<fixture>bounded-work</fixture>"
    packet += b" " * (XMP_LENGTH - len(packet))
    producer.directory("main", PRIMARY, [
        field(330, 16, layout.integers([8192 + index * 32 for index in range(children)], 8), 4608),
        field(700, 1, packet, XMP), field(50706, 1, b"\x01\x07\0\0"),
        field(50933, 16, layout.integer(CR_BASE, 8))])
    return Fixture("shared-work-" + str(children + 3), bytes(producer.data), layout,
                   producer.entries, producer.directories, producer.protected,
                   producer.mutable, False)


def invalid_fixtures():
    """Mutation recipes with an independently known structural defect."""
    for little in (True, False):
        fixture = make_fixture(big=True, little=little, camera_orders=(not little,))
        prefix = "big-le" if little else "big-be"
        layout = fixture.layout

        def changed(label, address, payload, reason="-"):
            name, data = fixture.changed(prefix + "-" + label, address, payload)
            return name, data, reason

        def field_change(label, directory, tag, component, value, reason="-"):
            address, payload = fixture.field(directory, tag, component, value)
            return changed(label, address, payload, reason)

        for offset_size, reserved in ((4, 0), (16, 0), (8, 1), (0, 0)):
            yield changed(f"header-{offset_size}-{reserved}", 4,
                          layout.integer(offset_size, 2) + layout.integer(reserved, 2), "invalid BigTIFF header")
        for value in (1 << 63, (1 << 64) - 1, SIZE + 1):
            yield changed("primary-" + str(value), 8, layout.integer(value, 8))
        for value in (16385, 1 << 63, (1 << 64) - 1, (1 << 63) - 1):
            yield changed("directory-count-" + str(value), PRIMARY, layout.integer(value, 8))
        for value in (1 << 63, (1 << 64) - 1, (1 << 63) - 1):
            yield field_change("value-count-" + str(value), "main", 270, "count", value)
            yield field_change("value-offset-" + str(value), "main", 270, "value", value)
        # Count fits signed domain but its8-byte product does not.
        address, payload = fixture.field("main", 270, "count", (1 << 63) // 8)
        data = bytearray(fixture.data)
        data[address:address + len(payload)] = payload
        address, payload = fixture.field("main", 270, "type", 12)
        data[address:address + len(payload)] = payload
        yield prefix + "-count-times-width-overflow", bytes(data), "TIFF field size overflow"
        for component, value in (("type", 17), ("type", 5), ("count", 257)):
            yield field_change(f"child-{component}-{value}", "main", 330, component, value)
        yield field_change("IFD8-on-value", "main", 256, "type", 18, "IFD type on non-pointer field")
        yield field_change("IFD-on-value", "main", 256, "type", 13, "IFD type on non-pointer field")
        yield field_change("invalid-field-type", "main", 256, "type", 19, "unsupported TIFF field type")
        yield field_change("duplicate-tag", "main", 256, "tag", 258, "duplicate TIFF tag")
        yield field_change("unknown-value-tag", "main", 256, "tag", 65000)
        # Graphs: missing singleton cardinality, duplicate visits, explicit cycle.
        yield field_change("exif-count-zero", "main", 34665, "count", 0)
        yield field_change("exif-count-two", "main", 34665, "count", 2)
        sub_at, sub_layout, _ = fixture.entries["main", 330]
        sub_pointer = sub_at + sub_layout.value_at
        pointer_array = int.from_bytes(fixture.data[sub_pointer:sub_pointer + 8], layout.order == "<" and "little" or "big")
        yield changed("repeated-subIFD", pointer_array + 8, layout.integer(1024, 8), "repeated or cyclic IFD")
        yield changed("subIFD-parent-cycle", pointer_array, layout.integer(PRIMARY, 8), "repeated or cyclic IFD")
        yield changed("next-parent-cycle", fixture.directories["main"]["next_offset_at"],
                      layout.integer(PRIMARY, 8), "repeated or cyclic IFD")
        yield changed("next-unsigned", fixture.directories["main"]["next_offset_at"], layout.integer(1 << 63, 8))
        for tag in (273, 324):
            directory = "main" if tag == 273 else "sub-tiles"
            yield field_change(f"extent-signed-{tag}", directory, tag, "type", 17, "invalid image extent type")
        yield field_change("unpaired-strips", "main", 279, "tag", 280, "unpaired image extents")
        yield field_change("mismatched-strips", "main", 279, "count", 1, "mismatched image extents")
        yield field_change("image-count-limit", "main", 273, "count", 65537)
        for value in (SIZE + 1, 1 << 63):
            yield changed("image-offset-" + str(value), 4096, layout.integer(value, 8))
        yield changed("image-length-outside", 4352, layout.integer(SIZE, 8))
        # Camera-profile list type/count and CR header/IFD structural rules.
        for value in (0, 257):
            yield field_change("profile-count-" + str(value), "main", 50933, "count", value)
        for typ in (3, 13, 17, 18):
            yield field_change("profile-pointer-type-" + str(typ), "main", 50933, "type", typ)
        yield field_change("profile-offset-zero", "main", 50933, "value", 0)
        yield field_change("profile-offset-unsigned", "main", 50933, "value", 1 << 63)
        cr_layout = fixture.directories["cr0"]["layout"]
        yield changed("cr-bad-bom", CR_BASE, b"ZZ")
        yield changed("cr-bad-magic", CR_BASE + 2, cr_layout.integer(42, 2), "invalid camera profile header")
        for relative in (0, 7, SIZE):
            yield changed("cr-firstIFD-" + str(relative), CR_BASE + 4, cr_layout.integer(relative, 4))
        yield changed("cr-empty-count", CR_BASE + 8, cr_layout.integer(0, 2), "empty camera profile IFD")
        yield changed("cr-entry-limit", CR_BASE + 8, cr_layout.integer(16385, 2), "TIFF entry limit")
        yield field_change("cr-duplicate-tag", "cr0", 50932, "tag", 50936, "duplicate TIFF tag")
        yield field_change("cr-unknown-tag", "cr0", 50932, "tag", 65000)
        data = bytearray(fixture.data)
        for component, value in (("tag", 34665), ("value", XMP - CR_BASE)):
            address, payload = fixture.field("cr0", 50941, component, value)
            data[address:address + len(payload)] = payload
        yield prefix + "-cr-exif-pointer-unsupported", bytes(data), "-"
        yield field_change("cr-wrong-name-type", "cr0", 50936, "type", 4, "unsupported camera profile field type")
        yield field_change("cr-modern-unqualified-tag", "cr0", 50941, "tag", 52551)
        yield field_change("cr-old-GainTableMap-unsupported", "cr0", 50941, "tag", 52525)
        yield field_change("cr-IFD8-classic-layout", "cr0", 50941, "type", 18)
        yield field_change("cr-LONG8-classic-layout", "cr0", 50941, "type", 16)
        yield field_change("cr-value-relative-outside", "cr0", 50936, "value", SIZE)
        yield field_change("cr-value-count-outside", "cr0", 50936, "count", (1 << 32) - 1)
        yield changed("cr-next-chain", fixture.directories["cr0"]["next_offset_at"],
                      cr_layout.integer(8, 4), "unsupported camera profile IFD chain")
        # Each pointer aliases an independently placed protected block. We do
        # not overwrite that block or ask the locator to establish the oracle.
        aliases = [("outer-header", 0, 16), ("main-table", PRIMARY, 32),
                   ("sub-table", 1024, 32), ("subIFD-list", 4608, 16),
                   ("original-raw", 6144, 16), ("opcode-list", 6400, 16),
                   ("image-strip", 81920, 16), ("image-tile", 83520, 16),
                   ("jpeg-preview", 82560, 16), ("cr-header", CR_BASE, 16),
                   ("cr-table", CR_BASE + 8, 16),
                   ("cr-relative-value", CR_BASE + 32768, 16)]
        for label, address, length in aliases:
            data = bytearray(fixture.data)
            for component, value in (("count", length), ("value", address)):
                at, value_bytes = fixture.field("main", 700, component, value)
                data[at:at + len(value_bytes)] = value_bytes
            yield prefix + "-XMP-alias-" + label, bytes(data), "XMP aliases protected extent"
        # The inverse alias keeps the XMP extent unchanged and moves a CR
        # counted value into it. Omitting CR protection would admit this file.
        yield field_change("cr-value-alias-XMP", "cr0", 50936, "value", XMP - CR_BASE,
                           "XMP aliases protected extent")
        for value in (0, 8, (1 << 20) + 1):
            yield field_change("XMP-count-" + str(value), "main", 700, "count", value)
        yield field_change("XMP-type", "main", 700, "type", 7, "unsupported XMP type or packet size")
        yield field_change("missing-DNGVersion", "main", 50706, "tag", 50707, "missing DNGVersion")
        yield field_change("invalid-DNGVersion-type", "main", 50706, "type", 7, "invalid DNGVersion")
        at, dng_layout, _ = fixture.entries["main", 50706]
        yield changed("DNGVersion-too-new", at + dng_layout.value_at, b"\x01\x08\0\0", "unsupported DNG version")
        # A BigTable pointer is not a self-contained field merely because its
        # TIFF value is inline. It must remain unsupported in this finite slice.
        yield field_change("modern-BigTableOffsets-unsupported", "main", 257, "tag", 52541)

    for little in (True, False):
        fixture = make_fixture(big=False, little=little, camera_orders=(not little,))
        address, payload = fixture.field("main", 330, "type", 18)
        yield "classic-IFD8-" + str(little), fixture.changed("unused", address, payload)[1], "unsupported TIFF field type"
        address, payload = fixture.field("main", 50933, "type", 16)
        yield "classic-profile-LONG8-" + str(little), fixture.changed("unused", address, payload)[1], "unsupported TIFF field type"

    # Two-profile arrays: classic out-of-line versus BigTIFF LONG inline8.
    for big in (False, True):
        fixture = make_fixture(big=big, little=True, camera_orders=(True, False), profile_type=4)
        at, layout, _ = fixture.entries["main", 50933]
        array = at + layout.value_at if big else 7680
        yield ("big" if big else "classic") + "-repeated-CR-header", fixture.changed(
            "unused", array + 4, layout.integer(CR_BASE, 4))[1], "repeated or cyclic IFD"
        # XMP overlaps the ExtraCameraProfiles pointer list itself.
        data = bytearray(fixture.data)
        for component, value in (("count", 16), ("value", array)):
            address, payload = fixture.field("main", 700, component, value)
            data[address:address + len(payload)] = payload
        yield ("big" if big else "classic") + "-XMP-alias-CR-list", bytes(data), "XMP aliases protected extent"
    fixture = work_fixture(254)
    yield fixture.name, fixture.data, "IFD work limit"
