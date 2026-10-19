"""Pure independent final-counter slice binding for original named cases."""
from pathlib import PurePosixPath as Path


def slices(intent,next_intent,counters):
    if type(counters) is not dict or set(counters)!={'client','server','copy','merge'}:raise ValueError('all four exact final counter streams required')
    before={**intent['before_fake_helper_counts'],**intent['before_external_counts']}
    end=({**next_intent['before_fake_helper_counts'],**next_intent['before_external_counts']} if next_intent is not None else {k:len(v) for k,v in counters.items()})
    if set(before)!=set(counters) or set(end)!=set(counters):raise ValueError('all counter streams required')
    values={}
    for name,stream in counters.items():
        maximum=6 if name in ('client','server') else 1
        if (type(stream) is not list or type(before[name]) is not int or type(end[name]) is not int
            or not 0<=before[name]<=end[name]<=len(stream) or end[name]-before[name]>maximum):raise ValueError('bounded monotone exact counter prefix required')
        values[name]=stream[before[name]:end[name]]
    return values


def helpers(root,intent,values):
    result=[];root=Path(root)
    for endpoint in ('client','server'):
        base=root/('left' if endpoint=='client' else 'right');control=intent['helper_controls'][endpoint]
        for value in values[endpoint]:
            candidate=Path(value['candidate']);destination=Path(value['destination'])
            if ('..' in candidate.parts or '..' in destination.parts or not candidate.is_relative_to(base)
                or not destination.is_relative_to(base) or candidate==destination or value['endpoint']!=endpoint or value['mode']!=control['mode']):
                raise ValueError('actual receiving counter escaped exact source control/endpoint')
            expected_destination=Path(control['destination'])/candidate.name if control.get('directory') is True else Path(control['destination'])
            if destination!=expected_destination or value['argv']!=['--unison-dng-validation-v1','--expected-sha256',value['sha256'],
                '--expected-size',str(value['size']),'--threads','1','--',str(candidate)]:raise ValueError('exact original receiving helper arguments required')
            result.append(dict(endpoint=endpoint,pid=value['pid'],candidate_sha256=value['sha256'],candidate_bytes=value['size'],mode=control['mode'],
                outcome=('cancelled' if 'cancellation' in intent else 'timed-out') if control['mode']=='hang' else 'completed'))
    return result


def externals(values):
    return [dict(endpoint='client',pid=value['group'],fixture_pid=value['pid'],kind=kind) for kind in ('copy','merge') for value in values[kind]]
