import copy,os,sys,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import execute as e
class Entry(unittest.TestCase):
    def plan(self):
        pins={str(e.ROOT/'bench/sync'/n):'a'*64 for n in e.worker.SCRIPT_NAMES}
        return dict(schema='unison-concurrent-synthetic-plan/1',workspace='/private/tmp/u-crs-unit-inert',
            parameters=dict(e.PARAMETERS),execution_source_sha256=pins,
            binaries={x:dict(label=x,path='/inert/'+x,sha256='b'*64) for x in ['stock','ox']},
            tool=dict(path=str(e.HERE/'fake_validator.py'),sha256='c'*64,build_id=e.worker.BUILD,threads=1),
            transport_source_sha256={n:'a'*64 for n in e.worker.SCRIPT_NAMES},
            interpreter=dict(path=e.PYTHON,sha256='d'*64))
    def check(self,plan):
        with patch.object(e,'read_manifest',return_value=plan),patch.object(e,'sources',return_value=self.plan()['execution_source_sha256']),patch.object(e,'artifact_sha',return_value='c'*64):
            return e.checked_plan('/private/tmp/inert-plan.json','a'*64)
    def test_exact_synthetic_plan(self):self.assertEqual(self.check(self.plan()),self.plan())
    def test_no_external_source_or_sdk_mode(self):
        for key,value in [('source',{}),('tool',dict(path='/sdk',sha256='c'*64,build_id='sdk',threads=1))]:
            plan=self.plan();plan[key]=value
            with self.assertRaises(ValueError):self.check(plan)
    def test_types_and_source_closure(self):
        for mutate in ['credits','threads','source','interpreter']:
            plan=self.plan()
            if mutate=='credits':plan['parameters']['cpu_credits']=True
            elif mutate=='threads':plan['tool']['threads']=True
            elif mutate=='source':plan['execution_source_sha256']={}
            else:plan['interpreter']['sha256']='bad'
            with self.assertRaises(ValueError):self.check(plan)
    def test_exact_nine_argument_child(self):
        argv=e.child_argv('/private/tmp/p.json','a'*64,'/private/tmp/u-crs-unit-inert')
        self.assertEqual(len(argv),9);self.assertEqual(argv[2:4],['--worker','--plan'])
    def start(self,args,plan):
        return dict(owner_pid=os.getppid(),child_pid=os.getpid(),target=e.TARGET,
            command=e.child_argv(args.plan,args.plan_sha256,args.workspace),cpu_credits=8,
            token_indexes=list(range(8)),io_mode='EX_GLOBAL',
            inherited_resource_fds=[dict(fd=100+i,device=1,inode=10+i) for i in range(9)])
    def worker_call(self,start,plan,args):
        with patch.object(e,'read_manifest',return_value=start),patch.object(e,'artifact_sha',return_value=plan['interpreter']['sha256']), \
             patch.object(e.os,'fstat',side_effect=lambda fd:SimpleNamespace(st_dev=1,st_ino=fd-90)), \
             patch.object(e.worker,'execute',return_value={}) as run:
            value=e.worker_entry(args,plan)
        return value,run
    def test_worker_actual_parent_and_inherited_bundle_before_kernel(self):
        plan=self.plan();args=SimpleNamespace(workspace=plan['workspace'],plan='/private/tmp/p.json',plan_sha256='a'*64)
        value,run=self.worker_call(self.start(args,plan),plan,args)
        self.assertEqual(value,0);run.assert_called_once()
    def test_wrong_parent_or_missing_fd_refuses_kernel(self):
        plan=self.plan();args=SimpleNamespace(workspace=plan['workspace'],plan='/private/tmp/p.json',plan_sha256='a'*64)
        for mutate in ['parent','fds','identity']:
            start=self.start(args,plan)
            if mutate=='parent':start['owner_pid']+=1
            elif mutate=='fds':start['inherited_resource_fds'].pop()
            else:start['inherited_resource_fds'][0]['inode']+=1
            with self.assertRaises(ValueError):self.worker_call(start,plan,args)
if __name__=='__main__':unittest.main()
