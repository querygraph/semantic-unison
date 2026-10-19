"""Original fixed metadata mutations; no file reads or process dispatch."""
import copy
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
