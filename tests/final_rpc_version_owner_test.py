import unittest
from final_rpc_version_owner import validate_reply,shim_text

GREETING='Unison RPC\nVERSIONS 1\n'
def refusal(v):return GREETING+'NOK Client RPC version not supported. Version received from client: "'+str(v)+'". Supported RPC versions: "1"\n'
class Version(unittest.TestCase):
    def test_only_rpc1_accepts_and_unsupported_is_not_fallback(self):
        for v in (0,1,999):
            result=validate_reply(v,GREETING+'OK\n' if v==1 else refusal(v))
            self.assertEqual(result['accepted'],v==1);self.assertFalse(result['ordinary_transfer_or_semantic_fallback_proved'])
    def test_no_wrong_advertisement_cross_version_or_empty_refusal(self):
        for v,text in ((0,GREETING+'OK\n'),(1,refusal(1)),(0,refusal(999)),(999,refusal(0)),(0,'Unison RPC\nVERSIONS 0\n'),(0,GREETING+'NOK arbitrary error\n')):
            with self.assertRaises(ValueError):validate_reply(v,text)
        for v in (True,-1,2):
            with self.assertRaises(ValueError):validate_reply(v,refusal(v))
    def test_shim_execs_same_process_and_qualified_close_before_exec(self):
        import ast
        tree=ast.parse(shim_text());calls=[n.func for n in ast.walk(tree) if isinstance(n,ast.Call)]
        self.assertTrue(any(isinstance(n,ast.Attribute) and n.attr=='execve' for n in calls))
        self.assertFalse(any(isinstance(n,ast.Attribute) and n.attr in ('Popen','fork','kill','close') for n in calls))
        self.assertIn('close_descriptors([fd])',shim_text());compile(shim_text(),'<original-exec-shim>','exec')
if __name__=='__main__':unittest.main()
