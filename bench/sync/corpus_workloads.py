"""Pure many-small/mixed/new-file corpus specification; no payload or sync IO.

This is a source contract for a separate batch runner. Existing fixed-cohort
result/log limits must not silently be reused for thousands of file traces.
"""
from dataclasses import dataclass

from workloads import layout

MAX_FILES = 16384
MAX_BYTES = 8*1024**3


@dataclass(frozen=True)
class File:
    relative_path: str
    seed_index: int
    before_present: bool
    edit: str | None
    semantic_update_expected: bool


@dataclass(frozen=True)
class Corpus:
    workload: str
    files: tuple[File, ...]
    file_bytes: int
    packet_bytes: int
    before_files: int
    added_files: int
    semantic_updates: int
    fallback_updates: int
    generated_target_bytes: int
    schema: str = 'unison-generated-corpus-workload/1'
    dispatcher_ready: bool = False
    qualification: str = 'Source-only; batch log/output accounting and actual receiving still required'


def plan(workload, *, count=4096, file_bytes=32768, packet_bytes=512):
    if workload not in ('many-small', 'mostly-eligible-mixed', 'new-files'):
        raise ValueError('explicit corpus workload required')
    if not (type(count) is int and 1024 <= count <= MAX_FILES
            and type(file_bytes) is int and 32768 <= file_bytes <= 262144
            and count*file_bytes <= MAX_BYTES):
        raise ValueError('bounded thousand-file generated corpus required')
    layout(file_bytes, packet_bytes)  # Shared exact header/extent preflight.
    rows=[]
    for index in range(count):
        before = workload != 'new-files'
        edit = 'fixed-xmp' if before else None
        if workload == 'mostly-eligible-mixed':
            # Exactly16/20 eligible changed files; three protected/unsupported
            # updates plus one new file. No private interpretation is required.
            slot = index % 20
            edit = {16:'metadata-raw',17:'metadata-opaque',18:'unsupported-signature',19:None}.get(slot,'fixed-xmp')
            before = slot != 19
        rows.append(File('group-%03d/image-%05d.dng'%(index//64,index), index,
                         before, edit, before and edit=='fixed-xmp'))
    known = sum(x.semantic_update_expected for x in rows)
    before = sum(x.before_present for x in rows)
    return Corpus(workload,tuple(rows),file_bytes,packet_bytes,before,count-before,
                  known,before-known,count*file_bytes)
