"""Pure shared-sync admission and receipt controls; no binary invocation."""
import copy
import itertools
from pathlib import Path
import runpy
import sys
from types import SimpleNamespace
from unittest.mock import patch

HERE = Path(__file__).resolve().parents[1] / 'bench/sync'
sys.path.insert(0, str(HERE))
from shared_audit import audit_shared
from batch_audit import audit
from ownership import OwnedGroup

owner = {'pid': 42, 'reaped': True, 'returncode': 0, 'cancel_reason': None,
         'group_cleanup_before_leader_reap': True, 'other_group_members_absent_before_reap': True}
call = {'returncode': 0, 'timed_out': False, 'capture_truncated': False,
        'supervisor_capture_truncated': False, 'client_cleanup': owner,
        'supervisor_cleanup': owner,
        'proxy': {'server_cleanup': owner, 'server_pid': 42, 'server_returncode': 0,
                  'fault': None, 'pump_errors': [], 'input_pump_joined': True}}
result = {'schema': 'unison-synthetic-sync/0', 'complete': True,
          'purpose': 'finite shared-harness qualification', 'binaries': {'stock': {}, 'ox': {}},
          'parameters': {'workers': [1, 2, 3], 'warmups': 0, 'repetitions': 1,
                         'modes': ['ordinary', 'receiver-clone', 'semantic'],
                         'loopback_cpu_credit_bound': 8, 'orchestration_cpu_credits': 2,
                         'maximum_declared_cpu_credit_sum': 8, 'file_mib': 2, 'files': 2},
          'samples': []}
for label, mode, worker in itertools.product(('stock', 'ox'), result['parameters']['modes'], (1, 2, 3)):
    result['samples'].append({'label': label, 'mode': mode, 'workers': worker,
            'phase': 'measured', 'repetition': 1, 'exact_result_and_unchanged_basis': True,
            'noop_preserved_receiver_inode': True, 'staging_cleaned': True,
            'private_fixture_removed': True,
            **{stage: copy.deepcopy(call) for stage in ('seed_sync', 'update_sync', 'noop_sync')}})
assert audit_shared(result)['cli_invocations'] == 54
try:
    audit(result)
except ValueError:
    pass
else:
    raise AssertionError('functional result passed timed-matrix audit')

mutations = [
    lambda r: r.update(complete=False),
    lambda r: r.update(partition={}),
    lambda r: r['samples'].pop(),
    lambda r: r['samples'].append(copy.deepcopy(r['samples'][0])),
    lambda r: r['parameters'].update(loopback_cpu_credit_bound=18),
    lambda r: r['parameters'].update(workers=[1, 2]),
    lambda r: r['parameters'].update(file_mib=512),
    lambda r: r['samples'][0].update(staging_cleaned=False),
    lambda r: r['samples'][0]['seed_sync']['client_cleanup'].update(reaped=False),
    lambda r: r['samples'][0]['update_sync']['supervisor_cleanup'].update(other_group_members_absent_before_reap=None),
    lambda r: r['samples'][0]['noop_sync']['proxy']['server_cleanup'].update(reaped=False),
    lambda r: r['samples'][0]['noop_sync']['proxy'].update(input_pump_joined=False),
    lambda r: r['samples'][0]['noop_sync']['proxy'].update(server_pid=43),
]
for mutate in mutations:
    changed = copy.deepcopy(result)
    mutate(changed)
    try:
        audit_shared(changed)
    except ValueError:
        pass
    else:
        raise AssertionError('unsettled/mismatched shared result accepted')
runpy.run_path(str(HERE / 'shared_budget_test.py'), run_name='shared_budget_controls')
# This is a fully mocked PID, never a signal to a historical process.
fake = OwnedGroup.__new__(OwnedGroup)
fake.process = SimpleNamespace(pid=42, returncode=None)
fake.reaped = False
fake.strict_group_settlement = True
with patch.object(fake, 'await_terminal', return_value=True), \
        patch('ownership.os.killpg'), patch('ownership.os.wait4') as wait, \
        patch('ownership.subprocess.run', return_value=SimpleNamespace(returncode=0, stderr='', stdout='bad')):
    try:
        fake.finish()
    except RuntimeError:
        pass
    else:
        raise AssertionError('malformed strict census accepted')
    wait.assert_not_called()
    assert not fake.reaped
print('PASS shared54CLI receipt fixture,13 refusal controls; timed matrix remains strict; no child/output')


# Properties are an optional successor; the original functional receipt remains
# valid when the flag is absent. These are fake records, no metadata APIs run.
property_result=copy.deepcopy(result)
property_result['parameters']['property_removal_controls']=True
for sample in property_result['samples']:
    sample.update(source_selected_properties_removed=True,retained_old_readers_preserved=True,
                  noop_properties_preserved=True,fixtures=[],old_reader_snapshots={},noop_property_epochs={})
    for index in range(2):
        name=str(index)+'.dng';before_hash=str(index)*64
        sample['fixtures'].append({'name':name,'before_sha256':before_hash})
        sample['old_reader_snapshots'][name]={'st_dev':1,'st_ino':index+10,'st_size':2*1048576,
            'st_mtime_ns':1,'st_mode':0o100640,'sha256':before_hash,
            'xattr_hex':b'generated-old-xattr'.hex(),'fork_hex':b'generated-old-native-fork'.hex()}
        sample['noop_property_epochs'][name]={'st_dev':1,'st_ino':index+100,'st_size':2*1048576,
            'st_mtime_ns':2,'st_ctime_ns':2,'st_mode':0o100400}
assert audit_shared(property_result)['cli_invocations']==54
for mutation in (
    lambda r:r['parameters'].update(property_removal_controls=1),
    lambda r:r['samples'][0].update(source_selected_properties_removed=False),
    lambda r:r['samples'][0].update(retained_old_readers_preserved=False),
    lambda r:r['samples'][0].update(noop_properties_preserved=False),
    lambda r:r['samples'][0]['old_reader_snapshots']['0.dng'].update(sha256='f'*64),
    lambda r:r['samples'][0]['old_reader_snapshots']['0.dng'].update(fork_hex=''),
    lambda r:r['samples'][0]['noop_property_epochs']['0.dng'].update(st_mode=0o100640),
    lambda r:r['samples'][0]['noop_property_epochs']['0.dng'].update(st_ino=10),
):
    broken=copy.deepcopy(property_result);mutation(broken)
    try:audit_shared(broken)
    except (ValueError,KeyError,TypeError):pass
    else:raise AssertionError('bad property witness accepted')
print('PASS optional property audit positive and8malformed witness controls; no nativeIO')
