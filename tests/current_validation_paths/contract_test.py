"""Original planning controls and exact original case coverage, zero child IO."""
import unittest
from pathlib import Path
from current_validation_paths.contract import plan,legacy_case_inventory
SOURCE=(Path(__file__).resolve().parents[1]/'validation_paths/run.py').read_text()


class CaseContract(unittest.TestCase):
    def test_every_original_default_case_is_preserved_in_order_and_budget(self):
        p=plan(SOURCE,'/private/tmp/u-vpath-'+'a'*16,'stock')
        self.assertEqual(len(p['rows']),21);self.assertEqual(sum(r['max_CLI_calls'] for r in p['rows']),69)
        self.assertEqual(sum(r['max_fake_validator_calls'] for r in p['rows']),54)
        self.assertEqual(len({r['name'] for r in p['rows']}),21)
        self.assertEqual(p['limits']['declared_producer_interruptions'],4)
        self.assertEqual(p['limits']['declared_client_SIGINT_controls'],2)
        self.assertFalse(p['runtime_admitted']);self.assertFalse(p['source_photos_or_retained_camera_inputs_allowed'])
    def test_omitted_or_reordered_legacy_families_refuse(self):
        for changed in (SOURCE.replace("('partial', 'error')","('partial', 'pass')",1),
                        SOURCE.replace("('error', 'warn'), ('error', 'off')","('error', 'off'), ('error', 'warn')",1),
                        SOURCE.replace('value = moved(root / label, binary, mode, policy)','value = missing_case(root / label, binary, mode, policy)',1)):
            self.assertNotEqual(changed,SOURCE)
            with self.assertRaises(ValueError):legacy_case_inventory(changed)
    def test_each_compiler_is_separate_and_wrong_namespace_refuses(self):
        self.assertEqual(plan(SOURCE,'/private/tmp/u-vpath-'+'b'*16,'ox')['compiler'],'ox')
        for compiler,path in (('both','/private/tmp/u-vpath-'+'a'*16),('stock','/tmp/u-vpath-'+'a'*16),('stock','/private/tmp/u-smg-'+'a'*16)):
            with self.assertRaises(ValueError):plan(SOURCE,path,compiler)

if __name__=='__main__':unittest.main()
