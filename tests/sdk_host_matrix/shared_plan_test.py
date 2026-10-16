"""Original inert command metadata only; never opens fixture/tool paths."""
import copy,unittest
from shared_plan import shared_matrix,REFERENCE,EXPERIMENTAL
class Shared(unittest.TestCase):
    def values(self):
        return (dict(executable='/not-opened/reference',build_id=REFERENCE),
                dict(executable='/not-opened/experimental',build_id=EXPERIMENTAL),
                [dict(codec=c,path='/not-opened/'+c,sha256='a'*64,size=100) for c in ['uncompressed','jpeg','jxl']],1073741824)
    def test_exact_three_codecs_twelve_calls_and_thread_budgets(self):
        p=shared_matrix(*self.values());self.assertEqual(len(p['cases']),12)
        for codec in ['uncompressed','jpeg','jxl']:
            cases=[c for c in p['cases'] if c['codec']==codec]
            self.assertEqual([c['threads_including_caller'] for c in cases],[1,1,2,6])
            self.assertEqual([c['backend'] for c in cases],['reference']+['experimental']*3)
        for c in p['cases']:
            self.assertLessEqual(c['threads_including_caller']+c['owner_cpu_credits'],8)
            self.assertEqual(c['command'][c['command'].index('--threads')+1],str(c['threads_including_caller']))
    def test_reference_protocol_and_experimental_memory_separated(self):
        for c in shared_matrix(*self.values())['cases']:
            if c['backend']=='reference':
                self.assertEqual(c['command'][1],'--unison-dng-validation-v1')
                self.assertNotIn('--host-memory-bytes',c['command'])
            else:
                self.assertEqual(c['command'][1],'--unison-dng-validation-area-memory-source-v0')
                self.assertIn('--host-memory-bytes',c['command'])
    def test_original_metadata_not_modified(self):
        args=self.values();before=copy.deepcopy(args);shared_matrix(*args);self.assertEqual(args,before)
    def test_no_runtime_or_hard_cap_claim(self):
        p=shared_matrix(*self.values())
        for k in ['runtime_admitted','runtime_qualified','hard_os_thread_cap','rss_cap','old_18_credit_plan_modified']:self.assertIs(p[k],False)
        self.assertTrue(p['requires_fresh_owned_executor']);self.assertEqual(p['limits']['token_indexes'],list(range(8)))
    def test_wrong_tool_domains_refused(self):
        for index in [0,1]:
            args=list(self.values());args[index]['build_id']='wrong'
            with self.assertRaises(ValueError):shared_matrix(*args)
    def test_existing_codec_and_memory_bounds_preserved(self):
        args=list(self.values());args[2]=args[2][:2]
        with self.assertRaises(ValueError):shared_matrix(*args)
        for value in [True,0,-1,2**63]:
            args=list(self.values());args[3]=value
            with self.assertRaises(ValueError):shared_matrix(*args)
if __name__=='__main__':unittest.main()
