import copy,unittest
from pathlib import Path
from final_worker_state_owner import audit_calls,command_check,driver_source,Temporary


def fixture():
    expected=[];calls=[]
    for label in ('stock','ox'):
        base='/private/tmp/owned/'+label
        for argv in ([label+'-compiler','components.ml'],[base+'/components'],[label+'-compiler','late_cancel.ml'],[base+'/late_cancel'],[label+'-compiler','-c','probe.c'],[label+'-compiler','restored_mutation.ml'],[base+'/restored_mutation']):
            expected.append(argv)
            log='original component checks\n'
            if Path(argv[0]).name=='late_cancel':log='\n'.join('PASS completed-before-owner '+m+': settled' for m in ('success','cancel','shutdown'))
            if Path(argv[0]).name=='restored_mutation':log='PASS active worker same-size mutation with exact restored native mtime refused; callerFD/accounting settled'
            calls.append(dict(command=argv,returncode=0,timed_out=False,capture_truncated=False,stdout=log,stderr='',aggregate_or_parent_terminal_proved=False,io_cpu_release_authorized=False,client_cleanup=dict(pid=1000+len(calls),returncode=0,reaped=True,other_group_members_absent_before_reap=True,group_cleanup_before_leader_reap=True,hard_kill_required=False)))
    return calls,expected


class Controls(unittest.TestCase):
    def test_two_compilers_exact_fourteen_calls(self):
        calls,expected=fixture();r=audit_calls(calls,expected)
        self.assertEqual((r['calls'],len(r['summaries'])),(14,6))
    def test_partial_reordered_or_extra_calls_never_pass(self):
        calls,expected=fixture()
        for changed in (calls[:-1],calls+[calls[0]],calls[1:]+calls[:1]):
            with self.assertRaises(ValueError):audit_calls(changed,expected)
    def test_missing_actual_settlement_capture_or_failure_refuses(self):
        for field in ('reaped','other_group_members_absent_before_reap','group_cleanup_before_leader_reap'):
            calls,expected=fixture();calls[0]['client_cleanup'][field]=False
            with self.assertRaises(ValueError):audit_calls(calls,expected)
        for field,value in (('returncode',1),('timed_out',True),('capture_truncated',True)):
            calls,expected=fixture();calls[0][field]=value
            with self.assertRaises(ValueError):audit_calls(calls,expected)
    def test_duplicate_invalid_pid_or_invented_authority_refuses(self):
        for pid in (True,0,-1,2**31,'1000',1000):
            calls,expected=fixture();calls[1]['client_cleanup']['pid']=pid
            with self.assertRaises(ValueError):audit_calls(calls,expected)
        for field in ('aggregate_or_parent_terminal_proved','io_cpu_release_authorized'):
            calls,expected=fixture();calls[0][field]=True
            with self.assertRaises(ValueError):audit_calls(calls,expected)
    def test_missing_late_mode_or_mutation_assertion_refuses(self):
        for index in (3,6,10,13):
            calls,expected=fixture();calls[index]['stdout']='PASS unrelated case'
            with self.assertRaises(ValueError):audit_calls(calls,expected)
    def test_driver_binding_only_removes_two_exact_imports(self):
        original='import tempfile\nfrom shared_child import invoke\n# original fixture\ninvoke(original_argv, env, deadline)\n'
        self.assertEqual(driver_source(original),'# original fixture\ninvoke(original_argv, env, deadline)\n')
        for bad in (original.replace('import tempfile\n',''),original+'import tempfile\n'):
            with self.assertRaises(ValueError):driver_source(bad)
    def test_temp_binding_single_exact_directory_and_no_fallback(self):
        class Target:
            def __init__(self):self.created=0
            def mkdir(self,mode):self.created+=1;assert mode==0o700
            def __str__(self):return '/private/tmp/owned/original'
        path=Target();temporary=Temporary(path)
        with self.assertRaises(ValueError):temporary.mkdtemp(prefix='different',dir='/private/tmp')
        self.assertEqual(path.created,0)
        self.assertEqual(temporary.mkdtemp(prefix='unison-component-worker-controls-',dir='/private/tmp'),str(path))
        with self.assertRaises(ValueError):temporary.mkdtemp(prefix='unison-component-worker-controls-',dir='/private/tmp')
        self.assertEqual(path.created,1)
    def test_command_binding_has_no_dynamic_or_extra_child(self):
        command_check(['compiler','source'],['compiler','source'])
        for command in (('compiler','source'),['compiler','different'],['compiler',True],['compiler','source','extra']):
            with self.assertRaises(ValueError):command_check(command,['compiler','source'])

if __name__=='__main__':unittest.main()
