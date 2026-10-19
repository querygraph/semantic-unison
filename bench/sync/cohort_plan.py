"""Immutable auto-cohort metadata contract; validation is not admission."""
from pathlib import PurePosixPath
import re
from auto_cohort import contract, exact, launch_argv

SCHEMA = 'unison-auto-cohort-plan/1'
LIMITS = dict(owner_observation_seconds=900, cli_observation_seconds=30,
              declared_logical_io_bytes=32*1024**3, physical_io_limit_enforced=False,
              retry_allowed=False, sdk_calls=0, camera_inputs=0)


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
              'cohort','artifact','execution_sha256','prerequisite_sha256',
              'limits','launch_argv','cpu_token_indexes','requires_temporary_borrow'}
    if type(plan) is not dict or set(plan) != fields or plan['schema'] != SCHEMA:
        raise ValueError('exact cohort plan schema required')
    workspace = PurePosixPath(path(plan['workspace']))
    if workspace.parent != PurePosixPath('/private/tmp') or re.fullmatch('unison-auto-cohort-[0-9a-f]{32}',workspace.name) is None:
        raise ValueError('fresh private cohort namespace required')
    cohort = plan['cohort']
    if not exact(cohort,contract(cohort['label'],cohort['selection'])):
        raise ValueError('cohort accounting differs')
    credits=cohort['reserved_credits']
    if (not exact(plan['cpu_token_indexes'],list(range(credits)))
            or plan['requires_temporary_borrow'] is not (credits==18)
            or not exact(plan['limits'],LIMITS)):
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
    expected=launch_argv(cohort,interpreter=plan['interpreter'],script=plan['script'],
                         output=str(workspace/'RESULT.json'),artifact=plan['artifact'])
    if not exact(plan['launch_argv'],expected):
        raise ValueError('exact plan launch differs')
    return plan
