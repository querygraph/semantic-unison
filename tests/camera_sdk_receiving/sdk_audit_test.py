"""Original inert diagnostic frames; no SDK, process, pool or camera access."""
import unittest
import sdk_audit as audit

SHA = 'a' * 64
SIZE = 193851848


def report(**changes):
    fields = dict(zip(audit.FIELDS, (SHA, str(SIZE), audit.BUILD, 'valid', 'success',
                                   'valid', '0', '2')))
    fields.update(changes)
    return ('UNISON-DNG-VALIDATION 1\n' + ''.join(k+' '+fields[k]+'\n' for k in audit.FIELDS)
            + 'END\n').encode('ascii')


def log(raw=None, *, count='0', pid='123', status='exit:0', outcome='completed',
        endpoint='server', clipped='false'):
    raw = report() if raw is None else raw
    prefix = '[server: validation-' if endpoint == 'server' else '[validation-'
    return (prefix+'process] Helper result v0 pid='+pid+' status='+status+' outcome='+outcome+
            ' candidate-sha256='+SHA+' candidate-bytes='+str(SIZE)+
            ' capture-truncated='+clipped+' stdout-truncated='+clipped+
            ' stderr-truncated=false stdout-hex='+raw.hex()+' stderr-hex=\n'+
            prefix+'group] Retained group v0 pid='+pid+' candidate-sha256='+SHA+
            ' other-members='+count+'\n')


class Controls(unittest.TestCase):
    def verdict(self, text):
        return audit.receiving_verdict(text, candidate_sha256=SHA, candidate_bytes=SIZE)

    def test_exact_bound_receipt_pass(self):
        result = self.verdict(log())
        self.assertTrue(result['report']['raw_digest_verified'])
        self.assertEqual(result['settlement']['helper_pid'], 123)

    def test_missing_optional_digest_is_not_verified_digest(self):
        result = self.verdict(log(report(**{'raw-digest': 'missing'})))
        self.assertFalse(result['report']['raw_digest_verified'])
        self.assertEqual(result['report']['raw-digest'], 'missing')

    def test_invalid_findings_and_bindings_are_not_pass(self):
        for key, values in {'raw-digest': ['mismatch', 'unsupported', 'not_checked'],
                            'structure': ['invalid', 'unsupported'],
                            'decode': ['failure', 'unsupported', 'not_checked'],
                            'errors': ['1', '00', '-1'], 'warnings': ['00', '9'*20],
                            'candidate-sha256': ['b'*64], 'candidate-size': ['1'],
                            'driver-build': ['wrong']}.items():
            for value in values:
                with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                    self.verdict(log(report(**{key: value})))

    def test_protocol_is_exact_not_prefix_or_reordered(self):
        raw = report()
        for changed in (raw[:-1], raw+b'extra\n', raw.replace(b'END\n', b'END\r\n'),
                        raw.replace(b'warnings 2', b'warnings\t2'),
                        raw.replace(b'errors 0\nwarnings 2', b'warnings 2\nerrors 0'), b'\xff'):
            with self.subTest(raw=changed), self.assertRaises(ValueError):
                self.verdict(log(changed))

    def test_settlement_does_not_imply_validation_pass(self):
        text = log(report(**{'errors': '1'}), status='exit:7')
        _, proof = audit.settled_helper(text, candidate_sha256=SHA, candidate_bytes=SIZE)
        self.assertEqual(proof['wait_status'], ['exit', 7])
        with self.assertRaises(ValueError):
            self.verdict(text)

    def test_missing_unknown_duplicate_and_other_endpoint_retain(self):
        for text in ('', log(count='unknown'), log(count='unobserved'), log(count='1'),
                     log()+log(), log(endpoint='client'), log(pid='none', status='none'),
                     log(status='stopped:19')):
            with self.subTest(text=text), self.assertRaises(ValueError):
                audit.settled_helper(text, candidate_sha256=SHA, candidate_bytes=SIZE)

    def test_clipped_or_failed_process_not_success(self):
        for text in (log(clipped='true'), log(outcome='timed-out'), log(status='signal:9')):
            with self.subTest(text=text), self.assertRaises(ValueError):
                self.verdict(text)

    def test_cross_bound_group_identity_rejected(self):
        text = log().replace('group] Retained group v0 pid=123', 'group] Retained group v0 pid=124')
        with self.assertRaises(ValueError):
            self.verdict(text)


if __name__ == '__main__':
    unittest.main()
