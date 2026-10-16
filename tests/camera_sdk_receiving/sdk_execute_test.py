"""Pure plan and pre-payload entry refusals; no camera/native/lock acquisition."""
import copy
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import sdk_execute as execute


class Controls(unittest.TestCase):
    def plan(self):
        return {'schema':'unison-camera-sdk-receiving-plan/1','parameters':dict(execute.PARAMETERS),
                'execution_source_sha256':{},'workspace':'/private/tmp/u-cs-fixed-case',
                'source':{'path':str(execute.SOURCE),
                    'historical_sha256':'1a4f578ee6f23730afec8495c90b37f5272042331f3375d332a9065ce5bb3ee2',
                    'identity':dict(st_size=193851848,st_dev=1,st_ino=2,st_mtime_ns=3,st_ctime_ns=4,
                                   st_mode=0o100400,st_nlink=1,st_uid=os.getuid())},
                'tool':{'path':'/private/tmp/unison-adobe-driver-build/unison-adobe-validator',
                        'sha256':'ca49a32bd5980b5cb16e10421d2d7a41542698a49f03a5b50007ff234b432b4a',
                        'build_id':'unison-sdk171-2724-v1-single','threads':1},
                'binaries':{label:{'label':label,'path':'/inert/'+label,'sha256':'0'*64}
                            for label in ('stock','ox')}}
    def check(self,value):
        with patch.object(execute,'read_manifest',return_value=value),patch.object(execute,'sources',return_value={}):
            return execute.checked_plan('/private/tmp/unused-plan.json','0'*64)
    def test_exact_scope_accepts_metadata_only(self):
        self.assertEqual(self.check(self.plan())['parameters']['calls'],2)
    def test_scope_and_ancestry_mutations_refused(self):
        mutations=[lambda p:p['parameters'].update(calls=7),
                   lambda p:p['parameters'].update(io_budget_enforced=0),
                   lambda p:p.update(execution_source_sha256={'wrong':'pin'}),
                   lambda p:p['source'].update(path='/Photo/original.DNG'),
                   lambda p:p['source']['identity'].update(st_mode=0o100600),
                   lambda p:p['source']['identity'].update(st_nlink=True),
                   lambda p:p.update(workspace='/Users/not-private'),
                   lambda p:p['binaries'].pop('ox'),
                   lambda p:p['tool'].update(threads=6),
                   lambda p:p['tool'].update(build_id='experimental'),
                   lambda p:p['tool'].update(sha256='b'*64)]
        for mutate in mutations:
            value=self.plan();mutate(value)
            with self.assertRaises(ValueError):self.check(value)
    def test_no_cpu_only_camera_route(self):
        import shared_dispatch
        with patch.object(shared_dispatch.Pool,'read') as pool,self.assertRaises(ValueError):
            shared_dispatch.run('camera-sdk-receive',execute.child_argv('/plan','0'*64,'/workspace'),
                                Path('/uncreated'),8)
        pool.assert_not_called()
    def test_worker_parent_binding_refusal_before_payload(self):
        with tempfile.TemporaryDirectory() as name:
            plan=self.plan();plan['workspace']=name
            args=SimpleNamespace(workspace=name,plan='/plan',plan_sha256='0'*64)
            with patch.object(execute,'stable_sha',return_value='0'*64), \
                 patch.object(execute,'read_manifest',return_value={'owner_pid':-1}), \
                 patch.object(execute.worker,'execute') as payload:
                with self.assertRaises(ValueError):execute.worker_entry(args,plan)
            payload.assert_not_called()

    def test_combined_uncertainty_enters_retention_not_failed_result(self):
        from close import UnresolvedIOOwnership, descriptor_observation
        class RetentionObserved(BaseException):
            pass
        with tempfile.TemporaryDirectory() as name:
            plan=self.plan();plan['workspace']=name
            args=SimpleNamespace(workspace=name,plan='/plan',plan_sha256='0'*64)
            fds=[os.open('/dev/null',os.O_RDONLY) for _ in range(9)]
            try:
                start={'owner_pid':os.getppid(),'child_pid':os.getpid(),
                       'target':'camera-sdk-receive','cpu_credits':8,'io_mode':'EX_GLOBAL',
                       'token_indexes':list(range(8)),
                       'command':execute.child_argv(args.plan,args.plan_sha256,name),
                       'inherited_resource_fds':[{'fd':fd,'device':os.fstat(fd).st_dev,
                                                  'inode':os.fstat(fd).st_ino} for fd in fds]}
                records=[descriptor_observation(fd,'original_disposable_fixture') for fd in fds[:2]]
                original=ValueError('original refusal')
                carrier=UnresolvedIOOwnership('two uncertain fixture closes',
                    retained_fds=[fds[2]],uncertain_closes=records,original_failure=original,
                    close_failure=OSError('injected uncertain close'))
                def retain(record):
                    record()
                    raise RetentionObserved()
                with patch.object(execute,'stable_sha',return_value='0'*64), \
                     patch.object(execute,'read_manifest',return_value=start), \
                     patch.object(execute.worker,'execute',side_effect=carrier) as payload, \
                     patch.object(execute,'retain_after_record',side_effect=retain) as retention:
                    with self.assertRaises(RetentionObserved):
                        execute.worker_entry(args,plan)
                import json
                saved=json.loads((Path(name)/'WORKER-OWNERSHIP-RETAINED.json').read_text())
                self.assertEqual(saved['uncertain_closes'],records)
                self.assertIsNone(saved['uncertain_fd'])
                self.assertEqual(saved['retained_fds'],[fds[2]])
                self.assertIn('original refusal',saved['original_failure'])
                self.assertFalse((Path(name)/'RESULT.json').exists())
                payload.assert_called_once();retention.assert_called_once()
            finally:
                for fd in fds:
                    os.close(fd)  # no actual close fault or real resources in this fixture


if __name__=='__main__':unittest.main()
