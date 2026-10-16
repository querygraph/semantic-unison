"""Exact shared SDK entry metadata guards; all artifacts/fixtures are doubles."""
import copy,os,stat,sys,time,unittest
from types import SimpleNamespace
from unittest.mock import patch
import shared_execute as e
class Entry(unittest.TestCase):
    def fixture(self):
        identity=dict(st_dev=1,st_ino=2,st_mode=stat.S_IFREG|0o400,st_size=10,st_mtime_ns=1,st_ctime_ns=2,st_nlink=1,st_uid=os.getuid())
        p=dict(schema='unison-shared-sdk-host-plan/1',workspace='/private/tmp/u-shm-unit-test',parameters=copy.deepcopy(e.PARAMETERS),execution_source_sha256={},
            tools={k:dict(executable='/private/tmp/inert-'+k,sha256='a'*64,build_id=b,manifest='/private/tmp/inert-'+k+'.json',manifest_sha256='b'*64) for k,b in [('reference',e.REFERENCE),('experimental',e.EXPERIMENTAL)]},
            fixtures=[dict(codec=c,path='/private/tmp/inert-'+c,sha256='c'*64,size=10,identity=dict(identity)) for c in ['uncompressed','jpeg','jxl']],host_memory_bytes=1073741824,
            interpreter=dict(path=e.PYTHON,sha256='56f92de75b49e94ceb314dba0a2ed6175156f6c61739e4827c28beca32948d29'))
        return p
    def check(self,p,observed_mode=None):
        def read(path,h):
            if str(path)=='/private/tmp/inert-plan.json':return p
            item=next(i for i in p['tools'].values() if i['manifest']==str(path))
            return dict(executable=item['executable'],executable_sha256=item['sha256'],build_id=item['build_id'],source_sha256='a'*64,adapter_headers_sha256={'area_scheduler.h':'a'*64})
        identity=self.fixture()['fixtures'][0]['identity']
        if observed_mode is not None:identity['st_mode']=stat.S_IFREG|observed_mode
        with patch.object(e,'read_manifest',side_effect=read),patch.object(e,'sources',return_value={}),patch.object(e,'artifact_sha',return_value='a'*64),patch.object(e.os,'lstat',return_value=SimpleNamespace(**identity)):
            return e.checked_plan('/private/tmp/inert-plan.json','f'*64)
    def test_exact_plan_and_nine_word_worker_command(self):
        p=self.fixture();self.assertEqual(self.check(p),p);self.assertEqual(len(e.child_argv('/inert','a'*64,p['workspace'])),9)
    def test_retained_generated_0644_is_preserved_not_chmodded(self):
        p=self.fixture()
        for f in p['fixtures']:f['identity']['st_mode']=stat.S_IFREG|0o644
        self.assertEqual(self.check(p,observed_mode=0o644),p)
    def test_unaccepted_writable_mode_refuses_even_with_matching_epoch(self):
        p=self.fixture()
        for f in p['fixtures']:f['identity']['st_mode']=stat.S_IFREG|0o600
        with self.assertRaises(ValueError):self.check(p,observed_mode=0o600)
    def test_limits_and_source_snapshot_refused(self):
        for mode in ['cpu','targets','memory','source','extra']:
            p=self.fixture()
            if mode=='cpu':p['parameters']['cpu_credits']=18
            elif mode=='targets':p['parameters']['native_thread_targets']=[True,2,6]
            elif mode=='memory':p['host_memory_bytes']=8*1073741824
            elif mode=='source':p['execution_source_sha256']={'extra':'x'}
            else:p['source_original']='no'
            with self.assertRaises(ValueError):self.check(p)
    def test_fixture_epoch_and_pin_refusal(self):
        for mode in ['mode','size','sha','original']:
            p=self.fixture()
            if mode=='mode':p['fixtures'][0]['identity']['st_mode']=stat.S_IFREG|0o600
            elif mode=='size':p['fixtures'][0]['size']=11
            elif mode=='sha':p['fixtures'][0]['sha256']='bad'
            else:p['fixtures'][0]['path']='/Users/inert-original'
            with self.assertRaises(ValueError):self.check(p)
    def test_dispatcher_has_no_cpu_only_sdk_route(self):
        import shared_dispatch as d
        from pathlib import Path
        with patch.object(d.Pool,'read') as pool:
            with self.assertRaises(ValueError):d.run(e.TARGET,[sys.executable,str(e.HERE/'shared_execute.py')],Path('/private/tmp/inert-output'),8)
            pool.assert_not_called()
    def test_dispatcher_rejects_noncanonical_worker_argv_before_pool(self):
        import shared_dispatch as d
        import shared_io_pool as io
        from pathlib import Path
        argv=[sys.executable,str(e.HERE/'shared_execute.py'),'--worker']
        out=Path('/private/tmp/u-shm-unit-test')
        admission=dict(state='ROOT_ADMITTED_ONE_SHARED_DISPATCH_IO_JOB',target=e.TARGET,command=argv,workspace=str(out),cpu_credits=8,io_manifest_sha256=io.CANONICAL_SHA256,start_deadline_unix=time.time()+60)
        with patch.object(io,'read_manifest',return_value=admission),patch.object(io.GlobalPool,'read') as pool:
            with self.assertRaises(ValueError):d.checked_io_request(dict(path='/inert',sha256='a'*64),e.TARGET,argv,out,8)
            pool.assert_not_called()
if __name__=='__main__':unittest.main()
