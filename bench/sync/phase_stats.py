"""Bounded local phase diagnostics, not total commit time or lifecycle evidence."""
import json
import math
import re

MAX_LOG=4*1024*1024
MAX_RECORDS=65536
MAXIMUM=(1<<63)-1
PREFIX=re.compile(r'^\[(?:server:\s*)?semantic-timings')
TAG=r'\[(?P<server>server: )?semantic-timings\] '
DECIMAL=r'(?P<seconds>(?:0|[1-9][0-9]{0,19})\.[0-9]{9})'
WORKER=re.compile(TAG+r'Semantic worker job (?P<job>0|[1-9][0-9]{0,18}) stage=(?P<stage>hash|parse|verify|write) calls=(?P<calls>0|[1-9][0-9]{0,18}) inclusive-seconds='+DECIMAL+r'\.')
UNAVAILABLE=re.compile(TAG+r'Semantic worker job (?P<job>0|[1-9][0-9]{0,18}) stage timing unavailable\.')
PUBLICATION=re.compile(TAG+r'Semantic bound publication native-inclusive-seconds='+DECIMAL+r'\.')
PUBLICATION_UNAVAILABLE=re.compile(TAG+r'Semantic bound publication timing unavailable\.')
SCOPE=('Normally returned reader-local inclusive intervals and bound native namespace publication only; '
       'worker phases overlap, include I/O/scheduling and exclude queue/admission/delivery. '
       'Publication precedes later readback/archive work and is not full transfer success or durability. '
       'No phase sum, isolated CPU, whole-application coverage or lifecycle proof is inferred.')


def parse(log, *, required_workers=False):
    if type(log) is not str or len(log)>MAX_LOG:
        raise ValueError('bounded phase diagnostic text required')
    records=[];seen=set();unavailable=set();worker_jobs=set();stages=set();publications=0
    for line in log.splitlines():
        if not PREFIX.match(line):continue
        if len(line)>256 or len(records)==MAX_RECORDS:
            raise ValueError('phase diagnostic record limit exceeded')
        match=WORKER.fullmatch(line)
        kind='worker'
        if match is None:match=UNAVAILABLE.fullmatch(line);kind='worker_unavailable'
        if match is None:match=PUBLICATION.fullmatch(line);kind='namespace_publication'
        if match is None:match=PUBLICATION_UNAVAILABLE.fullmatch(line);kind='namespace_unavailable'
        if match is None:raise ValueError('malformed phase diagnostic')
        endpoint='server' if match['server'] else 'client'
        row=dict(kind=kind,endpoint=endpoint,raw_line=line)
        if kind.startswith('worker'):
            job=int(match['job']);key=endpoint,job
            if job>MAXIMUM:raise ValueError('phase job exceeds signed int64')
            row['job']=job
            if kind=='worker':
                stage=match['stage'];calls=int(match['calls'])
                if not 1<=calls<=MAXIMUM or key in unavailable or (key,stage) in seen:
                    raise ValueError('invalid/duplicate/conflicting worker phase')
                seen.add((key,stage));stages.add(stage)
                row.update(stage=stage,calls=calls)
            else:
                if key in worker_jobs:raise ValueError('conflicting/duplicate unavailable worker')
                unavailable.add(key)
            worker_jobs.add(key)
        else:publications+=1
        if kind in ('worker','namespace_publication'):
            seconds=float(match['seconds'])
            if not math.isfinite(seconds) or seconds<0:raise ValueError('invalid phase duration')
            row['inclusive_seconds']=seconds
        else:row['inclusive_seconds']=None
        records.append(row)
    if required_workers and not worker_jobs:
        raise ValueError('requested semantic worker phase diagnostics missing')
    return dict(schema='unison-local-phase-observations/1',records=records,
        reported_worker_jobs=len(worker_jobs),observed_worker_stages=sorted(stages),
        unavailable_worker_jobs=len(unavailable),namespace_publication_observations=publications,
        worker_absence=None if worker_jobs else 'unavailable or no instrumented worker jobs; not measured zero',
        namespace_absence=None if publications else 'unavailable or unbound namespace path; not measured zero',
        scope=SCOPE)


def validate(value):
    """Rebind saved fields/counts/types to their retained raw records; no IO."""
    if value is None:return None
    if type(value) is not dict or type(value.get('records')) is not list or len(value['records'])>MAX_RECORDS:
        raise ValueError('bounded saved phase record list required')
    lines=[];size=0
    for row in value['records']:
        if type(row) is not dict or type(row.get('raw_line')) is not str or len(row['raw_line'])>256:
            raise ValueError('bounded raw phase record required')
        line=row['raw_line']
        if '\n' in line or '\r' in line:raise ValueError('one raw phase record per line required')
        size+=len(line)+1
        if size>MAX_LOG:raise ValueError('saved phase text exceeds bound')
        lines.append(line)
    parsed=parse('\n'.join(lines))
    try:
        # JSON comparison also rejects bool-for-int and int-for-float substitutions.
        same=json.dumps(parsed,sort_keys=True,allow_nan=False)==json.dumps(value,sort_keys=True,allow_nan=False)
    except (TypeError,ValueError,OverflowError,RecursionError) as error:
        raise ValueError('invalid saved phase field') from error
    if not same:raise ValueError('saved phase fields differ from raw records')
    return parsed
