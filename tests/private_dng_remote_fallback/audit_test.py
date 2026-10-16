"""Pure fabricated receipt/log controls; no child or payload access."""
from copy import deepcopy
import unittest
from audit import audit, PAIRS


def run():
    owner={'reaped':True,'returncode':0,'cancel_reason':None,
           'group_cleanup_before_leader_reap':True,'other_group_members_absent_before_reap':True}
    return {'returncode':0,'timed_out':False,'capture_truncated':False,
            'supervisor_capture_truncated':False,'client_cleanup':deepcopy(owner),
            'supervisor_cleanup':deepcopy(owner),'proxy':{'server_cleanup':dict(owner,pid=991),
            'server_pid':991,'server_returncode':0,'fault':None,'pump_errors':[],
            'input_pump_joined':True},'stdout':'Remote semantic fallback: no negotiated profile proves eligibility\n'
            'Using immutable receiver clone basis\nReceiver clone preserved 917504 logical bytes\n',
            'stderr':'','supervisor_output':''}


def result():
    return {'schema':'unison-private-dng-remote-fallback/1','complete':True,
            'parameters':{'file_bytes':1048576,'files':1,'client_workers':2,'server_workers':2,
                'owner_credits':2,'total_grant':8,'tag':50740,'adobe_validation':'off'},
            'cases':[dict(compiler_pair=list(pair),exact_output=True,basis_unchanged=True,
                noop_five_unchanged=True,source_complement_unchanged=True,staging_cleaned=True,
                calls={stage:run() for stage in ('seed','update','noop')}) for pair in sorted(PAIRS)]}


class Controls(unittest.TestCase):
    def test_fixed_scope(self):
        self.assertEqual(audit(result())['cli_calls'],12)
    def test_missing_duplicate_wrong_rows(self):
        for change in ('missing','duplicate','wrong','incomplete','parameters'):
            v=result()
            if change=='missing':v['cases'].pop()
            elif change=='duplicate':v['cases'][1]=deepcopy(v['cases'][0])
            elif change=='wrong':v['cases'][0]['compiler_pair']=['unknown','ox']
            elif change=='incomplete':v['complete']=False
            else:v['parameters']['total_grant']=18
            with self.subTest(change=change),self.assertRaises(ValueError):audit(v)
    def test_each_stage_ownership_and_preservation(self):
        for stage in ('seed','update','noop'):
            for owner in ('client_cleanup','supervisor_cleanup'):
                v=result();v['cases'][0]['calls'][stage][owner]['other_group_members_absent_before_reap']=False
                with self.subTest(stage=stage,owner=owner),self.assertRaises(ValueError):audit(v)
        for key in ('exact_output','basis_unchanged','noop_five_unchanged','source_complement_unchanged','staging_cleaned'):
            v=result();v['cases'][0][key]=False
            with self.subTest(key=key),self.assertRaises(ValueError):audit(v)
    def test_proxy_and_failure_refusals(self):
        for field,value in [('fault','failed'),('pump_errors',['failed']),('input_pump_joined',False),
                            ('server_returncode',1),('server_pid',992)]:
            v=result();v['cases'][0]['calls']['update']['proxy'][field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):audit(v)
    def test_mode_and_counter_refusals(self):
        for log in ('Local source clone completed before semantic planning\n',
                    'Remote semantic clone wrote 5 logical metadata bytes\n','',
                    'Remote semantic fallback: no negotiated profile proves eligibility\n'
                    'Using immutable receiver clone basis\nReceiver clone preserved 1048576 logical bytes\n'):
            v=result();v['cases'][0]['calls']['update']['stdout']=log
            with self.subTest(log=log),self.assertRaises(ValueError):audit(v)


if __name__=='__main__':unittest.main()
