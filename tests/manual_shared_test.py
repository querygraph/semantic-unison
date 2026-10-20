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
    shared_check = manual.command('ox-check', out, env)
    assert '--selftest' in shared_check and shared_check[shared_check.index('--selftest-workers')+1] == '3'
    assert shared_check[shared_check.index('--jobs')+1] == '2'
    assert manual.shared_resource_plan('ox-check', env)['compiler_jobs'] == 2
    assert manual.shared_resource_plan('ox-check', env)['declared_peak_credits'] == 8
    assert manual.shared_resource_plan('ox-check', env)['selftest_endpoint_workers'] == [3, 3]
    dune_check = manual.command('ox-dune-check', out, env)
    assert dune_check[dune_check.index('--build-system')+1] == 'dune'
    assert dune_check[dune_check.index('--selftest-workers')+1] == '3'
    assert manual.shared_resource_plan('ox-dune-check', env)['declared_peak_credits'] == 8
    one = manual.command('ox-build', out, dict(env, SHARED_CPU_CREDITS='3'))
    assert one[one.index('--jobs') + 1] == '1'
    legacy = manual.command('ox-make', out, {'OX_PREFIX': '/UNREAD-compiler'})
    assert '--selftest' in legacy and legacy[legacy.index('--jobs') + 1] == '4'
    inspector = manual.command('inspect-ox', out, env)
    assert '--build-only' in inspector and '--report' in inspector and '--selftest' not in inspector
    assert inspector[inspector.index('--report') + 1] == str(out / 'RESULT.json')
    assert manual.shared_resource_plan('inspect-ox', env)['declared_peak_credits'] == 3
    local_clone = manual.command('private-dng-local-clone', out, env)
    assert local_clone == [sys.executable, str(manual.ROOT / 'tests/private_dng_local_clone/run.py')]
    assert manual.shared_resource_plan('private-dng-local-clone', env)['declared_peak_credits'] == 5
    conformance = manual.command('sde-conformance', out, env)
    assert conformance == [sys.executable, str(manual.ROOT / 'tests/semantic/conformance/shared.py')]
    conformance_plan = manual.shared_resource_plan('sde-conformance', env)
    assert conformance_plan['compiler_jobs'] == 1 and conformance_plan['declared_peak_credits'] == 3
    assert conformance_plan['token_acquisition_implemented']
    framing = manual.command('dng-private-framing', out, env)
    assert framing == [sys.executable, str(manual.ROOT / 'tests/dng_private_data/run.py')]
    framing_plan = manual.shared_resource_plan('dng-private-framing', env)
    assert framing_plan['declared_peak_credits'] == 3 and framing_plan['compiler_jobs'] == 1
    assert framing_plan['token_acquisition_implemented']
    diagnostic = manual.command('dng-private-diagnostic', out, env)
    assert diagnostic == [sys.executable, str(manual.ROOT / 'tools/private-dng-framing/controls.py')]
    assert manual.shared_resource_plan('dng-private-diagnostic', env)['declared_peak_credits'] == 3
    assert manual.shared_resource_plan('dng-private-diagnostic', env)['compiler_jobs'] == 1
    for incomplete in ({}, {'FRAMING_PLAN': '/fixed', 'FRAMING_PLAN_SHA256': '0'*64}):
        try:
            manual.command('private-dng-framing-input', out, dict(env, **incomplete))
        except ValueError:
            pass
        else:
            raise AssertionError('framing input admitted without IO grant')
    framing_env = dict(env, FRAMING_PLAN='/fixed-plan', FRAMING_PLAN_SHA256='0'*64,
                       SHARED_IO_ADMISSION='/fixed-admission', SHARED_IO_ADMISSION_SHA256='1'*64)
    argv = manual.command('private-dng-framing-input', out, framing_env)
    assert argv[1] == str(manual.ROOT/'tools/private-dng-framing/admitted.py')
    assert argv[-4:] == ['--plan', '/fixed-plan', '--plan-sha256', '0'*64]
    assert manual.shared_resource_plan('private-dng-framing-input', framing_env)['declared_peak_credits'] == 3
    reuse_env = dict(env, INSPECTOR_RECEIPT='/NEVER-EXECUTED receipt.json',
                     INSPECT_INPUT='/NEVER-READ input.dng')
    reuse = manual.command('inspect-file', out, reuse_env)
    assert '--use-build' in reuse and '--build-only' not in reuse and '--ocamlopt' not in reuse
    assert reuse[-1] == reuse_env['INSPECT_INPUT']
    assert manual.shared_resource_plan('inspect-file', reuse_env)['declared_peak_credits'] == 3

    for target, changes in (
        ('ox-check', {'SHARED_CPU_CREDITS': '7'}),
        ('ox-dune-check', {'SHARED_CPU_CREDITS': '7'}),
        ('ox-build', {'JOBS': '5'}),
        ('ox-build', {'SHARED_CPU_CREDITS': '0'}),
        ('ox-build', {'SHARED_CPU_CREDITS': '9'}),
        ('ox-build', {'SHARED_CPU_CREDITS': 'bad'}),
        ('ox-make', {}),
        ('host-executor', {}),
        ('sync-functional', {'SHARED_CPU_CREDITS': '2'}),
        ('inspect-ox', {'SHARED_CPU_CREDITS': '2'}),
        ('dng-private-framing', {'SHARED_CPU_CREDITS': '2'}),
        ('dng-private-diagnostic', {'SHARED_CPU_CREDITS': '2'}),
        ('private-dng-local-clone', {'SHARED_CPU_CREDITS': '4'}),
    ):
        try:
            manual.command(target, out, dict(env, **changes))
        except ValueError:
            pass
        else:
            raise AssertionError('unqualified shared request admitted: ' + target)

