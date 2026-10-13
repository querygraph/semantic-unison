"""Independent SDE/0 and SDR/0 codec, derived from the wire specification.

This module deliberately imports no Unison code and invokes no production
executables. Integers, hashes, the preserved transcript, and fixture DNG bytes
are implemented here using only Python's standard library.
"""
from dataclasses import dataclass
import hashlib
import struct

MAX_INT = (1 << 63) - 1
MAX_REGION = 1 << 20
MAX_PAYLOAD = 16 << 20
MAX_ENVELOPE = MAX_PAYLOAD + 65536
MAX_REQUEST = 8192
SDE = b"SDE\0\0\0\0\0"
SDR = b"SDR\0\0\0\0\0"
DNG_PROFILE = b"org.firstpair.dng-xmp/0"
MULTI_PROFILE = b"org.firstpair.conformance-multi/0"


class Invalid(ValueError):
    pass


def u64(value):
    if not 0 <= value <= MAX_INT:
        raise Invalid("integer overflow")
    return struct.pack(">Q", value)


def digest(value):
    return hashlib.sha256(value).digest()


@dataclass(frozen=True)
class Region:
    offset: int
    length: int


@dataclass(frozen=True)
class Proof:
    profile: bytes
    size: int
    whole: bytes
    preserved: bytes
    regions: tuple
    old_hashes: tuple
    contents: tuple = ()


@dataclass(frozen=True)
class Envelope:
    profile: bytes
    nonce: bytes
    size: int
    base: bytes
    target: bytes
    preserved: bytes
    regions: tuple
    old_hashes: tuple
    payloads: tuple


def check_regions(size, regions, max_payload=MAX_PAYLOAD):
    if not 0 <= size <= MAX_INT or not 1 <= len(regions) <= 64:
        raise Invalid("invalid size or count")
    previous = total = 0
    for region in regions:
        if not (previous <= region.offset <= size and
                1 <= region.length <= MAX_REGION and
                region.length <= size - region.offset):
            raise Invalid("invalid extent")
        previous = region.offset + region.length
        total += region.length
        if total > max_payload:
            raise Invalid("payload limit")


def inspect(data, profile, regions):
    regions = tuple(regions)
    check_regions(len(data), regions)
    transcript = bytearray(b"SDE/0-preserved\0" + u64(len(data)) + u64(len(regions)))
    for region in regions:
        transcript += u64(region.offset) + u64(region.length)
    cursor = 0
    contents = []
    for region in regions:
        transcript += u64(cursor) + u64(region.offset - cursor) + data[cursor:region.offset]
        contents.append(data[region.offset:region.offset + region.length])
        cursor = region.offset + region.length
    transcript += u64(cursor) + u64(len(data) - cursor) + data[cursor:]
    return Proof(profile, len(data), digest(data), digest(transcript), regions,
                 tuple(map(digest, contents)), tuple(contents))


def plan(nonce, base, target):
    if len(nonce) != 32:
        raise Invalid("nonce length")
    if (base.profile, base.size, base.regions) != (target.profile, target.size, target.regions):
        raise Invalid("profile, size or layout changed")
    if base.preserved != target.preserved:
        raise Invalid("outside bytes changed")
    return Envelope(base.profile, nonce, base.size, base.whole, target.whole,
                    base.preserved, base.regions, base.old_hashes, target.contents)


def encode_envelope(value):
    if not 1 <= len(value.profile) <= 128 or len(value.nonce) != 32:
        raise Invalid("profile or nonce")
    check_regions(value.size, value.regions)
    if not (len(value.regions) == len(value.old_hashes) == len(value.payloads)):
        raise Invalid("record count")
    result = bytearray(SDE + u64(len(value.profile)) + value.profile + value.nonce +
                       u64(value.size) + value.base + value.target + value.preserved +
                       u64(len(value.regions)))
    for region, old, payload in zip(value.regions, value.old_hashes, value.payloads):
        if len(old) != 32 or len(payload) != region.length:
            raise Invalid("hash or payload length")
        result += u64(region.offset) + u64(region.length) + old + digest(payload) + payload
    if len(result) > MAX_ENVELOPE:
        raise Invalid("envelope limit")
    return bytes(result)


def encode_request(nonce, proof):
    if len(nonce) != 32 or not 1 <= len(proof.profile) <= 128:
        raise Invalid("nonce or profile")
    check_regions(proof.size, proof.regions)
    result = bytearray(SDR + nonce + u64(len(proof.profile)) + proof.profile +
                       u64(proof.size) + proof.whole + proof.preserved + u64(len(proof.regions)))
    for region, old in zip(proof.regions, proof.old_hashes):
        if len(old) != 32:
            raise Invalid("old hash length")
        result += u64(region.offset) + u64(region.length) + old
    if len(result) > MAX_REQUEST:
        raise Invalid("request limit")
    return bytes(result)


