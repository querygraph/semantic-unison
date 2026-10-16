"""Pure contract controls; no private source or canonical IO accessed."""
import copy
import unittest
from private_maker_plan import check,worker_argv,IDENTITY,GEOMETRY,SOURCE,TARGET


def fixture():
    return dict(schema='unison-private-maker-slice-plan/1',target=TARGET,
        workspace='/private/tmp/unison-private-maker-slice-'+'a'*32,
        source=dict(path=SOURCE,identity=dict(IDENTITY)),geometry=dict(GEOMETRY),
        worker_seconds=10,cpu_credits=8,io_mode='EX_GLOBAL',semantic_eligibility=False,
        sdk_validation=False,source_hash_requested=False,pointed_values_requested=False)


class Plan(unittest.TestCase):
    def test_exact_launch(self):
        plan=fixture();self.assertIs(check(plan),plan)
        argv=worker_argv(plan,interpreter='/python',plan_path='/plan',plan_sha256='b'*64)
        self.assertEqual(argv[2:],['--worker','--plan','/plan','--plan-sha256','b'*64,
                                  '--workspace',plan['workspace']])
    def test_no_scope_growth_or_alias(self):
        for key,value in [('cpu_credits',True),('cpu_credits',18),('worker_seconds',11),
                          ('io_mode','NONE'),('sdk_validation',True),
                          ('semantic_eligibility',0),('source_hash_requested',True),
                          ('pointed_values_requested',True),('workspace','/tmp/other')]:
            plan=fixture();plan[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):check(plan)
    def test_every_source_and_geometry_field_bound(self):
        for section in ('identity','geometry'):
            original=IDENTITY if section=='identity' else GEOMETRY
            for key,n in original.items():
                plan=fixture();target=plan['source']['identity'] if section=='identity' else plan['geometry']
                target[key]=n+1 if type(n) is int else 'big'
                with self.subTest(section=section,key=key),self.assertRaises(ValueError):check(plan)
        plan=fixture();plan['source']['path']='/Photo/original.DNG'
        with self.assertRaises(ValueError):check(plan)
    def test_unknown_fields_and_bad_argv_refuse(self):
        plan=fixture();plan['extra']=False
        with self.assertRaises(ValueError):check(plan)
        for changes in (dict(interpreter='python'),dict(plan_path='/a/../b'),dict(plan_sha256='Z'*64)):
            args=dict(interpreter='/python',plan_path='/plan',plan_sha256='b'*64);args.update(changes)
            with self.assertRaises(ValueError):worker_argv(fixture(),**args)


if __name__=='__main__':unittest.main()
