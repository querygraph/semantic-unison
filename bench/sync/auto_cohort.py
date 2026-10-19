"""Versioned pure cohort accounting. No admission, lock access or FD release."""
import json
from pathlib import PurePosixPath
from invocation_journal import _audit_attempted
from worker_config import endpoint_bound, worker_options

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
    directories = set()
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
        directory = entries[index * 3]['identity']['directory']
        if directory in directories:
            raise ValueError('reused cohort fixture directory')
        directories.add(directory)
        for offset, (stage, field) in enumerate(STAGES):
            entry = entries[index * 3 + offset]
            identity = entry['identity']
            run = row[field]
            if (identity['directory'] != directory or identity['mode'] != row['mode'] or identity['stage'] != stage
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


BACKGROUND = 'generated auto cohort; concurrent host activity disclosed; no quiet-window claim'


def parameters(cohort):
    # Reconstruct instead of trusting caller-supplied accounting fields.
    c = contract(cohort['label'], cohort['selection'])
    if not exact(c, cohort):
        raise ValueError('cohort contract differs')
    return dict(modes=list(MODES), workers=[c['selection']], file_mib=32, files=8,
                packet_bytes=8192, warmups=1, repetitions=5, timeout_seconds=30.0,
                background_note=BACKGROUND, measure_primary_reads=True,
                measure_semantic_phases=True, property_removal_controls=False,
                layout_only_controls=False, loopback_cpu_credit_bound=c['reserved_credits'],
                maximum_configured_endpoint_credit_sum=2*c['endpoint_permit_upper_bound'],
                orchestration_cpu_credits=2, maximum_declared_cpu_credit_sum=c['declared_peak_credits'],
                endpoint_cpu_budget_ceiling=8,
                endpoint_cpu_permit_upper_bounds=[dict(selection=c['selection'],
                                                      upper_bound=c['endpoint_permit_upper_bound'])])


def launch_argv(cohort, *, interpreter, script, output, artifact):
    """Exact generated command; metadata only, no subprocess or artifact reads.

    Artifact hashes are declarations here. A future owner must authenticate the
    plan and hash the actual files under its acquired IO reservation.
    """
    p = parameters(cohort)
    if set(artifact) != {'binary', 'compiler', 'binary_sha256', 'compiler_sha256'}:
        raise ValueError('exact artifact declaration required')
    for path in (interpreter, script, output, artifact['binary'], artifact['compiler']):
        if type(path) is not str or not path.startswith('/') or '\x00' in path:
            raise ValueError('absolute path required')
    for name in ('binary_sha256', 'compiler_sha256'):
        digest = artifact[name]
        if type(digest) is not str or len(digest) != 64 or any(c not in '0123456789abcdef' for c in digest):
            raise ValueError('SHA256 declaration required')
    label = cohort['label']
    argv = [interpreter, script, '--binary', label+'='+artifact['binary'],
            '--compiler', label+'='+artifact['compiler'],
            '--expected-binary-sha256', label+'='+artifact['binary_sha256'],
            '--expected-compiler-sha256', label+'='+artifact['compiler_sha256']]
    for option, value in (
            ('modes', ','.join(MODES)), ('workers', str(cohort['selection'])),
            ('endpoint-cpu-budget', '8'), ('loopback-cpu-credits', str(p['loopback_cpu_credit_bound'])),
            ('orchestration-cpu-credits', '2'), ('file-mib', '32'), ('files', '8'),
            ('packet-bytes', '8192'), ('warmups', '1'), ('repetitions', '5'),
            ('timeout', '30'), ('background-note', BACKGROUND), ('output', output)):
        argv += ['--'+option, value]
    return argv + ['--measure-primary-reads', '--measure-semantic-phases']


def check_launch(argv, cohort, **bindings):
    if not exact(argv, launch_argv(cohort, **bindings)):
        raise ValueError('exact cohort launch differs')


def audit_bound(result, cohort, artifact, *, fixture_root):
    """Full nested matrix plus declared parameters/artifacts; no file hashing."""
    root = PurePosixPath(fixture_root)
    if (type(fixture_root) is not str or not root.is_absolute()
            or str(root) != fixture_root or '..' in root.parts or '\x00' in fixture_root):
        raise ValueError('canonical absolute fixture root required')
    expected = parameters(cohort)
    for key, value in expected.items():
        if not exact(result['parameters'].get(key), value):
            raise ValueError('cohort parameter differs: '+key)
    label = cohort['label']
    if (result.get('purpose') != 'warm-cache performance' or 'partition' in result
            or set(result['binaries']) != {label} or set(result['compilers']) != {label}
            or result['compilers'][label]['path'] != artifact['compiler']
            or not exact(result['admitted_binary_sha256'], {label:artifact['binary_sha256']})
            or not exact(result['admitted_compiler_sha256'], {label:artifact['compiler_sha256']})):
        raise ValueError('cohort artifact/purpose declaration differs')
    # Command equality in audit() binds nested row outcomes to their journal;
    # this additional check binds every attempted client/server to its artifact.
    for entry in result['invocations']:
        if entry['command'][0] != artifact['binary'] or entry['outcome']['proxy']['server_command'][0] != artifact['binary']:
            raise ValueError('cohort call artifact differs')
        identity = entry['identity']
        flags = ['-debug', 'copy', '-debug', 'semantic', '-debug', 'semantic-reads',
                 '-debug', 'semantic-timings', '-clone',
                 'off' if identity['mode'] == 'ordinary' else 'auto',
                 *worker_options(cohort['selection'], 8)]
        if identity['mode'] == 'semantic':
            flags += ['-semanticdng']
        directory = PurePosixPath(identity['directory'])
        if directory.parent != root or str(directory) != identity['directory'] or '..' in directory.parts:
            raise ValueError('fixture outside bound namespace')
        client = [artifact['binary'], str(directory / 'left'),
                  'ssh://localhost/' + str(directory / 'right'),
                  '-sshcmd', str(root / 'launcher.py'), '-servercmd', artifact['binary'],
                  '-batch', '-auto', '-fastcheck', 'false', '-times', *flags]
        server = [artifact['binary'], '-server', '__new-rpc-mode', *flags]
        if (not exact(entry['command'], client)
                or not exact(entry['outcome']['proxy']['server_command'], server)):
            raise ValueError('cohort client/server command differs')
    return audit(result, cohort)
