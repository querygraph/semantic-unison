"""Original fake records only; no IO pool, executable or actual receiving run."""
import copy
import itertools
import unittest
from layout_receiving_result_audit import audit

PROFILE='org.firstpair.dng-layout/0'
command=['/python','/r/bench/sync/run.py','--shared-qualification','--layout-only-controls','--packet-bytes','256']
for label,letter in [('stock','a'),('ox','b')]:
    command += ['--binary',label+'=/'+label,'--compiler',label+'=/compiler-'+label,
                '--expected-binary-sha256',label+'='+letter*64,
                '--expected-compiler-sha256',label+'='+'c'*64]
request={'schema':'unison-layout-only-receiving-request/1','admission_fields':{
    'target':'sync-functional','cpu_credits':8,'command':command,
    'execution_source_sha256':{'/r/bench/sync/run.py':'0'*64}}}
owner={'pid':42,'reaped':True,'returncode':0,'cancel_reason':None,
       'group_cleanup_before_leader_reap':True,'other_group_members_absent_before_reap':True}
result={'schema':'unison-synthetic-sync/0','complete':True,'purpose':'finite shared-harness qualification',
        'parameters':{'workers':[1,2,3],'warmups':0,'repetitions':1,
            'modes':['ordinary','receiver-clone','semantic'],'loopback_cpu_credit_bound':8,
            'orchestration_cpu_credits':2,'maximum_declared_cpu_credit_sum':8,'file_mib':2,'files':2,
            'layout_only_controls':True,'packet_bytes':256},'samples':[],
        'binaries':{},'compilers':{},'admitted_binary_sha256':{},'admitted_compiler_sha256':{},
        'runner_sha256':{'run.py':'0'*64}}
for label,letter in [('stock','a'),('ox','b')]:
    result['binaries'][label]={'path':'/'+label,'sha256':letter*64}
    result['compilers'][label]={'path':'/compiler-'+label}
    result['admitted_binary_sha256'][label]=letter*64
    result['admitted_compiler_sha256'][label]='c'*64
for label,mode,worker in itertools.product(('stock','ox'),('ordinary','receiver-clone','semantic'),(1,2,3)):
    call={'command':['/'+label],'returncode':0,'timed_out':False,'capture_truncated':False,
          'supervisor_capture_truncated':False,'client_cleanup':owner,'supervisor_cleanup':owner,
          'stdout':'','stderr':'','supervisor_output':'','proxy':{'server_cleanup':owner,
            'server_pid':42,'server_returncode':0,'fault':None,'pump_errors':[],'input_pump_joined':True}}
    sample={'label':label,'mode':mode,'workers':worker,'phase':'measured','repetition':1,
            'exact_result_and_unchanged_basis':True,'noop_preserved_receiver_inode':True,
            'staging_cleaned':True,'private_fixture_removed':True,
            'fixtures':[{'name':f'image-{index:04d}.dng','size_bytes':2097152,'packet_offset':1024,
                         'packet_bytes':256,'layout_only':True,'opaque_private_extent':[256,128],
                         'opaque_xmp_references':[256,78]} for index in range(2)],
            **{stage:copy.deepcopy(call) for stage in ('seed_sync','update_sync','noop_sync')}}
    if mode=='semantic':
        sample['update_sync']['stdout']=(f'Remote semantic clone wrote 256 logical metadata bytes in 1 write calls (256 payload bytes; 4096-byte comparison windows; {PROFILE})\n')*2
        sample['counters']={'semantic_profiles':[PROFILE],'semantic_updates':2,
            'semantic_logical_write_bytes':512,'semantic_write_attempts':2,
            'semantic_payload_bytes':512,'semantic_comparison_windows':[4096]}
    result['samples'].append(sample)

class Controls(unittest.TestCase):
    def test_positive(self):
        self.assertEqual(audit(result,request)['semantic_rows'],6)
    def test_frozen_runner_default_packet_size(self):
        expected=copy.deepcopy(request)
        expected['admission_fields']['command'].remove('--packet-bytes')
        expected['admission_fields']['command'].remove('256')
        changed=copy.deepcopy(result);changed['parameters']['packet_bytes']=8192
        for sample in changed['samples']:
            for item in sample['fixtures']:item['packet_bytes']=8192
            if sample['mode']=='semantic':
                sample['update_sync']['stdout']=sample['update_sync']['stdout'].replace(
                    '256 logical','3072 logical').replace('256 payload','8192 payload')
                sample['counters'].update(semantic_logical_write_bytes=6144,semantic_payload_bytes=16384)
        self.assertEqual(audit(changed,expected)['semantic_rows'],6)
    def test_canonical_path_names_are_observations(self):
        changed=copy.deepcopy(result)
        changed['binaries']['stock']['path']='/private/stock'
        changed['compilers']['stock']['path']='/compiler-stock.opt'
        for sample in changed['samples']:
            if sample['label']=='stock':
                for stage in ('seed_sync','update_sync','noop_sync'):
                    sample[stage]['command'][0]='/private/stock'
        report=audit(changed,request)
        self.assertEqual(report['artifact_path_observations']['stock']['requested_binary'],'/stock')
        self.assertEqual(report['artifact_path_observations']['stock']['observed_binary'],'/private/stock')
    def test_mutations(self):
        changes=[
            lambda r:r['parameters'].update(layout_only_controls=False),
            lambda r:r['parameters'].update(layout_only_controls=1),
            lambda r:r['parameters'].update(property_removal_controls=True),
            lambda r:r['parameters'].update(packet_bytes=512),
            lambda r:r['admitted_binary_sha256'].update(stock='f'*64),
            lambda r:r['binaries']['ox'].update(path='/other'),
            lambda r:r['compilers']['ox'].update(path='relative'),
            lambda r:r['runner_sha256'].clear(),
            lambda r:r['samples'][0]['fixtures'][0].update(packet_offset=0),
            lambda r:r['samples'][0]['seed_sync'].update(command=['/other']),
            lambda r:next(s for s in r['samples'] if s['mode']=='semantic')['counters'].update(semantic_logical_write_bytes=1),
            lambda r:next(s for s in r['samples'] if s['mode']=='semantic')['update_sync'].update(stdout=''),
            lambda r:next(s for s in r['samples'] if s['mode']=='semantic')['update_sync'].update(
                stdout=next(s for s in r['samples'] if s['mode']=='semantic')['update_sync']['stdout'].replace(PROFILE,'org.firstpair.dng-xmp/1')),
        ]
        for mutate in changes:
            with self.subTest(mutate=mutate):
                changed=copy.deepcopy(result);mutate(changed)
                with self.assertRaises((ValueError,AssertionError)):audit(changed,request)

if __name__=='__main__':unittest.main()
