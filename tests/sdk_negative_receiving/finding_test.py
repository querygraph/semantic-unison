"""Original synthetic raw frames; zero SDK/process/payload activity."""
import unittest
from camera_sdk_receiving.sdk_audit import receipt,BUILD
from sdk_negative_receiving.finding import digest_mismatch,helper
SHA='a'*64


def raw():
    return ('UNISON-DNG-VALIDATION 1\ncandidate-sha256 '+SHA+
        '\ncandidate-size 4096\ndriver-build '+BUILD+
        '\nstructure valid\ndecode success\nraw-digest mismatch\nerrors 1\nwarnings 4\nEND\n').encode()


def log(data=None):
    return ('[server: validation-process] Helper result v0 pid=321 status=exit:0 outcome=completed candidate-sha256='+SHA+
        ' candidate-bytes=4096 capture-truncated=false stdout-truncated=false stderr-truncated=false stdout-hex='+(raw() if data is None else data).hex()+' stderr-hex=\n'+
        '[server: validation-group] Retained group v0 pid=321 candidate-sha256='+SHA+' other-members=0\n')


def parse(data):return digest_mismatch(data,candidate_sha256=SHA,candidate_bytes=4096)
def check(data):return helper(data,candidate_sha256=SHA,candidate_bytes=4096)


class NegativeFinding(unittest.TestCase):
    def test_expected_negative_does_not_pass_positive_parser(self):
        result=parse(raw());self.assertTrue(result['expected_negative_finding'])
        self.assertFalse(result['validation_passed']);self.assertFalse(result['resource_release_authorized'])
        with self.assertRaises(ValueError):receipt(raw(),candidate_sha256=SHA,candidate_bytes=4096,build_id=BUILD)
    def test_positive_missing_or_other_findings_are_not_expected_negative(self):
        for data in (raw().replace(b'mismatch',b'valid'),raw().replace(b'mismatch',b'missing'),
                     raw().replace(b'errors 1',b'errors 0'),raw().replace(b'decode success',b'decode failure'),
                     raw().replace(b'structure valid',b'structure invalid')):
            with self.assertRaises(ValueError):parse(data)
    def test_candidate_counts_and_framing_are_exact(self):
        variants=[raw().replace(SHA.encode(),b'b'*64),raw().replace(b'candidate-size 4096',b'candidate-size 4095'),
            raw().replace(BUILD.encode(),b'different'),raw().replace(b'errors 1',b'errors 01'),
            raw().replace(b'warnings 4',b'warnings -1'),raw().replace(b'errors 1',b'errors 4611686018427387904'),
            raw()[:-1],raw()+b'extra\n',raw().replace(b'END',b'END\xff'),
            raw().replace(b'raw-digest mismatch',b'raw-digest mismatch\nraw-digest mismatch')]
        for data in variants:
            with self.assertRaises(ValueError):parse(data)
    def test_known_helper_terminal_is_separate_from_publication_and_parent(self):
        result=check(log());self.assertEqual(result['settlement']['helper_pid'],321)
        self.assertTrue(result['parent_cli_audit_required']);self.assertTrue(result['destination_fence_required'])
        self.assertFalse(result['resource_release_authorized'])
    def test_absent_duplicate_truncated_signaled_or_live_helper_refuse(self):
        for data in ('',log()*2,log().replace('other-members=0','other-members=unknown'),
                     log().replace('other-members=0','other-members=1'),
                     log().replace('status=exit:0','status=signal:9'),
                     log().replace('status=exit:0','status=exit:1'),
                     log().replace('capture-truncated=false','capture-truncated=true'),
                     log().replace('candidate-bytes=4096','candidate-bytes=4095'),
                     log().replace('pid=321','pid=322',1),log(raw()[:-1])):
            with self.assertRaises(ValueError):check(data)

if __name__=='__main__':unittest.main()
