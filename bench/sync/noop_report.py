"""Pure interpretation of retained no-op samples; never executes synchronization."""
import math
import statistics


def require(value, message):
    if not value:
        raise ValueError(message)


def time_value(value):
    require(type(value) in (int, float) and math.isfinite(value) and value >= 0,
            'finite nonnegative saved time required')
    return value


def samples(result, *, cohort_label, selection, artifact):
    require(result.get('schema') == 'unison-synthetic-sync/0' and result.get('complete') is True,
            'complete saved sync result required')
    require(type(result['parameters']['warmups']) is int
            and type(result['parameters']['repetitions']) is int
            and result['parameters']['warmups'] >= 1 and result['parameters']['repetitions'] >= 5,
            'declared warmup and five measured repetitions required')
    rows = []
    for index, sample in enumerate(result['samples']):
        require(sample['label'] == cohort_label and sample['phase'] in ('warmup', 'measured')
                and type(sample['repetition']) is int and sample['repetition'] > 0,
                'exact cohort label and phase required')
        require(all(sample.get(k) is True for k in ('exact_result_and_unchanged_basis',
                'noop_preserved_receiver_inode', 'staging_cleaned')), 'saved exact/noop fences required')
        call = sample['noop_sync']
        require(call['returncode'] == 0 and call['timed_out'] is False
                and call['capture_truncated'] is False
                and call['supervisor_capture_truncated'] is False, 'completed bounded no-op required')
        for name in ('client_cleanup', 'supervisor_cleanup'):
            group = call[name]
            require(group['reaped'] is True and group['returncode'] == 0
                    and group['other_group_members_absent_before_reap'] is True,
                    'saved client/supervisor group settlement required')
        proxy = call['proxy']
        require(proxy['fault'] is None and proxy['pump_errors'] == []
                and proxy['cancellation_signals'] == [] and proxy['input_pump_joined'] is True
                and proxy['server_returncode'] == 0
                and proxy['server_cleanup']['returncode'] == 0
                and proxy['server_cleanup']['reaped'] is True, 'saved proxy/server settlement required')
        require(len({call['client_cleanup']['pid'], call['supervisor_cleanup']['pid'],
                     proxy['server_pid']}) == 3, 'distinct saved process roles required')
        binding = proxy['server_group_binding']
        require(binding['observed_before_native_reap'] is True
                and binding['native_pid'] == proxy['server_pid']
                and binding['native_process_group'] == binding['supervisor_process_group']
                == binding['supervisor_pid'] == call['supervisor_cleanup']['pid'],
                'saved server membership must bind the observed supervisor group')
        rows.append(dict(label=cohort_label, selection=selection, mode=sample['mode'],
            phase=sample['phase'], repetition=sample['repetition'], sample_index=index,
            wall_seconds=time_value(call['wall_seconds']),
            native_client_lifetime_seconds=time_value(call['native_client_lifetime_seconds']),
            artifact=artifact))
    return rows


def summarize(rows):
    grouped = {}
    keys = set()
    warmups = {}
    for row in rows:
        key = row['label'], str(row['selection']), row['mode']
        unique = key + (row['phase'], row['repetition'])
        require(unique not in keys, 'duplicate no-op sample identity')
        keys.add(unique)
        if row['phase'] == 'warmup':
            warmups[key] = warmups.get(key, 0)+1
        if row['phase'] == 'measured':
            grouped.setdefault(key, []).append(row['wall_seconds'])
    groups = []
    for (label, selection, mode), values in sorted(grouped.items()):
        require(len(values) >= 5 and warmups.get((label, selection, mode), 0) >= 1,
                'actual warmup plus five saved measured no-op samples required')
        groups.append(dict(label=label, selection=selection, mode=mode, samples=len(values),
            median_seconds=statistics.median(values), minimum_seconds=min(values),
            maximum_seconds=max(values), sorted_seconds=sorted(values)))
    return dict(schema='unison-saved-noop-report/1', state='SAVED_OBSERVATIONS_ONLY',
        raw_samples=rows, groups=groups,
        warmup_samples=sum(r['phase'] == 'warmup' for r in rows),
        measured_samples=sum(r['phase'] == 'measured' for r in rows),
        qualification='Warm no-change scans immediately after exact update and independent verification, not clean/cold startup',
        timing_scope='Saved invocation wall includes client and loopback supervisor settlement; native client lifetime retained separately',
        tail_scope='With five samples, maximum is descriptive only, not a qualified population tail estimate',
        actual_new_execution=False, quiet_window_claim=False, resource_release_authorized=False,
        physical_IO_or_throughput_proved=False, current_production_proved=False)


