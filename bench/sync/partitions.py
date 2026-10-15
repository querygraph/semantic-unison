"""Pure six-part matrix accounting; never dispatches a command or grants a slot."""
import copy
import statistics

from batch_audit import audit, require

SCHEMA = 'unison-sync-partition/1'
LABELS = ('stock', 'ox')
MODES = ('ordinary', 'receiver-clone', 'semantic')
WORKERS = (1, 6, 8)
COUNT = len(LABELS) * len(WORKERS)


def specification(index):
    require(type(index) is int and 0 <= index < COUNT, 'partition index must be0..5')
    label = LABELS[index // len(WORKERS)]
    workers = WORKERS[index % len(WORKERS)]
    return {'schema': SCHEMA, 'index': index, 'count': COUNT,
            'configurations': [[label, mode, workers] for mode in MODES]}


def audit_part(result):
    part = result['partition']
    require(part == specification(part['index']), 'partition declaration differs')
    params = result['parameters']
    require(params['modes'] == list(MODES) and params['workers'] == list(WORKERS),
            'partition must retain the full declared mode/worker universe')
    return audit(result, configurations=[tuple(value) for value in part['configurations']])


def common_parameters(result):
    params = dict(result['parameters'])
    # Background observations can differ by separately scheduled slot; preserve
    # each verbatim below, rather than pretend all parts ran in one window.
    params.pop('background_note', None)
    return params


def merge(parts):
    require(len(parts) == COUNT, 'all six partitions required')
    indexed = {}
    for part in parts:
        audit_part(part)
        index = part['partition']['index']
        require(index not in indexed, 'duplicate partition')
        indexed[index] = part
    require(set(indexed) == set(range(COUNT)), 'missing partition')
    first = indexed[0]
    fields = ('schema', 'purpose', 'repository_head', 'runner_sha256', 'host',
              'binaries', 'compilers', 'cache_state', 'transport', 'filesystem',
              'resource_scope', 'rss_units', 'unmeasured')
    for part in indexed.values():
        require(common_parameters(part) == common_parameters(first), 'partition parameters differ')
        for field in fields:
            require(part[field] == first[field], 'partition provenance differs: ' + field)
    result = copy.deepcopy(first)
    del result['partition']
    result['parameters']['background_note'] = 'Separate scheduled windows; see partition_provenance.'
    result['samples'] = [sample for index in range(COUNT) for sample in indexed[index]['samples']]
    result['partition_provenance'] = [
        {'partition': indexed[index]['partition'],
         'created_utc': indexed[index]['created_utc'],
         'background_note': indexed[index]['parameters'].get('background_note'),
         'fixture_capacity': indexed[index].get('fixture_capacity'),
         'temporary_directory': indexed[index].get('temporary_directory')}
        for index in range(COUNT)]
    result['summary'] = []
    for label in LABELS:
        for mode in MODES:
            for workers in WORKERS:
                rows = [row for row in result['samples'] if
                        (row['label'], row['mode'], row['workers'], row['phase']) ==
                        (label, mode, workers, 'measured')]
                values = [row['update_sync']['wall_seconds'] for row in rows]
                result['summary'].append({'label': label, 'mode': mode, 'workers': workers,
                    'samples': len(values), 'wall_seconds': {'median': statistics.median(values),
                    'minimum': min(values), 'maximum': max(values)}, 'all_results_exact': True})
    # Recheck the full Cartesian matrix: accepting each part is insufficient.
    proof = audit(result)
    result['partition_merge_proof'] = proof
    result['partition_merge_scope'] = ('Full row/CLI accounting only; each part needs its own '
        'actual aggregate and parent-terminal closure. This does not create a shared timing window.')
    return result
