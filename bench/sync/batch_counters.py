"""Batch-specific aggregate path counters; no ambiguous generic run import.

Counts bind to independently pinned successful call logs, not predictions. Mixed
per-file path attribution and physical writes are deliberately not inferred.
"""
import re

SDE = re.compile(r'Remote semantic clone wrote (\d+) logical metadata bytes in (\d+) write calls '\
                 r'\((\d+) payload bytes; (\d+)-byte comparison windows; ([^)]+)\)')
PRESERVED = re.compile(r'(?<!Local )Receiver clone preserved (\d+) logical bytes')


def audit(log, mode, corpus):
    if type(log) is not str or mode not in ('ordinary','receiver-clone','semantic'):
        raise ValueError('typed exact batch path observations required')
    semantic=SDE.findall(log);preserved=[int(n) for n in PRESERVED.findall(log)]
    starts=log.count('Using immutable receiver clone basis')
    source=log.count('Local source clone completed before semantic planning')
    if source or starts!=len(preserved) or starts>corpus.before_files:
        raise ValueError('remote batch clone path evidence inconsistent')
    if mode=='ordinary' and (semantic or starts):raise ValueError('ordinary mode selected new path')
    if mode=='receiver-clone' and (semantic or starts!=corpus.before_files):raise ValueError('receiver bases not all cloned')
    if mode=='semantic' and len(semantic)!=corpus.semantic_updates:
        raise ValueError('semantic update count differs from exact generated class count')
    if mode=='semantic' and starts>corpus.fallback_updates:
        raise ValueError('fallback clone count exceeds existing fallback bases')
    total=corpus.generated_target_bytes
    logical=total-len(semantic)*corpus.file_bytes-sum(preserved)+sum(int(row[0]) for row in semantic)
    if not 0<=logical<=total:raise ValueError('logical materialization model outside output extents')
    return dict(semantic_updates=len(semantic),receiver_clone_started=starts,
        receiver_clone_completed=len(preserved),same_offset_inherited_bytes=sum(preserved),
        semantic_returned_logical_write_bytes=sum(int(row[0]) for row in semantic),
        semantic_profiles=sorted({row[4] for row in semantic}),
        modeled_non_inherited_logical_bytes=logical,physical_write_bytes=None,
        mixed_per_file_path_attribution_proved=False)
