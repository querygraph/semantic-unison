#!/usr/bin/env python3
"""Pure shared-entrypoint boundary controls; no build, tool or child runs."""
from pathlib import Path
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

    for target, changes in (
        ('ox-build', {'JOBS': '5'}),
        ('ox-build', {'SHARED_CPU_CREDITS': '0'}),
        ('ox-build', {'SHARED_CPU_CREDITS': '9'}),
        ('ox-build', {'SHARED_CPU_CREDITS': 'bad'}),
        ('ox-make', {}),
        ('host-executor', {}),
        ('sync-functional', {'SHARED_CPU_CREDITS': '2'}),
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
    assert plan['endpoint_workers'] == [2, 2] and plan['declared_peak_credits'] == 6
    assert plan['orchestration_credits'] == 2 and plan['memory_reservation_gib'] == 32
    assert not plan['runtime_grant'] and not plan['token_acquisition_implemented']
    assert not plan['memory_enforced'] and not plan['physical_io_lane_resolved']
    build_plan = manual.shared_resource_plan('ox-build', env)
    assert build_plan['compiler_jobs'] == 2 and build_plan['declared_peak_credits'] == 4
    assert build_plan['token_acquisition_implemented']
    assert manual.shared_resource_plan('group-parser', env)['token_acquisition_implemented']
    from shared_dispatch import TARGETS
    assert 'sync-functional' not in TARGETS
    assert {'stock-build', 'ox-build', 'shared-entrypoints', 'group-parser'} <= TARGETS
print('PASS four shared/legacy selections and seven refusals; no output, build or child')
