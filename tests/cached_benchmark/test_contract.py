"""Original numeric/ownership-boundary controls; no pools, fixture IO or SDK."""
import copy
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from cached_benchmark import contract as C
from shared_cpu_pool import UnresolvedOwnership
from sdk_host_matrix import shared_binding as B


def plan():
    p = dict(schema='unison-cached-benchmark-plan/1',
             workspace='/private/tmp/unison-cached-sha-original-control', limits=copy.deepcopy(C.LIMITS),
             builds=[dict(label=label, compiler=C.COMPILERS[label],
                          src='/private/tmp/unison-build-'+label+'/src', receipt='/private/tmp/unison-'+label+'/RESULT.json')
                     for label in ('stock','ox')],
             source_sha256={name: 'a'*64 for name in C.sources()}, artifact_sha256={})
    p['artifact_sha256'] = {name: 'b'*64 for name in C.artifact_paths(p)}
    p['artifact_sha256'][C.PYTHON] = C.PYTHON_SHA
    return p


def result(p):
    samples = []
    for phase, repetition, label, workers in C.schedule():
        raw = dict(wall_seconds=1., process_cpu_seconds=float(workers), correct_digests=6,
                   peak_active_workers=workers, final_cpu_permits=0,
                   process_lifetime_peak_rss_bytes=4096., observed_fd_count_peak=20,
                   baseline_fd_count=12, final_fd_count=12,primary_logical_read_bytes=192*1048576,
                   primary_read_chunks=3072,primary_read_observations=6)
        samples.append(dict(raw, raw_stdout=json.dumps(raw), phase=phase, repetition=repetition,
                            compiler=label, workers=workers, throughput_mib_per_second=192.,
                            effective_cpu_cores=float(workers)))
    return dict(complete=True, samples=samples, source_sha256={k:p['source_sha256'][k]
        for k in C.benchmark_sources()}, runner_sha256=p['source_sha256']['bench/semantic/run.py'],
        inherited_resource_fds=[], parameters=dict(file_mib=32, jobs=6, workers=[1,2,4,6],
        warmups_per_configuration=1, measured_repetitions=5))


