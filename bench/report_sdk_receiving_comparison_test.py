from pathlib import Path
import sys
import unittest
import tempfile
import json
import hashlib
from unittest.mock import patch
sys.path[:0]=[str(Path(__file__).resolve().parents[1]/'tests'),str(Path(__file__).resolve().parents[1]/'tests/sdk_multifile')]
from report_sdk_receiving_comparison import summarize,markdown,read_receipt,main
from sdk_throughput.audit_test import fixture


class Report(unittest.TestCase):
    def test_complete_audited_samples_and_ratios(self):
        r,p,raw=fixture();d=summarize(r,p,raw_proxy_receipts=raw)
        self.assertTrue(d['complete']);self.assertEqual(len(d['attempted_rows']),24)
        self.assertEqual([g['measured_count'] for g in d['groups']],[5]*4)
        self.assertTrue(all(x['comparable_complete_cohorts'] for x in d['ratios']))
        self.assertFalse(d['resource_release_authorized']);self.assertIn('not isolated SDK decode',markdown(d))
    def test_failed_prefix_preserves_rows_and_never_computes_ratio(self):
        r,p,raw=fixture(7,False);d=summarize(r,p,raw_proxy_receipts=raw)
        self.assertEqual(d['attempted_cli_calls'],7);self.assertTrue(d['raw_failed_prefix_preserved'])
        self.assertTrue(all(x['observed_median_ratio_worker1_over_worker3'] is None for x in d['ratios']))
        self.assertEqual(sum(g['measured_count'] for g in d['groups']),3)
    def test_large_receipt_and_hash_binding(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'result.json';raw=json.dumps({'large':'x'*70000}).encode();p.write_bytes(raw)
            value,pin=read_receipt(p,hashlib.sha256(raw).hexdigest())
            self.assertEqual(len(value['large']),70000);self.assertEqual(pin['bytes'],len(raw))
            with self.assertRaises(ValueError):read_receipt(p,'0'*64)
    def test_close_uncertainty_is_not_an_ordinary_report_failure(self):
        from shared_cpu_pool import UnresolvedOwnership
        import os
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'receipt.json';p.write_text('{}');actual_close=os.close;seen=[]
            def fail(fd):seen.append(fd);raise OSError('injected close')
            with patch('private_camera_receiving.close.os.close',side_effect=fail):
                with self.assertRaises(UnresolvedOwnership) as caught:read_receipt(p)
            self.assertEqual(len(seen),1)
            self.assertEqual(caught.exception.uncertain_closes[0]['fd'],seen[0])
            actual_close(seen[0]) # disposable injection proves the close did not occur
    def test_report_entry_reaudits_full_receipts_and_writes_once(self):
        from sdk_throughput.plan import comparison
        r,p,proxies=fixture()
        with tempfile.TemporaryDirectory() as d:
            workspace=str(Path(d)/'cases');old=p['workspace']
            def relocate(value):
                if isinstance(value,str):return value.replace(old,workspace)
                if isinstance(value,list):return [relocate(x) for x in value]
                if isinstance(value,dict):return {k:relocate(v) for k,v in value.items()}
                return value
            r,p,proxies=map(relocate,(r,p,proxies))
            for row,proxy in zip(comparison(p['binaries'],p['tool'],workspace)['rows'],proxies):
                directory=Path(row['directory']);directory.mkdir(parents=True)
                (directory/'seed-proxy.json').write_text(json.dumps(proxy))
            argv=[]
            for name,value in [('plan',p),('result',r)]:
                path=Path(d)/(name+'.json');raw=json.dumps(value).encode();path.write_bytes(raw)
                argv+=['--'+name,str(path),'--'+name+'-sha256',hashlib.sha256(raw).hexdigest()]
            destination=Path(d)/'report';argv+=['--report-dir',str(destination)]
            main(argv)
            report=json.loads((destination/'sdk-receiving-comparison.json').read_text())
            self.assertEqual(report['sdk_helpers_settled'],48)
            self.assertEqual(len(report['inputs']),26)
            self.assertEqual(report['attempted_cli_calls'],24)
            self.assertTrue((destination/'sdk-receiving-comparison.md').exists())
            with self.assertRaises(FileExistsError):main(argv)
    def test_receipt_rejects_duplicate_keys_symlink_and_oversize(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'receipt.json';p.write_text('{"same":1,"same":2}')
            with self.assertRaises(ValueError):read_receipt(p)
            link=Path(d)/'link';link.symlink_to(p)
            with self.assertRaises(OSError):read_receipt(link)
            with p.open('wb') as stream:stream.truncate(16*1048576+1)
            with self.assertRaises(ValueError):read_receipt(p)
    def test_unknown_receipt_refuses_before_statistics(self):
        r,p,raw=fixture();r['invocations'][0]['state']='INTENT'
        with self.assertRaises(ValueError):summarize(r,p,raw_proxy_receipts=raw)


if __name__=='__main__':unittest.main()
