"""Inert named declarations only; no metadata read, lock or execution grant."""
import copy,hashlib,unittest
from current_validation_paths import admission as A
from current_validation_paths.contract import plan as case_plan,LIMITS
from current_validation_paths.parent_test import SOURCE

ENTRY='tests/current_validation_paths/entry.py'
EXECUTION=[A.LEGACY,ENTRY]
PRODUCTION=['src/semanticRuntime.ml']


def sha(data):return hashlib.sha256(data).hexdigest()


def fixture(compiler='stock',workspace='/private/tmp/u-vpath-'+'a'*16):
    legacy=SOURCE.encode();receipt=dict(path='/private/tmp/named-build-'+compiler+'/RESULT.json',sha256='b'*64)
    packet=dict(schema='unison-current-named-receiving-execution/1',repository=A.REPOSITORY,workspace=workspace,compiler=compiler,
        interpreter=dict(path=A.PYTHON,sha256=A.PYTHON_SHA),binary=dict(path='/private/tmp/named-build-'+compiler+'/src/unison',sha256='c'*64),
        build=dict(receipt=receipt,compiler=dict(path=A.COMPILERS[compiler],sha256='d'*64)),
        legacy_source=dict(path=A.REPOSITORY+'/'+A.LEGACY,bytes=len(legacy),sha256=sha(legacy)),
        rows=case_plan(SOURCE,workspace,compiler)['rows'],limits=copy.deepcopy(LIMITS),
        source_pins={A.LEGACY:sha(legacy),ENTRY:sha(b'entry')},production_sha256={'src/semanticRuntime.ml':sha(b'production')},
        prerequisite_sha256={receipt['path']:receipt['sha256']},cpu_policy_sha256=A.POLICY,io_manifest_sha256=A.IO)
    plan=dict(path='/private/tmp/named-plan/PLAN.json',sha256='7'*64);request=dict(path='/private/tmp/named-plan/REQUEST.json',sha256='8'*64)
    command=A.worker_command(packet,plan)
    grant=dict(schema='unison-current-named-receiving-admission/1',state='ADMITTED_ONE_CURRENT_NAMED_RECEIVING',request=request,plan=plan,
        workspace=workspace,compiler=compiler,command=command,source_pins=copy.deepcopy(packet['source_pins']),
        production_sha256=copy.deepcopy(packet['production_sha256']),limits=copy.deepcopy(LIMITS),cpu_token_indexes=list(range(8)),
        cpu_policy_sha256=A.POLICY,io_manifest_sha256=A.IO,start_deadline_unix=200,nonce='e'*32)
    return packet,grant,request,plan,command


def validate(packet,source=SOURCE):
    return A.validate(packet,source=source,execution_sources=EXECUTION,production_sources=PRODUCTION)


class Admission(unittest.TestCase):
    def test_each_compiler_plan_binds_all_original_cases_and_one_fresh_admission(self):
        for compiler in ('stock','ox'):
            packet,grant,request,plan,command=fixture(compiler)
            self.assertEqual(len(validate(packet)['rows']),21)
            self.assertEqual(A.check(grant,packet,request_ref=request,plan_ref=plan,command=command,now=199),tuple(range(8)))
            self.assertEqual(command[1],A.REPOSITORY+'/tests/current_validation_paths/entry.py')
    def test_packet_cannot_change_cases_limits_legacy_compiler_or_prerequisites(self):
        def rows(p):p['rows'][3]['max_CLI_calls']=5
        def limits(p):p['limits']['CLI_calls']=70
        def legacy(p):p['legacy_source']['bytes']+=1
        def compiler(p):p['build']['compiler']['path']=A.COMPILERS['ox']
        def extra(p):p['prerequisite_sha256']['/private/tmp/other.json']='9'*64
        def unpinned(p):p['source_pins'][A.LEGACY]='0'*64
        def binary(p):p['binary']['path']=A.PYTHON
        def workspace(p):p['workspace']='/private/tmp/u-other'
        for mutation in (rows,limits,legacy,compiler,extra,unpinned,binary,workspace):
            packet,*_=fixture();mutation(packet)
            with self.subTest(mutation=mutation.__name__),self.assertRaises(ValueError):validate(packet)
        packet,*_=fixture()
        with self.assertRaises(ValueError):validate(packet,SOURCE+'\n')
    def test_admission_cannot_be_reused_expired_widened_or_for_other_compiler(self):
        def expired(g):g['start_deadline_unix']=199
        def other(g):g['compiler']='ox'
        def negative(g):g['state']='ROOT_ADMITTED_ONE_CURRENT_SDK_NEGATIVE_RECEIVING'
        def command(g):g['command']=['/different']
        def credits(g):g['cpu_token_indexes']=list(range(18))
        def sources(g):g['source_pins']={}
        def nonce(g):g['nonce']='short'
        for mutation in (expired,other,negative,command,credits,sources,nonce):
            packet,grant,request,plan,cmd=fixture();mutation(grant)
            with self.subTest(mutation=mutation.__name__),self.assertRaises(ValueError):
                A.check(grant,packet,request_ref=request,plan_ref=plan,command=cmd,now=199)

if __name__=='__main__':unittest.main()
