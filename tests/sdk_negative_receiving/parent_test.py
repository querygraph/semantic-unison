"""Twelve fabricated pairs through real kernel/independent replay; no IO/SDK."""
import copy,hashlib,json,unittest
from sdk_merge_receiving.evidence_test import fixture
from sdk_negative_receiving.finding_test import log,SHA
from sdk_negative_receiving.plan import schedule
from sdk_negative_receiving.worker import execute
from sdk_negative_receiving.pair import audit as audit_pair
from sdk_negative_receiving.parent import audit
from sdk_merge_receiving.plan_test import inputs
PROXY=['/qualified/python','/qualified/proxy']


def setup():
    binaries,tool,_=inputs();packet=dict(binaries=binaries,tool=tool,workspace='/private/tmp/u-snr-'+'a'*16)
    records={};pins={};pairs={};reads=[]
    def key(row):return row['codec']+'-'+row['policy']+'-'+row['stage']
    def invoke(row):
        _,pair=fixture('seed');pair['client']['command']=copy.deepcopy(row['command'])
        pair['proxy']['command']=PROXY[:];pair['raw_proxy']['server_command']=copy.deepcopy(row['server_command'])
        if row['stage']=='negative':
            code=1 if row['policy']=='require' else 0
            pair['client']['returncode']=pair['client']['client_cleanup']['returncode']=code
            marker='rejected' if row['policy']=='require' else 'warning'
            pair['client']['stderr']='Adobe DNG validation '+marker+': SDK driver reported validation errors'
            pair['proxy']['stderr']=log()
        frame=json.dumps(pair['raw_proxy']).encode()
        raw=json.dumps(dict(identity=row['identity'],pair=pair,raw_proxy_hex=frame.hex()),sort_keys=True).encode()
        name=key(row)+'-PAIR.json';records[name]=raw;pins[key(row)]=dict(name=name,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
        pairs[key(row)]=(pair,frame)
        return pairs[key(row)]
    def verify(row,candidate):return dict(row=key(row),resource_release_authorized=False)
    result=execute(binaries,tool,packet['workspace'],prepare=lambda row:dict(sha256=SHA,bytes=4096),
        invoke=invoke,audit_transport=lambda row,out,candidate:audit_pair(row,*out,candidate,proxy_command=PROXY),
        verify_outputs=verify,persist=lambda value:None)
    saved=dict(result=result,pair_pins=pins)
    def read(pin):reads.append(pin['name']);return records[pin['name']]
    def replay():return audit(packet,saved,read_pinned=read,proxy_command=lambda row:PROXY,verify_outputs=verify)
    return saved,records,reads,replay


class ParentReplay(unittest.TestCase):
    def test_complete_matrix_replays_every_pair_and_event_without_release_authority(self):
        saved,records,reads,replay=setup();value=replay()
        self.assertEqual(value['cli_calls'],12);self.assertEqual(value['SDK_helpers'],6)
        self.assertEqual(len(reads),12);self.assertEqual(value['events_reconstructed'],24)
        self.assertTrue(value['worker_settlement_required']);self.assertTrue(value['inherited_resource_binding_required'])
        self.assertFalse(value['resource_release_authorized']);self.assertFalse(value['parent_terminal_proved'])
    def test_changed_raw_bytes_pin_and_worker_verdict_refuse(self):
        for kind in ('raw','pin','verdict','event','missing','candidate','release'):
            saved,records,_,replay=setup();first=next(iter(saved['pair_pins']));pin=saved['pair_pins'][first]
            if kind=='raw':records[pin['name']]+=b' '
            if kind=='pin':pin['sha256']='0'*64
            if kind=='verdict':saved['result']['results'][0]['transport']['resource_release_authorized']=True
            if kind=='event':saved['result']['events'][0]['command_sha256']='0'*64
            if kind=='missing':del saved['pair_pins'][first]
            if kind=='candidate':saved['result']['results'][1]['candidate']['sha256']='b'*64
            if kind=='release':saved['result']['resource_release_authorized']=True
            with self.subTest(kind=kind),self.assertRaises(ValueError):replay()
    def test_reordered_results_and_extra_unaccounted_pair_refuse(self):
        for kind in ('order','extra'):
            saved,_,_,replay=setup()
            if kind=='order':saved['result']['results'][0],saved['result']['results'][1]=saved['result']['results'][1],saved['result']['results'][0]
            else:saved['pair_pins']['unaccounted']=copy.deepcopy(next(iter(saved['pair_pins'].values())))
            with self.assertRaises(ValueError):replay()

if __name__=='__main__':unittest.main()
