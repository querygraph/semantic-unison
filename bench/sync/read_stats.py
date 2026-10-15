"""Strict parsing of optional, source-pinned primary-reader diagnostics.

These counters are not total application reads, syscalls or physical I/O.
"""
import re

PREFIX = re.compile(r'^\[(?:server: )?semantic-reads')
RECORD = re.compile(
    r'^\[(?P<server>server: )?semantic-reads\] Completed semantic worker job '
    r'(?P<job>[0-9]{1,19}) primary reader delivered (?P<bytes>[0-9]{1,19}) '
    r'logical bytes in (?P<chunks>[0-9]{1,19}) chunks \(saturated=false\)\.$')
MAXIMUM = (1 << 63) - 1
SCOPE = ('Delivered stable worker primary readers only; excludes nested readers '
         '(including output verification), legacy/validator reads, partial or '
         'cancelled readers, channel prefetch, syscalls and physical disk I/O.')


def parse(log, *, required=False):
    if len(log) > 4 * 1024 * 1024:
        raise ValueError('primary-reader log exceeds retained parser bound')
    records = []
    seen = set()
    for line in log.splitlines():
        if not PREFIX.match(line):
            continue
        match = RECORD.fullmatch(line) if len(line) <= 256 else None
        if match is None:
            raise ValueError('malformed or saturated primary-reader report')
        endpoint = 'server' if match['server'] else 'client'
        job, size, chunks = (int(match[name]) for name in ('job', 'bytes', 'chunks'))
        if max(job, size, chunks) > MAXIMUM:
            raise ValueError('primary-reader field exceeds signed int64')
        if (size == 0) != (chunks == 0) or size < chunks or size > chunks * 1048576:
            raise ValueError('impossible primary-reader byte/chunk relation')
        key = endpoint, job
        if key in seen or len(records) == 65536:
            raise ValueError('duplicate or excessive primary-reader reports')
        seen.add(key)
        records.append({'endpoint': endpoint, 'job': job,
                        'logical_bytes': size, 'chunks': chunks})
    if required and not records:
        raise ValueError('requested primary-reader diagnostics missing')
    return {'reported_jobs': len(records),
            'logical_bytes': sum(row['logical_bytes'] for row in records) if records else None,
            'chunks': sum(row['chunks'] for row in records) if records else None,
            'records': records, 'scope': SCOPE,
            'absence': None if records else 'unavailable or no primary-reader jobs; not measured zero'}
