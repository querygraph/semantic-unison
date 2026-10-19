"""Versioned pure cohort accounting. No admission, lock access or FD release."""
import json
from invocation_journal import _audit_attempted
from worker_config import endpoint_bound

SELECTORS = (1, 2, 4, 8, 'auto')
MODES = ('ordinary', 'receiver-clone', 'semantic')
STAGES = (('seed', 'seed_sync'), ('update', 'update_sync'), ('noop', 'noop_sync'))


def exact(left, right):
    return json.dumps(left, sort_keys=True, allow_nan=False) == json.dumps(right, sort_keys=True, allow_nan=False)


def contract(label, selection):
    if label not in ('stock', 'ox') or not any(exact(selection, x) for x in SELECTORS):
        raise ValueError('exact compiler and worker selection required')
    bound = endpoint_bound(selection, 8)
    declared = 2 * bound + 2
    return dict(schema='unison-auto-cohort/1', label=label, selection=selection,
                endpoint_cpu_ceiling=8, endpoint_permit_upper_bound=bound,
                declared_peak_credits=declared, reserved_credits=8 if declared <= 8 else 18,
                modes=list(MODES), warmups=1, repetitions=5, rows=18, cli_invocations=54)


def audit_attempted(result, cohort):
    expected = contract(cohort['label'], cohort['selection'])
    if not exact(cohort, expected):
        raise ValueError('cohort contract differs')
    for entry in result.get('invocations', []):
        identity = entry['identity']
        if identity['label'] != cohort['label'] or not exact(identity['workers'], cohort['selection']):
            raise ValueError('journal crosses cohort boundary')
    return _audit_attempted(result, modes=MODES, stages=tuple(x[0] for x in STAGES),
                            maximum=54, workers=(cohort['selection'],))


def audit(result, cohort):
    lifecycle = audit_attempted(result, cohort)
    if result.get('schema') != 'unison-synthetic-sync/0' or result.get('complete') is not True:
        raise ValueError('complete sync result required')
    expected = {(mode, phase, repetition) for mode in MODES
                for phase, count in (('warmup', 1), ('measured', 5))
                for repetition in range(1, count + 1)}
    seen = set()
    entries = result['invocations']
    if len(entries) != 54 or len(result['samples']) != 18:
        raise ValueError('exact 18 rows/54 calls required')
    for index, row in enumerate(result['samples']):
        key = (row['mode'], row['phase'], row['repetition'])
        if type(row['repetition']) is not int or key not in expected or key in seen:
            raise ValueError('missing, duplicate or unexpected row')
        seen.add(key)
        if row['label'] != cohort['label'] or not exact(row['workers'], cohort['selection']):
            raise ValueError('row crosses cohort boundary')
        for name in ('exact_result_and_unchanged_basis', 'noop_preserved_receiver_inode',
                     'staging_cleaned', 'private_fixture_removed'):
            if row.get(name) is not True:
                raise ValueError('functional proof missing')
        for offset, (stage, field) in enumerate(STAGES):
            entry = entries[index * 3 + offset]
            identity = entry['identity']
            run = row[field]
            if (identity['mode'] != row['mode'] or identity['stage'] != stage
                    or not exact(entry['outcome'], run)):
                raise ValueError('row/journal outcome binding differs')
            proxy = run['proxy']
            if (run['returncode'] != 0 or run.get('timed_out') is not False
                    or run['supervisor_cleanup']['returncode'] != 0
                    or proxy['server_returncode'] != 0 or proxy.get('fault') is not None
                    or proxy.get('pump_errors') != []
                    or any(run[name].get('cancel_reason') is not None
                           for name in ('client_cleanup', 'supervisor_cleanup'))):
                raise ValueError('successful call required')
    return dict(lifecycle, rows=18, cli_invocations=54, functional_success_inferred=True,
                parent_terminal_proved=False, token_release_authorized=False,
                scope='nested cohort journal and functional rows; not artifact authentication or measurements')
