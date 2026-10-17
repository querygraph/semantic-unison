"""Pure coverage analysis of saved candidate geometry; never vendor recognition.

This accepts only the existing diagnostic's redacted records. It cannot inspect
inline scalar values or the contents of any outlined value, including pointers
hidden in byte arrays. No result authorizes semantic hashing or payload reads.
"""
from private_maker_shape import WIDTHS, MAX_ENTRIES


def analyze(shape, *, payload_length, ifd_offset=0):
    def require(ok, message):
        if not ok:
            raise ValueError(message)
    def integer(value, upper):
        return type(value) is int and 0 <= value <= upper
    require(integer(payload_length, 64 * 1048576) and payload_length >= 6
            and integer(ifd_offset, payload_length - 6), 'bounded payload geometry required')
    require(type(shape) is dict and shape.get('schema') == 'unison-private-maker-candidate-shape/1'
            and shape.get('semantic_eligibility') is False
            and shape.get('private_reference_closure_proved') is False,
            'saved non-authorizing shape diagnostic required')
    rows = shape.get('entries')
    require(type(rows) is list and 1 <= len(rows) <= MAX_ENTRIES, 'bounded candidate table required')
    table_end = ifd_offset + 2 + len(rows) * 12 + 4
    require(table_end <= payload_length, 'candidate table outside payload')
    intervals = [(ifd_offset, table_end, 'candidate_directory')]
    tags = set(); opaque = []; inline = []; outside = []
    for row in rows:
        require(type(row) is dict, 'typed candidate entry required')
        tag, kind, count = (row.get(k) for k in ('tag', 'type', 'count'))
        require(integer(tag, 65535) and tag not in tags and type(kind) is int
                and kind in WIDTHS and integer(count, 2**32 - 1), 'invalid or duplicate entry')
        tags.add(tag)
        size = count * WIDTHS[kind]
        require(type(row.get('value_bytes')) is int and row['value_bytes'] == size
                and type(row.get('out_of_line')) is bool and row['out_of_line'] == (size > 4)
                and row.get('private_pointer_semantics_verified') is False,
                'candidate geometry contradicts entry shape')
        if size <= 4:
            require(row.get('payload_relative_offset') is None
                    and row.get('declared_extent_within_payload') is None,
                    'inline slot is not an observed pointer')
            inline.append(tag)
            continue
        start = row.get('payload_relative_offset')
        require(type(start) is int, 'explicit relative offset required')
        within = 0 <= start <= payload_length and size <= payload_length - start
        require(type(row.get('declared_extent_within_payload')) is bool
                and row['declared_extent_within_payload'] == within, 'extent classification differs')
        if not within:
            outside.append(tag)
            continue
        intervals.append((start, start + size, tag))
        if kind == 7:
            opaque.append(dict(tag=tag, offset=start, bytes=size))
    overlaps = []
    for i, (start, end, owner) in enumerate(intervals):
        for other_start, other_end, other_owner in intervals[:i]:
            if max(start, other_start) < min(end, other_end):
                overlaps.append(dict(owners=[other_owner, owner],
                                     start=max(start, other_start), end=min(end, other_end)))
    gaps = []; cursor = 0
    for start, end, _ in sorted(intervals, key=lambda item: (item[0], item[1])):
        if start > cursor:
            gaps.append(dict(offset=cursor, bytes=start - cursor))
        cursor = max(cursor, end)
    if cursor < payload_length:
        gaps.append(dict(offset=cursor, bytes=payload_length - cursor))
    return dict(schema='unison-private-maker-coverage/1', payload_length=payload_length,
                candidate_directory=dict(offset=ifd_offset, bytes=table_end - ifd_offset),
                inline_tags=inline, opaque_outlined_values=opaque,
                outside_payload_tags=outside, overlaps=overlaps, unclassified_gaps=gaps,
                represented_union_bytes=payload_length - sum(g['bytes'] for g in gaps),
                maker_format_recognized=False, private_reference_closure_proved=False,
                semantic_eligibility=False, payload_bytes_read=0,
                scope='Saved declared extents only; gaps are not verified padding, inline values '
                      'may be pointers, opaque values may contain nested or external references.')
