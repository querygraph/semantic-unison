import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
"""Callable two-probe journal worker; owns no resource-release authority."""
import copy
import math
import time

from mixed_validation.audit import audit
from shared_cpu_pool import UnresolvedOwnership


def execute_plan(plan, *, deadline, **callbacks):
    """Consume the exact source contract; caller still proves admission/FDs."""
    from mixed_validation.plan import commands
    argv=commands(plan)
    return execute(argv,deadline=deadline,
                   metadata_version=plan['metadata']['version'],
                   headroom=plan['limits']['probe_seconds'],**callbacks)


def execute(commands, *, deadline, metadata_version, prepare, invoke, persist,
            check_sources, verify_input, clock=time.monotonic, headroom=120,
            inspect=audit):
    """Callbacks run under the caller's retained IO/CPU ownership.

    persist must durably publish a detached snapshot or raise. An uncertain
    callback must raise UnresolvedOwnership; this function never closes locks.
    verify_input checks the caller's pinned input after the outcome is durable.
    """
    if (type(commands) is not list or len(commands)!=2
            or any(type(c) is not list or len(c)!=8
                   or any(type(x) is not str or '\0' in x for x in c)
                   for c in commands)):
        raise ValueError('exact two bounded probe commands required')
    if (type(deadline) not in (int,float) or not math.isfinite(deadline)
            or type(headroom) not in (int,float) or not math.isfinite(headroom)
            or headroom<=0):
        raise ValueError('finite deadline and positive headroom required')
    frozen=copy.deepcopy(commands)
    result=dict(schema='unison-mixed-validation-worker/1',complete=False,
                phase='PREPARING_NO_CALL',invocations=[],failure='worker not finished')

    def save():
        try: persist(copy.deepcopy(result))
        except UnresolvedOwnership: raise
        except BaseException as error:
            # A publication error cannot prove whether the last intent/outcome
            # reached storage. Keep the actual owner and original exception.
            raise UnresolvedOwnership('mixed journal publication unresolved') from error

    save()
    try:
        for index,command in enumerate(frozen):
            if deadline-clock()<headroom:
                raise TimeoutError('insufficient headroom before next probe')
            check_sources()
            prepare(index,copy.deepcopy(command))
            check_sources()
            if deadline-clock()<headroom:
                raise TimeoutError('insufficient headroom after preparation')
            entry=dict(index=index,state='INTENT',outcome=None)
            result['phase']='CALL_MAY_HAVE_STARTED'
            result['invocations'].append(entry)
            save()
            outcome=invoke(index,copy.deepcopy(command),deadline)
            entry.update(state='OUTCOME',outcome=copy.deepcopy(outcome))
            save()
            proof=inspect(outcome,command=copy.deepcopy(command),
                          metadata_version=metadata_version,require_admission=True)
            verify_input(index,copy.deepcopy(command))
            check_sources()
            if proof['functional_status']!='PASSED':
                raise ValueError('mixed probe functional failure; successor not started')
        result.update(complete=True,phase='FINISHED')
        del result['failure']
        save()
        return copy.deepcopy(result)
    except UnresolvedOwnership:
        raise
    except BaseException as error:
        result['failure']=repr(error)
        save()
        raise
