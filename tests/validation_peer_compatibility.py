"""Actual mixed-version empty-root handshakes; zero SDK or camera payload.

Owns every loopback client/server/group before return. This file is intentionally
outside the frozen all-scanned SDK execution closure and changes no production.
"""
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import time
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'tests'), str(ROOT / 'bench/sync'),
               str(ROOT / 'tests/camera_sdk_concurrency')]
from run import measure_invocation, InvocationFailure
from camera_sdk_concurrency.invocation import artifact_sha, SCRIPT_NAMES
from camera_sdk_concurrency.worker import prepare_scripts
from camera_sdk_concurrency.persistence import save
from shared_cpu_pool import UnresolvedOwnership
from shared_process_owner import retain_after_record
from validation_process import records
from all_scanned_sdk_paths import parse as parse_inputs
from all_scanned_sdk_groups import audit as audit_server_group

EXPECTED = 'Requested all-scanned Adobe validation requires dng-validation-all-scanned-v1 on both replicas'


def settled(out):
    if (out.get('capture_truncated') is not False
            or out.get('supervisor_capture_truncated') is not False):
        raise ValueError('full call capture required')
    for owner in (out['client_cleanup'], out['supervisor_cleanup']):
        if (owner['reaped'] is not True or owner['group_cleanup_before_leader_reap'] is not True
                or owner['other_group_members_absent_before_reap'] is not True):
            raise ValueError('owned call group settlement incomplete')
    if out['proxy']['input_pump_joined'] is not True:
        raise ValueError('native server input pump unresolved')
    audit_server_group(out)


def main():
    root = Path(tempfile.mkdtemp(prefix='u-peer-compat-', dir='/private/tmp'))
    result = dict(complete=False, calls=[], binary_receipts={}, scope='Actual current/older peer empty-root negotiation only; no SDK/camera/payload transfer or broad interop claim')
    save(root, result)
    pins = {name: artifact_sha(ROOT / 'bench/sync' / name) for name in SCRIPT_NAMES}
    for label in ('stock', 'ox'):
        new_receipt = Path('/private/tmp/unison-validation-scope-' + label + '-007-20261017/RESULT.json')
        old_receipt = Path('/private/tmp/unison-snapshot-worker-' + label + '-select-005-20261017/RESULT.json')
        current, old = json.loads(new_receipt.read_text()), json.loads(old_receipt.read_text())
        for value in (current, old):
            assert value['complete'] and value['build_exit'] == 0
            assert artifact_sha(value['binary']) == value['binary_sha256']
        for value, present in ((current, True), (old, False)):
            source = Path(value['workspace']) / 'src/dngCandidateValidation.ml'
            assert artifact_sha(source) == value['source_sha256']['src/dngCandidateValidation.ml']
            assert ('dng-validation-all-scanned-v1' in source.read_text()) == present
        result['binary_receipts'][label] = dict(current=dict(path=str(new_receipt), sha256=artifact_sha(new_receipt)),
                                               older=dict(path=str(old_receipt), sha256=artifact_sha(old_receipt)))
        directory = root / label; directory.mkdir(mode=0o700)
        for name in ('left', 'right', 'state'): (directory / name).mkdir(mode=0o700)
        prepare_scripts(directory, pins)
        for policy in ('require', 'off'):
            flags = ['-semanticworkers', '3', '-maxthreads', '3', '-adobevalidate', policy,
                     '-adobevalidatescope', 'all-scanned', '-debug', 'validation-process',
                     '-debug', 'validation-group', '-debug', 'validation-input']
            server_flags = ['-semanticworkers', '3', '-maxthreads', '3', '-adobevalidate', 'off']
            command = [current['binary'], str(directory / 'left'), 'ssh://localhost/' + str(directory / 'right'),
                       '-sshcmd', str(directory / 'launcher.py'), '-servercmd', old['binary'],
                       '-batch', '-auto', '-fastcheck', 'false', *flags]
            env = dict(os.environ, UNISON=str(directory / 'state'),
                       UNISON_SYNC_BENCH_BINARY=old['binary'],
                       UNISON_SYNC_BENCH_SERVER_FLAGS=json.dumps(server_flags),
                       UNISON_SYNC_BENCH_PROXY_RECEIPT=str(directory / (policy + '-proxy.json')),
                       UNISON_SYNC_BENCH_SOCKET=str(directory / (policy + '-peer.sock')),
                       UNISON_SYNC_BENCH_DEADLINE_SECONDS='35')
            for name in ('UNISON_SYNC_BENCH_FAULT', 'UNISON_SYNC_BENCH_CHILD_PID_FILE',
                         'UNISON_CONCURRENT_SYNTHETIC_ROOT'): env.pop(name, None)
            row = dict(label=label, policy=policy, command=command, state='INTENT')
            result['calls'].append(row); save(root, result)
            try:
                try: out = measure_invocation(command, env, 30, directory / 'proxy.py', strict_group_settlement=True)
                except InvocationFailure as error: out = error.outcome
            except BaseException as error:
                raise UnresolvedOwnership('mixed-peer outcome unavailable; retain owner') from error
            row.update(state='OUTCOME', outcome=out); save(root, result)
            try: settled(out)
            except BaseException as error:
                raise UnresolvedOwnership('mixed-peer group outcome unknown; retain owner') from error
            log = '\n'.join(out[name] for name in ('stdout', 'stderr', 'supervisor_output'))
            assert not records.parse(log) and not records.parse_groups(log) and not parse_inputs(log)
            assert not list((directory / 'left').iterdir()) and not list((directory / 'right').iterdir())
            proxy = out['proxy']
            assert proxy['server_command'] is not None
            assert proxy['server_command'][0] == old['binary'] and proxy['server_command'][-len(server_flags):] == server_flags
            if policy == 'require': assert out['returncode'] != 0 and EXPECTED in log
            else: assert out['returncode'] == 0 and 'Nothing to do:' in log and not out.get('fault')
            row['expected_result_verified'] = True; save(root, result)
    result.update(complete=True, SDK_invoked=False, retained_camera_payload_opened=False)
    save(root, result)
    print(json.dumps(dict(workspace=str(root), cli_calls=4, SDK_calls=0, complete=True)), flush=True)


if __name__ == '__main__':
    try: main()
    except UnresolvedOwnership as error: retain_after_record(lambda: print(repr(error), flush=True))
