#!/usr/bin/env python3
"""Pure accounting controls over historical rows; no new measurements/children."""
import copy
import json
from pathlib import Path

from batch_audit import audit
from partitions import COUNT, audit_part, merge, specification
from run_bounded import audit_measurement

refusals = 0


def refuse(function):
    global refusals
    try:
        function()
    except (ValueError, KeyError):
        refusals += 1
        return
    raise AssertionError('invalid partition accepted')


def main():
    source = Path(__file__).parent / 'results/warm-128MiB-4files-20261015.json'
    historical = json.loads(source.read_text())
    parts = []
    for index in range(COUNT):
        part = copy.deepcopy(historical)
        part['partition'] = specification(index)
        wanted = {tuple(value) for value in part['partition']['configurations']}
        part['samples'] = [row for row in part['samples'] if
                           (row['label'], row['mode'], row['workers']) in wanted]
        # Deliberately stale summary must never be trusted by the merger.
        part['summary'] = [{'untrusted': True}]
        assert audit_part(part)['cli_invocations'] == 54
        assert audit_part(part, expected_partition=index)['cli_invocations'] == 54
        refuse(lambda: audit_part(part, expected_partition=(index + 1) % COUNT))
        refuse(lambda: audit(part))
        parts.append(part)
    row = {'file_mib': 128, 'files': 4, 'expected_cli_invocations': 54}
    assert audit_measurement(parts[0], row, 0)['cli_invocations'] == 54
    refuse(lambda: audit_measurement(parts[0], row, 1))
    refuse(lambda: audit_measurement(parts[0], dict(row, file_mib=512), 0))
    refuse(lambda: audit_measurement(parts[0], dict(row, expected_cli_invocations=324), 0))
    combined = merge(list(reversed(parts)))
    assert combined['partition_merge_proof']['rows'] == 108
    assert combined['partition_merge_proof']['cli_invocations'] == 324
    assert combined['summary'] == historical['summary']
    assert len(combined['partition_provenance']) == COUNT
    for index in (-1, 6, True, '0'):
        refuse(lambda: specification(index))
    refuse(lambda: merge(parts[:-1]))
    refuse(lambda: merge(parts[:-1] + [parts[0]]))
    mutations = {
        'missing-row': lambda p: p['samples'].pop(),
        'duplicate-row': lambda p: p['samples'].append(p['samples'][0]),
        'unsettled-client': lambda p: p['samples'][0]['update_sync']['client_cleanup'].update(reaped=False),
        'incomplete-part': lambda p: p.update(complete=False),
        'wrong-declaration': lambda p: p['partition'].update(count=5),
        'wrong-repository': lambda p: p.update(repository_head='foreign'),
        'wrong-runner': lambda p: p.update(runner_sha256={'foreign': '0' * 64}),
        'wrong-host': lambda p: p['host'].update(machine='foreign'),
        'wrong-filesystem': lambda p: p['filesystem'].update(VolumeUUID='foreign'),
        'wrong-parameters': lambda p: p['parameters'].update(files=3),
        'wrong-binary': lambda p: p.update(binaries={**p['binaries'], 'foreign': {}}),
        'changed-binary-hash': lambda p: p['binaries']['stock'].update(sha256='0' * 64),
        'wrong-compiler': lambda p: p.update(compilers={}),
        'wrong-cache': lambda p: p.update(cache_state='cold'),
    }
    for name, mutate in mutations.items():
        changed = copy.deepcopy(parts)
        mutate(changed[1])
        refuse(lambda: merge(changed))
    changed = copy.deepcopy(parts)
    changed[1]['parameters']['background_note'] = 'different observed slot activity'
    accepted = merge(changed)
    assert accepted['partition_provenance'][1]['background_note'] == 'different observed slot activity'
    print('PASS six54-CLI partitions/full324-CLI merge;%d refusals; allocated result binding, summaries and slot provenance retained' % refusals)


if __name__ == '__main__':
    main()
