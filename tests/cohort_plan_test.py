"""Original fixed metadata mutations; no file reads or process dispatch."""
import copy
import hashlib
import json
import tempfile
from unittest.mock import patch
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'bench/sync'))
import auto_cohort as cohort
import cohort_plan


def fixture(selection):
    c=cohort.contract('stock',selection)
    p=dict(schema=cohort_plan.SCHEMA,workspace='/private/tmp/unison-auto-cohort-'+'a'*32,
           interpreter='/qualified/python',interpreter_sha256='b'*64,script='/repo/bench/sync/run.py',
           cohort=c,artifact=dict(binary='/build/unison',compiler='/switch/ocamlopt',
                                 binary_sha256='c'*64,compiler_sha256='d'*64),
           execution_sha256={'bench/sync/run.py':'e'*64},prerequisite_sha256={'/proof/build.json':'f'*64},
           limits=copy.deepcopy(cohort_plan.LIMITS),cpu_token_indexes=list(range(c['reserved_credits'])),
           requires_temporary_borrow=c['reserved_credits']==18)
    p['launch_argv']=cohort.launch_argv(c,interpreter=p['interpreter'],script=p['script'],
                                      output=p['workspace']+'/RESULT.json',artifact=p['artifact'])
    return p


class Plan(unittest.TestCase):
    def test_all_source_cohorts(self):
        for selection in cohort.SELECTORS:
            p=fixture(selection); before=copy.deepcopy(p)
            self.assertEqual(cohort_plan.validate(p,execution_sources=['bench/sync/run.py']),before)
            self.assertEqual(p,before)

    def test_metadata_and_artifact_authentication(self):
        with tempfile.TemporaryDirectory(prefix='cohort-metadata-') as temporary:
            root=Path(temporary).resolve()
            (root/'bench/sync').mkdir(parents=True)
            source=root/'bench/sync/run.py';source.write_bytes(b'original generated metadata fixture')
            proof=root/'proof.json';proof.write_bytes(b'original prerequisite fixture')
            p=fixture(1);p['script']=str(source)
            p['execution_sha256']={'bench/sync/run.py':hashlib.sha256(source.read_bytes()).hexdigest()}
            p['prerequisite_sha256']={str(proof):hashlib.sha256(proof.read_bytes()).hexdigest()}
            for key in ('binary','compiler'):
                f=root/key;f.write_bytes(('generated '+key).encode())
                p['artifact'][key]=str(f)
                p['artifact'][key+'_sha256']=hashlib.sha256(f.read_bytes()).hexdigest()
            interpreter=root/'python';interpreter.write_bytes(b'generated inert interpreter fixture')
            p['interpreter']=str(interpreter);p['interpreter_sha256']=hashlib.sha256(interpreter.read_bytes()).hexdigest()
            p['launch_argv']=cohort.launch_argv(p['cohort'],interpreter=p['interpreter'],script=p['script'],
                output=p['workspace']+'/RESULT.json',artifact=p['artifact'])
            f=root/'plan.json';raw=json.dumps(p).encode();f.write_bytes(raw)
            h=hashlib.sha256(raw).hexdigest()
            self.assertEqual(cohort_plan.checked_metadata(str(f),h,repository=root,
                execution_sources=['bench/sync/run.py']),p)
            self.assertEqual(len(cohort_plan.verify_artifacts(p)),3)
            source.write_bytes(b'changed')
            with self.assertRaises(ValueError):cohort_plan.checked_metadata(str(f),h,repository=root,
                execution_sources=['bench/sync/run.py'])
            (root/'binary').write_bytes(b'changed artifact')
            with self.assertRaises(ValueError):cohort_plan.verify_artifacts(p)

    def test_uncertainty_propagates_without_retry(self):
        from shared_io_pool import UnresolvedIOOwnership
        error=UnresolvedIOOwnership('injected qualified uncertainty',retained_fds=(900,),
            uncertain_closes=({'fd':901,'observed_before_close':{'inode':123}},),
            original_failure=ValueError('original refusal'))
        with patch('cached_benchmark.contract.read_bytes',side_effect=error) as reader:
            with self.assertRaises(UnresolvedIOOwnership) as caught:
                cohort_plan.verify_artifacts(fixture(1))
            self.assertIs(caught.exception,error)
            self.assertEqual(reader.call_count,1)
            self.assertEqual(error.uncertain_fds,(901,))
            self.assertEqual(error.retained_fds,(900,))

    def test_refusals(self):
        for mutation in ('extra','traversal','borrow','tokens','limit','pin','inventory','argv','prereq','bool'):
            p=fixture('auto')
            if mutation=='extra':p['admitted']=True
            if mutation=='traversal':p['workspace']='/private/tmp/../tmp/unison-auto-cohort-'+'a'*32
            if mutation=='borrow':p['requires_temporary_borrow']=False
            if mutation=='tokens':p['cpu_token_indexes']=list(range(8))
            if mutation=='limit':p['limits']['owner_observation_seconds']=1800
            if mutation=='pin':p['execution_sha256']['bench/sync/run.py']='G'*64
            if mutation=='inventory':p['execution_sha256']['other.py']='e'*64
            if mutation=='argv':p['launch_argv']+=['--prepare-only']
            if mutation=='prereq':p['prerequisite_sha256']={}
            if mutation=='bool':p['cpu_token_indexes'][1]=True
            with self.subTest(mutation=mutation),self.assertRaises(ValueError):
                cohort_plan.validate(p,execution_sources=['bench/sync/run.py'])

if __name__=='__main__':unittest.main()
