"""Pure fixed shared-eight repeated-matrix audit; never releases resources.

Lifecycle evidence and optional measurement completeness are separate. A caller
must still prove its own worker/group settlement and close its held descriptors.
This module grants no execution, payload access, or timing-window admission.
"""
import json

import batch_audit
import invocation_journal
import phase_stats


PARAMETERS = {
    'modes': ['ordinary', 'receiver-clone', 'semantic'],
    'workers': [1, 2, 3], 'warmups': 1, 'repetitions': 5,
    'file_mib': 32, 'files': 2,
    'loopback_cpu_credit_bound': 8, 'orchestration_cpu_credits': 2,
    'maximum_declared_cpu_credit_sum': 8,
    'measure_primary_reads': True, 'measure_semantic_phases': True,
}
ROWS = 108
CALLS = 3 * ROWS


def exact(left, right):
    # Ordinary Python equality accepts True == 1 and erases receipt type errors.
    return json.dumps(left, sort_keys=True, allow_nan=False) == json.dumps(
        right, sort_keys=True, allow_nan=False)


def audit_attempted(result):
    """Bounded failed-prefix proof, with the original journal's strict protocol."""
    return invocation_journal._audit_attempted(
        result, modes=tuple(PARAMETERS['modes']),
        stages=('seed', 'update', 'noop'), maximum=CALLS)


def audit(result):
    require = batch_audit.require
    for key, value in PARAMETERS.items():
        require(exact(result['parameters'][key], value), 'timed parameter differs: ' + key)
    require(result['purpose'] == 'warm-cache performance', 'timed purpose differs')
    require(not result['parameters'].get('property_removal_controls', False)
            and not result['parameters'].get('layout_only_controls', False),
            'separate functional controls cannot change timed fixtures')
    summary = batch_audit.audit(result, PARAMETERS)
    prefix = audit_attempted(result)
    require(summary['rows'] == ROWS and summary['cli_invocations'] == CALLS
            and prefix['attempted_cli_invocations'] == CALLS
            and prefix['server_not_created_invocations'] == 0, 'timed matrix incomplete')
    directories = set()
    for row_index, sample in enumerate(result['samples']):
        directory = None
        for offset, (stage, field) in enumerate((('seed', 'seed_sync'),
                                                ('update', 'update_sync'),
                                                ('noop', 'noop_sync'))):
            entry = result['invocations'][3 * row_index + offset]
            identity = entry['identity']
            require(all(exact(identity[key], sample[key]) for key in ('label', 'mode', 'workers'))
                    and identity['stage'] == stage
                    and exact(entry['outcome'], sample[field]), 'row/journal binding differs')
            if directory is None:
                directory = identity['directory']
                require(directory not in directories, 'reused timed fixture directory')
                directories.add(directory)
            require(identity['directory'] == directory, 'row fixture directory changed')

    # Malformed/missing telemetry is a measurement refusal, not evidence of an
    # unclosed process. Do not turn this result into a fabricated numeric zero.
    missing = []
    for index, sample in enumerate(result['samples']):
        if sample['mode'] != 'semantic':
            continue
        try:
            phases = phase_stats.validate(sample['counters']['semantic_phase_observations'])
            if (phases is None or phases['observed_worker_stages'] != ['hash', 'parse', 'verify', 'write']
                    or phases['unavailable_worker_jobs']
                    or not any(r['kind'] == 'namespace_publication' for r in phases['records'])
                    or any(r['kind'] == 'namespace_unavailable' for r in phases['records'])):
                raise ValueError('incomplete phase observations')
        except (KeyError, TypeError, ValueError, OverflowError, RecursionError):
            missing.append(index)
    return dict(summary, journal_bound=True,
                phase_measurements_qualified=not missing,
                phase_measurement_incomplete_rows=missing,
                scope='Fixed shared-eight repeated lifecycle/output matrix; phase qualification '
                      'is separate. Not aggregate owner closure, quiet timing, physical IO, '
                      'hard RSS/FD bounds, or complete commit/durability accounting.')
