import copy,unittest
from archive_roundtrip_contract import fixture,stage,verify,STAGES

class Contract(unittest.TestCase):
    def values(self,index):
        r=stage(index);archive={'client':{'arA':'a'*64},'server':{'arB':'b'*64}}
        return dict(returncode=1 if index==5 else 0,
            log='no saved common base is available' if index==5 else ('Built-in DNG scalar merge verified' if r['expected_merge'] else ''),
            left=fixture('4','Gold') if index==5 else r['expected'],right=fixture('3','Rose') if index==5 else r['expected'],
            archives_before=copy.deepcopy(archive),archives_after=copy.deepcopy(archive),target_before={'inode':1},target_after={'inode':1})
    def test_all_ten_ordered_stage_contracts(self):
        self.assertEqual(len(STAGES),10)
        for i in range(10):
            r=verify(i,**self.values(i));self.assertFalse(r['process_or_resource_closure_proved'])
        self.assertEqual(stage(6)['writes'],{'left':fixture('3','Gold'),'right':fixture('3','Gold')})
        self.assertEqual([i for i in range(10) if stage(i)['generation']=='baseline'],[2,3])
    def test_fixture_is_fixed_size_and_only_xmp_changes(self):
        a=fixture();b=fixture('5','Rose');self.assertEqual(len(a),65536)
        self.assertEqual(a[:1024],b[:1024]);self.assertEqual(a[9216:],b[9216:]);self.assertNotEqual(a[1024:9216],b[1024:9216])
    def test_archive_reset_and_baseline_rebuild_refuse(self):
        for mutation in ('empty','rename','rebuild','mismatch'):
            v=self.values(2)
            if mutation=='empty':v['archives_after']['server']={}
            elif mutation=='rename':v['archives_after']['client']={'arNEW':'c'*64}
            else:v['log']='No archive files were found' if mutation=='rebuild' else 'Archive format mismatch'
            with self.assertRaises(ValueError):verify(2,**v)
    def test_arbitrary_exit_signal_or_wrong_refusal_cannot_pass(self):
        for code in (0,3,70,-15,True):
            v=self.values(5);v['returncode']=code
            with self.assertRaises(ValueError):verify(5,**v)
        for text in ('ordinary error','Uncaught unix error: no saved common base is available'):
            v=self.values(5);v['log']=text
            with self.assertRaises(ValueError):verify(5,**v)
    def test_refusal_preserves_both_edits_and_noop_preserves_identity(self):
        v=self.values(5);v['right']=v['left']
        with self.assertRaises(ValueError):verify(5,**v)
        for i in (2,9):
            v=self.values(i);v['target_after']={'inode':2}
            with self.assertRaises(ValueError):verify(i,**v)
    def test_merge_marker_and_exact_payload_are_required(self):
        for i in (1,8):
            v=self.values(i);v['log']=''
            with self.assertRaises(ValueError):verify(i,**v)
            v=self.values(i);v['left']=v['left'][:-1]+b'!'
            with self.assertRaises(ValueError):verify(i,**v)
        for i in (True,-1,10):
            with self.assertRaises(ValueError):stage(i)

if __name__=='__main__':unittest.main()
