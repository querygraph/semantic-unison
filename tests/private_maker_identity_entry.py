"""One-use model-field diagnostic boundary; requires a fresh exact IO grant."""
import argparse
import os
from pathlib import Path
import re
import sys
import time

from private_maker_execute import document, save, PYTHON
from private_maker_plan import ROOT, SOURCE, IDENTITY
from private_maker_identity import selected_field, read_candidate, interpret
from shared_cpu_pool import UnresolvedOwnership
from shared_process_owner import retain_after_record

TARGET = 'private-maker-model'
SAVED_RESULT = '/private/tmp/unison-private-maker-slice-13f46b93c0ed4271af7cc389113808aa/RESULT.json'


def require(ok, message):
    if not ok: raise ValueError(message)


def sources():
    return [ROOT / path for path in (
        'tests/private_maker_identity_entry.py', 'tests/private_maker_identity.py',
        'tests/private_maker_coverage.py', 'tests/private_maker_shape.py',
        'tests/private_maker_slice.py', 'tests/private_maker_plan.py',
        'tests/private_maker_execute.py', 'tests/private_maker_audit.py',
        'tests/private_camera_receiving/close.py', 'tests/sdk_host_matrix/shared_binding.py',
        'tests/shared_io_pool.py', 'tests/shared_cpu_pool.py', 'tests/shared_process_owner.py')]


def check(plan):
    require(type(plan) is dict and set(plan) == {'schema', 'target', 'workspace', 'source',
        'saved_result', 'worker_seconds', 'cpu_credits', 'io_mode', 'max_requested_read_bytes',
        'semantic_eligibility', 'sdk_validation', 'source_hash_requested'}, 'exact model plan required')
    require(plan['schema'] == 'unison-private-maker-model-plan/1' and plan['target'] == TARGET
        and type(plan['worker_seconds']) is int and plan['worker_seconds'] == 10
        and type(plan['cpu_credits']) is int and plan['cpu_credits'] == 8
        and type(plan['max_requested_read_bytes']) is int and plan['max_requested_read_bytes'] == 9
        and plan['io_mode'] == 'EX_GLOBAL'
        and all(plan[k] is False for k in ('semantic_eligibility', 'sdk_validation', 'source_hash_requested')),
        'exact diagnostic-only nine-byte shared8 scope required')
    require(type(plan['workspace']) is str and re.fullmatch(
        r'/private/tmp/unison-private-maker-model-[0-9a-f]{32}', plan['workspace']) is not None,
        'fresh model workspace namespace required')
    source = plan['source']
    require(type(source) is dict and set(source) == {'path', 'identity'} and source['path'] == SOURCE
        and type(source['identity']) is dict and source['identity'] == IDENTITY
        and all(type(v) is int for v in source['identity'].values()), 'exact retained clone epoch required')
    saved = plan['saved_result']
    require(type(saved) is dict and set(saved) == {'path', 'sha256'} and saved['path'] == SAVED_RESULT
        and type(saved['sha256']) is str and re.fullmatch('[0-9a-f]{64}', saved['sha256']) is not None,
        'pinned saved slice result required')
    return plan


def checked_plan(path, digest):
    plan = check(document(path, digest))
    saved = document(plan['saved_result']['path'], plan['saved_result']['sha256'])
    require(saved['schema'] == 'unison-private-maker-worker/1' and saved['complete'] is True
            and saved['diagnostic']['outcome'] == 'CANDIDATE_SHAPE', 'actual saved candidate result required')
    selected_field(saved['diagnostic']['shape'])
    return plan


def child_argv(path, digest, workspace):
    return [sys.executable, str(Path(__file__).resolve()), '--worker', '--plan', str(path),
            '--plan-sha256', digest, '--workspace', str(workspace)]


