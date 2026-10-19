"""Original saved-only aggregation vectors; fabricated timings are never measurements."""
import copy
import hashlib
import json
import tempfile
from unittest.mock import patch
import unittest
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'bench/sync'))
import auto_cohort as A
from auto_cohort_test import receipt
from cohort_plan_test import fixture
import cohort_report as R


def record(label,selection):
    plan=fixture(selection);plan['cohort']=A.contract(label,selection)
    result=receipt(selection);c=plan['cohort'];artifact=plan['artifact']
    root='/private/tmp/unison-sync-bench-fabricated-'+label+'-'+str(selection)
    result.update(parameters=A.parameters(c),temporary_directory=root,host={'system':'Darwin'},
        binaries={label:{}},compilers={label:{'path':artifact['compiler']}},
        admitted_binary_sha256={label:artifact['binary_sha256']},
        admitted_compiler_sha256={label:artifact['compiler_sha256']})
    for i,row in enumerate(result['samples']):
        row['label']=label
        row['counters']['semantic_logical_write_bytes']=0
        row['counters']['materialization_non_inherited_logical_bytes_model']=11
        directory=root+'/'+str(i)
        for offset,(stage,field) in enumerate(A.STAGES):
            entry=result['invocations'][i*3+offset];entry['identity'].update(label=label,directory=directory)
            flags=['-debug','copy','-debug','semantic','-debug','semantic-reads','-debug','semantic-timings',
                   '-clone','off' if row['mode']=='ordinary' else 'auto','-semanticworkers',
                   '0' if selection=='auto' else str(selection),'-semanticcpubudget','8','-maxthreads',
                   str(max(2,8 if selection=='auto' else selection))]
            if row['mode']=='semantic':flags+=['-semanticdng']
            command=[artifact['binary'],directory+'/left','ssh://localhost/'+directory+'/right',
                '-sshcmd',root+'/launcher.py','-servercmd',artifact['binary'],
                '-batch','-auto','-fastcheck','false','-times',*flags]
            run=row[field];run['command']=command
            run['proxy']['server_command']=[artifact['binary'],'-server','__new-rpc-mode',*flags]
            run['proxy']['forwarded_protocol_bytes']={'client_to_server_bytes':2,'server_to_client_bytes':7}
            run['wall_seconds']=1000 if row['phase']=='warmup' else row['repetition']/(1 if selection==1 else 2)
            entry['command']=copy.deepcopy(command);entry['outcome']=copy.deepcopy(run)
    return dict(plan=plan,result=result)


class Report(unittest.TestCase):
    def test_full_typed_matrix_all_samples_and_unknowns(self):
        records=[record(label,s) for s in A.SELECTORS for label in ('stock','ox')]
        before=copy.deepcopy(records);report=R.summarize(records)
        self.assertTrue(report['matrix_complete']);self.assertEqual(report['missing_cohorts'],[])
        self.assertEqual((len(report['groups']),report['raw_samples_retained']),(30,180))
        for g in report['groups']:
            self.assertEqual(g['update_wall_seconds']['samples'],[1,2,3,4,5] if g['selection']==1 else [.5,1,1.5,2,2.5])
            self.assertIsNone(g['application_read_bytes']['median'])
            self.assertIsNone(g['physical_storage_write_bytes']['median'])
            self.assertEqual(g['returned_semantic_write_bytes']['median'],0)
            self.assertEqual(g['non_inherited_extent_model_bytes']['median'],11)
            self.assertEqual(g['client_to_server_bytes']['median'],2)
            self.assertEqual(g['server_to_client_bytes']['median'],7)
            self.assertEqual(g['descriptive_one_worker_wall_ratio'],1 if g['selection']==1 else 2)
        self.assertFalse(report['resource_release_authorized']);self.assertEqual(records,before)

    def test_partial_matrix_not_promoted_and_failed_prefix_retained(self):
        v=record('stock',1);v['result']['complete']=False;v['result']['failure']='original failure'
        v['result']['invocations']=v['result']['invocations'][:1]
        v['result']['samples']=v['result']['samples'][:1]
        report=R.summarize([v])
        self.assertFalse(report['matrix_complete']);self.assertEqual(len(report['missing_cohorts']),9)
        self.assertEqual(report['cohorts'][0]['functional_status'],'FAILED_PREFIX')
        self.assertEqual(report['cohorts'][0]['failure'],'original failure')
        self.assertEqual(report['cohorts'][0]['raw_sample_indexes'],[0]);self.assertEqual(report['groups'],[])

    def test_unknown_or_duplicate_refuses(self):
        value=record('stock','auto')
        with self.assertRaises(ValueError):R.summarize([value,value])
        value['result']['invocations'][0]['state']='INTENT'
        with self.assertRaises(ValueError):R.summarize([value])

    def test_saved_manifest_roundtrip_and_hash_refusal(self):
        with tempfile.TemporaryDirectory(prefix='cohort-report-metadata-') as temporary:
            folder=Path(temporary).resolve();entry=record('stock',1);paths={}
            for kind in ('plan','result'):
                path=folder/(kind+'.json');data=json.dumps(entry[kind]).encode();path.write_bytes(data)
                paths[kind]=dict(path=str(path),sha256=hashlib.sha256(data).hexdigest())
            manifest=folder/'manifest.json'
            raw=json.dumps(dict(schema='unison-auto-cohort-report-input/1',records=[paths])).encode()
            manifest.write_bytes(raw);output=folder/'report.json'
            argv=['cohort_report.py','--manifest',str(manifest),'--manifest-sha256',
                  hashlib.sha256(raw).hexdigest(),'--output',str(output)]
            with patch.object(sys,'argv',argv):R.main()
            report=json.loads(output.read_text())
            self.assertEqual(report['raw_samples_retained'],18)
            self.assertEqual(report['state'],'INCOMPLETE_MATRIX')
            self.assertEqual(len(report['saved_inputs']),2)
            output.unlink();(folder/'result.json').write_text('{}')
            with patch.object(sys,'argv',argv),self.assertRaises(ValueError):R.main()
            self.assertFalse(output.exists())

    def test_no_baseline_or_zero_denominator_invents_no_ratio(self):
        value=record('stock',2)
        self.assertTrue(all(g['descriptive_one_worker_wall_ratio'] is None for g in R.summarize([value])['groups']))
        value=record('stock',1)
        for i,row in enumerate(value['result']['samples']):
            row['update_sync']['wall_seconds']=0
            value['result']['invocations'][i*3+1]['outcome']=copy.deepcopy(row['update_sync'])
        self.assertTrue(all(g['descriptive_one_worker_wall_ratio'] is None for g in R.summarize([value])['groups']))


if __name__=='__main__':unittest.main()
