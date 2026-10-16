import unittest
from live_records import parse,bound,IncompleteEvidence

D='a'*64
LINE=f'[server: validation-live] Live span v0 owner-pid=11 pid=22 candidate-sha256={D} candidate-bytes=123 clock=monotonic-seconds-v0 samples=3 valid=true first=1 last=2'
class Records(unittest.TestCase):
    def bind(self,record,**changes):
        args=dict(endpoint='server',owner_pid=11,helper_pid=22,candidate_sha256=D,candidate_bytes=123)
        args.update(changes);return bound(record,**args)
    def test_bound_span_contracts_rounding(self):
        r=parse(LINE)[0];span=self.bind(r)
        self.assertGreater(span['first_ns'],10**9)
        self.assertLess(span['last_ns'],2*10**9)
        self.assertFalse(span['settlement_proved'])
    def test_typed_independent_bindings(self):
        for args in [dict(owner_pid=True),dict(helper_pid=True),dict(candidate_bytes=True),dict(candidate_sha256='bad')]:
            with self.assertRaises(IncompleteEvidence):self.bind(parse(LINE)[0],**args)
    def test_extreme_exponent_refused(self):
        with self.assertRaises(IncompleteEvidence):parse(LINE.replace('last=2','last=1e'+'9'*100))
    def test_empty_and_unrelated(self):self.assertEqual(parse('unrelated\n'),[])
    def test_binding_changes_refused(self):
        for args in [dict(endpoint='client'),dict(owner_pid=12),dict(helper_pid=23),
                     dict(candidate_sha256='b'*64),dict(candidate_bytes=124)]:
            with self.subTest(args=args),self.assertRaises(IncompleteEvidence):self.bind(parse(LINE)[0],**args)
    def test_unknown_malformed_fields(self):
        for line in [LINE+' extra=1',LINE.replace('v0','v1'),LINE.replace('first=1','first=nan'),
                     LINE.replace('last=2','last=inf'),LINE.replace('samples=3','samples=03')]:
            with self.assertRaises(IncompleteEvidence):parse(line)
    def test_count_pid_size_bounds(self):
        for old,new in [('samples=3','samples=65537'),('pid=22','pid=2147483648'),
                        ('owner-pid=11','owner-pid=2147483648'),('candidate-bytes=123','candidate-bytes=9223372036854775808')]:
            with self.assertRaises(IncompleteEvidence):parse(LINE.replace(old,new))
    def test_invalid_and_single_sample_unknown(self):
        invalid=LINE.replace('valid=true','valid=false').replace('first=1','first=none').replace('last=2','last=none')
        for line in [invalid,LINE.replace('samples=3','samples=1')]:
            with self.assertRaises(IncompleteEvidence):self.bind(parse(line)[0])
    def test_reversed_zero_and_invalid_trusted_fields(self):
        for line in [LINE.replace('last=2','last=0'),LINE.replace('samples=3','samples=0'),LINE.replace('valid=true','valid=false')]:
            with self.assertRaises(IncompleteEvidence):parse(line)
    def test_record_limit(self):
        with self.assertRaises(IncompleteEvidence):parse((LINE+'\n')*4097)
    def test_zero_duration_not_live_overlap(self):
        with self.assertRaises(IncompleteEvidence):self.bind(parse(LINE.replace('last=2','last=1'))[0])
if __name__=='__main__':unittest.main()
