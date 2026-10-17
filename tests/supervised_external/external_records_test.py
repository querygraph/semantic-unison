"""Original parser controls and saved real logs; zero new external helpers."""
import dataclasses
import hashlib
import json
from pathlib import Path
import unittest

import external_records as records

LINE = ('[external-process] External result v0 pid=42 status=exit:0 outcome=completed '
        'cpu-weight=2 other-members=0 capture-truncated=false')


class Records(unittest.TestCase):
    def test_success_is_historical_immutable_and_not_authority(self):
        r = records.parse('ordinary log\n' + LINE + '\n')[0]
        self.assertEqual((r.pid, r.status, r.cpu_weight, r.other_members), (42, ('exit', 0), 2, 0))
        self.assertFalse(r.producer_authenticated)
        self.assertFalse(r.resource_release_authorized)
        with self.assertRaises(dataclasses.FrozenInstanceError): r.pid = 7
        self.assertEqual(records.parse(LINE.replace('[external-process]', '[server: external-process]'))[0].endpoint, 'server')
    def test_unknown_unobserved_and_absence_stay_distinct(self):
        for value in ('unknown', 'unobserved'):
            r = records.parse(LINE.replace('other-members=0', 'other-members='+value))[0]
            self.assertEqual(r.group_observation, value)
            self.assertIsNone(r.other_members)
        self.assertEqual(records.parse('ordinary External result v0 mention'), [])
        self.assertEqual(len(records.parse(LINE+'\n'+LINE)), 2)  # PID reuse is not inferred away.
    def test_findings_do_not_become_success_or_complete_capture(self):
        r = records.parse(LINE.replace('exit:0', 'exit:7').replace('capture-truncated=false', 'capture-truncated=true'))[0]
        self.assertEqual(r.status, ('exit', 7)); self.assertTrue(r.capture_truncated)
        nochild = LINE.replace('pid=42 status=exit:0 outcome=completed', 'pid=none status=none outcome=failed').replace('other-members=0','other-members=unobserved')
        self.assertIsNone(records.parse(nochild)[0].pid)
    def test_malformed_fields_refuse(self):
        changes = [('v0','v1'), ('pid=42','pid=0'), ('pid=42','pid=2147483648'),
                   ('exit:0','exit:256'), ('exit:0','exit:-1'), ('exit:0','signal:-0'),
                   ('exit:0','signal:2147483648'), ('status=exit:0','status=none'),
                   ('pid=42','pid=none'), ('cpu-weight=2','cpu-weight=0'),
                   ('cpu-weight=2','cpu-weight=02'), ('cpu-weight=2','cpu-weight=9223372036854775808'),
                   ('other-members=0','other-members=00'), ('other-members=0','other-members=-1'),
                   ('other-members=0','other-members=2147483648'), ('capture-truncated=false','capture-truncated=0')]
        for old,new in changes:
            with self.subTest(new=new), self.assertRaises(ValueError): records.parse(LINE.replace(old,new))
        with self.assertRaises(ValueError): records.parse(LINE+' extra-field')
    def test_limits_and_encoding(self):
        for value in (None, 'x'*(records.MAX_LOG_BYTES+1), 'é'*(records.MAX_LOG_BYTES//2+1),
                      '[external-process] '+'x'*513, '\n'.join([LINE]*4097), '\ud800'):
            with self.subTest(kind=type(value)), self.assertRaises(ValueError): records.parse(value)
    def test_saved_real_stock_and_ox_helper_records(self):
        q = json.loads((Path(__file__).resolve().parents[1]/'qualification/external-process-current-interface-actual-20261016.json').read_text())
        seen = []
        for row in q['rows']:
            report = row['report']
            for case in ('observed', 'exiftool-readonly'):
                command = next(c for c in report['commands'] if c['cwd'].endswith('/'+case))
                raw = Path(command['log']).read_bytes()
                self.assertEqual(hashlib.sha256(raw).hexdigest(), command['log_sha256'])
                parsed = records.parse(raw.decode()); self.assertEqual(len(parsed), 1)
                expected = next(r for r in report['observed_helpers'] if r['case']==case)
                self.assertEqual((parsed[0].pid, parsed[0].status, parsed[0].other_members),
                                 (expected['pid'], tuple(expected['status']), expected['other_members']))
                self.assertEqual(parsed[0].cpu_weight, 1)
                if case=='observed':
                    self.assertEqual(parsed[0].pid, int((Path(command['cwd'])/'helper.pid').read_text()))
                seen.append(parsed[0])
        self.assertEqual(len(seen), 4)


if __name__ == '__main__': unittest.main()
