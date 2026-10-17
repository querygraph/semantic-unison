import unittest
from all_scanned_sdk_audit import successful_helpers, BUILD

SHA = 'a' * 64
SIZE = 1234


def frame(endpoint, pid, *, count='0', errors='0', digest='valid', status='exit:0'):
    raw = ('UNISON-DNG-VALIDATION 1\ncandidate-sha256 ' + SHA +
           '\ncandidate-size 1234\ndriver-build ' + BUILD +
           '\nstructure valid\ndecode success\nraw-digest ' + digest +
           '\nerrors ' + errors + '\nwarnings 4\nEND\n').encode()
    prefix = '[server: validation-' if endpoint == 'server' else '[validation-'
    return (prefix + 'process] Helper result v0 pid=' + str(pid) + ' status=' + status +
            ' outcome=completed candidate-sha256=' + SHA + ' candidate-bytes=1234' +
            ' capture-truncated=false stdout-truncated=false stderr-truncated=false stdout-hex=' +
            raw.hex() + ' stderr-hex=\n' + prefix + 'group] Retained group v0 pid=' + str(pid) +
            ' candidate-sha256=' + SHA + ' other-members=' + count + '\n')


class Audit(unittest.TestCase):
    def audit(self, log, phase='validate'):
        return successful_helpers(log, candidate_sha256=SHA, candidate_bytes=SIZE, phase=phase)

    def test_both_endpoints_bound_without_claiming_transfer_or_resource_release(self):
        result = self.audit(frame('client', 101) + frame('server', 102))
        self.assertEqual(result['sdk_helpers'], 2)
        self.assertEqual({e['endpoint'] for e in result['endpoints']}, {'client', 'server'})
        self.assertTrue(all(e['report']['raw_digest_verified'] for e in result['endpoints']))
        self.assertFalse(result['resource_release_authorized'])
        self.assertFalse(result['unchanged_transfer_proved'])
        self.assertFalse(result['candidate_path_isolation_proved'])

    def test_off_baseline_absence_is_not_process_authority(self):
        self.assertFalse(self.audit('', 'baseline')['resource_release_authorized'])
        with self.assertRaises(ValueError): self.audit(frame('client', 101), 'baseline')

    def test_duplicate_missing_unknown_and_cross_bound_groups_rejected(self):
        client, server = frame('client', 101), frame('server', 102)
        for text in ('', client, client + client, client + frame('server', 101),
                     client + frame('server', 102, count='unknown'),
                     client + frame('server', 102, count='1'),
                     client + server.replace('group] Retained group v0 pid=102',
                                             'group] Retained group v0 pid=103'),
                     client + server + server):
            with self.subTest(text=text), self.assertRaises(ValueError): self.audit(text)

    def test_settled_failures_are_not_verdicts_missing_digest_stays_unverified(self):
        client = frame('client', 101)
        for changed in (dict(errors='1'), dict(digest='mismatch'), dict(status='signal:9')):
            with self.assertRaises(ValueError): self.audit(client + frame('server', 102, **changed))
        result = self.audit(client + frame('server', 102, digest='missing'))
        self.assertFalse(result['endpoints'][1]['report']['raw_digest_verified'])

    def test_expected_identity_types_and_capture_fences(self):
        for size in (True, 0, 256 * 1048576 + 1):
            with self.assertRaises(ValueError):
                successful_helpers('', candidate_sha256=SHA, candidate_bytes=size, phase='baseline')
        text = frame('client', 101) + frame('server', 102)
        with self.assertRaises(ValueError):
            self.audit(text.replace('capture-truncated=false', 'capture-truncated=true'))


if __name__ == '__main__': unittest.main()
