"""Original synthetic expected-failure transport evidence; never launch a child."""
import copy,json,unittest
from sdk_merge_receiving.evidence_test import fixture
from sdk_negative_receiving.finding_test import log,SHA
from sdk_negative_receiving.transport_audit import audit


def packet(policy='require'):
    row,pair=fixture('seed')
    for command in (row['command'],row['server_command']):
        at=command.index('-adobevalidate');command[at+1]=policy
    pair['client']['command']=copy.deepcopy(row['command'])
    pair['raw_proxy']['server_command']=copy.deepcopy(row['server_command'])
    pair['client']['returncode']=pair['client']['client_cleanup']['returncode']=2 if policy=='require' else 0
    marker='rejected' if policy=='require' else 'warning'
    pair['client']['stderr']='Adobe DNG validation '+marker+': SDK driver reported validation errors\n'
    pair['proxy']['stderr']=log()
    return row,pair


def check(row,pair,policy='require',raw=None):
    return audit(pair,client_command=row['command'],proxy_command=pair['proxy']['command'],
        server_command=row['server_command'],policy=policy,candidate_sha256=SHA,candidate_bytes=4096,
        raw_proxy_bytes=json.dumps(pair['raw_proxy']).encode() if raw is None else raw)


class DesignatedFailure(unittest.TestCase):
    def test_require_and_warn_keep_actual_exits_and_resource_limits(self):
        for policy in ('require','warn'):
            row,pair=packet(policy);before=copy.deepcopy(pair);value=check(row,pair,policy)
            self.assertEqual(pair,before);self.assertEqual(value['expected_client_exit'],2 if policy=='require' else 0)
            self.assertTrue(value['destination_fence_required']);self.assertTrue(value['worker_settlement_required'])
            self.assertFalse(value['resource_release_authorized']);self.assertFalse(value['parent_terminal_proved'])
    def test_generic_failed_cli_or_missing_negative_never_passes(self):
        for part in ('marker','reason','helper'):
            row,pair=packet()
            if part=='marker':pair['client']['stderr']='SDK driver reported validation errors'
            if part=='reason':pair['client']['stderr']='Adobe DNG validation rejected: unrelated error'
            if part=='helper':pair['proxy']['stderr']=''
            with self.assertRaises(ValueError):check(row,pair)
    def test_status_group_capture_and_server_failures_refuse(self):
        mutations=[('client-code',1),('client-code',False),('reap',False),('group',False),
            ('kill',True),('clip',True),('timeout',True),('server-code',1),('server-code',False),
            ('server-reap',False),('input-eof',False),('server-alias',101),('proxy-code',1),('counter',True)]
        for kind,value in mutations:
            row,pair=packet();client=pair['client'];frame=pair['raw_proxy']
            if kind=='client-code':client['returncode']=client['client_cleanup']['returncode']=value
            if kind=='reap':client['client_cleanup']['reaped']=value
            if kind=='group':client['client_cleanup']['other_group_members_absent_before_reap']=value
            if kind=='kill':client['client_cleanup']['hard_kill_required']=value
            if kind=='clip':client['capture_truncated']=value
            if kind=='timeout':client['timed_out']=value
            if kind=='server-code':frame['server_returncode']=value
            if kind=='server-reap':frame['server_reaped']=value
            if kind=='input-eof':frame['input_eof_forwarded']=value
            if kind=='server-alias':frame['server_pid']=value
            if kind=='proxy-code':pair['proxy']['returncode']=value
            if kind=='counter':frame['forwarded_protocol_bytes']['client_to_server_bytes']=value
            with self.subTest(kind=kind,value=value),self.assertRaises(ValueError):check(row,pair)
    def test_raw_frame_or_policy_mismatch_refuses(self):
        row,pair=packet()
        with self.assertRaises(ValueError):check(row,pair,raw=json.dumps({**pair['raw_proxy'],'server_returncode':1}).encode())
        for command in (row['command'],row['server_command']):
            before=command[:];command[command.index('-adobevalidate')+1]='off'
            with self.assertRaises(ValueError):check(row,pair)
            command[:]=before
    def test_unqualified_policy_and_wrong_success_status_refuse(self):
        row,pair=packet('warn')
        with self.assertRaises(ValueError):check(row,pair,'off')
        pair['client']['returncode']=pair['client']['client_cleanup']['returncode']=1
        with self.assertRaises(ValueError):check(row,pair,'warn')

if __name__=='__main__':unittest.main()
