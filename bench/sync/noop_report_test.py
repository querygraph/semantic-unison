"""Original in-memory saved-shape examples; no process or benchmark execution."""
import copy
import unittest
from noop_report import samples, summarize, from_saved


def fixture():
    group=dict(pid=20,reaped=True,returncode=0,other_group_members_absent_before_reap=True)
    proxy=dict(fault=None,pump_errors=[],cancellation_signals=[],input_pump_joined=True,
        server_pid=30,server_returncode=0,server_cleanup=dict(reaped=True,returncode=0),
        server_group_binding=dict(observed_before_native_reap=True,native_pid=30,
            native_process_group=20,supervisor_process_group=20,supervisor_pid=20))
    call=dict(returncode=0,timed_out=False,capture_truncated=False,supervisor_capture_truncated=False,client_cleanup=dict(group,pid=10),
              supervisor_cleanup=group,proxy=proxy,wall_seconds=1.,native_client_lifetime_seconds=.9)
    row=dict(label='stock',mode='ordinary',phase='measured',repetition=1,
        exact_result_and_unchanged_basis=True,noop_preserved_receiver_inode=True,
        staging_cleaned=True,noop_sync=call)
    rows=[]
    for i in range(6):
        item=copy.deepcopy(row);item.update(phase='warmup' if i==0 else 'measured',repetition=max(i,1))
        item['noop_sync']['wall_seconds']=float(100 if i==0 else i);rows.append(item)
    return dict(schema='unison-synthetic-sync/0',complete=True,
                parameters=dict(warmups=1,repetitions=5),samples=rows)


class Reports(unittest.TestCase):
    def extract(self, value):
        return samples(value,cohort_label='stock',selection=1,artifact='inert-pinned-record')

    def test_warmup_retained_but_not_used_in_measured_distribution(self):
        report=summarize(self.extract(fixture()))
        self.assertEqual(report['warmup_samples'],1)
        self.assertEqual(report['measured_samples'],5)
        self.assertEqual(report['groups'][0]['median_seconds'],3.)
        self.assertEqual(len(report['raw_samples']),6)
        self.assertFalse(report['resource_release_authorized'])

    def test_failed_or_incomplete_or_changed_noop_refuses(self):
        for action in [lambda j:j.update(complete=False),
                       lambda j:j['samples'][0].update(noop_preserved_receiver_inode=False),
                       lambda j:j['samples'][0]['noop_sync'].update(returncode=1),
                       lambda j:j['samples'][0]['noop_sync']['proxy'].update(input_pump_joined=False),
                       lambda j:j['samples'][0]['noop_sync']['proxy']['server_group_binding'].update(native_process_group=99)]:
            value=fixture();action(value)
            with self.assertRaises(ValueError):self.extract(value)

    def test_boolean_nan_and_negative_times_refuse(self):
        for value in [True,float('nan'),float('inf'),-1.]:
            data=fixture();data['samples'][0]['noop_sync']['wall_seconds']=value
            with self.assertRaises(ValueError):self.extract(data)

    def test_pinned_collection_rejects_changed_or_duplicate_saved_bytes(self):
        import json,hashlib
        raw=json.dumps(fixture()).encode()
        ref=dict(path='/private/tmp/inert-noop/RESULT.json',bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
        saved=dict(schema='unison-auto-cohort-report/1',matrix_complete=False,saved_inputs=[ref])
        index=dict(schema='unison-ten-cohort-actual-closure/1',cohorts=[dict(label='stock',selection=1,workspace='/private/tmp/inert-noop')])
        got=from_saved(json.dumps(saved).encode(),json.dumps(index).encode(),load=lambda path,limit:raw)
        self.assertEqual(got['measured_samples'],5)
        with self.assertRaises(ValueError):
            from_saved(json.dumps(saved).encode(),json.dumps(index).encode(),load=lambda path,limit:raw+b' ')
        saved['saved_inputs'].append(ref)
        with self.assertRaises(ValueError):
            from_saved(json.dumps(saved).encode(),json.dumps(index).encode(),load=lambda path,limit:raw)

    def test_duplicate_or_missing_measured_samples_refuse(self):
        rows=self.extract(fixture())
        with self.assertRaises(ValueError):summarize(rows+[rows[-1]])
        with self.assertRaises(ValueError):summarize(rows[:-1])
        with self.assertRaises(ValueError):summarize(rows[1:])


if __name__=='__main__':unittest.main()
