"""Original tiny generated fixture controls; no Unison/transport/native calls."""
import hashlib
from pathlib import Path
import tempfile
import unittest

import case


class FixtureControls(unittest.TestCase):
    def test_default_uniform_bytes_preserved(self):
        with tempfile.TemporaryDirectory() as name:
            root=Path(name)/'case';length=case.prepare(root)
            value=(root/'left/synthetic-private.dng').read_bytes()
            self.assertEqual(hashlib.sha256(value).hexdigest(),
                '9d43bb830f7b68f077892689f4dda840adf6e0af7da99ecade0b6cdff897d9e6')
            self.assertEqual(value[case.fixtures.XMP:case.fixtures.XMP+length],
                             b'<synthetic-metadata>1</synthetic-metadata>')

    def test_distinct_body_fixed_and_control_region_unchanged(self):
        with tempfile.TemporaryDirectory() as name:
            base=Path(name);data=[]
            for label,layout in (('a','distinct-raw-v1'),('b','distinct-raw-v1'),('c','uniform-v1')):
                directory=base/label;case.prepare(directory,payload_layout=layout)
                data.append((directory/'left/synthetic-private.dng').read_bytes())
            self.assertEqual(data[0],data[1]);self.assertNotEqual(data[0],data[2])
            self.assertEqual(data[0][:case.fixtures.RAW],data[2][:case.fixtures.RAW])
            self.assertEqual(len(data[0]),1048576)
            # An independent block-boundary uniqueness control, not an image
            # validity or entropy/compression/performance qualification.
            raw=data[0][case.fixtures.RAW:];blocks=[raw[i:i+1024] for i in range(0,len(raw),1024)]
            self.assertEqual(len(set(blocks)),len(blocks))

    def test_unknown_layout_refuses_before_workspace_creation(self):
        with tempfile.TemporaryDirectory() as name:
            root=Path(name)/'absent'
            with self.assertRaises(ValueError):case.prepare(root,payload_layout='unknown')
            self.assertFalse(root.exists())


if __name__=='__main__':unittest.main()
