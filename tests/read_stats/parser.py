#!/usr/bin/env python3
"""Pure primary-reader parser controls; no compiler/native/tool invocation."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'bench/sync'))
from read_stats import parse, MAXIMUM
from run import internal_counters


def line(job=0, size=65536, chunks=1, server=False):
    prefix = '[server: semantic-reads]' if server else '[semantic-reads]'
    return (f'{prefix} Completed semantic worker job {job} primary reader delivered '
            f'{size} logical bytes in {chunks} chunks (saturated=false).')


def rejected(text, **kwargs):
    try:
        parse(text, **kwargs)
    except ValueError:
        return
    raise AssertionError('accepted malformed report: ' + text[:160])


results = []
first = line()
value = parse(first + '\n' + line(server=True), required=True)
assert value['reported_jobs'] == 2 and value['logical_bytes'] == 131072
assert value['records'][0]['endpoint'] != value['records'][1]['endpoint']
results.append('client/server job IDs have separate namespaces')
assert parse('ordinary noise')['logical_bytes'] is None
assert parse(line(size=0, chunks=0))['logical_bytes'] == 0
results.append('missing reports differ from reported zero')
rejected('', required=True)
rejected(first + '\n' + first)
for text in [first.replace('saturated=false', 'saturated=true'),
             first.replace('primary reader delivered', 'read'),
             first.replace('semantic-reads]', 'semantic-reads-bad]'),
             first.replace('job 0', 'job -1'),
             first.replace('job 0', 'job ' + str(MAXIMUM + 1)),
             first.replace('job 0', 'job ' + '0' * 20),
             first.replace('65536 logical', '-1 logical'),
             first.replace('65536 logical', str(MAXIMUM + 1) + ' logical'),
             first.replace('in 1 chunks', 'in -1 chunks'),
             first.replace('in 1 chunks', 'in ' + str(MAXIMUM + 1) + ' chunks'),
             first.replace('65536 logical', '\u0661 logical'),
             first + ' unexpected',
             line(size=0, chunks=1), line(size=1, chunks=0),
             line(size=1, chunks=2), line(size=1048577, chunks=1)]:
    rejected(text)
results.append('18 missing/duplicate/malformed/saturated/bounds controls reject')
rejected('x' * (4 * 1024 * 1024 + 1))
results.append('retained log cap rejects excessive input')
semantic = ('Remote semantic clone wrote 3072 logical metadata bytes in 1 write calls '
            '(8192 payload bytes; 4096-byte comparison windows; org.firstpair.dng-xmp/0)\n')
old = internal_counters(semantic, 'semantic', 1, 2097152)
assert old['application_read_bytes'] is None and old['primary_reader_reads'] is None
measured = internal_counters(semantic + first, 'semantic', 1, 2097152, primary_reads=True)
assert measured['primary_reader_reads']['logical_bytes'] == 65536
assert measured['application_read_bytes'] is None
try:
    internal_counters(semantic, 'semantic', 1, 2097152, primary_reads=True)
except ValueError:
    pass
else:
    raise AssertionError('measured semantic mode accepted missing diagnostics')
results.append('benchmark default stays off and primary metrics never become total application reads')
work = Path(tempfile.mkdtemp(prefix='unison-read-parser-')).resolve()
sources = [Path(__file__).resolve(), ROOT / 'bench/sync/read_stats.py', ROOT / 'bench/sync/run.py']
report = {'schema': 'unison-primary-read-parser-controls/1', 'groups': results,
          'source_pins': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                          for p in sources},
          'scope': 'Pure Python static receipt/benchmark-counter parsing only; no compiler, native, SDK or Unison process.'}
(work / 'RESULT.json').write_text(json.dumps(report, indent=2) + '\n')
print('PASS', len(results), 'pure parser groups:', work / 'RESULT.json')
