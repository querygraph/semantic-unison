"""Fabricated crash/producer captures only; not an actual crash qualification."""
import json,unittest
from current_validation_paths.producer_evidence import audit
from sdk_merge_receiving.evidence_test import fixture as normal_fixture


def fixture():
    row,pair=normal_fixture('seed');root='/private/tmp/generated-case';size=2097173
    observer=dict(root=root,identity=[1,9],name='resumed.DNG',kind='complete',source_bytes=size,source_sha256='a'*64,
        staged_bytes=size,staged_sha256='a'*64)
    record=dict(source=root+'/left/resumed.DNG',destination=root+'/right/.resumed.stage.unison.tmp',pid=201,group=201,
        size=size,sha256='a'*64,device=1,inode=2,interrupt='complete',nofile_hard=256)
    stage=dict(record=record,stage_identity=[1,2,33152,size,1,1,1,501],source_sha256='a'*64,staged_sha256='a'*64,
        staged_bytes=size,old_destination_absent=True,validator_calls_before_copy_return=0,resource_release_authorized=False)
    sent=dict(pid=103,signal=9,owned_unreaped_before_signal=True,group=102,
        reason='observed generated external-copy stage; owned receiver interruption')
    release=dict(marker=root+'/external-copy.release',copy_fixture_released=True,producer_signalled=False,resource_release_authorized=False)
    frame=dict(schema='unison-generated-producer-interruption/1',server_command=row['server_command'],server_pid=103,
        server_returncode=-9,server_reaped=True,server_group=102,resource_release_authorized=False,
        transport=dict(event=dict(stage=stage,signal=sent,release=release),counts=dict(client_to_server_bytes=5,server_to_client_bytes=7,
            discarded_client_bytes=3),client_eof_observed=True,server_eof_observed=True,input_eof_forwarded=False,discard_permitted_only_after_owned_signal=True))
    pair['raw_proxy']=frame;pair['client']['returncode']=pair['client']['client_cleanup']['returncode']=3
    pair['client']['stderr']='Lost connection with the server\n[external-process] External result v0 pid=201 status=exit:0 outcome=completed cpu-weight=1 other-members=0 capture-truncated=false\n'
    return row,pair,observer


def check(row,pair,observer):
    return audit(pair,client_command=row['command'],proxy_command=pair['proxy']['command'],server_command=row['server_command'],
        raw_proxy_bytes=json.dumps(pair['raw_proxy']).encode(),observer=observer)

class Evidence(unittest.TestCase):
    def test_owned_receiver_crash_plus_normally_reaped_producer_is_not_success(self):
        result=check(*fixture());self.assertEqual(result['client_returncode'],3);self.assertEqual(result['produced']['inode'],2)
        self.assertFalse(result['resource_release_authorized']);self.assertFalse(result['publication_proved'])
    def test_wrong_signal_reap_or_proxy_owner_refuses(self):
        for key,value in [('server_returncode',0),('server_reaped',False),('server_group',101),('server_pid',101)]:
            row,pair,observer=fixture();pair['raw_proxy'][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):check(row,pair,observer)
    def test_signalling_counter_pid_cannot_be_labelled_owned_receiver(self):
        row,pair,observer=fixture();pair['raw_proxy']['transport']['event']['signal']['pid']=201
        with self.assertRaises(ValueError):check(row,pair,observer)
    def test_changed_staging_identity_or_validated_before_copy_return_refuses(self):
        for field,value in [('old_destination_absent',False),('validator_calls_before_copy_return',1),('staged_sha256','b'*64),('stage_identity',[1,999,33152,2097173,1,1,1,501])]:
            row,pair,observer=fixture();pair['raw_proxy']['transport']['event']['stage'][field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):check(row,pair,observer)
    def test_unknown_external_group_or_failed_producer_refuses(self):
        for old,new in [('other-members=0','other-members=unknown'),('status=exit:0','status=signal:9'),('pid=201','pid=999')]:
            row,pair,observer=fixture();pair['client']['stderr']=pair['client']['stderr'].replace(old,new)
            with self.subTest(new=new),self.assertRaises(ValueError):check(row,pair,observer)
    def test_protocol_or_release_claim_cannot_hide_interruption(self):
        row,pair,observer=fixture();pair['raw_proxy']['transport']['input_eof_forwarded']=True
        with self.assertRaises(ValueError):check(row,pair,observer)
        row,pair,observer=fixture();pair['raw_proxy']['transport']['event']['release']['producer_signalled']=True
        with self.assertRaises(ValueError):check(row,pair,observer)
    def test_successful_client_or_missing_connection_failure_is_not_crash_evidence(self):
        row,pair,observer=fixture();pair['client']['returncode']=pair['client']['client_cleanup']['returncode']=0
        with self.assertRaises(ValueError):check(row,pair,observer)
        row,pair,observer=fixture();pair['client']['stderr']=pair['client']['stderr'].replace('Lost connection with the server','missing')
        with self.assertRaises(ValueError):check(row,pair,observer)

if __name__=='__main__':unittest.main()
