"""Original inert lifecycle controls; no child, transport, SDK or file payload."""
import unittest
from sdk_merge_receiving.ledger import Ledger
from sdk_merge_receiving.plan import CODECS, STAGES

A, B, C = ('%064x' % n for n in (1, 2, 3))

class Lifecycle(unittest.TestCase):
    def finish(self, ledger, index, code=0, helpers=None):
        ledger.finish(index, returncode=code, transport_record_sha256=A,
                      helper_record_sha256s=[] if helpers is None else helpers)

    def test_full_matrix_still_requires_independent_audit(self):
        ledger = Ledger()
        for codec in CODECS:
            for stage in STAGES:
                index = ledger.begin(codec, stage, A)
                self.finish(ledger, index, helpers=[B,C] if stage == 'update' else [])
        result = ledger.report()
        self.assertTrue(result['complete'])
        self.assertEqual(result['state'], 'COMPLETE_REQUIRES_AUDIT')
        self.assertFalse(result['resource_release_authorized'])
        self.assertFalse(result['worker_settlement_proved'])
        result['entries'].clear()
        self.assertEqual(len(ledger.report()['entries']), 9)
        with self.assertRaises(ValueError): ledger.begin('jxl','noop',A)

    def test_pending_intent_never_becomes_known_failed_prefix(self):
        ledger=Ledger(); ledger.begin('uncompressed','seed',A)
        self.assertEqual(ledger.report()['state'], 'UNRESOLVED_INTENT')
        with self.assertRaises(ValueError): ledger.begin('uncompressed','update',A)
        self.assertFalse(ledger.report()['resource_release_authorized'])

    def test_every_failed_helper_prefix_stops_without_noncreation_claim(self):
        for helpers in ([], [B], [B,C]):
            ledger=Ledger(); self.finish(ledger,ledger.begin('uncompressed','seed',A))
            self.finish(ledger,ledger.begin('uncompressed','update',A),1,helpers)
            report=ledger.report()
            self.assertEqual(report['state'],'FAILED_PREFIX_REQUIRES_AUDIT')
            self.assertFalse(report['helper_noncreation_proved'])
            self.assertFalse(report['resource_release_authorized'])
            with self.assertRaises(ValueError): ledger.begin('uncompressed','noop',A)

    def test_order_and_outcome_replacement_refused(self):
        ledger=Ledger()
        with self.assertRaises(ValueError): ledger.begin('jpeg','seed',A)
        index=ledger.begin('uncompressed','seed',A); self.finish(ledger,index)
        with self.assertRaises(ValueError): self.finish(ledger,index)
        with self.assertRaises(ValueError): ledger.begin('uncompressed','seed',A)

    def test_bad_terminal_evidence_leaves_intent_pending(self):
        for code, refs in ((True, []),(0,[B]),(1,[B,B]),(1,['bad']), (1,[A,B,C])):
            ledger=Ledger(); index=ledger.begin('uncompressed','seed',A)
            with self.assertRaises(ValueError): self.finish(ledger,index,code,refs)
            self.assertEqual(ledger.report()['state'],'UNRESOLVED_INTENT')

if __name__ == '__main__': unittest.main()
