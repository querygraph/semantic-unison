"""Original synthetic coverage controls; no private-media reads."""
import copy
import unittest
from private_maker_coverage import analyze


def row(tag, kind=7, count=8, offset=18):
    widths = {3: 2, 4: 4, 7: 1}
    size = widths[kind] * count
    return dict(tag=tag, type=kind, count=count, value_bytes=size, out_of_line=size > 4,
                payload_relative_offset=offset if size > 4 else None,
                declared_extent_within_payload=(0 <= offset and offset + size <= 64) if size > 4 else None,
                private_pointer_semantics_verified=False)


def shape(*rows):
    return dict(schema='unison-private-maker-candidate-shape/1', entries=list(rows),
                semantic_eligibility=False, private_reference_closure_proved=False)


class Coverage(unittest.TestCase):
    def test_gaps_not_padding_and_no_authority(self):
        result = analyze(shape(row(1)), payload_length=64)
        self.assertEqual(result['unclassified_gaps'], [dict(offset=26, bytes=38)])
        self.assertEqual(result['represented_union_bytes'], 26)
        self.assertEqual(result['payload_bytes_read'], 0)
        for key in ('maker_format_recognized', 'semantic_eligibility', 'private_reference_closure_proved'):
            self.assertIs(result[key], False)

    def test_overlap_directory_and_other_value(self):
        result = analyze(shape(row(1, offset=20), row(2, offset=24)), payload_length=64)
        self.assertEqual(len(result['overlaps']), 3)
        self.assertEqual(result['represented_union_bytes'], 32)

    def test_adjacent_values_are_not_overlap(self):
        result = analyze(shape(row(1, offset=30), row(2, offset=38)), payload_length=64)
        self.assertEqual(result['overlaps'], [])
        self.assertEqual(result['unclassified_gaps'], [dict(offset=46, bytes=18)])

    def test_inline_scalar_and_outside_extent_remain_unknown(self):
        result = analyze(shape(row(1, kind=4, count=1), row(2, offset=-1)), payload_length=64)
        self.assertEqual(result['inline_tags'], [1])
        self.assertEqual(result['outside_payload_tags'], [2])

    def test_nonzero_directory_start(self):
        result = analyze(shape(row(1, offset=22)), payload_length=64, ifd_offset=4)
        self.assertEqual(result['unclassified_gaps'][0], dict(offset=0, bytes=4))

    def test_reject_contradictions_and_boolean_integers(self):
        base = shape(row(1))
        for field, value in [('tag', True), ('type', True), ('count', True),
                             ('value_bytes', True), ('out_of_line', 1),
                             ('declared_extent_within_payload', 1),
                             ('payload_relative_offset', True), ('value_bytes', 9)]:
            changed = copy.deepcopy(base); changed['entries'][0][field] = value
            with self.assertRaises(ValueError): analyze(changed, payload_length=64)

    def test_reject_duplicate_truncated_and_authorizing_input(self):
        for bad in (shape(row(1), row(1)), shape(), dict(shape(row(1)), semantic_eligibility=True)):
            with self.assertRaises(ValueError): analyze(bad, payload_length=64)
        with self.assertRaises(ValueError): analyze(shape(row(1)), payload_length=10)
        with self.assertRaises(ValueError): analyze(shape(row(1)), payload_length=True)


if __name__ == '__main__': unittest.main()
