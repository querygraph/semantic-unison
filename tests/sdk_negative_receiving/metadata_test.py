"""Original metadata reader doubles forbid every media/artifact open."""
import copy
import hashlib
import json
from types import SimpleNamespace
import unittest
from sdk_negative_receiving import metadata
from sdk_negative_receiving.admission_test import fixture,EXECUTION,PRODUCTION

class Metadata(unittest.TestCase):
    def prepare(self,mutation=None):
        packet,*_=fixture();files={};self.reads=[];self.observations=[]
        def put(path,value):
            data=(json.dumps(value,sort_keys=True)+'\n').encode();files[path]=data
            return hashlib.sha256(data).hexdigest()
        for inventory in (packet['execution_sha256'],packet['production_sha256']):
            for name in inventory:
                data=('original source '+name).encode();files[packet['repository']+'/'+name]=data
                inventory[name]=hashlib.sha256(data).hexdigest()
        ancestry=dict(path='/private/tmp/generation.json',sha256=put('/private/tmp/generation.json',dict(original=True)))
        packet['prerequisite_sha256'][ancestry['path']]=ancestry['sha256']
        declarations={packet['input_manifest']['path']:dict(schema='unison-current-sdk-merge-inputs/1',
            cases=copy.deepcopy(packet['cases']),ancestry=[ancestry]),
            packet['sdk_manifest']['path']:dict(executable=packet['tool']['path'],
                executable_sha256=packet['tool']['sha256'],build_id=packet['tool']['build_id'],threads=1)}
        for label in ('stock','ox'):
            build=packet['builds'][label]
            declarations[build['receipt']['path']]=dict(complete=True,selftest_requested=True,
                build_exit=0,selftest_exit=0,binary=packet['binaries'][label]['path'],
                compiler=build['compiler']['path'],binary_sha256=packet['binaries'][label]['sha256'],
                compiler_sha256=build['compiler']['sha256'],source_sha256=copy.deepcopy(packet['production_sha256']))
        if mutation=='manifest':declarations[packet['input_manifest']['path']]['cases'][0]['xmp_size']=12
        if mutation=='sdk':declarations[packet['sdk_manifest']['path']]['threads']=2
        if mutation=='build':declarations[packet['builds']['stock']['receipt']['path']]['build_exit']=True
        if mutation=='compiled':declarations[packet['builds']['ox']['receipt']['path']]['source_sha256'][PRODUCTION[0]]='0'*64
        for name,value in declarations.items():packet['prerequisite_sha256'][name]=put(name,value)
        for ref in [packet['input_manifest'],packet['sdk_manifest']]+[b['receipt'] for b in packet['builds'].values()]:
            ref['sha256']=packet['prerequisite_sha256'][ref['path']]
        plan_ref=dict(path='/private/tmp/current-plan.json',sha256=put('/private/tmp/current-plan.json',packet))
        if mutation=='source':files[packet['repository']+'/'+EXECUTION[0]]=b'changed'
        def read(path,limit):
            self.reads.append(path)
            if path not in files:raise AssertionError('payload/artifact open forbidden: '+str(path))
            self.assertLessEqual(len(files[path]),limit)
            return files[path]
        def observe(name):
            self.observations.append(name);value=dict(packet['source_observations'][name])
            if mutation=='epoch':value['st_mtime_ns']+=1
            return SimpleNamespace(**value)
        return plan_ref,read,observe,packet

    def check(self,mutation=None):
        ref,read,observe,packet=self.prepare(mutation)
        return metadata.checked(ref,execution_sources=EXECUTION,production_sources=PRODUCTION,
            expected_uid=501,read=read,observe=observe)

    def test_all_metadata_bound_without_opening_any_artifact_or_dng(self):
        packet,contract,proof=self.check()
        self.assertEqual(proof['input_metadata_fences'],12)
        self.assertFalse(proof['input_payload_opened']);self.assertFalse(proof['execution_artifacts_opened'])
        self.assertFalse(proof['runtime_admitted']);self.assertEqual(len(self.observations),12)
        self.assertFalse(set(self.observations).intersection(self.reads))
        self.assertEqual(len(contract['rows']),12)

    def test_source_manifest_sdk_build_and_input_fence_changes_refuse(self):
        for mutation in ('source','manifest','sdk','build','compiled','epoch'):
            with self.subTest(mutation=mutation),self.assertRaises(ValueError):self.check(mutation)

if __name__=='__main__':unittest.main()
