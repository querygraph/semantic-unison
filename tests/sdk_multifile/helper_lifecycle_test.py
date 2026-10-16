"""Actual original Python helpers inside modeled CLI transport; zero SDK calls."""
import copy
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'tests'),str(ROOT/'tests/sdk_host_matrix'),str(ROOT/'tests/camera_sdk_concurrency')]
from sdk_multifile import worker
from sdk_multifile.plan import plan as command_plan,BUILD
from invocation import SCRIPT_NAMES
from combined_test import frame
from shared_child import invoke


class Helpers(unittest.TestCase):
    def test_actual_helpers_close_before_modeled_cli_outcome_and_parent_audit(self):
        root=Path(tempfile.mkdtemp(prefix='u-smr-helpers-',dir='/private/tmp'));root.chmod(0o700)
        data={'uncompressed.dng':b'original tiny uncompressed fixture', 'jpeg.dng':b'original distinct tiny jpeg fixture'}
        sources=[dict(candidate_id=n,sha256=hashlib.sha256(v).hexdigest(),bytes=len(v)) for n,v in data.items()]
        p=dict(workspace=str(root),sources=sources,tool=dict(path='/inert/sdk',sha256='a'*64,threads=1,build_id=BUILD),
               binaries={n:dict(label=n,path='/inert/'+n,sha256='a'*64) for n in ('stock','ox')},transport_source_sha256={n:'a'*64 for n in SCRIPT_NAMES})
        raw={};outcomes=[];saved=[]
        def prepare(d,label):
            for name,value in data.items():(d/'left'/name).write_bytes(value)
            return dict(original_tiny_files=True,native_clone_proved=False)
        class Invoke:
            def __init__(self,directory,*,binary,tool,journal,**kw):self.d=Path(directory);self.binary=binary;self.journal=journal
            def __call__(self):
                argv=command_plan(self.binary,p['tool'],self.d)['command']
                self.journal.begin(dict(label=self.binary['label'],mode='semantic',workers=3,directory=str(self.d),stage='seed'),argv)
                log=''
                for source in sources:
                    path=self.d/'left'/source['candidate_id']
                    out=invoke([sys.executable,'-B','-c',
                        'import hashlib,sys; print(hashlib.sha256(open(sys.argv[1],"rb").read()).hexdigest())',str(path)],
                        dict(os.environ,PYTHONDONTWRITEBYTECODE='1'),time.monotonic()+10)
                    proof=out['client_cleanup']
                    assert out['returncode']==0 and not out['timed_out'] and not out['capture_truncated']
                    assert proof['reaped'] and proof['other_group_members_absent_before_reap'] and out['stdout'].strip()==source['sha256']
                    outcomes.append(out)
                    # SDK protocol is explicitly synthetic; PID/group status below
                    # bind actual children. Omit live diagnostics: no overlap claim.
                    log+='\n'.join(line for line in frame(proof['pid'],source['sha256'],source['bytes'],1,2).splitlines()
                                   if 'validation-live' not in line)+'\n'
                for name,value in data.items():(self.d/'right'/name).write_bytes(value)
                owner=dict(pid=900001,returncode=0,reaped=True,group_cleanup_before_leader_reap=True,other_group_members_absent_before_reap=True)
                proxy=dict(schema='unison-loopback-protocol-count/1',server_pid=9,server_returncode=0,server_command=[argv[0],'-server'],
                           server_cleanup=dict(owner,pid=9),input_pump_joined=True,pump_errors=[])
                out=dict(command=argv,returncode=0,timed_out=False,capture_truncated=False,supervisor_capture_truncated=False,
                         client_cleanup=owner,supervisor_cleanup=dict(owner,pid=900002),stdout=log,stderr='',supervisor_output='',proxy=proxy)
                raw[str(self.d/'seed-proxy.json')]=copy.deepcopy(proxy);self.journal.finish(out);return out
        with patch.object(worker,'prepare_scripts',return_value=p['transport_source_sha256']),patch.object(worker,'Invoker',Invoke):
            result=worker.execute(p,root,time.monotonic()+60,prepare_sources=prepare,read_proxy=lambda path:raw[str(path)],persist=lambda v:saved.append(copy.deepcopy(v)))
        self.assertTrue(result['complete']);self.assertEqual(result['parent_audit']['sdk_helpers_settled'],4)
        self.assertEqual(len({o['client_cleanup']['pid'] for o in outcomes}),4)
        for case in result['cases']:
            self.assertIsNone(case['case']['validation']['known_live_overlap_observed'])
        self.assertFalse(result['parent_audit']['resource_release_authorized'])
        receipt=dict(result=result,actual_original_helper_outcomes=outcomes,
                     scope='Four actual original Python hash children/group proofs in modeled two-CLI worker composition. Synthetic SDK protocol, inert CLI/server PIDs. Zero SDK/native/retained payload/canonical IO; not real transport qualification.')
        (root/'CONTROL-RESULT.json').write_text(json.dumps(receipt,indent=2)+'\n')
        print(json.dumps(dict(workspace=str(root),actual_original_helpers=4,sdk_calls=0)),flush=True)


if __name__=='__main__':
    from shared_cpu_pool import UnresolvedOwnership
    from shared_process_owner import retain_after_record
    try:Helpers().test_actual_helpers_close_before_modeled_cli_outcome_and_parent_audit()
    except UnresolvedOwnership as error:
        retain_after_record(lambda:print(repr(error),flush=True))
