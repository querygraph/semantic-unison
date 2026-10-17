import unittest
from all_scanned_sdk_audit_test import frame, input_frame, SHA, SIZE
from all_scanned_sdk_audit import successful_helpers
from all_scanned_sdk_paths import parse, audit


class Paths(unittest.TestCase):
    def fixture(self):
        directory = '/private/tmp/u-paths'
        log = (frame('client', 201) + frame('server', 202)
               + input_frame('client', 201, 11, directory)
               + input_frame('server', 202, 12, directory))
        helpers = successful_helpers(log, candidate_sha256=SHA, candidate_bytes=SIZE, phase='validate')
        return directory, log, helpers

    def test_exact_private_stage_owner_and_helper_join(self):
        directory, log, helpers = self.fixture()
        proof = audit(log, directory=directory, endpoint_pids=dict(client=11, server=12), helpers=helpers, phase='validate')
        self.assertTrue(proof['private_owner_context_observed'])
        self.assertFalse(proof['OS_argv_traced'])

    def test_missing_duplicate_wrong_owner_borrowed_and_original_path_refused(self):
        directory, original, helpers = self.fixture()
        for change in ('missing', 'duplicate', 'borrowed', 'owner', 'original'):
            log = original
            if change == 'missing': log = '\n'.join(l for l in log.splitlines() if 'validation-input]' not in l)
            elif change == 'duplicate': log += input_frame('client', 201, 11, directory)
            elif change == 'borrowed': log = log.replace('borrowed-output=true', 'borrowed-output=false')
            elif change == 'owner': log = log.replace('validation-scan-11'.encode().hex(), 'validation-scan-99'.encode().hex())
            else:
                row = parse(log)[0]
                log = log.replace(row['path'].encode().hex(), (directory + '/left/image.dng').encode().hex())
            with self.assertRaises(ValueError):
                audit(log, directory=directory, endpoint_pids=dict(client=11, server=12), helpers=helpers, phase='validate')

    def test_unavailable_nul_dot_and_odd_hex_rejected(self):
        _, log, _ = self.fixture(); row = parse(log)[0]
        for encoded in ('unavailable', 'f', b'/tmp/../input'.hex(), b'/tmp/input\0'.hex()):
            with self.assertRaises(ValueError): parse(log.replace(row['path'].encode().hex(), encoded))


if __name__ == '__main__': unittest.main()
