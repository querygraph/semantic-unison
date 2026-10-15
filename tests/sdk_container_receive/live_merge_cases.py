"""Production-path case body; callable only by a separately admitted owner.

This module supplies no native CLI, admission, process supervisor or timeout.
run_sync must retain and settle its owned CLI child and retain unresolved helper
ownership on ambiguous interruption; ordinary subprocess.run is insufficient.
"""
import importlib.util
import os
from pathlib import Path
import sys

import prepare_merged as prep
sys.path.insert(0, str(prep.ROOT / 'tests/validation_process'))
import records
spec = importlib.util.spec_from_file_location('live_host_plan', prep.ROOT / 'tests/sdk_host_matrix/plan.py')
host = importlib.util.module_from_spec(spec)
spec.loader.exec_module(host)


def audit_merge(log, target, build_id):
    processes, groups = records.parse(log), records.parse_groups(log)
    prep.require(len(processes) == len(groups) == 2, 'exactly two complete helper observations required')
    prep.require({item.endpoint for item in processes} == {item.endpoint for item in groups}
                 == {'client', 'server'}, 'both receiving endpoints required')
    result = []
    for endpoint in ('client', 'server'):
        process = next(item for item in processes if item.endpoint == endpoint)
        group = next(item for item in groups if item.endpoint == endpoint)
        prep.require(process.pid == group.pid and process.candidate_sha256 == group.candidate_sha256
                     == target['sha256'] and process.candidate_bytes == target['bytes'],
                     'helper/candidate binding mismatch')
        prep.require(process.outcome == 'completed' and process.status == ('exit', 0)
                     and process.complete_capture, 'helper did not complete with bounded full capture')
        prep.require(group.observation == 'observed' and group.other_members == 0,
                     'helper group unresolved; retain hold, never signal historical PID')
        report = host.receipt(process.stdout.decode('ascii'),
                              {'fixture': {'sha256': target['sha256'], 'size': target['bytes']},
                               'build_id': build_id})
        result.append({'endpoint': endpoint, 'historical_pid': process.pid,
                       'candidate_sha256': target['sha256'], 'receipt': report,
                       'raw_stdout_hex': process.stdout.hex(), 'raw_stderr_hex': process.stderr.hex(),
                       'retained_group_other_members': 0})
    return result


def no_helpers(log):
    prep.require(not records.parse(log) and not records.parse_groups(log), 'unexpected helper invocation')


def identity(path):
    st = path.stat()
    return [st.st_dev, st.st_ino, st.st_size, st.st_mtime_ns, st.st_ctime_ns]


def run_cases(packet, workspace, run_sync):
    """Nine CLI runs, three sequential codecs; six SDK calls only on merges.

    Caller validates all preparation, source/tool/build pins BEFORE entering and
    again after return. Caller owns the aggregate300s supervisor and unresolved
    markers. This body is not itself a lifecycle or runtime authorization.
    """
    spec = importlib.util.spec_from_file_location('live_validation_paths',
                                                prep.ROOT / 'tests/validation_paths/run.py')
    paths = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(paths)
    prep.require(packet['schema'] == 'unison-live-sdk-merge-preparation/1'
                 and [item['codec'] for item in packet['cases']] == list(prep.CODECS), 'case packet schema')
    paths.ADMISSION_OPTIONS[:] = ['-semanticvolumejobs', '1']
    tool = packet['tool']
    builds = {item['kind']: item for item in packet['builds']}
    stock, ox = builds['stock']['binary']['path'], builds['ox']['binary']['path']

    class Session(paths.Session):
        def config(self, endpoint):
            return {'adobevalidator': tool['executable'], 'adobevalidatorhash': tool['sha256'],
                    'adobevalidatorbuild': tool['build_id'], 'adobevalidatorthreads': '1',
                    'adobevalidatetimeout': '60'}

    options = ('-semanticmergebasecache', '-merge', 'Name *.dng -> unison:dng-xmp-scalars/0',
               '-debug', 'validation-process', '-debug', 'validation-group')
    results = []
    for case in packet['cases']:
        session = Session(workspace / case['codec'], stock)
        # Keep ordinary production process-group spawning. The loopback only
        # selects the current Ox server and its private state directory.
        session.launcher.write_text('#!/usr/bin/python3\nimport os,sys\n'
            'a=sys.argv[1:]\ni=a.index(' + repr(stock) + ')\n'
            'os.environ["UNISON"]=' + repr(str(session.server_state)) + '\n'
            'a[i]=' + repr(ox) + '\nos.execv(a[i],a[i:])\n')
        states = case['states']
        for item in states.values():
            prep.require(prep.pin(item['path']) == item, 'frozen scalar state changed')
        (session.left / 'image.dng').write_bytes(Path(states['base']['path']).read_bytes())
        def sync(policy):
            session.sequence += 1
            command = session.command(policy=policy, options=options)
            outcome = run_sync(command, dict(os.environ, UNISON=str(session.client_state)),
                               session.root / ('run-%02d.log' % session.sequence))
            prep.require(outcome['returncode'] == 0 and outcome['direct_child_reaped']
                         and not outcome['capture_truncated'],
                         'CLI unsettled/failed; retain unresolved helper ownership until audited')
            return outcome['log']
        no_helpers(sync('off'))
        prep.require(prep.pin(session.right / 'image.dng')['sha256'] == states['base']['sha256'], 'seed mismatch')
        (session.left / 'image.dng').write_bytes(Path(states['left']['path']).read_bytes())
        (session.right / 'image.dng').write_bytes(Path(states['right']['path']).read_bytes())
        log = sync('require')
        prep.require('Built-in DNG scalar merge verified' in log, 'built-in scalar merge not observed')
        receipts = audit_merge(log, states['target'], tool['build_id'])
        outputs = [session.left / 'image.dng', session.right / 'image.dng']
        prep.require(all(prep.pin(path)['sha256'] == states['target']['sha256'] for path in outputs), 'merged bytes mismatch')
        before = [identity(path) for path in outputs]
        no_helpers(sync('require'))
        prep.require([identity(path) for path in outputs] == before, 'noop changed output identity')
        prep.require(all(prep.pin(path)['sha256'] == states['target']['sha256'] for path in outputs), 'noop changed bytes')
        prep.require(not list(session.left.rglob('.unison.*')) and not list(session.right.rglob('.unison.*')),
                     'receiving staging remains')
        results.append({'codec': case['codec'], 'receipts': receipts, 'output_identities': before,
                        'target_sha256': states['target']['sha256']})
    return results
