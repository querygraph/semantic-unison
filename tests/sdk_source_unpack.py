"""Pure official-source ZIP preflight; extraction uses the retained OS tool.

No automatic extraction, SDK execution, permission grant or resource release.
Reject archive links and unsafe names before an extractor is ever started.
"""
from pathlib import PurePosixPath
import stat
import zipfile

ROOT='dng_sdk_1_7_1'
MAX_FILES=8192
MAX_FILE=64*1048576
MAX_TOTAL=160*1048576


def members(entries):
    if type(entries) is not list or not 0<len(entries)<=MAX_FILES:raise ValueError('bounded exact ZIP inventory required')
    paths={};total=0;rows=[]
    for item in entries:
        name=item.filename
        if (type(name) is not str or not name or len(name.encode())>4096 or '\\' in name
                or any(ord(c)<32 or ord(c)==127 for c in name)):
            raise ValueError('unsafe source member name')
        canonical=name[:-1] if name.endswith('/') else name;path=PurePosixPath(canonical)
        if (str(path)!=canonical or path.is_absolute() or '..' in path.parts or not path.parts
                or path.parts[0]!=ROOT or any(len(p.encode())>255 or ':' in p for p in path.parts)):
            raise ValueError('source member escapes exact SDK root')
        if canonical in paths:raise ValueError('duplicate normalized source entry')
        if type(item.file_size) is not int or type(item.compress_size) is not int or not 0<=item.file_size<=MAX_FILE or item.compress_size<0:
            raise ValueError('invalid or oversized source entry')
        if item.flag_bits&1 or item.compress_type not in (zipfile.ZIP_STORED,zipfile.ZIP_DEFLATED):raise ValueError('encrypted/unreviewed ZIP member')
        mode=(item.external_attr>>16)&0xffff;kind=stat.S_IFMT(mode);directory=item.is_dir()
        if directory:
            if kind not in (0,stat.S_IFDIR) or item.file_size!=0:raise ValueError('invalid source directory entry')
        elif kind not in (0,stat.S_IFREG):raise ValueError('archive links/devices/FIFO refused')
        total+=item.file_size
        if total>MAX_TOTAL:raise ValueError('declared source total exceeds bound')
        paths[canonical]=directory;rows.append(dict(path=canonical,directory=directory,bytes=item.file_size,crc32=item.CRC))
    for name in paths:
        for parent in PurePosixPath(name).parents:
            if str(parent) in paths and not paths[str(parent)]:raise ValueError('file/directory prefix collision')
    return dict(entries=len(rows),files=sum(not r['directory'] for r in rows),directories=sum(r['directory'] for r in rows),
                declared_bytes=total,members=rows,archive_links_allowed=False)
