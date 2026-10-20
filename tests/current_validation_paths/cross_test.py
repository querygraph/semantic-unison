"""Cross-compiler peer successor controls; inert sessions and fabricated captures only."""
import unittest
from current_validation_paths import cross_contract as C,recipes,successors,dng_test
from current_validation_paths.cross_cases import bind,PAYLOAD
from current_validation_paths.dng_cases import BASE,LEFT,RIGHT
from current_validation_paths.fs_cases import KEY,ACL_TEXT
from current_validation_paths.parent_test import SOURCE
WORKSPACE='/private/tmp/u-xpeer-0123456789abcdef'


class Contract(unittest.TestCase):
    def test_five_cases_twelve_calls_two_validators_one_designated_skip(self):
        rows=C.plan(WORKSPACE,'stock')['rows']
        self.assertEqual(sum(r['max_CLI_calls'] for r in rows),12);self.assertEqual(sum(r['max_fake_validator_calls'] for r in rows),2)
        with self.assertRaises(ValueError):C.plan('/private/tmp/u-fsprop-0123456789abcdef','ox')
        self.assertEqual(C.call('conflict-skip',2),('require',[],'pass','pass',1,C.SKIPPED))
        self.assertEqual(C.call('dng-receive',1)[0],'off');self.assertEqual(C.call('properties',1)[1],C.PROPS)
        for name,calls,_ in C.CASES:
            with self.assertRaises(ValueError):C.call(name,calls+1)
    def test_phase_runs_the_peer_as_server_and_the_plan_compiler_as_client(self):
        scripts=recipes.scripts(recipes.literal_templates(SOURCE),'/repo');row=C.plan(WORKSPACE,'ox')['rows'][0]
        value=recipes.successor_phase(C,row,1,scripts,'/bin/ox-unison',server_binary='/bin/stock-unison')
        self.assertEqual(value['command'][0],'/bin/ox-unison');self.assertEqual(value['command'][value['command'].index('-servercmd')+1],'/bin/stock-unison')
        self.assertEqual(value['server_command'][0],'/bin/stock-unison')
        self.assertEqual(successors.server_binary(dict(binary=dict(path='/a'),peer=dict(binary=dict(path='/b')))),'/b')
        self.assertEqual(successors.server_binary(dict(binary=dict(path='/a'))),'/a')


class Path:
    store={}
    def __init__(self,path):self.path=str(path)
    def __truediv__(self,name):return Path(self.path+'/'+name)
    def entry(self):return self.store[self.path]
    def read_bytes(self):return self.entry()['data']
    def write_bytes(self,data):self.store.setdefault(self.path,dict(xattr={},acl=None))['data']=data
    def exists(self):return self.path in self.store
    def unlink(self):del self.store[self.path]
    def xattr(self,key,data=None):
        if data is not None:self.entry()['xattr'][key]=data;return len(data)
        return self.entry()['xattr'][key]
    def acl(self,text=None):
        if text is not None:self.entry()['acl']=text or None
        return self.entry()['acl']


def fake_session(outcome):
    class Session:
        original_assertions=dict(verify_call=lambda call,data,previous=None,endpoint='server':None)
        def __init__(self,root,binary):
            self.name=str(root).rsplit('/',1)[1];self.left=Path(str(root)+'/left');self.right=Path(str(root)+'/right')
            self.sequence=0;self.helpers=dict(client=[],server=[])
        def calls(self,endpoint='server'):return self.helpers[endpoint]
        def sync(self,*,policy,options,success=True,exit=None,designated=None):
            self.sequence+=1;e=C.call(self.name,self.sequence)
            assert (policy,list(options),(0 if success else 2) if exit is None else exit,designated)==(e[0],e[1],e[4],e[5])
            return outcome(self,self.sequence)
    return Session


def mirror(s,source,target,properties):
    for path in [p for p in Path.store if p.startswith(target.path+'/')]:
        if source.path+path[len(target.path):] not in Path.store:del Path.store[path]
    for path,entry in list(Path.store.items()):
        if path.startswith(source.path+'/'):
            old=Path.store.get(target.path+path[len(source.path):],dict(xattr={},acl=None))
            Path.store[target.path+path[len(source.path):]]=dict(data=entry['data'],
                xattr=dict(entry['xattr']) if properties else old['xattr'],acl=entry['acl'] if properties else old['acl'])


def declared(s,sequence):
    name=s.name
    if name=='conflict-skip' and sequence==2:return C.SKIPPED
    if name=='seed-update' and sequence==3:return 'Nothing to do: replicas have not changed since last sync.'
    if name=='seed-update' and sequence==1:
        Path.store[s.left.path+'/b.bin']=dict(Path.store[s.right.path+'/b.bin'])
    reverse=name=='reverse-deletion' and sequence==2 or name=='properties' and sequence==2 or name=='dng-receive' and sequence==3
    if reverse:mirror(s,s.right,s.left,name=='properties')
    else:mirror(s,s.left,s.right,name=='properties')
    if name=='dng-receive' and sequence>1:s.helpers['client' if reverse else 'server'].append({})
    return 'Synchronization complete'


class Cases(unittest.TestCase):
    def setUp(self):Path.store.clear()
    def test_declared_peer_behavior_passes_every_case(self):
        for name,function in bind(fake_session(declared)).items():
            with self.subTest(name=name):self.assertTrue(function(WORKSPACE+'/'+name,'/bin/u')['result'])
    def test_one_way_properties_or_ungated_receive_fails(self):
        def one_way(s,sequence):
            if s.name=='properties' and sequence==2:return 'Synchronization complete'
            if s.name=='dng-receive' and sequence==3:mirror(s,s.right,s.left,False);return ''
            return declared(s,sequence)
        for name in ('properties','dng-receive'):
            Path.store.clear()
            with self.subTest(name=name),self.assertRaises(AssertionError):bind(fake_session(one_way))[name](WORKSPACE+'/'+name,'/bin/u')


class Replay(dng_test.Replay):
    """A complete fabricated cross-peer run; the peer is the server everywhere."""
    def build(self):
        def endpoints(row,sequence,phase):
            if row['family']=='dng-receive':return {2:['server'],3:['client']}.get(sequence,[])
            return []
        return dng_test.fabricate(C,WORKSPACE,endpoints)
    def test_complete_d_inventory_replays_to_exact_totals(self):
        value=self.replay(*self.build())
        self.assertTrue(value['complete']);self.assertEqual((value['cli_calls'],value['fake_validators'],value['original_completed_cases']),(12,2,5))
    def test_designated_line_removed_or_named_schema_refuses(self):
        packet,*rest=self.build();del packet['peer']
        with self.assertRaisesRegex(ValueError,'proxy configuration|differs'):self.replay(packet,*rest)


if __name__=='__main__':unittest.main()