class Reader:
    def __init__(self, data):
        self.data = data
        self.cursor = 0

    def take(self, length):
        stop = self.cursor + length
        if length < 0 or stop > len(self.data):
            raise Invalid("truncated")
        result = self.data[self.cursor:stop]
        self.cursor = stop
        return result

    def integer(self, maximum=MAX_INT):
        result = struct.unpack(">Q", self.take(8))[0]
        if result > maximum:
            raise Invalid("integer limit")
        return result

    def finish(self):
        if self.cursor != len(self.data):
            raise Invalid("trailing bytes")


def decode_envelope(data, max_payload=MAX_PAYLOAD):
    if not 1 <= max_payload <= MAX_PAYLOAD or len(data) > max_payload + 65536:
        raise Invalid("envelope limit")
    reader = Reader(data)
    if reader.take(8) != SDE:
        raise Invalid("version")
    profile = reader.take(reader.integer(128))
    if not profile:
        raise Invalid("empty profile")
    nonce, size = reader.take(32), reader.integer()
    base, target, preserved = (reader.take(32) for _ in range(3))
    count = reader.integer(64)
    if count == 0:
        raise Invalid("empty count")
    regions, old_hashes, payloads = [], [], []
    for _ in range(count):
        region = Region(reader.integer(), reader.integer(MAX_REGION))
        regions.append(region)
        check_regions(size, regions, max_payload)
        old_hashes.append(reader.take(32))
        expected = reader.take(32)
        payload = reader.take(region.length)
        if digest(payload) != expected:
            raise Invalid("payload hash")
        payloads.append(payload)
    reader.finish()
    return Envelope(profile, nonce, size, base, target, preserved,
                    tuple(regions), tuple(old_hashes), tuple(payloads))


def decode_request(data):
    if len(data) > MAX_REQUEST:
        raise Invalid("request limit")
    reader = Reader(data)
    if reader.take(8) != SDR:
        raise Invalid("version")
    nonce = reader.take(32)
    profile = reader.take(reader.integer(128))
    if not profile:
        raise Invalid("empty profile")
    size, whole, preserved, count = reader.integer(), reader.take(32), reader.take(32), reader.integer(64)
    if count == 0:
        raise Invalid("empty count")
    regions, hashes = [], []
    for _ in range(count):
        regions.append(Region(reader.integer(), reader.integer(MAX_REGION)))
        check_regions(size, regions)
        hashes.append(reader.take(32))
    reader.finish()
    return nonce, Proof(profile, size, whole, preserved, tuple(regions), tuple(hashes))


def binds(nonce, proof, envelope):
    return (envelope.nonce == nonce and envelope.profile == proof.profile and
            envelope.size == proof.size and envelope.base == proof.whole and
            envelope.preserved == proof.preserved and envelope.regions == proof.regions and
            envelope.old_hashes == proof.old_hashes)


def dng_fixture(little, packet):
    """256-byte classic TIFF: strip at160, XMP at96, opaque tail at255."""
    if len(packet) != 16:
        raise Invalid("fixture packet length")
    order = "<" if little else ">"
    result = bytearray(256)
    result[:8] = (b"II" if little else b"MM") + struct.pack(order + "HI", 42, 8)
    result[8:10] = struct.pack(order + "H", 4)
    for index, (tag, field_type, count, value) in enumerate(
            ((273, 4, 1, 160), (279, 4, 1, 64), (700, 1, 16, 96), (50706, 1, 4, 0))):
        at = 10 + index * 12
        result[at:at + 12] = struct.pack(order + "HHII", tag, field_type, count, value)
    # TIFF BYTE[4] is inline bytes and remains the same in either byte order.
    result[54:58] = b"\x01\x04\0\0"
    result[96:112] = packet
    result[160:224] = bytes(range(64))
    result[255] = 0xA7
    return bytes(result)


def golden_values():
    nonce = bytes(range(32))
    regions = (Region(0, 3), Region(3, 2), Region(11, 4), Region(27, 5))
    base = bytes((29 + i * 113) & 255 for i in range(32))
    target = bytearray(base)
    target[0:3] = b"NEW"
    target[11:15] = b"X\0MP"
    target[27:32] = b"final"
    yield "multi", MULTI_PROFILE, regions, nonce, base, bytes(target)
    for little in (True, False):
        base = dng_fixture(little, b"<x>one</x>      ")
        target = dng_fixture(little, b"<x>two</x>      ")
        yield "dng-le" if little else "dng-be", DNG_PROFILE, (Region(96, 16),), nonce, base, target
