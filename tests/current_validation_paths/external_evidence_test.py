"""Fabricated external owner diagnostics, never real child settlement."""
import unittest
from current_validation_paths.external_evidence import audit
LINE='[external-process] External result v0 pid=201 status=exit:0 outcome=completed cpu-weight=1 other-members=0 capture-truncated=false\n'
ENTRY=dict(endpoint='client',pid=201,fixture_pid=202,kind='merge')

class External(unittest.TestCase):
    def test_shell_group_and_original_fixture_pid_can_differ(self):
        value=audit(LINE,[ENTRY],{101,102,103});self.assertEqual(value[0]['actual_status'],['exit',0])
        self.assertFalse(value[0]['resource_release_authorized'])
    def test_unknown_failed_or_incomplete_external_child_refuses(self):
        for old,new in [('status=exit:0','status=exit:1'),('outcome=completed','outcome=timed-out'),
            ('other-members=0','other-members=unknown'),('other-members=0','other-members=1'),
            ('cpu-weight=1','cpu-weight=2'),('capture-truncated=false','capture-truncated=true')]:
            with self.subTest(new=new),self.assertRaises(ValueError):audit(LINE.replace(old,new),[ENTRY],{101,102,103})
    def test_missing_extra_duplicate_or_wrong_endpoint_refuses(self):
        for log,expected in [('',[ENTRY]),(LINE,[]),(LINE*2,[ENTRY,ENTRY]),(LINE.replace('[external-process]','[server: external-process]'),[ENTRY])]:
            with self.subTest(log=log),self.assertRaises(ValueError):audit(log,expected,{101,102,103})
    def test_counters_cannot_alias_transport_owner_or_hide_typed_identity(self):
        for key,value in [('pid',101),('pid',True),('fixture_pid',103),('fixture_pid',False)]:
            entry=dict(ENTRY);entry[key]=value
            with self.subTest(key=key,value=value),self.assertRaises(ValueError):audit(LINE,[entry],{101,102,103})
    def test_no_external_expected_still_rejects_malformed_external_trace(self):
        self.assertEqual(audit('ordinary diagnostics',[],{101}),[])
        with self.assertRaises(ValueError):audit('[external-process] unknown record',[],{101})

if __name__=='__main__':unittest.main()
