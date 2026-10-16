"""Installed ExifTool package inventory; OS Perl runtime remains a trust boundary."""
import hashlib
import os
from pathlib import Path
import stat
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from mixed_validation.artifacts import verified_hash
from private_camera_receiving.close import close_descriptors

PACKAGE=Path('/usr/local/Cellar/exiftool/13.10/libexec/lib')
SCRIPT=Path('/usr/local/Cellar/exiftool/13.10/bin/exiftool')
PERL=Path('/usr/bin/perl5.34')


def system_perl():
    fd=os.open(PERL,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC)
    try:
        before=os.fstat(fd)
        if (not stat.S_ISREG(before.st_mode) or before.st_uid!=0 or before.st_nlink!=1
                or not 0<before.st_size<=16*1048576 or before.st_mode&0o022):
            raise ValueError('owned system Perl interpreter identity refused')
        raw=bytearray()
        while len(raw)<before.st_size:
            block=os.read(fd,min(65536,before.st_size-len(raw)))
            if not block:raise ValueError('short Perl interpreter read')
            raw.extend(block)
        stamp=lambda s:(s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns,s.st_mode,s.st_uid)
        if os.read(fd,1) or stamp(before)!=stamp(os.fstat(fd)) or stamp(before)!=stamp(os.lstat(PERL)):
            raise ValueError('Perl interpreter changed')
        return dict(path=str(PERL),bytes=before.st_size,sha256=hashlib.sha256(raw).hexdigest())
    finally:close_descriptors([fd])


def package_paths():
    if PACKAGE.resolve()!=PACKAGE:raise ValueError('canonical installed package required')
    paths=[]
    for p in PACKAGE.rglob('*'):
        s=os.lstat(p)
        if stat.S_ISDIR(s.st_mode):continue
        if not stat.S_ISREG(s.st_mode):raise ValueError('package symlink/special entry refused')
        paths.append(p)
    if not 1<=len(paths)<=512:raise ValueError('bounded exact package required')
    return sorted(paths)


def capture():
    # Source/tool installation only. This function never opens a media input.
    rows=[];paths=package_paths()
    for p in [SCRIPT,*paths]:
        item=dict(path=str(p),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
        verified_hash(item);rows.append(item)
    if package_paths()!=paths:raise ValueError('installed package roster changed')
    return dict(schema='unison-mixed-exiftool-package/1',version='13.10',
                executable=rows[0],modules=rows[1:],system_interpreter=system_perl(),
                package_root=str(PACKAGE),package_roster_complete=True,
                full_runtime_dependency_inventory_complete=False,
                trust_boundary='Existing OS Perl module search paths and system dylibs; not a hermetic Perl runtime or image/pixel qualification.')


def verify(metadata):
    from mixed_validation.execute import document
    verified_hash(metadata['inventory'])
    record=document(metadata['inventory']['path'],metadata['inventory']['sha256'])
    if (record.get('schema')!='unison-mixed-exiftool-package/1'
            or record.get('version')!=metadata['version'] or metadata['version']!='13.10'
            or record.get('executable')!=metadata['executable']
            or record.get('package_root')!=str(PACKAGE)
            or record.get('package_roster_complete') is not True
            or record.get('full_runtime_dependency_inventory_complete') is not False):
        raise ValueError('exact metadata package contract differs')
    rows=record['modules'];expected=package_paths()
    if type(rows) is not list or [r['path'] for r in rows]!=[str(p) for p in expected]:
        raise ValueError('exact metadata package roster differs')
    for item in [record['executable'],*rows]:verified_hash(item)
    if system_perl()!=record['system_interpreter'] or package_paths()!=expected:
        raise ValueError('metadata runtime/package changed')
    return dict(package_modules_verified=len(rows),system_interpreter_verified=True,
                full_runtime_dependency_inventory_complete=False,execution_authorized=False)
