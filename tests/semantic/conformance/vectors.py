"""Fixed small goldens and deterministic bounded conformance cases."""
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import struct
import sys

sys.dont_write_bytecode = True

from reference import (DNG_PROFILE, MAX_ENVELOPE, MAX_INT, MAX_PAYLOAD,
                       MAX_REGION, MAX_REQUEST, MULTI_PROFILE, Envelope, Invalid,
                       Proof, Region, binds, decode_envelope, decode_request,
                       digest, encode_envelope, encode_request, golden_values,
                       inspect, plan, u64)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def golden_files():
    result = {}
    metadata = []
    for name, profile, regions, nonce, base, target in golden_values():
        before, after = inspect(base, profile, regions), inspect(target, profile, regions)
        envelope = plan(nonce, before, after)
        files = {"base": base, "target": target, "sde": encode_envelope(envelope),
                 "sdr": encode_request(nonce, before)}
        for suffix, data in files.items():
            result[f"{name}.{suffix}"] = data
        metadata.append({"name": name, "profile": profile.decode(),
                         "nonce_hex": nonce.hex(),
                         "regions": [{"offset": r.offset, "length": r.length} for r in regions],
                         "preserved_sha256": before.preserved.hex(),
                         "files": {suffix: {"bytes": len(data), "sha256": sha(data)}
                                   for suffix, data in files.items()}})
    result["manifest.json"] = (json.dumps({
        "format": "independent-sde-sdr-goldens-v1",
        "normative_source": "doc/semantic-delta-v0.md",
        "generation": "Python standard-library reference.py; no production calls",
        "vectors": metadata}, indent=2) + "\n").encode()
    return result


def verify_goldens(directory):
    for name, expected in golden_files().items():
        actual = (directory / name).read_bytes()
        if actual != expected:
            raise AssertionError(f"committed independent golden differs: {name}")


def set_integer(data, at, value):
    return data[:at] + struct.pack(">Q", value) + data[at + 8:]


def mutate_byte(data, at):
    return data[:at] + bytes([data[at] ^ 1]) + data[at + 1:]


