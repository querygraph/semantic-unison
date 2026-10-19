import unittest
from corpus_workloads import plan
from batch_counters import audit


class Counters(unittest.TestCase):
    def test_exact_semantic_count_requires_actual_lines(self):
        corpus=plan('many-small',count=1024)
        line='Remote semantic clone wrote 512 logical metadata bytes in 1 write calls (512 payload bytes; 1048576-byte comparison windows; org.firstpair.dng-xmp/1)\n'
        result=audit(line*1024,'semantic',corpus)
        self.assertEqual(result['semantic_updates'],1024)
        self.assertEqual(result['modeled_non_inherited_logical_bytes'],524288)
        self.assertIsNone(result['physical_write_bytes'])
        with self.assertRaises(ValueError):audit(line*1023,'semantic',corpus)

    def test_new_files_have_no_receiver_basis_or_sde(self):
        corpus=plan('new-files',count=1024)
        self.assertEqual(audit('','semantic',corpus)['semantic_updates'],0)
        with self.assertRaises(ValueError):audit('Using immutable receiver clone basis','semantic',corpus)

    def test_ordinary_clone_and_impossible_model_refuse(self):
        corpus=plan('many-small',count=1024)
        with self.assertRaises(ValueError):audit('Using immutable receiver clone basis\nReceiver clone preserved 32768 logical bytes','ordinary',corpus)
        with self.assertRaises(ValueError):audit(('Using immutable receiver clone basis\nReceiver clone preserved 99999999 logical bytes\n')*1024,'receiver-clone',corpus)


if __name__=='__main__':unittest.main()
