"""Directed fabricated-proof controls; no transport, binaries or payload."""
import copy
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'bench/sync'))
import auto_cohort
import invocation_journal
from timed_shared_test import fixture


def receipt(selection):
    value = fixture()
    value['samples'] = [row for row in value['samples'] if row['label'] == 'stock' and row['workers'] == 1]
    value['invocations'] = [entry for entry in value['invocations']
                            if entry['identity']['label'] == 'stock' and entry['identity']['workers'] == 1]
    for row in value['samples']:
        row['workers'] = selection
    for index, entry in enumerate(value['invocations']):
        entry['index'] = index
        entry['identity']['workers'] = selection
    return value


class Cohort(unittest.TestCase):
    def test_all_selectors_and_reservations(self):
        for selection, peak, reserved in ((1,4,8),(2,6,8),(4,10,18),(8,18,18),('auto',18,18)):
            cohort = auto_cohort.contract('stock', selection)
            self.assertEqual((cohort['declared_peak_credits'],cohort['reserved_credits']), (peak,reserved))
            value = receipt(selection); before = copy.deepcopy(value)
            proof = auto_cohort.audit(value, cohort)
            self.assertEqual(proof['cli_invocations'],54)
            self.assertFalse(proof['token_release_authorized'])
            self.assertEqual(value,before)

    def test_typed_selection_and_contract(self):
        for selection in (True, 1.0, '8', 3, 18, None):
            with self.subTest(selection=selection), self.assertRaises(ValueError):
                auto_cohort.contract('stock',selection)
        cohort=auto_cohort.contract('stock','auto'); cohort['reserved_credits']=8
        with self.assertRaises(ValueError):auto_cohort.audit(receipt('auto'),cohort)

    def test_directed_proof_corruptions(self):
        for mutation in ('intent','group','cross','row','missing','boolean','exit','pump','binding'):
            value=receipt('auto'); run=value['invocations'][0]['outcome']
            if mutation=='intent':value['invocations'][0]['state']='INTENT'
            if mutation=='group':run['client_cleanup']['other_group_members_absent_before_reap']=False
            if mutation=='cross':value['invocations'][0]['identity']['workers']=8
            if mutation=='row':value['samples'][0]['workers']=8
            if mutation=='missing':value['samples'].pop()
            if mutation=='boolean':value['samples'][0]['repetition']=True
            if mutation=='exit':run['returncode']=1
            if mutation=='pump':run['proxy']['input_pump_joined']=False
            if mutation=='binding':value['samples'][0]['seed_sync']['command']=['changed']
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                auto_cohort.audit(value,auto_cohort.contract('stock','auto'))

    def test_exact_launch_and_bound_result(self):
        artifact=dict(binary='/fabricated/unison',compiler='/fabricated/ocamlopt',
                      binary_sha256='a'*64,compiler_sha256='b'*64)
        bindings=dict(interpreter='/fake/python',script='/fake/run.py',output='/fake/RESULT.json',artifact=artifact)
        cohort=auto_cohort.contract('stock','auto')
        argv=auto_cohort.launch_argv(cohort,**bindings)
        auto_cohort.check_launch(argv,cohort,**bindings)
        for extra in (['--workers','8'],['--prepare-only'],['--timeout','300']):
            with self.assertRaises(ValueError):auto_cohort.check_launch(argv+extra,cohort,**bindings)
        value=receipt('auto');value['parameters']=auto_cohort.parameters(cohort)
        value['binaries']={'stock':{}};value['compilers']={'stock':{'path':artifact['compiler']}}
        value['admitted_binary_sha256']={'stock':artifact['binary_sha256']}
        value['admitted_compiler_sha256']={'stock':artifact['compiler_sha256']}
        for index,entry in enumerate(value['invocations']):
            mode=entry['identity']['mode']
            flags=['-debug','copy','-debug','semantic','-debug','semantic-reads',
                   '-debug','semantic-timings','-clone','off' if mode=='ordinary' else 'auto',
                   '-semanticworkers','0','-semanticcpubudget','8','-maxthreads','8']
            if mode=='semantic':flags+=['-semanticdng']
            command=['/fabricated/unison',entry['identity']['directory'],*flags]
            entry['command']=command;entry['outcome']['command']=command
            row=value['samples'][index//3]
            row[auto_cohort.STAGES[index%3][1]]=copy.deepcopy(entry['outcome'])
        auto_cohort.audit_bound(value,cohort,artifact)
        for mutation in ('budget','hash','flags'):
            broken=copy.deepcopy(value)
            if mutation=='budget':broken['parameters']['loopback_cpu_credit_bound']=8
            if mutation=='hash':broken['admitted_binary_sha256']['stock']='c'*64
            if mutation=='flags':broken['invocations'][0]['command'][-1]='2'
            with self.subTest(mutation=mutation),self.assertRaises(ValueError):
                auto_cohort.audit_bound(broken,cohort,artifact)

    def test_failed_prefix_separate_and_legacy_unchanged(self):
        value=receipt(8); value['complete']=False; value['invocations']=value['invocations'][:1]
        self.assertEqual(auto_cohort.audit_attempted(value,auto_cohort.contract('stock',8))['attempted_cli_invocations'],1)
        with self.assertRaises(ValueError):auto_cohort.audit(value,auto_cohort.contract('stock',8))
        with self.assertRaises(ValueError):invocation_journal.audit_attempted(value)

if __name__=='__main__':unittest.main()
