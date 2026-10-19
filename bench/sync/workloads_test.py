"""Independent tiny byte-oracle controls; no paths, native calls or benchmark IO."""
from dataclasses import replace
import struct
import unittest
from workloads import KINDS, initial_writes, layout, packet, recipe


def materialize(source, changes, length):
    output = bytearray(source + bytes(length-len(source)))
    for change in changes:
        if change.xor:
            for i, value in enumerate(change.data):
                output[change.offset+i] ^= value
        else:
            output[change.offset:change.offset+len(change.data)] = change.data
    return bytes(output)


class Workloads(unittest.TestCase):
    def setUp(self):
        self.layout = layout(32768, 512, 1024)
        noise = bytes((i*37+13) & 255 for i in range(32768))
        self.source = materialize(noise, initial_writes(self.layout), len(noise))

    def test_header_independent_directory_decode(self):
        count, = struct.unpack_from('<H', self.source, 8)
        rows = dict((tag, (typ, count, value)) for tag, typ, count, value in
                    (struct.unpack_from('<HHII', self.source, 10+12*i) for i in range(count)))
        self.assertEqual(rows[700], (1, 512, 1024))
        self.assertEqual(rows[513], (4, 1, 31744))
        self.assertEqual(rows[514], (4, 1, 1024))
        self.assertEqual(rows[273], (4, 1, 4096))
        self.assertEqual(rows[279], (4, 1, 27648))

    def test_fixed_edit_changes_only_declared_packet(self):
        p = recipe(self.layout, 'fixed-xmp')
        target = materialize(self.source, p.writes, p.target_size)
        self.assertEqual(target[:1024], self.source[:1024])
        self.assertEqual(target[1536:], self.source[1536:])
        self.assertEqual(target[1024:1536], packet(512, 2))

    def test_growing_packet_relocates_and_preserves_all_old_payload(self):
        p = recipe(self.layout, 'growing-xmp', growth=256)
        target = materialize(self.source, p.writes, p.target_size)
        self.assertEqual(len(target), 32768+768)
        self.assertEqual(struct.unpack_from('<II', target, 62), (768, 32768))
        self.assertEqual(target[32768:], packet(768, 2))
        self.assertEqual(target[70:32768], self.source[70:])
        self.assertEqual(target[:62], self.source[:62])
        self.assertEqual(p.expected_transfer, 'exact-fallback-fixture')

    def test_preview_raw_opaque_each_changes_exact_selected_byte(self):
        for kind, position in [('metadata-preview', 31744), ('metadata-raw', 4096), ('metadata-opaque', 256)]:
            p = recipe(self.layout, kind)
            target = materialize(self.source, p.writes, p.target_size)
            outside = [i for i, (a, b) in enumerate(zip(self.source, target))
                       if a != b and not 1024 <= i < 1536]
            self.assertEqual(outside, [position])
            self.assertEqual(p.expected_transfer, 'exact-fallback-fixture')

    def test_boolean_and_overflow_dimensions_refuse(self):
        for args in [(True, 512, 1024), (2147483649, 512, 1024),
                     (32768, True, 1024), (32768, 1048576, 1024), (32768, 512, True)]:
            with self.assertRaises(ValueError): layout(*args)
        for growth in [True, 0, -1, 1048576]:
            with self.assertRaises(ValueError): recipe(self.layout, 'growing-xmp', growth=growth)

    def test_forged_layout_and_unknown_recipe_refuse(self):
        for value in [replace(self.layout, image_offset=0), replace(self.layout, packet_count_field=0), replace(self.layout, header=b'bad')]:
            with self.assertRaises(ValueError): recipe(value, 'fixed-xmp')
        with self.assertRaises(ValueError): recipe(self.layout, 'unknown')
        self.assertEqual(len(KINDS), 5)


if __name__ == '__main__':
    unittest.main()
