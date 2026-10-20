"""Immutable auto-cohort metadata contract; validation is not admission."""
from pathlib import PurePosixPath
import re
from auto_cohort import reconstruct, exact, launch_argv

SCHEMA = 'unison-auto-cohort-plan/2'
LIMITS = dict(owner_observation_seconds=900, cli_observation_seconds=30,
              declared_logical_io_bytes=32*1024**3, physical_io_limit_enforced=False,
              retry_allowed=False, sdk_calls=0, camera_inputs=0)


def limits(cohort):
    canonical = reconstruct(cohort)
    if not exact(canonical, cohort):
        raise ValueError('cohort declaration differs')
    if canonical['schema'] == 'unison-auto-cohort/1':
        return dict(LIMITS)
    return dict(LIMITS, owner_observation_seconds=7200,
                cli_observation_seconds=180, declared_logical_io_bytes=4*1024**4)


def path(value):
    if (type(value) is not str or not value.startswith('/') or '\x00' in value
            or str(PurePosixPath(value)) != value or '..' in PurePosixPath(value).parts):
        raise ValueError('canonical absolute path required')
    return value


def digest(value):
    if type(value) is not str or re.fullmatch('[0-9a-f]{64}',value) is None:
        raise ValueError('exact SHA256 required')
    return value


def validate(plan, *, execution_sources):
    """Pure structural checks against a caller's trusted source inventory.

    Caller must authenticate plan bytes and trusted inventory, verify current
    source/build hashes, acquire IO then the exact CPU set, and prove settlement.
    No runtime grant is created by accepting an 18-credit source plan.
    """
    fields = {'schema','workspace','interpreter','interpreter_sha256','script',
              'cohort','artifact','build_receipt','execution_sha256','prerequisite_sha256',
              'limits','launch_argv','cpu_token_indexes','requires_temporary_borrow'}
    if type(plan) is not dict or set(plan) != fields or plan['schema'] != SCHEMA:
        raise ValueError('exact cohort plan schema required')
    workspace = PurePosixPath(path(plan['workspace']))
    if workspace.parent != PurePosixPath('/private/tmp') or re.fullmatch('unison-auto-cohort-[0-9a-f]{32}',workspace.name) is None:
        raise ValueError('fresh private cohort namespace required')
    cohort = plan['cohort']
    if not exact(cohort,reconstruct(cohort)):
        raise ValueError('cohort accounting differs')
    credits=cohort['reserved_credits']
    if (not exact(plan['cpu_token_indexes'],list(range(credits)))
            or plan['requires_temporary_borrow'] is not (credits==18)
            or not exact(plan['limits'],limits(cohort))):
        raise ValueError('exact resource request required')
    for key in ('interpreter','script'):
        path(plan[key])
    digest(plan['interpreter_sha256'])
    for key in ('binary','compiler'):
        path(plan['artifact'][key])
    sources=plan['execution_sha256']
    if type(sources) is not dict or set(sources)!=set(execution_sources) or not sources:
        raise ValueError('trusted complete execution inventory required')
    for name,value in sources.items():
        if (type(name) is not str or PurePosixPath(name).is_absolute()
                or '..' in PurePosixPath(name).parts or str(PurePosixPath(name))!=name):
            raise ValueError('repository-relative source required')
        digest(value)
    prerequisites=plan['prerequisite_sha256']
    if type(prerequisites) is not dict or not prerequisites:
        raise ValueError('qualified prerequisite receipts required')
    for name,value in prerequisites.items():
        path(name);digest(value)
    if path(plan['build_receipt']) not in prerequisites:
        raise ValueError('build receipt must be an authenticated prerequisite')
    expected=launch_argv(cohort,interpreter=plan['interpreter'],script=plan['script'],
                         output=str(workspace/'RESULT.json'),artifact=plan['artifact'])
    if not exact(plan['launch_argv'],expected):
        raise ValueError('exact plan launch differs')
    return plan


def checked_metadata(plan_path, plan_sha256, *, repository, execution_sources):
    """Authenticate bounded plan/source/receipt bytes, never executable payloads.

    This is cooperative epoch fencing, not protection against hostile same-UID
    writers. The supplied trusted inventory must be fixed by the reviewed owner.
    read_bytes uses the qualified multi-close uncertainty carrier.
    """
    import hashlib
    import json
    from cached_benchmark.contract import read_bytes
    from shared_cpu_pool import unique_object
    digest(plan_sha256)
    raw = read_bytes(path(plan_path), 1048576)
    if hashlib.sha256(raw).hexdigest() != plan_sha256:
        raise ValueError('plan SHA differs')
    plan = validate(json.loads(raw, object_pairs_hook=unique_object),
                    execution_sources=execution_sources)
    root = PurePosixPath(path(str(repository)))
    if plan['script'] != str(root/'bench/sync/run.py'):
        raise ValueError('runner outside trusted repository')
    for name, expected in plan['execution_sha256'].items():
        if hashlib.sha256(read_bytes(str(root/name), 16*1048576)).hexdigest() != expected:
            raise ValueError('execution source changed: '+name)
    for name, expected in plan['prerequisite_sha256'].items():
        if hashlib.sha256(read_bytes(name, 16*1048576)).hexdigest() != expected:
            raise ValueError('prerequisite changed: '+name)
    return plan


