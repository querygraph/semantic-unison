"""Pure adversarial mixed-task audits over saved original fake receipts."""
import copy
import json
from pathlib import Path
import unittest

from audit import audit,audit_prefix

Q=Path(__file__).resolve().parents[1]/'qualification/mixed-validation-fake-controls-actual-20261016.json'


def fixture(label='stock',mode='pass'):
    q=json.loads(Q.read_text())
    row=next(r for r in q['rows'] if r['label']==label)
    return copy.deepcopy(next(c for c in row['report']['cases'] if c['mode']==mode))


def check(case):
    return audit(case['outcome'],command=case['outcome']['command'],metadata_version='synthetic-only',
                 expected_helpers=dict(sdk=case['sdk_pid'],metadata=case['metadata_pid']))


class Audit(unittest.TestCase):
    def test_all_eight_actual_fake_cases_preserve_verdict_and_settlement(self):
        for label in ('stock','ox'):
            for mode in ('pass','sdk-error','metadata-error','both-error'):
                with self.subTest(label=label,mode=mode):
                    case=fixture(label,mode);p=check(case)
                    self.assertEqual(p['functional_status'],'PASSED' if mode=='pass' else 'FAILED')
                    self.assertEqual(p['sdk_accepted'],case['sdk_accepted'])
                    self.assertEqual(p['metadata_accepted'],case['metadata_accepted'])
                    self.assertEqual(p['known_helper_settlements'],2)
                    self.assertFalse(p['resource_release_authorized']);self.assertFalse(p['producer_authenticated'])
    def test_unknown_group_and_missing_records_refuse(self):
        for transform in (lambda s:s.replace('other-members=0','other-members=unknown',1),
                          lambda s:s.replace('other-members=0','other-members=unobserved',1),
                          lambda s:'\n'.join(x for x in s.splitlines() if not x.startswith('SDK_RESULT ')),
                          lambda s:s.replace('MIXED_CLOSED','UNFINISHED',1)):
            c=fixture();c['outcome']['stdout']=transform(c['outcome']['stdout'])
            with self.assertRaises(ValueError):check(c)
    def test_exact_command_pid_counters_and_extra_records_are_bound(self):
        for mutation in ('command','pid','weight','counter','duplicate','owner','bool'):
            c=fixture();out=c['outcome'];expected=list(out['command'])
            if mutation=='command':out['command'][3]+='-different'
            elif mutation=='pid':c['sdk_pid']+=1
            elif mutation=='weight':
                for stream in ('stdout','stderr'):out[stream]=out[stream].replace('cpu-weight=1','cpu-weight=2')
            elif mutation=='counter':out['stdout']=out['stdout'].replace('hashes=16','hashes=15')
            elif mutation=='duplicate':out['stdout']+='\n'+next(x for x in out['stdout'].splitlines() if x.startswith('SDK_RESULT '))
            elif mutation=='owner':out['client_cleanup']['pid']+=1
            else:out['returncode']=False
            with self.subTest(mutation=mutation),self.assertRaises(ValueError):
                audit(out,command=expected,metadata_version='synthetic-only',expected_helpers=dict(sdk=c['sdk_pid'],metadata=c['metadata_pid']))
    def test_probe_group_and_truncation_are_not_functional_failure_release(self):
        for field in ('reaped','other_group_members_absent_before_reap'):
            c=fixture();c['outcome']['client_cleanup'][field]=False
            with self.assertRaises(ValueError):check(c)
        for field in ('timed_out','capture_truncated'):
            c=fixture();c['outcome'][field]=True
            with self.assertRaises(ValueError):check(c)
    def test_protocol_contradiction_cannot_keep_a_pass(self):
        c=fixture();out=c['outcome'];line=next(x for x in out['stdout'].splitlines() if x.startswith('SDK_RESULT '))
        start=line.index('stdout-hex=')+len('stdout-hex=');end=line.index(' stderr-hex=')
        raw=bytes.fromhex(line[start:end]).replace(b'errors 0',b'errors 1')
        out['stdout']=out['stdout'].replace(line,line[:start]+raw.hex()+line[end:])
        with self.assertRaises(ValueError):check(c)
    def test_metadata_protocol_failure_is_separate_from_known_process_settlement(self):
        c=fixture();p=audit(c['outcome'],command=c['outcome']['command'],metadata_version='wrong-version')
        self.assertEqual(p['functional_status'],'FAILED');self.assertFalse(p['metadata_fields_verified'])
        self.assertEqual(p['known_helper_settlements'],2)
    def test_metadata_numeric_version_preserves_decimal_spelling(self):
        c=fixture();out=c['outcome'];line=next(x for x in out['stdout'].splitlines() if x.startswith('METADATA_RESULT stdout-hex='))
        raw=bytes.fromhex(line.split('=',1)[1]).replace(b'"synthetic-only"',b'13.10')
        out['stdout']=out['stdout'].replace(line,'METADATA_RESULT stdout-hex='+raw.hex())
        self.assertTrue(audit(out,command=out['command'],metadata_version='13.10')['metadata_fields_verified'])
        self.assertFalse(audit(out,command=out['command'],metadata_version='13.1')['metadata_fields_verified'])
        with self.assertRaises(ValueError):audit(out,command=out['command'],metadata_version=True)
    def test_prefix_distinguishes_complete_failed_and_unstarted(self):
        stock,ox=fixture(),fixture('ox');commands=[stock['outcome']['command'],ox['outcome']['command']]
        result=dict(schema='unison-mixed-validation-worker/1',complete=True,phase='FINISHED',
          invocations=[dict(index=i,state='OUTCOME',outcome=c['outcome']) for i,c in enumerate((stock,ox))])
        p=audit_prefix(result,commands=commands,metadata_version='synthetic-only')
        self.assertEqual((p['functional_status'],p['sdk_helpers_settled']),('PASSED',2))
        failed=fixture(mode='sdk-error');commands[0]=failed['outcome']['command']
        result.update(complete=False,phase='CALL_MAY_HAVE_STARTED',failure='original SDK findings',
          invocations=[dict(index=0,state='OUTCOME',outcome=failed['outcome'])])
        p=audit_prefix(result,commands=commands,metadata_version='synthetic-only')
        self.assertEqual((p['functional_status'],p['sdk_helpers_settled']),('FAILED',1))
        result['invocations'].append(dict(index=1,state='OUTCOME',outcome=ox['outcome']))
        with self.assertRaises(ValueError):audit_prefix(result,commands=commands,metadata_version='synthetic-only')
        result.update(invocations=[],phase='PREPARING_NO_CALL')
        self.assertEqual(audit_prefix(result,commands=commands,metadata_version='synthetic-only')['attempted_probes'],0)
        result.update(invocations=[dict(index=0,state='INTENT',outcome=failed['outcome'])],phase='CALL_MAY_HAVE_STARTED')
        with self.assertRaises(ValueError):audit_prefix(result,commands=commands,metadata_version='synthetic-only')


if __name__=='__main__':unittest.main()