with patch.object(manual, 'checked_build', return_value={'binary': '/NEVER-execute',
                                                       'compiler': '/NEVER-query',
                                                       'binary_sha256':'a'*64,'compiler_sha256':'b'*64}):
    argv = manual.command('sync-functional', out,
                          dict(env, STOCK_RECEIPT='unread', OX_RECEIPT='unread'))
    assert '--shared-qualification' in argv and '--qualification' not in argv
    assert '--measure-semantic-phases' not in argv
    measured = manual.command('sync-functional', out, dict(env, STOCK_RECEIPT='unread',
                              OX_RECEIPT='unread', MEASURE_SEMANTIC_PHASES='1'))
    assert measured.count('--measure-semantic-phases') == 1
    try:manual.command('sync-functional', out, dict(env, STOCK_RECEIPT='unread', OX_RECEIPT='unread', MEASURE_SEMANTIC_PHASES='true'))
    except ValueError:pass
    else:raise AssertionError('invalid timing opt-in accepted')
    prop_argv = manual.command('sync-functional',out,dict(env,STOCK_RECEIPT='unread',OX_RECEIPT='unread',SYNC_PROPERTY_REMOVAL_CONTROLS='1',SHARED_IO_ADMISSION='/fixed',SHARED_IO_ADMISSION_SHA256='0'*64))
    assert '--property-removal-controls' in prop_argv
    assert '--property-removal-controls' not in argv
    layout_env=dict(env,STOCK_RECEIPT='unread',OX_RECEIPT='unread',
                    SYNC_LAYOUT_ONLY_CONTROLS='1',SHARED_IO_ADMISSION='/fixed',SHARED_IO_ADMISSION_SHA256='0'*64)
    assert '--layout-only-controls' in manual.command('sync-functional',out,layout_env)
    assert '--layout-only-controls' not in argv
    for bad in (dict(layout_env,SYNC_LAYOUT_ONLY_CONTROLS='true'),
                dict(layout_env,SYNC_PROPERTY_REMOVAL_CONTROLS='1'),
                dict(layout_env,SHARED_IO_ADMISSION='')):
        try:manual.command('sync-functional',out,bad)
        except ValueError:pass
        else:raise AssertionError('unqualified layout-only command')
    assert manual.shared_resource_plan('sync-functional', dict(env,SYNC_PROPERTY_REMOVAL_CONTROLS='1'))['retained_property_reader_limit'] == 36
    assert argv.count('--expected-binary-sha256') == 2
    assert argv.count('--expected-compiler-sha256') == 2
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
        shared_dispatch.run('group-parser', [sys.executable, str(Path(__file__).resolve())], out, 8)
    except ValueError as error:
        assert 'waitid' in str(error)
    else:
        raise AssertionError('unsupported interpreter acquired shared ownership')
print('PASS unsupported interpreter refusal before pool read/acquisition')
