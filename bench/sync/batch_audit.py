"""Pure audit of complete benchmark rows and every CLI/server owner receipt."""
import itertools


def require(value, message):
    if not value:
        raise ValueError(message)


def audit(result, expected_parameters=None, *, configurations=None):
    require(result['schema'] == 'unison-synthetic-sync/0' and result['complete'], 'incomplete benchmark')
    params = result['parameters']
    if expected_parameters is not None:
        for key, value in expected_parameters.items():
            require(params[key] == value, 'measurement parameters differ: ' + key)
    require(params['modes'] == ['ordinary', 'receiver-clone', 'semantic']
            and params['warmups'] >= 1 and params['repetitions'] >= 5, 'full timed matrix required')
    labels = set(result['binaries'])
    require(labels == {'stock', 'ox'}, 'stock/Ox comparison required')
    if configurations is None:
        require('partition' not in result, 'partition is not a complete matrix')
        configurations = list(itertools.product(sorted(labels), params['modes'], params['workers']))
    else:
        require('partition' in result, 'explicit partition metadata required')
        require(len(configurations) == len(set(configurations)) and configurations,
                'invalid partition configurations')
        require(all(label in labels and mode in params['modes'] and worker in params['workers']
                    for label, mode, worker in configurations), 'unknown partition configuration')
    expected = set()
    for label, mode, worker in configurations:
        for phase, count in (('warmup', params['warmups']), ('measured', params['repetitions'])):
            expected.update((label, mode, worker, phase, repetition) for repetition in range(1, count+1))
    seen = set()
    native = 0
    for sample in result['samples']:
        identity = tuple(sample[key] for key in ('label', 'mode', 'workers', 'phase', 'repetition'))
        require(identity in expected and identity not in seen, 'duplicate/unexpected measurement row')
        seen.add(identity)
        require(sample['exact_result_and_unchanged_basis'] and sample['noop_preserved_receiver_inode']
                and sample['staging_cleaned'] and sample['private_fixture_removed'], 'row preservation/cleanup failed')
        for stage in ('seed_sync', 'update_sync', 'noop_sync'):
            run = sample[stage]
            client, supervisor, proxy = run['client_cleanup'], run['supervisor_cleanup'], run['proxy']
            require(run['returncode'] == 0 and not run['timed_out'] and not run['capture_truncated'], 'CLI failed')
            require(client['reaped'] and client['returncode'] == 0 and client['cancel_reason'] is None
                    and client['group_cleanup_before_leader_reap'], 'client ownership unsettled')
            require(supervisor['reaped'] and supervisor['returncode'] == 0 and supervisor['cancel_reason'] is None
                    and supervisor['group_cleanup_before_leader_reap'], 'supervisor ownership unsettled')
            require(proxy['server_cleanup']['reaped'] and proxy['server_cleanup']['returncode'] == 0
                    and proxy['server_cleanup']['cancel_reason'] is None and proxy['server_returncode'] == 0
                    and proxy['server_pid'] == proxy['server_cleanup']['pid']
                    and not run['supervisor_capture_truncated']
                    and proxy['fault'] is None and not proxy['pump_errors'] and proxy['input_pump_joined'],
                    'native server ownership unsettled')
            native += 1
    require(seen == expected, 'missing measured/warmup rows')
    return {'rows': len(seen), 'cli_invocations': native, 'all_client_server_supervisor_settled': True,
            'scope': 'declared matrix rows and retained per-invocation receipts; not aggregate owner closure, physical I/O or aggregate RSS'}
