"""Original fabricated raw transport evidence; no child or media access."""
import copy
import json
import unittest
from sdk_merge_receiving.evidence import bind
from sdk_merge_receiving.helpers import audit as helpers
from sdk_merge_receiving.helpers_test import frame, SHA
from sdk_merge_receiving.plan import schedule
from sdk_merge_receiving.plan_test import inputs

PROXY=['/qualified/python','-m','qualified.proxy']

def fixture(stage='update'):
    row=next(r for r in schedule(*inputs())['rows'] if r['codec']=='uncompressed' and r['stage']==stage)
    def child(command,pid,log):
        return dict(command=command,returncode=0,timed_out=False,capture_truncated=False,
            stdout=log,stderr='',client_cleanup=dict(pid=pid,returncode=0,reaped=True,
                hard_kill_required=False,other_group_members_absent_before_reap=True,
                group_cleanup_before_leader_reap=True),aggregate_or_parent_terminal_proved=False,
            io_cpu_release_authorized=False)
    raw=dict(schema='unison-retained-merge-proxy/1',server_command=row['server_command'],
        server_pid=103,server_returncode=0,server_reaped=True,server_group=102,
        input_eof_forwarded=True,output_eof_forwarded=True,
        forwarded_protocol_bytes=dict(client_to_server_bytes=7,server_to_client_bytes=9),
        parent_group_audit_required=True,sdk_helper_audit_required=True,resource_release_authorized=False)
    pair=dict(client=child(row['command'],101,frame('client') if stage=='update' else ''),
        proxy=child(PROXY,102,frame('server',pid=124) if stage=='update' else ''),
        raw_proxy=raw,external_sdk_audit_required=True,resource_release_authorized=False)
    return row,pair


def audit(row,pair,raw=None):
    return bind(row,pair,expected_proxy_command=PROXY,
                raw_proxy_bytes=json.dumps(pair['raw_proxy']).encode() if raw is None else raw)

class Evidence(unittest.TestCase):
    def test_all_phases_bind_to_both_peers_and_raw_bytes(self):
        for stage in ('seed','update','noop'):
            row,pair=fixture(stage);before=copy.deepcopy((row,pair))
            result=audit(row,pair)
            self.assertEqual(len(result['helper_record_sha256s']),2 if stage=='update' else 0)
            verdict=helpers(result['log'],stage=stage,returncode=result['returncode'],
                            candidate_sha256=SHA,candidate_bytes=256)
            self.assertFalse(verdict['resource_release_authorized'])
            self.assertEqual((row,pair),before)

    def test_rejects_unbound_or_unknown_lifecycle(self):
        for mutation in ('client-command','proxy-command','server-command','alias',
                         'bool-code','group','reap','timeout','capture','kill','server-reap',
                         'server-group','bool-counter','counter','release','extra-helper'):
            row,pair=fixture();client=pair['client'];proxy=pair['proxy'];raw=pair['raw_proxy']
            if mutation=='client-command':client['command']=['/different/client']
            if mutation=='proxy-command':proxy['command']=['/different/proxy']
            if mutation=='server-command':raw['server_command']=['/different/server']
            if mutation=='alias':proxy['client_cleanup']['pid']=101
            if mutation=='bool-code':client['returncode']=False
            if mutation=='group':client['client_cleanup']['other_group_members_absent_before_reap']=False
            if mutation=='reap':client['client_cleanup']['reaped']=False
            if mutation=='timeout':client['timed_out']=True
            if mutation=='capture':proxy['capture_truncated']=True
            if mutation=='kill':proxy['client_cleanup']['hard_kill_required']=True
            if mutation=='server-reap':raw['server_reaped']=False
            if mutation=='server-group':raw['server_group']=101
            if mutation=='bool-counter':raw['forwarded_protocol_bytes']['client_to_server_bytes']=True
            if mutation=='counter':raw['forwarded_protocol_bytes']['server_to_client_bytes']=0
            if mutation=='release':pair['resource_release_authorized']=True
            if mutation=='extra-helper':client['stdout']+=frame('client',pid=125)
            with self.subTest(mutation=mutation),self.assertRaises(ValueError):audit(row,pair)

    def test_separate_raw_frame_and_duplicate_fields_cannot_be_substituted(self):
        row,pair=fixture();raw=json.dumps(pair['raw_proxy']).encode()
        for data in (b'{}',b'{"schema":"forged",'+raw[1:],raw[:-1],b'[]'):
            with self.subTest(data=data[:30]),self.assertRaises(ValueError):audit(row,pair,data)

    def test_raw_diagnostic_changes_change_the_bound_transport_hash(self):
        row,pair=fixture();first=audit(row,pair)
        pair['client']['stderr']='extra complete diagnostic\n'
        second=audit(row,pair)
        self.assertNotEqual(first['transport_record_sha256'],second['transport_record_sha256'])
        self.assertEqual(first['helper_record_sha256s'],second['helper_record_sha256s'])

if __name__=='__main__':unittest.main()
