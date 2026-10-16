"""Pure interval evidence validation; never establishes process/FD settlement."""

class IncompleteEvidence(ValueError):
    """Unknown overlap; callers must not turn this into resource-release proof."""


def overlap(events, *, expected, clock_id):
    if type(clock_id) is not str or not 1 <= len(clock_id) <= 128:
        raise IncompleteEvidence('explicit bounded common clock identity required')
    if type(expected) is not list or len(expected) != 2:
        raise IncompleteEvidence('exactly two independently bound helpers required')
    bindings = {}
    for row in expected:
        if (type(row) is not dict or set(row) != {'pid','candidate_id','threads'}
                or type(row['pid']) is not int or row['pid'] <= 0
                or type(row['candidate_id']) is not str or not 1 <= len(row['candidate_id']) <= 512
                or type(row['threads']) is not int or row['threads'] != 1
                or row['pid'] in bindings):
            raise IncompleteEvidence('distinct single-thread helper bindings required')
        bindings[row['pid']] = row['candidate_id']
    if len(set(bindings.values())) != 2:
        raise IncompleteEvidence('two distinct receiving candidates required')
    if type(events) is not list or len(events) != 4:
        raise IncompleteEvidence('exactly one start/end per helper required')
    starts, ends = {}, {}
    previous = -1
    for event in events:
        if (type(event) is not dict
                or set(event) != {'kind','pid','candidate_id','clock_id','tick_ns'}
                or event['clock_id'] != clock_id
                or type(event['pid']) is not int or event['pid'] not in bindings
                or event['candidate_id'] != bindings[event['pid']]
                or type(event['tick_ns']) is not int or not 0 <= event['tick_ns'] < 2**63
                or event['tick_ns'] < previous):
            raise IncompleteEvidence('event binding or ordered common-clock timestamp differs')
        previous = event['tick_ns']
        pid = event['pid']
        if event['kind'] == 'start' and pid not in starts and pid not in ends:
            starts[pid] = event['tick_ns']
        elif (event['kind'] == 'end' and pid in starts and pid not in ends
              and event['tick_ns'] > starts[pid]):
            ends[pid] = event['tick_ns']
        else:
            raise IncompleteEvidence('duplicate, missing or reversed helper interval')
    if set(starts) != set(ends) or set(starts) != set(bindings):
        raise IncompleteEvidence('incomplete helper interval census')
    common = max(0, min(ends.values()) - max(starts.values()))
    return {'overlap_ns':common, 'overlap_observed':common > 0,
            'intervals':[dict(pid=pid,candidate_id=bindings[pid],
                              start_ns=starts[pid],end_ns=ends[pid]) for pid in sorted(bindings)],
            'clock_id':clock_id, 'settlement_proved':False,
            'timestamp_producer_qualified':False, 'throughput_qualified':False}
