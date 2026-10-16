"""Finite functional-scope audit; does not relax the timed matrix audit."""
import itertools
import stat
import properties as property_controls
from batch_audit import require


def audit_shared(result):
    require(result['schema'] == 'unison-synthetic-sync/0' and result['complete'] is True,
            'shared result incomplete')
    require('partition' not in result, 'shared run cannot be a performance partition')
    params = result['parameters']
    expected_parameters = {'workers': [1, 2, 3], 'warmups': 0, 'repetitions': 1,
                           'modes': ['ordinary', 'receiver-clone', 'semantic'],
                           'loopback_cpu_credit_bound': 8, 'orchestration_cpu_credits': 2,
                           'maximum_declared_cpu_credit_sum': 8, 'file_mib': 2, 'files': 2}
    for key, value in expected_parameters.items():
        require(params[key] == value, 'shared parameter differs: ' + key)
    require(result['purpose'] == 'finite shared-harness qualification', 'shared scope differs')
    require(set(result['binaries']) == {'stock', 'ox'}, 'shared stock/Ox pair required')
    property_mode = params.get('property_removal_controls', False)
    require(type(property_mode) is bool, 'typed property control flag required')
    expected = set(itertools.product(('stock', 'ox'), expected_parameters['modes'], (1, 2, 3)))
    seen = set()
    calls = 0
    for sample in result['samples']:
        key = (sample['label'], sample['mode'], sample['workers'])
        require(type(sample['workers']) is int and key in expected and key not in seen and sample['phase'] == 'measured'
                and type(sample['repetition']) is int and sample['repetition'] == 1,
                'duplicate/unexpected shared row')
        seen.add(key)
        require(all(sample[name] is True for name in ('exact_result_and_unchanged_basis',
                    'noop_preserved_receiver_inode', 'staging_cleaned', 'private_fixture_removed')),
                'shared row preservation failed')
        if property_mode:
            require(all(sample.get(name) is True for name in ('source_selected_properties_removed',
                        'retained_old_readers_preserved', 'noop_properties_preserved')),
                    'shared property/old reader preservation failed')
            fixtures = sample['fixtures']
            names = {item['name'] for item in fixtures}
            require(len(fixtures) == len(names) == 2, 'two property fixture identities required')
            old, current = sample['old_reader_snapshots'], sample['noop_property_epochs']
            require(set(old) == set(current) == names, 'property witness names differ')
            for item in fixtures:
                before, after = old[item['name']], current[item['name']]
                require(all(type(before[k]) is int for k in ('st_dev','st_ino','st_size','st_mtime_ns','st_mode'))
                        and all(type(after[k]) is int for k in ('st_dev','st_ino','st_size','st_mtime_ns','st_ctime_ns','st_mode')),
                        'typed property witnesses required')
                require(before['st_size'] == after['st_size'] == 2*1048576
                        and stat.S_ISREG(before['st_mode']) and stat.S_IMODE(before['st_mode']) == 0o640
                        and stat.S_ISREG(after['st_mode']) and stat.S_IMODE(after['st_mode']) == 0o400,
                        'property witness size/mode differs')
                require(before['sha256'] == item['before_sha256']
                        and before['xattr_hex'] == property_controls.OLD_VALUE.hex()
                        and before['fork_hex'] == property_controls.OLD_FORK.hex()
                        and (before['st_dev'],before['st_ino']) != (after['st_dev'],after['st_ino']),
                        'old reader content/properties or replacement identity differs')
        for stage in ('seed_sync', 'update_sync', 'noop_sync'):
            run = sample[stage]
            require(run['returncode'] == 0 and not run['timed_out'] and not run['capture_truncated'],
                    'shared CLI failed')
            for owner_name in ('client_cleanup', 'supervisor_cleanup'):
                owner = run[owner_name]
                require(owner['reaped'] is True and owner['returncode'] == 0
                        and owner['cancel_reason'] is None
                        and owner['group_cleanup_before_leader_reap'] is True
                        and owner['other_group_members_absent_before_reap'] is True,
                        'shared direct owner unsettled')
            proxy = run['proxy']
            server = proxy['server_cleanup']
            require(server['reaped'] is True and server['returncode'] == 0
                    and server['cancel_reason'] is None and proxy['server_returncode'] == 0
                    and type(server['pid']) is int and server['pid'] > 0
                    and proxy['server_pid'] == server['pid']
                    and not run['supervisor_capture_truncated'] and proxy['fault'] is None
                    and not proxy['pump_errors'] and proxy['input_pump_joined'] is True,
                    'shared server/pumps unsettled')
            calls += 1
    require(seen == expected and calls == 54, 'shared matrix rows/calls missing')
    return {'rows': len(seen), 'cli_invocations': calls,
            'all_client_server_supervisor_settled': True,
            'scope': 'finite functional output/ownership only; no quiet timing, hard CPU/RSS or physical IO proof'}