def verify_artifacts(plan):
    """Hash executable bytes; caller must already own admitted IO/CPU resources.

    No lock ownership is inferred or acquired here. Returns hashes, not a grant.
    An uncertain close propagates as retained ownership without numeric retry.
    """
    import hashlib
    from cached_benchmark.contract import read_bytes
    declarations = {
        plan['interpreter']: plan['interpreter_sha256'],
        plan['artifact']['binary']: plan['artifact']['binary_sha256'],
        plan['artifact']['compiler']: plan['artifact']['compiler_sha256']}
    if len(declarations) != 3:
        raise ValueError('distinct interpreter/binary/compiler required')
    actual = {}
    for name, expected in declarations.items():
        path(name);digest(expected)
        actual[name] = hashlib.sha256(read_bytes(name, 256*1048576)).hexdigest()
        if actual[name] != expected:
            raise ValueError('executable artifact changed: '+name)
    return actual


def production_sources(repository):
    """Current source inventory, independently enumerated rather than plan-chosen."""
    from pathlib import Path
    root = Path(repository)
    names = sorted(str(p.relative_to(root)) for p in (root/'src').rglob('*')
                   if p.is_file() and (p.suffix in ('.ml','.mli','.c','.h')
                       or p.name in ('Makefile','Makefile.OCaml','dune','dune-project')
                       or p.name.endswith('.ox.mli.in')))
    if not {'src/semanticRuntime.ml','src/semanticWorkers.ml','src/semanticMergeCache.ml'} <= set(names):
        raise ValueError('production worker/runtime/cache inventory missing')
    return names


def execution_sources(repository):
    """Fixed transitive benchmark/owner support inventory, metadata enumeration."""
    from pathlib import Path
    root=Path(repository)
    names = [str(p.relative_to(root)) for p in (root/'bench/sync').glob('*.py')]
    names += ['tests/shared_dispatch.py','tests/manual.py','tests/shared_cpu_pool.py',
              'tests/shared_io_pool.py','tests/shared_process_owner.py',
              'tests/cached_benchmark/contract.py','tests/cohort_entry.py',
              'tests/sdk_host_matrix/shared_binding.py',
              'tests/qualification/semantic-observation-20261013.json',
              'tests/checked_worker/qualification.json',
              'tests/private_camera_receiving/close.py']
    return sorted(set(names))


def verify_build(plan, receipt, *, repository):
    """Bind successful current production build to declared binary and compiler.

    Must run inside admitted IO ownership: reads current production sources.
    The receipt itself must already be authenticated by checked_metadata.
    This is neither an independent rerun of selftests nor a machine grant.
    """
    import hashlib
    from cached_benchmark.contract import read_bytes
    if (receipt.get('complete') is not True or receipt.get('selftest_requested') is not True
            or type(receipt.get('build_exit')) is not int or receipt['build_exit'] != 0
            or type(receipt.get('selftest_exit')) is not int or receipt['selftest_exit'] != 0):
        raise ValueError('successful qualified build/selftest receipt required')
    artifact=plan['artifact']
    for key in ('binary','compiler','binary_sha256','compiler_sha256'):
        actual=receipt.get(key)
        if key in ('binary','compiler') and type(actual) is str:
            from pathlib import Path
            actual=str(Path(actual).resolve())
        if actual != artifact[key]:
            raise ValueError('build artifact declaration differs: '+key)
    pins=receipt['source_sha256']
    names=production_sources(repository)
    if {name for name in pins if name.startswith('src/')} != set(names):
        raise ValueError('complete current production inventory required')
    for name in names:
        digest(pins[name])
        if hashlib.sha256(read_bytes(str(PurePosixPath(repository)/name),16*1048576)).hexdigest() != pins[name]:
            raise ValueError('production source changed: '+name)
    return dict(production_sources_verified=len(names), build_selftest_receipt_bound=True,
                selftests_rerun=False, scope='authenticated historical build plus current production bytes')
