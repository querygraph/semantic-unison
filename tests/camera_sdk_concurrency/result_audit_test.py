import unittest
from unittest.mock import patch
import result_audit as a
from synthetic_case import BUILD
class ParentAudit(unittest.TestCase):
    def plan(self):return dict(workspace='/private/tmp/u-concurrent',tool=dict(build_id=BUILD))
    def result(self):return dict(schema='unison-concurrent-synthetic-worker/1',complete=False,
        phase='PREPARING_NO_CALL',sdk_validation_claimed=False,semantic_eligibility_claimed=False,
        invocations=[],cases=[],failure='original preparation refusal')
    def test_zero_call_known_preparation(self):
        with patch.object(a,'audit_attempted') as external:
            proof=a.audit(self.result(),self.plan(),'/private/tmp/u-concurrent')
        external.assert_not_called();self.assertEqual(proof['attempted_cli_invocations'],0)
    def test_zero_call_cannot_cover_possible_dispatch(self):
        for change in [dict(phase='CALL_MAY_HAVE_STARTED'),dict(complete=True),dict(failure=''),dict(sdk_validation_claimed=True)]:
            with self.subTest(change=change),self.assertRaises(ValueError):
                a.audit(dict(self.result(),**change),self.plan(),'/private/tmp/u-concurrent')
    def test_reject_mistyped_complete_or_wrong_scope(self):
        for change in [dict(complete=0),dict(schema='other'),dict(invocations=[{}]*3)]:
            with self.assertRaises(ValueError):a.audit(dict(self.result(),**change),self.plan(),'/private/tmp/u-concurrent')
    def test_prefix_cannot_skip_independent_call_settlement(self):
        result=dict(self.result(),invocations=[{}])
        with patch.object(a,'audit_attempted',side_effect=ValueError('unknown actual call')) as external:
            with self.assertRaisesRegex(ValueError,'unknown actual call'):
                a.audit(result,self.plan(),'/private/tmp/u-concurrent')
        external.assert_called_once_with(result)
    def test_namespace_and_tool_fences(self):
        for plan in [dict(self.plan(),workspace='/wrong'),dict(self.plan(),tool=dict(build_id='real-sdk'))]:
            with self.assertRaises(ValueError):a.audit(self.result(),plan,'/private/tmp/u-concurrent')
if __name__=='__main__':unittest.main()
