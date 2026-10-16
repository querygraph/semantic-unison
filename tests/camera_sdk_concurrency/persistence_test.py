import json,os,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import persistence as p
from shared_cpu_pool import UnresolvedOwnership
class Persistence(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.d=Path(self.tmp.name);self.d.chmod(0o700)
    def tearDown(self):self.tmp.cleanup()
    def test_actual_replace_and_private_mode(self):
        p.save(self.d,{'phase':'first'});p.save(self.d,{'phase':'second'})
        self.assertEqual(json.loads((self.d/'RESULT.json').read_text()),{'phase':'second'})
        self.assertFalse((self.d/'RESULT.next').exists())
        self.assertEqual((self.d/'RESULT.json').stat().st_mode & 0o777,0o600)
    def test_existing_temporary_preserved_without_overwrite(self):
        (self.d/'RESULT.next').write_bytes(b'original retained failure')
        with self.assertRaises(FileExistsError):p.save(self.d,{})
        self.assertEqual((self.d/'RESULT.next').read_bytes(),b'original retained failure')
    def test_unsafe_namespace_or_nonfinite_json_refused(self):
        self.d.chmod(0o755)
        with self.assertRaises(ValueError):p.save(self.d,{})
        self.d.chmod(0o700)
        with self.assertRaises(ValueError):p.save(self.d,{'bad':float('nan')})
        self.assertFalse((self.d/'RESULT.next').exists())
    def test_size_limit_refuses_before_temporary_creation(self):
        with patch.object(p,'MAX_BYTES',4):
            with self.assertRaises(ValueError):p.save(self.d,{'too':'large'})
        self.assertFalse((self.d/'RESULT.next').exists())
    def test_symlink_namespace_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            link=Path(tmp)/'link';link.symlink_to(self.d)
            with self.assertRaises(ValueError):p.save(link,{})
    def test_combined_close_uncertainty_retains_both_identities(self):
        observed=os.stat(self.d)
        with patch.object(p.os,'open',side_effect=[900001,900002]), \
             patch.object(p.os,'fstat',return_value=observed), \
             patch.object(p.os,'write',side_effect=OSError('original injected write')), \
             patch.object(p.os,'close',side_effect=OSError('injected uncertain close')) as close:
            with self.assertRaises(UnresolvedOwnership) as caught:p.save(self.d,{})
        self.assertEqual([call.args[0] for call in close.call_args_list],[900002,900001])
        self.assertEqual({r['fd'] for r in caught.exception.uncertain_closes},{900001,900002})
        self.assertIsInstance(caught.exception.original_failure,UnresolvedOwnership)
        self.assertIn('original injected write',repr(caught.exception.original_failure.original_failure))
    def test_directory_close_uncertainty_after_publication(self):
        observed=os.stat(self.d)
        with patch.object(p.os,'open',side_effect=[900001,900002]),patch.object(p.os,'fstat',return_value=observed), \
             patch.object(p.os,'write',side_effect=lambda fd,data:len(data)),patch.object(p.os,'fsync'), \
             patch.object(p.os,'replace') as replace, \
             patch.object(p.os,'close',side_effect=[None,OSError('uncertain directory close')]) as close:
            with self.assertRaises(UnresolvedOwnership) as caught:p.save(self.d,{})
        replace.assert_called_once();self.assertEqual(close.call_count,2)
        self.assertEqual(caught.exception.uncertain_closes[0]['fd'],900001)
if __name__=='__main__':unittest.main()
