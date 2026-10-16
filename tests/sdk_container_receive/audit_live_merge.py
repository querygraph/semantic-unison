#!/usr/bin/env python3
"""Independent retained live-merge evidence audit; never execute any tool."""
import argparse
import json
from pathlib import Path

import prepare_merged as prep
import live_merge_cases as cases


def audit(packet, workspace, terminal):
    workspace = Path(workspace)
    prep.require(terminal['exit_code'] == 0 and terminal['running_session_returned'] is False,
                 'actual parent tool terminal required, not ps absence')
    prep.require(packet['schema'] == 'unison-live-sdk-merge-preparation/1'
                 and [item['codec'] for item in packet['cases']] == list(prep.CODECS), 'preparation schema')
    prep.require(not list(workspace.glob('*UNRESOLVED*')), 'unresolved ownership markers remain')
    result = json.loads((workspace / 'RESULT.json').read_text())
    start = json.loads((workspace / 'WRAPPER-START.json').read_text())
    prep.require(prep.pin(start['prepared']['path']) == start['prepared']
                 and json.loads(Path(start['prepared']['path']).read_text()) == packet,
                 'wrapper preparation binding')
    phase_start = json.loads((workspace / 'AGGREGATE-START.json').read_text())
    aggregate = json.loads((workspace / 'AGGREGATE-CLOSED.json').read_text())
    supervisor = json.loads((workspace / 'SUPERVISOR-CLOSED.json').read_text())
    prep.require(result['complete'] and result['cli_runs'] == 9 and result['validation_calls'] == 6,
                 'incomplete receiving matrix')
    prep.require(start['mode'] == result['mode'] and result['mode'] in ('native', 'mock'), 'mode mismatch')
    prep.require([item['codec'] for item in result['results']] == list(prep.CODECS),
                 'exact unique ordered codec results required')
    if result['mode'] == 'native':
        prep.require(start['admission'] is not None, 'native return lacks admission')
        admission = prep.checked(start['admission'])
        dispatch = json.loads((workspace / 'START.json').read_text())
        prep.require(admission['state'] == 'ROOT_ADMITTED_FINITE_UNISON_LIVE_MERGE_V1'
                     and admission['prepared'] == start['prepared']
                     and admission['workspace'] == str(workspace.resolve())
                     and admission['source_pins'] == start['sources']
                     and dispatch['mode'] == 'native' and dispatch['pid'] == aggregate['pid']
                     and dispatch['unix'] < admission['startDeadlineUnix'],
                     'native admission/dispatch binding mismatch')
        prep.require(cases.host.tool(Path(packet['tool']['manifest']), False) == packet['tool'],
                     'native return requires qualified v1 tool, not mock protocol')
    else:
        prep.require(packet['tool']['build_id'].startswith('MOCK-') and start['admission'] is None,
                     'mock return mode/provenance mismatch')

    prep.require(aggregate['pid'] == phase_start['pid'] and aggregate['reaped']
                 and aggregate['other_cli_group_members_absent_before_reap']
                 and aggregate['returncode'] == 0 and aggregate['within_wall_limit']
                 and not aggregate['timed_out'] and aggregate['fault'] is None,
                 'aggregate owner not cleanly closed')
    prep.require(supervisor['aggregate'] == aggregate and supervisor['external_proofs_accepted']
                 and supervisor['expected_helper_calls'] == 6, 'supervisor/proof binding')
    for index in range(1, 10):
        entry = json.loads((workspace / ('CLI-%02d-START.json' % index)).read_text())
        closed = json.loads((workspace / ('CLI-%02d-CLOSED.json' % index)).read_text())
        prep.require(entry['pid'] == closed['pid'] and closed['reaped']
                     and closed['other_cli_group_members_absent_before_reap']
                     and closed['returncode'] == 0 and not closed['timed_out'] and closed['fault'] is None,
                     'CLI owner closure mismatch')
    actual = []
    for case in packet['cases']:
        root = workspace / case['codec']
        cases.no_helpers((root / 'run-01.log').read_text())
        receipts = cases.audit_merge((root / 'run-02.log').read_text(), case['states']['target'],
                                     packet['tool']['build_id'])
        cases.no_helpers((root / 'run-03.log').read_text())
        for side in ('left', 'right'):
            path = root / side / 'image.dng'
            reference = case['states']['target']
            proof = prep.pin(path)
            prep.require(proof['bytes'] == reference['bytes'] and proof['sha256'] == reference['sha256'],
                         'retained output changed')
            prep.require(not list((root / side).rglob('.unison.*')), 'staging leftovers')
        recorded = next(item for item in result['results'] if item['codec'] == case['codec'])
        prep.require(recorded['target_sha256'] == case['states']['target']['sha256']
                     and recorded['receipts'] == receipts
                     and recorded['output_identities'] == [cases.identity(root / side / 'image.dng')
                                                          for side in ('left', 'right')],
                     'executor receipts/retained identities disagree')
        actual.append({'codec': case['codec'], 'receipts': receipts,
                       'target_sha256': case['states']['target']['sha256']})
    helpers = json.loads((workspace / 'HELPER-PROOFS-COMPLETE.json').read_text())
    prep.require(helpers['cli_runs'] == 9 and helpers['sdk_calls'] == 6
                 and helpers['results'] == result['results'], 'helper completion differs')
    return {'complete': True, 'mode': result['mode'], 'independent_receipts': actual,
            'actual_parent_terminal': terminal,
            'scope': 'retained evidence consistency and exact outputs, not independent pixel/native instrumentation'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepared', type=Path, required=True)
    parser.add_argument('--workspace', type=Path, required=True)
    parser.add_argument('--parent-terminal', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    result = audit(json.loads(args.prepared.read_text()), args.workspace,
                   json.loads(args.parent_terminal.read_text()))
    result['prepared'] = prep.pin(args.prepared)
    result['auditor'] = prep.pin(__file__)
    with args.report.open('x') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')
    print('PASS retained receiving evidence, six raw protocols and nine CLI closures; no dispatch')
