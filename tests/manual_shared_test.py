#!/usr/bin/env python3
"""Pure shared-entrypoint boundary controls; no build, tool or child runs."""
from pathlib import Path
import io
import runpy
import sys
from unittest.mock import patch
import manual

out = Path('/UNCREATED-shared-control')
env = {'OX_PREFIX': '/UNREAD-compiler', 'SHARED_CPU_CREDITS': '8'}
with patch.object(Path, 'is_file', return_value=True):
    argv = manual.command('ox-build', out, env)
    assert argv[argv.index('--jobs') + 1] == '2' and '--selftest' not in argv
    assert argv[argv.index('--build-system') + 1] == 'make'
    one = manual.command('ox-build', out, dict(env, SHARED_CPU_CREDITS='3'))
    assert one[one.index('--jobs') + 1] == '1'
    legacy = manual.command('ox-make', out, {'OX_PREFIX': '/UNREAD-compiler'})
    assert '--selftest' in legacy and legacy[legacy.index('--jobs') + 1] == '4'
    inspector = manual.command('inspect-ox', out, env)
    assert '--build-only' in inspector and '--report' in inspector and '--selftest' not in inspector
    assert inspector[inspector.index('--report') + 1] == str(out / 'RESULT.json')
    assert manual.shared_resource_plan('inspect-ox', env)['declared_peak_credits'] == 3

    for target, changes in (
        ('ox-build', {'JOBS': '5'}),
        ('ox-build', {'SHARED_CPU_CREDITS': '0'}),
        ('ox-build', {'SHARED_CPU_CREDITS': '9'}),
        ('ox-build', {'SHARED_CPU_CREDITS': 'bad'}),
        ('ox-make', {}),
        ('host-executor', {}),
        ('sync-functional', {'SHARED_CPU_CREDITS': '2'}),
        ('inspect-ox', {'SHARED_CPU_CREDITS': '2'}),
    ):
        try:
            manual.command(target, out, dict(env, **changes))
        except ValueError:
            pass
        else:
            raise AssertionError('unqualified shared request admitted: ' + target)

with patch.object(manual, 'checked_build', return_value={'binary': '/NEVER-execute',
                                                       'compiler': '/NEVER-query'}):
    argv = manual.command('sync-functional', out,
                          dict(env, STOCK_RECEIPT='unread', OX_RECEIPT='unread'))
    assert '--shared-qualification' in argv and '--qualification' not in argv
    assert argv[argv.index('--loopback-cpu-credits') + 1] == '8'
    assert argv[argv.index('--orchestration-cpu-credits') + 1] == '2'
    plan = manual.shared_resource_plan('sync-functional', env)
    assert plan['cpu_token_indexes'] == list(range(8))
    assert plan['endpoint_workers'] == [3, 3] and plan['declared_peak_credits'] == 8
    assert plan['orchestration_credits'] == 2 and plan['memory_reservation_gib'] == 32
    assert not plan['runtime_grant'] and plan['token_acquisition_implemented']
    assert not plan['memory_enforced'] and not plan['physical_io_lane_resolved']
    build_plan = manual.shared_resource_plan('ox-build', env)
    assert build_plan['compiler_jobs'] == 2 and build_plan['declared_peak_credits'] == 4
    assert build_plan['token_acquisition_implemented']
    assert manual.shared_resource_plan('group-parser', env)['token_acquisition_implemented']
    from shared_dispatch import TARGETS
    assert 'sync-functional' in TARGETS
    assert {'stock-build', 'ox-build', 'shared-entrypoints', 'group-parser'} <= TARGETS
print('PASS shared/legacy command selections and budget refusals; no output, build or child')

inspector_main = runpy.run_path(str(manual.ROOT / 'tools/semantic-inspect/run.py'))['main']
for arguments in (['--build-only'], ['--report', '/NEVER-CREATED'],
                  ['--build-only', '--report', '/NEVER-CREATED', '--', '/NEVER-READ.dng']):
    with patch.object(sys, 'argv', ['inspector'] + arguments), patch.object(sys, 'stderr', io.StringIO()), \
            patch('subprocess.run', side_effect=AssertionError('unexpected compiler/inspector execution')), \
            patch('tempfile.mkdtemp', side_effect=AssertionError('unexpected workspace')):
        try:
            inspector_main()
        except SystemExit as error:
            assert error.code == 2
        else:
            raise AssertionError('ambiguous build-only command admitted')
print('PASS three inspector build-only refusals before workspace/compiler/payload access')

import shared_dispatch
with patch.object(shared_dispatch.os, 'waitid', None), \
        patch.object(shared_dispatch.Pool, 'read', side_effect=AssertionError('pool touched')):
    try:
        shared_dispatch.run('group-parser', [], out, 8)
    except ValueError:
        pass
    else:
        raise AssertionError('unsupported interpreter acquired shared ownership')
print('PASS unsupported interpreter refusal before pool read/acquisition')
