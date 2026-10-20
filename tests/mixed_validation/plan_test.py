"""Pure plan mutation controls; no pool, media or SDK access."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import copy
import unittest
from mixed_validation.plan import commands,LIMITS,SCHEMA,TARGET


def artifact(name,size=32):return dict(path='/private/tmp/prepared/'+name,sha256='a'*64,bytes=size)
def fixture():
    return dict(schema=SCHEMA,target=TARGET,workspace='/private/tmp/unison-mixed-control',
                probes=[dict(label=label,executable=artifact(label),build_receipt=artifact(label+'.json'))
                        for label in ('stock','ox')],
                sdk=dict(executable=artifact('sdk'),manifest=artifact('sdk.json'),build_id='unison-sdk171-2724-v1-single'),
                metadata=dict(executable=artifact('exiftool'),version='13.59',inventory=artifact('metadata-inventory.json')),
                input=artifact('uncompressed-original.dng',4096),
                input_epoch=dict(st_dev=1,st_ino=2,st_size=4096,st_mtime_ns=3,st_ctime_ns=4,
                                 st_mode=0o100644,st_nlink=1,st_uid=501),
                ancestry=[artifact('ancestry.json')],source_pins=[artifact('worker.py')],limits=copy.deepcopy(LIMITS))


class Plan(unittest.TestCase):
    def test_exact_commands_without_mutation(self):
        p=fixture();before=copy.deepcopy(p);argv=commands(p)
        self.assertEqual(p,before);self.assertEqual(len(argv),2)
        self.assertEqual(argv[0][3],p['workspace']+'/stock/uncompressed.dng')
        self.assertEqual(argv[1][3],p['workspace']+'/ox/uncompressed.dng')
        self.assertEqual(argv[0][4:],['a'*64,'unison-sdk171-2724-v1-single','a'*64,'4096'])

    def test_no_limit_expansion_or_bool_numeric_alias(self):
        for key,value in [('cpu_credits',18),('cpu_credits',True),('probes',True),
                          ('helper_seconds',90),('backend_payload_bytes',1),
                          ('physical_io_budget_enforced',0),('token_indexes',[False,1,2,3,4,5,6,7])]:
            p=fixture();p['limits'][key]=value
            with self.subTest(key=key,value=value),self.assertRaises(ValueError):commands(p)

    def test_reorder_alias_or_unqualified_sdk(self):
        for mode in ('order','alias','sdk','version','epoch','size','link','unknown'):
            p=fixture()
            if mode=='order':p['probes'].reverse()
            elif mode=='alias':p['probes'][1]['executable']=p['probes'][0]['executable']
            elif mode=='sdk':p['sdk']['build_id']='experimental'
            elif mode=='version':p['metadata']['version']=13.1
            elif mode=='epoch':p['input_epoch']['st_ino']=True
            elif mode=='size':p['input_epoch']['st_size']+=1
            elif mode=='link':p['input_epoch']['st_nlink']=2
            else:p['runtime_granted']=True
            with self.subTest(mode=mode),self.assertRaises(ValueError):commands(p)

    def test_path_and_inventory_refusals(self):
        for value in ('relative','/private/tmp/a/../b','/private//tmp/x','/private/tmp/x\0'):
            p=fixture();p['input']['path']=value
            with self.subTest(path=value),self.assertRaises(ValueError):commands(p)
        p=fixture();p['source_pins']*=2
        with self.assertRaises(ValueError):commands(p)
        p=fixture();p['sdk']['executable']['path']=p['workspace']+'/late-sdk'
        with self.assertRaises(ValueError):commands(p)
        p=fixture();p['input']['sha256']='not a hash'
        with self.assertRaises(ValueError):commands(p)

    def test_worker_consumes_derived_commands_and_plan_headroom(self):
        from worker import execute_plan
        p=fixture();launched=[];saved=[]
        def invoke(index,command,deadline):
            launched.append(command);return {'index':index}
        result=execute_plan(p,deadline=1000,clock=lambda:0,
                            prepare=lambda *a:None,invoke=invoke,persist=saved.append,
                            check_sources=lambda:None,verify_input=lambda *a:None,
                            inspect=lambda *a,**k:dict(functional_status='PASSED'))
        self.assertTrue(result['complete']);self.assertEqual(launched,commands(p))
        with self.assertRaises(TimeoutError):
            execute_plan(p,deadline=119,clock=lambda:0,prepare=lambda *a:None,
                         invoke=invoke,persist=saved.append,check_sources=lambda:None,
                         verify_input=lambda *a:None)
        self.assertEqual(len(launched),2)


if __name__=='__main__':unittest.main()
