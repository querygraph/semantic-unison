import unittest
from sdk_merge_receiving.plan_test import inputs
from sdk_negative_receiving.plan import schedule


class Plan(unittest.TestCase):
    def test_exact_twelve_serial_calls_six_negative_helpers(self):
        binaries,tool,_=inputs();p=schedule(binaries,tool,'/private/tmp/u-snr-'+'a'*16)
        self.assertEqual(len(p['rows']),12);self.assertEqual(sum(r['expected_sdk_helpers'] for r in p['rows']),6)
        self.assertEqual(len({r['directory'] for r in p['rows']}),6)
        self.assertEqual(p['token_indexes'],list(range(8)));self.assertLessEqual(p['configured_endpoint_plus_owner_credits'],8)
        for i,r in enumerate(p['rows']):
            self.assertEqual(r['stage'],'seed' if i%2==0 else 'negative')
            self.assertNotIn('-merge',r['command']);self.assertNotIn('-semanticmergebasecache',r['server_flags'])
            expected='off' if r['stage']=='seed' else r['policy']
            for command in (r['command'],r['server_command']):self.assertEqual(command[command.index('-adobevalidate')+1],expected)
            self.assertEqual(r['command'][r['command'].index('-force')+1],r['directory']+'/left')
            self.assertEqual(r['expected_client_exit'],1 if r['stage']=='negative' and r['policy']=='require' else 0)
    def test_old_or_noncanonical_namespace_refuses(self):
        binaries,tool,old=inputs()
        for name in (old,'/tmp/u-snr-'+'a'*16,'/private/tmp/u-snr-'+'a'*15,'/private/tmp/../tmp/u-snr-'+'a'*16):
            with self.assertRaises(ValueError):schedule(binaries,tool,name)
    def test_unqualified_sdk_and_aliased_peers_refuse(self):
        binaries,tool,_=inputs();tool['threads']=2
        with self.assertRaises(ValueError):schedule(binaries,tool,'/private/tmp/u-snr-'+'a'*16)
        binaries,tool,_=inputs();binaries['ox']['path']=binaries['stock']['path']
        with self.assertRaises(ValueError):schedule(binaries,tool,'/private/tmp/u-snr-'+'a'*16)

if __name__=='__main__':unittest.main()
