"""Original tiny fixtures: opaque references remain byte-exact across XMP edits."""
from pathlib import Path
import struct
import tempfile
from fixtures import create, edit, packet, sha256

with tempfile.TemporaryDirectory(prefix='unison-layout-fixture-') as temporary:
    directory=Path(temporary)
    for layout in (False,True):
        first=directory/('layout' if layout else 'strict')
        metadata=create(first,65536,256,3,layout_only=layout)
        before=first.read_bytes()
        assert metadata['before_sha256']==sha256(first)
        assert struct.unpack_from('<H',before,8)[0]==(6 if layout else 4)
        if layout:
            assert struct.unpack_from('<HHII',before,10+4*12)==(50740,1,128,256)
            assert struct.unpack_from('<HHII',before,10+5*12)==(65000,13,1,1024)
            assert struct.unpack_from('<I',before,256)[0]==1024
            assert metadata['opaque_xmp_references']==[256,78]
        other=directory/('repeat-'+str(layout))
        create(other,65536,256,3,layout_only=layout)
        assert other.read_bytes()==before
        expected=edit(first,metadata)
        after=first.read_bytes()
        assert after[:1024]==before[:1024] and after[1280:]==before[1280:]
        assert after[1024:1280]==packet(256,2) and expected!=metadata['before_sha256']
        assert after[metadata['protected_image_offset']:]==before[metadata['protected_image_offset']:]
    try:create(directory/'invalid',65536,256,0,layout_only=1)
    except ValueError:pass
    else:raise AssertionError('untyped layout fixture flag')
    assert not (directory/'invalid').exists()
print('PASS original tiny layout/private-reference fixtures, deterministic bytes and XMP-only edits')
