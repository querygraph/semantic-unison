"""Fabricated full SDK frames and owner diagnostics only; never invokes SDK."""
import unittest
from sdk_merge_receiving.helpers import audit
from sdk_merge_receiving.plan import BUILD

SHA='1'*64

def frame(endpoint, *, pid=123, members='0', status='exit:0', size=256,
          digest=SHA, clip='false', raw_digest='valid'):
    raw=('UNISON-DNG-VALIDATION 1\ncandidate-sha256 '+digest+
         '\ncandidate-size '+str(size)+'\ndriver-build '+BUILD+
         '\nstructure valid\ndecode success\nraw-digest '+raw_digest+
         '\nerrors 0\nwarnings 4\nEND\n').encode().hex()
    prefix='server: ' if endpoint=='server' else ''
    return ('['+prefix+'validation-process] Helper result v0 pid='+str(pid)+
        ' status='+status+' outcome=completed candidate-sha256='+digest+
        ' candidate-bytes='+str(size)+' capture-truncated='+clip+
        ' stdout-truncated=false stderr-truncated=false stdout-hex='+raw+' stderr-hex=\n'+
        '['+prefix+'validation-group] Retained group v0 pid='+str(pid)+
        ' candidate-sha256='+digest+' other-members='+members+'\n')


def check(log, stage='update', code=0):
    return audit(log,stage=stage,returncode=code,candidate_sha256=SHA,candidate_bytes=256)

class Helpers(unittest.TestCase):
    def test_both_endpoint_receipts_preserve_warnings_and_scope(self):
        result=check(frame('client')+frame('server',pid=124))
        self.assertEqual(result['helper_count'],2)
        self.assertEqual([x['report']['warnings'] for x in result['helpers']],['4','4'])
        self.assertFalse(result['resource_release_authorized'])
        self.assertFalse(result['output_bytes_verified'])

    def test_missing_digest_stays_explicitly_unverified(self):
        result=check(frame('client',raw_digest='missing')+frame('server',pid=124))
        self.assertFalse(result['helpers'][0]['report']['raw_digest_verified'])

    def test_successful_nonvalidating_phases_reject_helpers(self):
        for stage in ('seed','noop'):
            self.assertEqual(check('normal output\n',stage)['helper_count'],0)
            with self.assertRaises(ValueError):check(frame('client'),stage)

    def test_failed_or_truncated_evidence_never_proves_noncreation(self):
        for log in ('',frame('client'),frame('client')+frame('server',pid=124)):
            with self.assertRaises(ValueError):check(log,code=1)
        for log in (frame('client'),frame('client')*2,
                    frame('client')+frame('server',members='unknown'),
                    frame('client')+frame('server',members='1'),
                    frame('client')+frame('server',size=255),
                    frame('client')+frame('server',digest='2'*64),
                    frame('client')+frame('server',status='signal:9'),
                    frame('client')+frame('server',clip='true'),
                    frame('client')+frame('server')[:-3]):
            with self.subTest(log=log[-90:]),self.assertRaises(ValueError):check(log)

if __name__=='__main__':unittest.main()
