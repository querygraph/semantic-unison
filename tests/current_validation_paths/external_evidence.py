"""Source-bound original COPY/MERGE child/group records, not generic stdout trust.

Caller must bind every prepared fixture script and counter to the exact current
production executable. The fixtures never print External result lookalikes.
No process operation or release authority is supplied by this parser.
"""
from supervised_external.external_records import parse


def audit(log,expected,transport_pids):
    if type(expected) is not list or len(expected)>2:raise ValueError('bounded original external expectations required')
    records=parse(log)
    if len(records)!=len(expected):raise ValueError('all external children must have source-bound counters')
    remaining={}
    for record in records:
        key=(record.endpoint,record.pid)
        if key in remaining:raise ValueError('duplicate external process observation')
        remaining[key]=record
    result=[]
    for entry in expected:
        if (type(entry) is not dict or set(entry)!={'endpoint','pid','fixture_pid','kind'} or entry['endpoint'] not in ('client','server')
            or entry['kind'] not in ('copy','merge') or type(entry['pid']) is not int or not 0<entry['pid']<2**31
            or entry['pid'] in transport_pids or type(entry['fixture_pid']) is not int or not 0<entry['fixture_pid']<2**31
            or entry['fixture_pid'] in transport_pids):raise ValueError('exact distinct original external child identity required')
        key=(entry['endpoint'],entry['pid'])
        if key not in remaining:raise ValueError('external counter/process binding differs')
        record=remaining.pop(key)
        if (record.status!=('exit',0) or record.outcome!='completed' or record.cpu_weight!=1
            or record.group_observation!='observed' or record.other_members!=0 or record.capture_truncated):
            raise ValueError('external fixture child/group/capture not normally settled')
        result.append(dict(expected=entry,actual_status=list(record.status),other_group_members_before_reap=0,
            source_fixture_binding_required=True,resource_release_authorized=False))
    if remaining:raise ValueError('unbound external child remains')
    return result