def from_saved(saved_raw, index_raw, *, load):
    """Caller authenticates root metadata; rehash every referenced saved input."""
    import hashlib
    import json
    from pathlib import Path
    old = json.loads(saved_raw)
    index = json.loads(index_raw)
    require(old.get('schema') == 'unison-auto-cohort-report/1'
            and index.get('schema') == 'unison-ten-cohort-actual-closure/1',
            'exact saved-report and closure-index schemas required')
    verified = {}
    results = {}
    for ref in old['saved_inputs']:
        require(set(ref) == {'path', 'bytes', 'sha256'} and type(ref['bytes']) is int
                and 0 < ref['bytes'] <= 32*1048576 and Path(ref['path']).is_absolute(),
                'exact bounded saved-input pin required')
        require(ref['path'] not in verified, 'duplicate saved input path')
        raw = load(ref['path'], 32*1048576)
        require(len(raw) == ref['bytes'] and hashlib.sha256(raw).hexdigest() == ref['sha256'],
                'saved input SHA/size differs')
        verified[ref['path']] = dict(ref)
        if Path(ref['path']).name == 'RESULT.json':
            results[str(Path(ref['path']).parent)] = json.loads(raw)
    rows = []
    for cohort in index['cohorts']:
        artifact = verified[str(Path(cohort['workspace'])/'RESULT.json')]
        rows.extend(samples(results[cohort['workspace']], cohort_label=cohort['label'],
                            selection=cohort['selection'], artifact=artifact))
    report = summarize(rows)
    report['input_pins_verified'] = list(verified.values())
    report['input_matrix_complete_claim'] = old.get('matrix_complete')
    return report


def main():
    import argparse
    import hashlib
    import json
    from pathlib import Path
    import sys
    root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(root/'tests'))
    from cached_benchmark.contract import read_bytes
    from cached_benchmark.entry import write
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--saved-report', type=Path, required=True)
    p.add_argument('--saved-report-sha256', required=True)
    p.add_argument('--closure-index', type=Path, required=True)
    p.add_argument('--closure-index-sha256', required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    refs = []
    roots = []
    for path, expected in [(a.saved_report, a.saved_report_sha256),
                           (a.closure_index, a.closure_index_sha256)]:
        raw = read_bytes(path.resolve(), 8*1048576)
        require(hashlib.sha256(raw).hexdigest() == expected, 'root metadata SHA differs')
        roots.append(raw)
        refs.append(dict(path=str(path.resolve()), bytes=len(raw), sha256=expected))
    report = from_saved(*roots, load=lambda path, limit: read_bytes(Path(path), limit))
    report.update(saved_report_pin=refs[0], closure_index_pin=refs[1])
    write(a.output, report)
    print(json.dumps(dict(groups=len(report['groups']), warmups=report['warmup_samples'],
                          measured=report['measured_samples'], output=str(a.output))))


if __name__ == '__main__':
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]/'tests'))
    from shared_cpu_pool import UnresolvedOwnership
    from shared_process_owner import retain_after_record
    from shared_io_pool import uncertainty_records
    try:
        main()
    except UnresolvedOwnership as error:
        import json
        retain_after_record(lambda: print(json.dumps(dict(state='UNRESOLVED_METADATA_OWNER',
            error=repr(error), retained_fds=list(error.retained_fds),
            uncertain_closes=list(uncertainty_records(error, {})))), flush=True))
