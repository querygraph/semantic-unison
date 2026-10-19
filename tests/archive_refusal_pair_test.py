import json,unittest
from unittest.mock import patch
from batch_artifacts_test import MemoryStore
from batch_transport_test import pending
from batch_transport import Call
from batch_artifacts import publish
import archive_refusal_pair as A


def evidence(mutate=lambda x:None):
    store=MemoryStore();pins={}
    for role,pid,code in [('client',42,1),('proxy',43,0)]:
        p=pending(code);out=p.finish(1);out['command']=[role];out['client_cleanup']['pid']=pid;p.owner.pid=pid
        raw=b'no saved common base is available' if role=='client' else b''
        p.capture_owners[0].chunks=[raw];p.capture_owners[0].total=len(raw)
        pins[role]=A.finish(Call(p,[role],store,role),1,store,[role],(1,2) if role=='client' else (0,))
    frame=dict(schema='unison-retained-merge-proxy/1',server_command=['server'],server_pid=44,server_returncode=0,
        server_reaped=True,server_group=43,input_eof_forwarded=True,output_eof_forwarded=True,
        forwarded_protocol_bytes=dict(client_to_server_bytes=1,server_to_client_bytes=2),
        parent_group_audit_required=True,sdk_helper_audit_required=True,resource_release_authorized=False)
    mutate(frame);pins['server_frame']=publish(store,'frame',json.dumps(frame).encode())
    return store,pins

class Refusal(unittest.TestCase):
    def test_exact_normal_negative_proves_closure_but_never_release(self):
        store,pins=evidence();r=A.audit(store,pins,client_command=['client'],proxy_command=['proxy'],server_command=['server'])
        self.assertEqual(r['client_exit'],1);self.assertFalse(r['resource_release_authorized'])
    def test_zero_only_default_audit_still_rejects_negative(self):
        from batch_transport import restore
        store,pins=evidence()
        with self.assertRaises(ValueError):restore(store,pins['client'],['client'])
    def test_wrong_exit_and_missing_group_proof_refuse(self):
        for code in (0,3,-15,True):
            s,p=evidence()
            with self.assertRaises(ValueError):A.child(s,p['client'],['client'],(code,))
        s,p=evidence()
        # Re-publish a separate record with incomplete actual cleanup.
        v=s.read_json(p['client']['name'],expected_sha256=p['client']['sha256']);v['outcome']['client_cleanup']['reaped']=False
        pin=s.write('bad.json',v)
        with self.assertRaises(ValueError):A.child(s,pin,['client'],(1,2))
    def test_server_identity_signal_and_eof_refuse(self):
        for mutation in (lambda f:f.update(server_pid=42),lambda f:f.update(server_returncode=-15),lambda f:f.update(server_returncode=True),lambda f:f.update(server_reaped=False),lambda f:f.update(input_eof_forwarded=False)):
            s,p=evidence(mutation)
            with self.assertRaises(ValueError):A.audit(s,p,client_command=['client'],proxy_command=['proxy'],server_command=['server'])
    def test_uncertainty_or_partial_capture_not_reclassified(self):
        p=pending(1);s=MemoryStore();p.capture_owners[0].error=OSError('uncertain capture')
        c=Call(p,['never-execute'],s,'bad')
        with self.assertRaises(ValueError):A.finish(c,1,s,['never-execute'],(1,2))
        self.assertIsNone(c.record)
        marker=RuntimeError('original retained unknown');p=pending()
        def fail(d):raise marker
        p.finish=fail;c=Call(p,['never-execute'],s,'unknown')
        with self.assertRaises(RuntimeError) as got:A.finish(c,1,s,['never-execute'],(1,2))
        self.assertIs(got.exception,marker)
    def test_other_phase_cannot_start_negative_adapter(self):
        with patch.object(A,'launch') as launch:
            with self.assertRaises(ValueError):A.invoke([],{},proxy_command=[],proxy_environment={},server_command=[],socket_path='/never',deadline=0,pass_fds=(),store=MemoryStore(),name='c0-1',read_proxy_bytes=lambda:b'')
            launch.assert_not_called()

if __name__=='__main__':unittest.main()
