"""Original fabricated raw captures only; never create a child or SDK helper."""
import copy,json,unittest
from sdk_merge_receiving.evidence_test import fixture
from current_validation_paths.evidence import audit
SHA='a'*64


def expected(mode='pass',pid=321,endpoint='server'):
    return dict(endpoint=endpoint,pid=pid,candidate_sha256=SHA,candidate_bytes=4096,mode=mode,
        outcome='timed-out' if mode=='hang' else 'completed')


def lines(entry):
    mode=entry['mode'];pid=entry['pid'];endpoint=entry['endpoint'];prefix='server: ' if endpoint=='server' else ''
    if mode=='hang':payload=b'';status='signal:-11'
    else:
        payload=('UNISON-DNG-VALIDATION 1\ncandidate-sha256 '+('0'*64 if mode=='wrong-receipt' else SHA)+
            '\ncandidate-size 4096\ndriver-build validation-path-'+endpoint+'-v1\nstructure valid\ndecode success\nraw-digest missing\nerrors '+('1' if mode=='error' else '0')+'\nwarnings 0\nEND\n').encode();status='exit:0'
    return ('['+prefix+'validation-process] Helper result v0 pid='+str(pid)+' status='+status+' outcome='+entry['outcome']+
        ' candidate-sha256='+SHA+' candidate-bytes=4096 capture-truncated=false stdout-truncated=false stderr-truncated=false stdout-hex='+payload.hex()+' stderr-hex=\n'+
        '['+prefix+'validation-group] Retained group v0 pid='+str(pid)+' candidate-sha256='+SHA+' other-members=0\n')


def bundle(mode='pass',code=0):
    row,pair=fixture('seed');pair['client']['returncode']=pair['client']['client_cleanup']['returncode']=code
    entry=expected(mode);pair['proxy']['stderr']=lines(entry)
    return row,pair,[entry]


def check(row,pair,helpers,code=0,raw=None):
    return audit(pair,client_command=row['command'],proxy_command=pair['proxy']['command'],server_command=row['server_command'],
        raw_proxy_bytes=json.dumps(pair['raw_proxy']).encode() if raw is None else raw,expected_client_exit=code,expected_helpers=helpers)


class ProcessEvidence(unittest.TestCase):
    def test_all_original_fake_modes_and_missing_digest_are_explicit(self):
        for mode in ('pass','delay','error','wrong-receipt','mutate','hang'):
            row,pair,helpers=bundle(mode)
            value=check(row,pair,helpers);self.assertEqual(len(value['helper_observations']),1)
            self.assertFalse(value['resource_release_authorized']);self.assertTrue(value['publication_fence_required'])
            report=value['helper_observations'][0]['report']
            if report:self.assertTrue(report['synthetic_fixture_only']);self.assertFalse(report['raw_digest_verified'])
    def test_failed2_requires_declared_helper_and_noop_requires_no_helper(self):
        row,pair,helpers=bundle('error',2);self.assertEqual(check(row,pair,helpers,2)['client_returncode'],2)
        with self.assertRaises(ValueError):check(row,pair,[],2)
        row,pair,_=bundle();pair['proxy']['stderr']=''
        self.assertEqual(check(row,pair,[])['helper_observations'],[])
    def test_missing_duplicate_unknown_group_or_truncated_helper_refuse(self):
        for mutation in ('missing','duplicate','group','capture','candidate','mode'):
            row,pair,helpers=bundle();text=pair['proxy']['stderr']
            if mutation=='missing':pair['proxy']['stderr']=''
            if mutation=='duplicate':pair['proxy']['stderr']*=2
            if mutation=='group':pair['proxy']['stderr']=text.replace('other-members=0','other-members=unknown')
            if mutation=='capture':pair['proxy']['stderr']=text.replace('capture-truncated=false','capture-truncated=true')
            if mutation=='candidate':helpers[0]['candidate_bytes']=4095
            if mutation=='mode':helpers[0]['mode']='error'
            with self.subTest(mutation=mutation),self.assertRaises(ValueError):check(row,pair,helpers)
    def test_transport_status_trace_raw_frame_and_boolean_counters_refuse(self):
        for mutation in ('status','trace','raw','pump','counter','server','alias'):
            row,pair,helpers=bundle();raw=None
            if mutation=='status':pair['client']['returncode']=1
            if mutation=='trace':row['command']+=['-nodebug','validation-process'];pair['client']['command']=row['command']
            if mutation=='raw':raw=json.dumps({**pair['raw_proxy'],'server_reaped':False}).encode()
            if mutation=='pump':pair['raw_proxy']['input_eof_forwarded']=False
            if mutation=='counter':pair['raw_proxy']['forwarded_protocol_bytes']['client_to_server_bytes']=True
            if mutation=='server':pair['raw_proxy']['server_returncode']=False
            if mutation=='alias':helpers[0]['pid']=pair['client']['client_cleanup']['pid']
            with self.subTest(mutation=mutation),self.assertRaises(ValueError):check(row,pair,helpers,raw=raw)
    def test_six_directory_helpers_are_each_bound_not_collapsed_by_endpoint(self):
        row,pair,_=bundle();helpers=[expected(pid=321+i) for i in range(6)]
        pair['proxy']['stderr']=''.join(lines(e) for e in helpers)
        self.assertEqual(len(check(row,pair,helpers)['helper_observations']),6)

if __name__=='__main__':unittest.main()
