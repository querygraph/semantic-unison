"""Prospective nine-byte model-field observation; no executable payload route.

Caller must separately own an exact IO admission and bind the saved shape and
source epoch. A model-like string is evidence for investigation, not vendor
recognition, a pointer grammar, or semantic eligibility.
"""
import os
from pathlib import Path
import stat
import time
from private_camera_receiving.close import close_descriptors
from private_maker_coverage import analyze
from private_maker_slice import FIELDS, stamp

PAYLOAD_OFFSET = 10990
PAYLOAD_LENGTH = 6556
TAG = 21
RELATIVE_OFFSET = 450
READ_BYTES = 9


def selected_field(saved_shape):
    """Check geometry from the consumed slice, without opening camera data."""
    coverage = analyze(saved_shape, payload_length=PAYLOAD_LENGTH)
    if coverage['overlaps'] or coverage['outside_payload_tags']:
        raise ValueError('unambiguous in-payload geometry required')
    rows = saved_shape['entries']
    match = [row for row in rows if row['tag'] == TAG]
    if (len(rows) != 33 or len(match) != 1
            or match[0]['type'] != 2 or match[0]['count'] != READ_BYTES
            or match[0]['payload_relative_offset'] != RELATIVE_OFFSET):
        raise ValueError('exact saved candidate ASCII field required')
    return dict(tag=TAG, offset=PAYLOAD_OFFSET + RELATIVE_OFFSET, bytes=READ_BYTES)


def interpret(raw):
    if type(raw) is not bytes or len(raw) != READ_BYTES:
        raise ValueError('exact nine candidate bytes required')
    # Require one terminal NUL, printable ASCII, and nonempty trimmed content.
    # Preserve invalid bytes in hex for a faithful bounded diagnostic.
    text = None
    if raw[-1:] == b'\0' and all(32 <= b <= 126 for b in raw[:-1]) and raw[:-1].strip():
        text = raw[:-1].decode('ascii')
    return dict(schema='unison-private-maker-model-observation/1', tag=TAG,
                raw_hex=raw.hex(), candidate_text=text, printable_terminated_ascii=text is not None,
                maker_format_recognized=False, private_reference_closure_proved=False,
                semantic_eligibility=False,
                scope='One candidate model field; text alone identifies neither vendor nor private grammar.')


def read_candidate(source, saved_shape, *, deadline):
    field = selected_field(saved_shape)
    if (type(source) is not dict or set(source) != {'path', 'identity'}
            or type(source['path']) is not str or not Path(source['path']).is_absolute()
            or '..' in Path(source['path']).parts):
        raise ValueError('exact absolute source binding required')
    expected = source['identity']
    if (type(expected) is not dict or set(expected) != set(FIELDS)
            or any(type(v) is not int or v < 0 for v in expected.values())
            or not field['offset'] + READ_BYTES <= expected['st_size'] <= 512 * 1048576
            or type(deadline) not in (int, float) or not time.monotonic() < deadline < float('inf')):
        raise ValueError('bounded source epoch and fresh finite deadline required')
    fd = os.open(source['path'], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC)
    try:
        def fence():
            if stamp(os.fstat(fd)) != expected or stamp(os.lstat(source['path'])) != expected:
                raise ValueError('candidate source epoch or name changed')
        fence()
        info = os.fstat(fd)
        if (not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or info.st_uid != os.getuid()
                or stat.S_IMODE(info.st_mode) != 0o400):
            raise ValueError('owned single-link readonly retained input required')
        if time.monotonic() >= deadline:
            raise ValueError('candidate observation deadline elapsed before read')
        raw = os.pread(fd, READ_BYTES, field['offset'])
        fence()
        if time.monotonic() >= deadline:
            raise ValueError('candidate observation deadline elapsed after read')
        result = interpret(raw)
        result.update(read_range=dict(offset=field['offset'], requested=READ_BYTES, received=len(raw)),
                      source_epoch_unchanged=True, full_input_hash_computed=False,
                      fd_closure_proved_by_return=True)
        return result
    finally:
        close_descriptors([fd])