def audit_worker(result, plan, *, parent_pid, worker_pid):
    check(plan)
    require(type(result) is dict and set(result) == {'schema', 'complete', 'diagnostic', 'failure',
        'parent_pid', 'worker_pid', 'canonical_metadata_bound', 'external_children_started'},
        'exact worker result required')
    require(result['schema'] == 'unison-private-maker-model-worker/1'
        and type(result['complete']) is bool and result['canonical_metadata_bound'] is True
        and type(result['parent_pid']) is int and result['parent_pid'] == parent_pid
        and type(result['worker_pid']) is int and result['worker_pid'] == worker_pid
        and type(result['external_children_started']) is int and result['external_children_started'] == 0,
        'actual worker identity and zero external children required')
    if result['complete']:
        require(result['failure'] is None and type(result['diagnostic']) is dict,
                'complete diagnostic required')
        value = result['diagnostic']
        raw_hex = value.get('raw_hex')
        require(type(raw_hex) is str and re.fullmatch('[0-9a-f]{18}', raw_hex) is not None,
                'exact bounded raw field required')
        expected = interpret(bytes.fromhex(raw_hex))
        expected.update(read_range=dict(offset=11440, requested=9, received=9),
                        source_epoch_unchanged=True, full_input_hash_computed=False,
                        fd_closure_proved_by_return=True)
        # Exact typed JSON comparison also rejects True in integer positions.
        import json
        require(json.dumps(value, sort_keys=True) == json.dumps(expected, sort_keys=True),
                'independent model-field diagnostic differs')
    else:
        require(result['diagnostic'] is None and type(result['failure']) is str
                and 0 < len(result['failure']) <= 4096, 'known closed failure must preserve reason')
    return dict(worker_complete=result['complete'], external_children_started=0,
                maximum_requested_payload_bytes=9, semantic_eligibility=False,
                resource_release_authorized=False)


def worker(args, plan):
    from sdk_host_matrix.shared_binding import verify
    require(sys.executable == PYTHON and args.workspace == plan['workspace'],
            'qualified interpreter and exact worker namespace required')
    root = Path(args.workspace); until = time.monotonic() + 3
    while True:
        try: start = document(root / 'SHARED-START.json'); break
        except FileNotFoundError:
            require(time.monotonic() < until, 'actual owner START absent')
            time.sleep(.005)
    binding = verify(start, child_argv(args.plan, args.plan_sha256, root),
                     parent_pid=os.getppid(), worker_pid=os.getpid(), target=TARGET)
    result = dict(schema='unison-private-maker-model-worker/1', complete=False, diagnostic=None,
                  failure=None, parent_pid=os.getppid(), worker_pid=os.getpid(),
                  canonical_metadata_bound=binding['canonical_metadata_bound'], external_children_started=0)
    try:
        saved = document(plan['saved_result']['path'], plan['saved_result']['sha256'])
        result['diagnostic'] = read_candidate(plan['source'], saved['diagnostic']['shape'],
                                             deadline=time.monotonic() + 10)
        result['complete'] = True
        audit_worker(result, plan, parent_pid=os.getppid(), worker_pid=os.getpid())
    except UnresolvedOwnership: raise
    except Exception as error:
        result['diagnostic'] = None
        result['failure'] = repr(error)
    save(root / 'RESULT.json', result)
    return 0 if result['complete'] else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for field in ('plan', 'plan-sha256'): parser.add_argument('--' + field, required=True)
    for field in ('workspace', 'admission', 'admission-sha256'): parser.add_argument('--' + field)
    parser.add_argument('--worker', action='store_true')
    args = parser.parse_args(); plan = checked_plan(args.plan, args.plan_sha256)
    root = Path(plan['workspace'])
    if args.worker: return worker(args, plan)
    require(args.admission and args.admission_sha256 and not args.workspace,
            'fresh exact IO admission required')
    require(not root.exists() and not root.is_symlink(), 'workspace consumed; never replay')
    from shared_dispatch import checked_io_request, run
    command = child_argv(args.plan, args.plan_sha256, root)
    admission = dict(path=args.admission, sha256=args.admission_sha256)
    checked_io_request(admission, TARGET, command, root, 8)
    os.umask(0o077); root.mkdir(mode=0o700)
    return run(TARGET, command, root, 8, io_admission=admission)


if __name__ == '__main__':
    try: raise SystemExit(main())
    except UnresolvedOwnership as error:
        retain_after_record(lambda: print(repr(error), file=sys.stderr, flush=True))
