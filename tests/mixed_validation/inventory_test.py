"""Exact closure checks with inert hash callback; no media or helper access."""
import unittest
from inventory import paths,verify,ROOT


class Inventory(unittest.TestCase):
    def fixture(self):return dict(source_pins=[dict(path=str(p),sha256='a'*64,bytes=1) for p in paths()])
    def test_required_current_paths_and_all_checks(self):
        names=set(paths())
        for name in ('src/supervisedExternal.ml','src/dngValidation.ml','src/semanticRuntime.ml',
                     'tests/mixed_validation/execute.py','tests/sdk_host_matrix/shared_child.py',
                     'tests/private_camera_receiving/close.py'):
            self.assertIn(ROOT/name,names)
        self.assertLessEqual(len(names),512)
        checked=[];verify(self.fixture(),checker=checked.append)
        self.assertEqual(len(checked),len(names))
    def test_omitted_extra_duplicate_and_hash_failure_refuse(self):
        for mode in ('omit','extra','duplicate'):
            plan=self.fixture();rows=plan['source_pins']
            if mode=='omit':rows.pop()
            elif mode=='extra':rows.append(dict(path='/inert/extra',sha256='a'*64,bytes=1))
            else:rows[-1]=rows[0]
            with self.subTest(mode=mode),self.assertRaises(ValueError):verify(plan,checker=lambda x:None)
        def refuse(item):raise ValueError('current source hash differs')
        with self.assertRaisesRegex(ValueError,'hash differs'):verify(self.fixture(),checker=refuse)


if __name__=='__main__':unittest.main()
