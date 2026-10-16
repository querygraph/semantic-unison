"""Fixed inert-artifact controls; never execute a binary or read camera data."""
import hashlib
import io
import sys
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import artifact_pins as a


class Controls(unittest.TestCase):
    def test_label_domain(self):
        self.assertEqual(a.parse(['stock='+'a'*64]), {'stock':'a'*64})
        for bad in (['x'], ['='+'a'*64], ['x='+'A'*64], ['x='+'a'*63], ['x='+'a'*64]*2):
            with self.assertRaises(ValueError):
                a.parse(bad)

    def test_disabled_does_not_open(self):
        with patch.object(os,'open',side_effect=AssertionError('artifact opened')):
            self.assertEqual(a.verify({'old':'/unopened'},{}),{})

    def test_exact_pin_and_mismatch(self):
        with tempfile.TemporaryDirectory() as name:
            p=Path(name)/'inert';p.write_bytes(b'not executable')
            digest=hashlib.sha256(p.read_bytes()).hexdigest()
            self.assertEqual(a.verify({'s':p},{'s':digest}),{'s':digest})
            with self.assertRaises(ValueError):a.verify({'s':p},{'s':'0'*64})
            with self.assertRaises(ValueError):a.verify({'s':p},{'other':digest})

    def test_worker_refuses_mismatch_before_any_executable_metadata_call(self):
        import run as benchmark
        with tempfile.TemporaryDirectory() as name:
            p=Path(name)/'inert';p.write_bytes(b'not a program');p.chmod(0o700)
            digest=hashlib.sha256(p.read_bytes()).hexdigest()
            for binary_pin,compiler_pin in [('0'*64,digest),(digest,'0'*64)]:
                argv=['bench','--binary','stock='+str(p),'--compiler','stock='+str(p),
                      '--qualification','--output',str(Path(name)/'never-created.json'),
                      '--expected-binary-sha256','stock='+binary_pin,
                      '--expected-compiler-sha256','stock='+compiler_pin]
                with patch.object(sys,'argv',argv),patch.object(sys,'stderr',io.StringIO()), \
                     patch.object(benchmark,'binary_info',side_effect=AssertionError('executed binary')) as binary, \
                     patch.object(benchmark.subprocess,'check_output',side_effect=AssertionError('executed compiler')) as compiler, \
                     self.assertRaises(SystemExit) as refused:
                    benchmark.main()
                self.assertEqual(refused.exception.code,2)
                binary.assert_not_called();compiler.assert_not_called()
                self.assertFalse((Path(name)/'never-created.json').exists())

    def test_regular_nonempty_bounded_before_read(self):
        with tempfile.TemporaryDirectory() as name:
            p=Path(name)/'inert';p.touch()
            with self.assertRaises(ValueError):a.stable_sha(p)
            with p.open('wb') as f:f.truncate(a.MAX_BYTES+1)
            with patch.object(os,'read',side_effect=AssertionError('oversize body opened')):
                with self.assertRaises(ValueError):a.stable_sha(p)
            q=Path(name)/'link';q.symlink_to(p)
            with self.assertRaises(OSError):a.stable_sha(q)

    def test_visible_replacement_rejected_and_fd_closed(self):
        with tempfile.TemporaryDirectory() as name:
            p=Path(name)/'inert';p.write_bytes(b'abc');q=Path(name)/'other';q.write_bytes(b'abc')
            close=os.close
            with patch.object(os,'lstat',return_value=q.lstat()),patch.object(os,'close',wraps=close) as closed:
                with self.assertRaises(ValueError):a.stable_sha(p)
                self.assertEqual(closed.call_count,1)

if __name__=='__main__':unittest.main()
