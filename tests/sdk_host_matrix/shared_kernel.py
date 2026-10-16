"""One-use injected call kernel; owns no runtime entry point or release authority."""
import copy,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tests'));sys.path.insert(0,str(ROOT/'bench/sync'))
from shared_cpu_pool import UnresolvedOwnership
from invocation_journal import Journal
from shared_plan import shared_matrix
from shared_result import audit

class Kernel:
    def __init__(self,reference,experimental,fixtures,memory_bytes):
        self.args=copy.deepcopy((reference,experimental,fixtures,memory_bytes))
        self.proposal=shared_matrix(*self.args);self.used=False
    def execute(self,*,invoke,persist):
        if self.used:raise ValueError('one matrix only; no retry')
        self.used=True
        result=dict(schema='unison-shared-sdk-kernel/1',complete=False,rows=[],
                    resource_release_authorized=False)
        def save():persist(copy.deepcopy(result))
        journal=Journal(result,save);save()
        try:
            for index,case in enumerate(self.proposal['cases'],1):
                journal.begin(dict(index=index,codec=case['codec'],backend=case['backend']),case['command'])
                try:out=invoke(copy.deepcopy(case))
                except UnresolvedOwnership:raise
                except BaseException as error:
                    if not hasattr(error,'outcome'):
                        raise UnresolvedOwnership('possible SDK call without returned outcome') from error
                    out=error.outcome
                    try:journal.finish(out)
                    except BaseException as persist_error:
                        raise UnresolvedOwnership('returned SDK evidence could not be persisted') from persist_error
                    raise
                try:journal.finish(out)
                except BaseException as error:
                    raise UnresolvedOwnership('returned SDK evidence could not be persisted') from error
                result['rows'].append(dict(index=index,command=case['command'],outcome=out))
                # Stop starting calls immediately on the first functional failure.
                result['functional_audit']=audit(*self.args,result['rows'],require_complete=False)
                save()
            result['complete']=True;save();return result
        except UnresolvedOwnership:raise
        except BaseException as error:
            result['complete']=False;result['failure']=repr(error)
            save();raise
