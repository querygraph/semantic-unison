"""Prepare one repeated generated-fixture shared sync matrix; never create a runtime admission."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import time
from unittest.mock import patch

import manual
import shared_dispatch as dispatch
import shared_io_pool as io

ROOT=Path(__file__).resolve().parents[1]


def pin(path):
    path=Path(path);data=path.read_bytes()
    return dict(path=str(path),bytes=len(data),sha256=hashlib.sha256(data).hexdigest())


def save(path,value):
    with Path(path).open('x') as out:json.dump(value,out,indent=2);out.write('\n')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('stock','ox','nonce','report'):p.add_argument('--'+name,required=True)
    args=p.parse_args()
    if re.fullmatch('[0-9a-f]{8}',args.nonce) is None:raise ValueError('eight-hex fresh nonce required')
    workspace=Path('/private/tmp/u-timed-'+args.nonce)
    admission=Path('/private/tmp/unison-sync-timed-admission-v1-'+args.nonce+'.json')
    request_path=ROOT/'doc/sync-timed-request-v1.json'
    plan_path=ROOT/'doc/sync-timed-plan-v1.json'
    if any(x.exists() for x in (workspace,admission,request_path,plan_path)):
        raise ValueError('new namespace/documents required; no overwrite or replay')
    env=dict(SHARED_CPU_CREDITS='8',OUTPUT_DIR=str(workspace),STOCK_RECEIPT=args.stock,
        OX_RECEIPT=args.ox,MEASURE_SEMANTIC_PHASES='1',
        SHARED_IO_ADMISSION=str(admission),SHARED_IO_ADMISSION_SHA256='0'*64)
    builds=[manual.checked_build(env[label+'_RECEIPT']) for label in ('STOCK','OX')]
    command=manual.command('sync-timed',workspace,env)
    from timed_shared import check_argv
    check_argv(command,interpreter=sys.executable,script=str(ROOT/'bench/sync/run.py'),output=workspace/'RESULT.json')
    paths={Path(dispatch.__file__),ROOT/'tests/manual.py',ROOT/'tests/shared_io_pool.py',
        ROOT/'tests/shared_cpu_pool.py',ROOT/'tests/shared_process_owner.py',
        ROOT/'bench/sync/ownership.py',Path(command[1])}
    paths.update((ROOT/'bench/sync').glob('*.py'))
    fields=dict(state='ROOT_ADMITTED_ONE_SHARED_DISPATCH_IO_JOB',target='sync-timed',
        command=command,workspace=str(workspace),cpu_credits=8,io_manifest_sha256=io.CANONICAL_SHA256,
        execution_source_sha256={str(path):pin(path)['sha256'] for path in sorted(paths)})
    prospective=dict(fields,start_deadline_unix=time.time()+600)
    # Check the existing guard with an in-memory prospective admission and a
    # fake manifest result. This does not read/acquire the canonical pool or
    # publish an admission file. Root must separately authorize the real run.
    with patch.object(io,'read_manifest',return_value=prospective),patch.object(io.GlobalPool,'read',return_value='NO_LOCK_METADATA_CHECK'):
        assert dispatch.checked_io_request(dict(path=str(admission),sha256='0'*64),
            'sync-timed',command,workspace,8)[0]=='NO_LOCK_METADATA_CHECK'
    limits=dict(rows=108,CLI_calls_max=324,files_per_row=2,file_bytes_each=33554432,
        endpoint_workers_max=[3,3],owner_credits=2,cpu_indexes=list(range(8)),
        retained_property_readers_max=0,per_CLI_seconds=30,owner_observation_seconds=600,
        warmups=1,measured_repetitions=5,workers=[1,2,3],
        private_fixture_live_capacity_declared_bytes=5*64*1024**2,
        logical_IO_budget_declared_bytes=64*1024**3,IO_budget_instrumented=False,
        compilation_calls=0,SDK_Adobe_camera_Photo_payload_calls=0,
        compiler_metadata_queries=4,Unison_binary_version_queries=2,
        Darwin_sysctl_metadata_queries=2,Darwin_diskutil_metadata_queries=1,git_metadata_queries=1,
        CLI_call_count_scope='324 journaled seed/update/noop clients; two extra binary version queries separately declared',
        unknown='Retain actual owner and IO/CPU descriptions on unknown; no broad aggregate kill/retry.',
        scope='Repeated generated32MiB matrix under shared8; host activity uncontrolled, not physical IO/hard resource bounds or full SOL matrix.')
    prerequisites=[pin(args.stock),pin(args.ox),pin(ROOT/'tests/qualification/phase-format-correction-actual-20261018.json'),
        pin(ROOT/'tests/qualification/sync-phase-collection-actual-20261018.json'),
        pin('/private/tmp/unison-timed-dispatch-controls-20261018-001/SHARED-CLOSED.json'),
        pin('/private/tmp/unison-timed-regression-manual_shared_test-20261018-001/SHARED-CLOSED.json'),
        pin('/private/tmp/unison-timed-regression-shared_sync_controls-20261018-001/SHARED-CLOSED.json'),
        pin(ROOT/'tests/qualification/semantic-phase-observations-actual-20261017.json'),
        pin(ROOT/'tests/qualification/bound-publication-timing-actual-20261018.json')]
    plan=dict(schema='unison-sync-timed-plan/1',state='SOURCE_ONLY_NOT_ADMITTED',
        command=command,workspace=str(workspace),limits=limits,
        diagnostics=dict(primary_reads=True,semantic_phases=True,raw_streams_preserved=True,
            phase_intervals_inclusive=True,phase_sum_or_total_commit_claim=False,
            explicit_unavailable_retained=True,source_field_types_rebound_to_raw=True),
        next_step='One repeated32MiB dataset toward full SOL matrix; no old run replay or full benchmark completion claim.')
    save(plan_path,plan)
    env['SHARED_IO_ADMISSION_SHA256']='ROOT_PUBLISHED_SHA_REQUIRED'
    request=dict(schema='unison-sync-timed-request/1',state='PREPARED_NOT_ADMITTED_NOT_DISPATCHED',
        integration_head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        plan=pin(plan_path),admission_path=str(admission),admission_fields=fields,
        launch_argv=[sys.executable,str(ROOT/'tests/manual.py'),'sync-timed'],
        launch_environment=env,prerequisites=prerequisites,interpreter=pin(sys.executable),
        production_source_sha256={n:d for n,d in builds[0]['source_sha256'].items() if n.startswith('src/')},
        limits=limits,deadline_policy='Root supplies fresh deadline; exact one use only; refuse expired/stale/started grant.',
        supersession='New fixed repeated target/current corrected emitter binaries; every earlier smoke/benchmark grant remains consumed or retired. No reuse or automatic successor.')
    assert all(request['production_source_sha256'][n]==d for n,d in builds[1]['source_sha256'].items() if n.startswith('src/'))
    save(request_path,request)
    save(args.report,dict(state='METADATA_PREPARATION_ONLY_NO_RUNTIME_GRANT',request=pin(request_path),plan=pin(plan_path),
        command_checked_by_manual=True,prospective_IO_guard_checked_with_fake_manifest=True,
        canonical_pool_acquired=False,runtime_workspace_created=workspace.exists(),runtime_admission_created=admission.exists(),
        Unison_compiler_SDK_Photo_payload_invocations=0,source_preparer=pin(Path(__file__))))
    print('PREPARED',json.dumps(pin(request_path)),flush=True)


if __name__=='__main__':main()
