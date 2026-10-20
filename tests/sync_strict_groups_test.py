"""Fixed source regression for every benchmark profile's group census selection."""
import ast
import hashlib
from pathlib import Path
import subprocess
from types import SimpleNamespace
import unittest

ROOT=Path(__file__).resolve().parents[1]
BASELINE='59f4f4db:bench/sync/run.py'
BASELINE_SHA='6d9db0606d88c7ae6f816325a46773e706373ef4947122ab3d9665aea31b0049'


def selection(source):
    calls=[node for node in ast.walk(ast.parse(source)) if isinstance(node,ast.Call)
           and isinstance(node.func,ast.Name) and node.func.id=='measure_invocation']
    if len(calls)!=1:raise ValueError('one benchmark dispatch site required')
    values=[key.value for key in calls[0].keywords if key.arg=='strict_group_settlement']
    if len(values)!=1:raise ValueError('one explicit group census selection required')
    return compile(ast.Expression(values[0]),'<actual benchmark census selection>','eval')


class Strict(unittest.TestCase):
    def test_actual_dispatch_all_profiles_and_retained_regression(self):
        current=(ROOT/'bench/sync/run.py').read_bytes()
        completed=subprocess.run(['git','show',BASELINE],cwd=ROOT,capture_output=True,timeout=3)
        self.assertEqual(completed.returncode,0)
        self.assertEqual(hashlib.sha256(completed.stdout).hexdigest(),BASELINE_SHA)
        now=selection(current);before=selection(completed.stdout)
        for shared,budget in ((True,8),(False,8),(False,18),(False,None)):
            args=SimpleNamespace(shared_qualification=shared,loopback_cpu_credits=budget)
            with self.subTest(shared=shared,budget=budget):
                self.assertIs(eval(now,{'args':args}),True)
                self.assertIs(eval(before,{'args':args}),shared)
        # The consumed performance run took this exact failing old branch.
        self.assertIs(eval(before,{'args':SimpleNamespace(shared_qualification=False)}),False)

    def test_missing_or_duplicate_dispatch_refuses(self):
        for source in ('pass', 'measure_invocation()','measure_invocation(strict_group_settlement=True)\nmeasure_invocation(strict_group_settlement=True)'):
            with self.subTest(source=source),self.assertRaises(ValueError):selection(source)

if __name__=='__main__':unittest.main()