class Contract(unittest.TestCase):
    def test_finite_shape(self):
        p=plan();self.assertIs(C.validate(p),p)
        a=C.benchmark_argv(p,list(range(10,19)))
        self.assertEqual(a[a.index('--workers')+1],'1,2,4,6')
        self.assertEqual(a[a.index('--inherited-resource-fds')+1],','.join(map(str,range(10,19))))
        for n in (0,8,10):
            with self.assertRaises(ValueError):C.benchmark_argv(p,list(range(10,10+n)))

    def test_exact_source_and_artifact_sets(self):
        for field in ('source_sha256','artifact_sha256'):
            p=plan();p[field].pop(next(iter(p[field])))
            with self.assertRaises(ValueError):C.validate(p)

    def test_limits_and_workspace_are_not_caller_expandable(self):
        for change in (lambda p:p['limits'].update(cpu_credits=18),
                       lambda p:p['limits']['workers'].__setitem__(0,True),
                       lambda p:p.update(workspace='/private/tmp/elsewhere'),
                       lambda p:p['builds'][0].update(compiler='/private/tmp/source.DNG'),
                       lambda p:p['builds'][0].update(src='/Users/alexy/Pictures/src')):
            p=plan();change(p)
            with self.assertRaises(ValueError):C.validate(p)

    def test_raw_schedule_and_derived_values(self):
        p=plan();v=result(p);proof=C.audit(v,p,[])
        self.assertEqual(proof['completed_native_batches'],48)
        self.assertFalse(proof['resource_release_authorized'])
        self.assertFalse(proof['quiet_timing'])
        for change in (lambda r:r['samples'].pop(),
                       lambda r:r['samples'][0].update(workers=6),
                       lambda r:r['samples'][0].update(throughput_mib_per_second=193.),
                       lambda r:r['samples'][0].update(final_fd_count=13),
                       lambda r:r.update(inherited_resource_fds=[{'fd':99}]),
                       lambda r:r.update(complete=1)):
            altered=copy.deepcopy(v);change(altered)
            with self.assertRaises(ValueError):C.audit(altered,p,[])

    def test_nonfinite_and_bool_counters_refuse(self):
        for field,value in [('wall_seconds',float('nan')),('peak_active_workers',True),
                            ('final_cpu_permits',False),('correct_digests',5),
                            ('primary_logical_read_bytes',1),('primary_read_observations',5)]:
            p=plan();v=result(p);row=v['samples'][0];raw=json.loads(row['raw_stdout'])
            raw[field]=value;row[field]=value;row['raw_stdout']=json.dumps(raw)
            with self.assertRaises(ValueError):C.audit(v,p,[])

    def test_partial_is_failed_without_release_authority(self):
        p=plan();v=result(p);v.update(complete=False,samples=v['samples'][:3])
        a=C.audit(v,p,[])
        self.assertEqual(a['functional_status'],'FAILED_PREFIX')
        self.assertFalse(a['resource_release_authorized'])

    def test_close_uncertainty_has_one_attempt_and_original_failure(self):
        for fail_read in (False,True):
            with tempfile.TemporaryDirectory() as tmp:
                path=Path(tmp)/'metadata.json';path.write_bytes(b'{}')
                real_close=os.close;calls=[]
                def close(fd):
                    calls.append(fd);real_close(fd);raise OSError('reported close uncertainty')
                with patch('os.close',side_effect=close):
                    if fail_read:
                        with patch('os.read',side_effect=ValueError('original read failure')):
                            with self.assertRaises(UnresolvedOwnership) as caught:C.read_bytes(path,64)
                    else:
                        with self.assertRaises(UnresolvedOwnership) as caught:C.read_bytes(path,64)
                self.assertEqual(len(calls),1)
                self.assertEqual(len(caught.exception.uncertain_closes),1)
                if fail_read:self.assertIn('original read failure',repr(caught.exception.original_failure))

    def test_cached_target_cannot_enter_cpu_only(self):
        from shared_dispatch import run
        p=plan();argv=C.worker_argv(p,'/private/tmp/plan.json','a'*64)
        with self.assertRaises(ValueError):run(C.TARGET,argv,Path(p['workspace']),8)

    def test_exact_nine_metadata_binding_without_live_pool(self):
        p=plan();argv=C.worker_argv(p,'/private/tmp/plan.json','a'*64)
        identities=tuple((11,100+i) for i in range(9))
        rows=[dict(fd=10+i,device=d,inode=n) for i,(d,n) in enumerate(identities)]
        start=dict(owner_pid=1,child_pid=2,target=C.TARGET,command=argv,cpu_credits=8,
                   token_indexes=list(range(8)),io_mode='EX_GLOBAL',inherited_resource_fds=rows)
        def observe(fd):
            d,n=identities[fd-10]
            return os.stat_result((stat.S_IFREG|0o600,n,d,1,os.getuid(),0,0,0,0,0))
        with patch.object(B,'inventory',return_value=identities):
            proof=B.verify(start,argv,parent_pid=1,worker_pid=2,observe=observe,target=C.TARGET)
            self.assertFalse(proof['lock_ownership_independently_proved'])
            self.assertFalse(proof['resource_release_authorized'])
            for key,value in [('owner_pid',9),('cpu_credits',18),('token_indexes',list(range(8,16)))]:
                changed=copy.deepcopy(start);changed[key]=value
                with self.assertRaises(ValueError):
                    B.verify(changed,argv,parent_pid=1,worker_pid=2,observe=observe,target=C.TARGET)

    def test_parent_rechecks_saved_artifact_and_preserves_failed_prefix(self):
        from cached_benchmark import entry
        with tempfile.TemporaryDirectory(prefix='unison-cached-sha-control-',dir='/private/tmp') as tmp:
            w=Path(tmp);p=plan();p['workspace']=str(w);v=result(p)
            work=w/'unison-sha-bench-original-fake';work.mkdir(mode=0o700)
            v['retained_workspace']=str(work);v['compilers']={}
            for b in p['builds']:
                (work/b['label']).mkdir(mode=0o700);binary=work/b['label']/'hash-bench'
                binary.write_bytes(b'original fake, never executed')
                v['compilers'][b['label']]=dict(actual_production_build=b['src'],
                    linked_object_sha256={k:h for k,h in p['artifact_sha256'].items()
                        if Path(k).is_relative_to(Path(b['src']))},
                    executable_sha256=p['artifact_sha256'][b['compiler']],
                    benchmark_binary_path=str(binary),
                    benchmark_binary_sha256=hashlib.sha256(binary.read_bytes()).hexdigest())
            (w/'SHARED-START.json').write_text(json.dumps(dict(inherited_resource_fds=[])))
            (w/'BENCHMARK-BINDING.json').write_text(json.dumps(dict(parent_pid=1,worker_pid=2,
                                                                 inherited_resource_fds=[])))
            argv=C.worker_argv(p,'/private/tmp/inert-plan','a'*64)
            with patch.object(entry,'checked_plan',return_value=p),patch.object(entry,'verify'):
                a=entry.parent_audit(v,argv,w,parent_pid=1,worker_pid=2)
                self.assertTrue(a['measured_executable_hashes_reverified'])
                self.assertFalse(a['resource_release_authorized'])
                binary.write_bytes(b'changed fake artifact')
                with self.assertRaises(ValueError):entry.parent_audit(v,argv,w,parent_pid=1,worker_pid=2)
                v.update(complete=False,samples=v['samples'][:2])
                (w/'WORKER-FAILURE.json').write_text(json.dumps(dict(error='original failed sample')))
                a=entry.parent_audit(v,argv,w,parent_pid=1,worker_pid=2)
                self.assertEqual(a['functional_status'],'FAILED_PREFIX')
                self.assertTrue(a['group_settlement_still_required'])


if __name__=='__main__':unittest.main()