def wire_cases():
    """(name, wire kind, exact bytes, decoder ceiling, accepted, error class).

    Every expected acceptance is obtained from the independent reference
    decoder. Error-class text is used only for the advertised outer caps; other
    invalid cases do not depend on production error-message wording.
    """
    cases = []

    def add(name, kind, data, limit=MAX_PAYLOAD, error=""):
        try:
            if kind == "sde":
                value = decode_envelope(data, limit)
                assert encode_envelope(value) == data
            else:
                nonce, value = decode_request(data)
                assert encode_request(nonce, value) == data
            accepted = True
        except Invalid:
            accepted = False
        cases.append((name, kind, data, limit, accepted, error))

    goldens = golden_files()
    response, request = goldens["multi.sde"], goldens["multi.sdr"]
    profile_length = len(MULTI_PROFILE)
    sde_size = 16 + profile_length + 32
    sde_count = sde_size + 8 + 96
    sde_op = sde_count + 8
    sdr_size = 48 + profile_length
    sdr_count = sdr_size + 8 + 64
    sdr_op = sdr_count + 8
    for name in ("multi", "dng-le", "dng-be"):
        add(name, "sde", goldens[f"{name}.sde"])
        add(name, "sdr", goldens[f"{name}.sdr"])
    for kind, data, profile_at, size_at, count_at, op_at in (
            ("sde", response, 8, sde_size, sde_count, sde_op),
            ("sdr", request, 40, sdr_size, sdr_count, sdr_op)):
        add("unknown-version", kind, mutate_byte(data, 7))
        add("unknown-magic", kind, mutate_byte(data, 0))
        add("profile-zero", kind, set_integer(data, profile_at, 0))
        add("profile-over-limit", kind, set_integer(data, profile_at, 129))
        add("profile-u64-overflow", kind, set_integer(data, profile_at, 1 << 63))
        add("size-u64-overflow", kind, set_integer(data, size_at, 1 << 63))
        add("count-zero", kind, set_integer(data, count_at, 0))
        add("count-over-limit", kind, set_integer(data, count_at, 65))
        add("count-u64-overflow", kind, set_integer(data, count_at, (1 << 64) - 1))
        add("zero-file-with-operation", kind, set_integer(data, size_at, 0))
        add("offset-u64-overflow", kind, set_integer(data, op_at, 1 << 63))
        add("offset-past-eof", kind, set_integer(data, op_at, 33))
        add("length-zero", kind, set_integer(data, op_at + 8, 0))
        add("length-over-limit", kind, set_integer(data, op_at + 8, MAX_REGION + 1))
        add("length-u64-overflow", kind, set_integer(data, op_at + 8, 1 << 63))
        add("extent-past-eof", kind, set_integer(data, op_at, 31))
        # The second operation follows the first record and (SDE only) payload.
        second_at = op_at + (80 + 3 if kind == "sde" else 48)
        add("overlapping-operation", kind, set_integer(data, second_at, 2))
        third_at = second_at + (80 + 2 if kind == "sde" else 48)
        add("out-of-order-operation", kind, set_integer(data, third_at, 0))
        add("trailing-byte", kind, data + b"\0")
        add("missing-nonce-byte", kind, data[:(16 + profile_length if kind == "sde" else 8)] +
            data[(17 + profile_length if kind == "sde" else 9):])
    add("replacement-hash-mismatch", "sde", mutate_byte(response, sde_op + 80))
    add("replacement-hash-field-mismatch", "sde", mutate_byte(response, sde_op + 48))

    # Standalone decoding cannot authorize these otherwise canonical records.
    envelope = decode_envelope(response)
    for name, value in (
            ("nonce-zero", replace(envelope, nonce=bytes(32))),
            ("unknown-profile", replace(envelope, profile=b"unregistered.conformance/0")),
            ("profile-length-one", replace(envelope, profile=b"x")),
            ("profile-length-128", replace(envelope, profile=b"p" * 128)),
            ("wrong-whole-base-proof", replace(envelope, base=digest(b"wrong base"))),
            ("wrong-preservation-proof", replace(envelope, preserved=digest(b"wrong preservation"))),
            ("wrong-old-range-proof", replace(envelope, old_hashes=(digest(b"wrong old"),) + envelope.old_hashes[1:])),
            ("wrong-target-digest", replace(envelope, target=digest(b"wrong target"))),
            ("incomplete-local-region-list", replace(envelope, regions=envelope.regions[:-1],
                                                     old_hashes=envelope.old_hashes[:-1],
                                                     payloads=envelope.payloads[:-1]))):
        add(name, "sde", encode_envelope(value))

    def synthetic(profile, regions):
        payloads = tuple(bytes([65 + i % 26]) * r.length for i, r in enumerate(regions))
        return Envelope(profile, bytes(range(32)), max(r.offset + r.length for r in regions),
                        digest(b"claimed base"), digest(b"claimed target"),
                        digest(b"claimed complement"), tuple(regions),
                        tuple(digest(b"claimed old" + u64(i)) for i in range(len(regions))), payloads)

    def both(name, value):
        add(name, "sde", encode_envelope(value))
        proof = Proof(value.profile, value.size, value.base, value.preserved,
                      value.regions, value.old_hashes)
        add(name, "sdr", encode_request(value.nonce, proof))

    both("single-byte-at-signed-int64-eof", synthetic(b"boundary/0", [Region(MAX_INT - 1, 1)]))
    last_byte = encode_envelope(synthetic(b"boundary/0", [Region(MAX_INT - 1, 1)]))
    at = 16 + len(b"boundary/0") + 32 + 8 + 96 + 8
    add("extent-end-signed-int64-overflow", "sde", set_integer(last_byte, at, MAX_INT))
    last_proof = Proof(b"boundary/0", MAX_INT, digest(b"claimed base"), digest(b"claimed complement"),
                       (Region(MAX_INT - 1, 1),), (digest(b"claimed old"),))
    last_request = encode_request(bytes(range(32)), last_proof)
    at = 48 + len(b"boundary/0") + 8 + 64 + 8
    add("extent-end-signed-int64-overflow", "sdr", set_integer(last_request, at, MAX_INT))
    for length in (1, MAX_REGION - 1, MAX_REGION):
        both(f"region-bytes-{length}", synthetic(b"boundary/0", [Region(0, length)]))
    # A maximal valid envelope has a128-byte profile,64 records,16MiB payload.
    # Sixteen large packets leave room for the other48 one-byte packets.
    lengths = [MAX_REGION - 3] * 16 + [1] * 48
    offsets = []
    cursor = 0
    for length in lengths:
        offsets.append(Region(cursor, length))
        cursor += length
    assert cursor == MAX_PAYLOAD
    maximum = synthetic(b"p" * 128, offsets)
    both("maximum-valid-wire-shape", maximum)
    max_sde = encode_envelope(maximum)
    assert len(max_sde) == MAX_PAYLOAD + 5408
    assert len(encode_request(maximum.nonce, Proof(maximum.profile, maximum.size,
               maximum.base, maximum.preserved, maximum.regions, maximum.old_hashes))) == 3328
    add("declared-payload-exact", "sde", encode_envelope(synthetic(b"boundary/0", [Region(0, 16)])), 16)
    add("declared-payload-plus-one", "sde", encode_envelope(synthetic(b"boundary/0", [Region(0, 17)])), 16)
    add("declared-DNG-payload-exact", "sde", encode_envelope(synthetic(DNG_PROFILE, [Region(0, MAX_REGION)])), MAX_REGION)
    add("declared-DNG-payload-plus-one", "sde", encode_envelope(synthetic(DNG_PROFILE,
        [Region(0, MAX_REGION), Region(MAX_REGION, 1)])), MAX_REGION)
    add("declared-payload-zero", "sde", response, 0)
    add("declared-payload-over-core", "sde", response, MAX_PAYLOAD + 1)
    # Extend a valid16MiB request by one adjacent region. No packet allocation
    # is needed for SDR, and SDE framing reaches the payload sum check first.
    overflow_regions = (Region(MAX_PAYLOAD, 1),)
    short_max = synthetic(b"boundary/0", [Region(i * MAX_REGION, MAX_REGION) for i in range(16)])
    overflow_sde = set_integer(encode_envelope(short_max), 16 + len(short_max.profile) + 32, MAX_PAYLOAD + 1)
    count_at = 16 + len(short_max.profile) + 32 + 8 + 96
    overflow_sde = set_integer(overflow_sde, count_at, 17) + u64(MAX_PAYLOAD) + u64(1) + digest(b"old") + digest(b"z") + b"z"
    add("aggregate-payload-plus-one", "sde", overflow_sde)
    short_proof = Proof(short_max.profile, MAX_PAYLOAD + 1, short_max.base, short_max.preserved,
                        short_max.regions, short_max.old_hashes)
    overflow_sdr = encode_request(short_max.nonce, short_proof)
    sdr_count_at = 48 + len(short_max.profile) + 8 + 64
    overflow_sdr = set_integer(overflow_sdr, sdr_count_at, 17) + u64(overflow_regions[0].offset) + u64(1) + digest(b"old")
    add("aggregate-payload-plus-one", "sdr", overflow_sdr)
    add("envelope-cap-minus-one", "sde", bytes(MAX_ENVELOPE - 1))
    add("envelope-cap-exact", "sde", bytes(MAX_ENVELOPE))
    add("envelope-cap-plus-one", "sde", bytes(MAX_ENVELOPE + 1), error="envelope too large")
    add("request-cap-minus-one", "sdr", bytes(MAX_REQUEST - 1))
    add("request-cap-exact", "sdr", bytes(MAX_REQUEST))
    add("request-cap-plus-one", "sdr", bytes(MAX_REQUEST + 1), error="request too large")
    return cases


def case_manifest(cases):
    return {"format": "independent-sde-sdr-boundaries-v1",
            "generation": "deterministic vectors.py recipes; no production calls",
            "maximum_structural_wire_bytes": {"sde": MAX_PAYLOAD + 5408, "sdr": 3328},
            "declared_outer_caps_bytes": {"sde": MAX_ENVELOPE, "sdr": MAX_REQUEST},
            "cases": [{"name": name, "wire": kind, "bytes": len(data), "sha256": sha(data),
                       "max_payload": limit, "structurally_accepted": accepted,
                       "expected_outer_cap_error": error or None}
                      for name, kind, data, limit, accepted, error in cases]}


def write_goldens(directory):
    directory.mkdir(parents=True, exist_ok=True)
    for name, data in golden_files().items():
        (directory / name).write_bytes(data)
    (directory / "boundary-manifest.json").write_text(json.dumps(case_manifest(wire_cases()), indent=2) + "\n")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Regenerate independent committed conformance goldens.")
    parser.add_argument("--write-goldens", action="store_true", required=True)
    arguments = parser.parse_args()
    write_goldens(Path(__file__).resolve().parent / "golden")
