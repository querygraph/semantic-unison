"""Original fabricated metadata only; no source/artifact/input read or grant."""
import copy
import unittest
from sdk_merge_receiving import admission as A
from sdk_merge_receiving.plan import LIMITS
from sdk_merge_receiving.plan_test import inputs
from sdk_merge_receiving.inputs_test import fixture as input_fixture

EXECUTION=['tests/sdk_merge_receiving/entry.py','tests/sdk_merge_receiving/admission.py']
PRODUCTION=['src/semanticRuntime.ml','src/semanticWorkers.ml']

def fixture():
    binaries,tool,workspace=inputs();cases,observations=input_fixture()
    input_ref=dict(path='/private/tmp/input-manifest.json',sha256='1'*64)
    sdk_ref=dict(path='/private/tmp/sdk-manifest.json',sha256='2'*64)
    builds={label:dict(receipt=dict(path='/private/tmp/'+label+'-build.json',sha256='3'*64),
        compiler=dict(path=A.COMPILERS[label],sha256='4'*64)) for label in ('stock','ox')}
    refs=[input_ref,sdk_ref]+[b['receipt'] for b in builds.values()]
    packet=dict(schema='unison-current-sdk-merge-execution/1',repository=A.REPOSITORY,
        workspace=workspace,interpreter=dict(path=A.PYTHON,sha256=A.PYTHON_SHA),binaries=binaries,
        tool=tool,builds=builds,cases=cases,source_observations=observations,
        input_manifest=input_ref,sdk_manifest=sdk_ref,execution_sha256={name:'5'*64 for name in EXECUTION},
        production_sha256={name:'6'*64 for name in PRODUCTION},
        prerequisite_sha256={r['path']:r['sha256'] for r in refs},limits=copy.deepcopy(LIMITS),
        cpu_policy_sha256=A.POLICY,io_manifest_sha256=A.IO)
    request=dict(path='/private/tmp/request.json',sha256='7'*64)
    plan=dict(path='/private/tmp/plan.json',sha256='8'*64)
    command=A.worker_command(packet,plan)
    grant=dict(schema='unison-current-sdk-merge-admission/1',state='ROOT_ADMITTED_ONE_CURRENT_SDK_MERGE',
        request=request,plan=plan,workspace=workspace,command=command,
        execution_sha256=copy.deepcopy(packet['execution_sha256']),
        production_sha256=copy.deepcopy(packet['production_sha256']),limits=copy.deepcopy(LIMITS),
        cpu_token_indexes=list(range(8)),cpu_policy_sha256=A.POLICY,io_manifest_sha256=A.IO,
        start_deadline_unix=200,nonce='9'*32)
    return packet,grant,request,plan,command


def validate(packet):
    return A.validate(packet,execution_sources=EXECUTION,production_sources=PRODUCTION,expected_uid=501)

class Admission(unittest.TestCase):
    def test_exact_matrix_and_fresh_grant_declarations_without_execution(self):
        packet,grant,request,plan,command=fixture();before=copy.deepcopy((packet,grant))
        result=validate(packet)
        self.assertEqual(len(result['rows']),9);self.assertFalse(result['runtime_admitted'])
        self.assertEqual(A.check(grant,packet,request_ref=request,plan_ref=plan,command=command,now=100),tuple(range(8)))
        self.assertEqual((packet,grant),before)

    def test_packet_source_artifact_budget_and_ancestry_substitutions_refused(self):
        for mutation in ('repository','interpreter','inventory','production','compiler','prerequisite',
                         'limits','policy','io','source-mode','source-alias','artifact-alias'):
            packet,*_=fixture()
            if mutation=='repository':packet['repository']='/different/repository'
            if mutation=='interpreter':packet['interpreter']['sha256']='0'*64
            if mutation=='inventory':packet['execution_sha256'].pop(EXECUTION[0])
            if mutation=='production':packet['production_sha256']['src/unrequested.ml']='0'*64
            if mutation=='compiler':packet['builds']['ox']['compiler']['path']=A.COMPILERS['stock']
            if mutation=='prerequisite':packet['prerequisite_sha256'][packet['input_manifest']['path']]='0'*64
            if mutation=='limits':packet['limits']['sdk_calls']=True
            if mutation=='policy':packet['cpu_policy_sha256']='0'*64
            if mutation=='io':packet['io_manifest_sha256']='0'*64
            names=list(packet['source_observations'])
            if mutation=='source-mode':packet['source_observations'][names[0]]['st_mode']=0o100600
            if mutation=='source-alias':packet['source_observations'][names[1]]['st_ino']=packet['source_observations'][names[0]]['st_ino']
            if mutation=='artifact-alias':packet['tool']['path']=packet['binaries']['stock']['path']
            with self.subTest(mutation=mutation),self.assertRaises(ValueError):validate(packet)

    def test_expired_or_nonfinite_observation_is_not_renewed(self):
        for deadline,now in ((100,100),(99,100),(float('nan'),100),(float('inf'),100),(200,True),(200,float('nan'))):
            packet,grant,request,plan,command=fixture();grant['start_deadline_unix']=deadline
            with self.subTest(deadline=deadline,now=now),self.assertRaises(ValueError):
                A.check(grant,packet,request_ref=request,plan_ref=plan,command=command,now=now)

    def test_old_slot_command_or_resource_substitution_never_passes(self):
        for mutation in ('state','request','plan','workspace','command','source','production',
                         'tokens','bool-token','limits','nonce','policy','io'):
            packet,grant,request,plan,command=fixture();grant=copy.deepcopy(grant)
            if mutation=='state':grant['state']='CONSUMED_ACTUAL_CLOSED'
            if mutation=='request':grant['request']['sha256']='0'*64
            if mutation=='plan':grant['plan']['sha256']='0'*64
            if mutation=='workspace':grant['workspace']='/private/tmp/old-slot'
            if mutation=='command':grant['command'].append('--retry')
            if mutation=='source':grant['execution_sha256'][EXECUTION[0]]='0'*64
            if mutation=='production':grant['production_sha256'][PRODUCTION[0]]='0'*64
            if mutation=='tokens':grant['cpu_token_indexes']=list(range(18))
            if mutation=='bool-token':grant['cpu_token_indexes'][0]=False
            if mutation=='limits':grant['limits']['per_cli_seconds']=120.0
            if mutation=='nonce':grant['nonce']='old'
            if mutation=='policy':grant['cpu_policy_sha256']='0'*64
            if mutation=='io':grant['io_manifest_sha256']='0'*64
            with self.subTest(mutation=mutation),self.assertRaises(ValueError):
                A.check(grant,packet,request_ref=request,plan_ref=plan,command=command,now=100)

if __name__=='__main__':unittest.main()
