"""Filesystem property transition successor controls; inert sessions, fabricated captures, tiny real files."""
import copy,hashlib,json,os,sys,tempfile,unittest
from pathlib import Path
from current_validation_paths import fs_contract as C,recipes,parent,successors,admission
from current_validation_paths.fs_cases import bind,KEY,ACL_TEXT,MiB
from current_validation_paths import dng_test
from current_validation_paths.parent_test import SOURCE
WORKSPACE='/private/tmp/u-fsprop-0123456789abcdef'


class Contract(unittest.TestCase):
    def test_six_cases_seventeen_zero_exit_calls_no_validators(self):
        rows=C.plan(WORKSPACE,'ox')['rows']
        self.assertEqual([r['name'] for r in rows],[n for n,_ in C.CASES]);self.assertEqual(sum(r['max_CLI_calls'] for r in rows),17)
        self.assertEqual({r['max_fake_validator_calls'] for r in rows},{0})
        for bad in ('/private/tmp/u-dmerge-0123456789abcdef','/tmp/u-fsprop-0123456789abcdef'):
            with self.assertRaises(ValueError):C.plan(bad,'stock')
        for name,calls in C.CASES:
            for sequence in range(1,calls+1):
                policy,options,client,server,code,designated=C.call(name,sequence)
                self.assertEqual((policy,client,server,code,designated),('require','pass','pass',0,None))
                recipes.successor_options(C,'/x',options)
            with self.assertRaises(ValueError):C.call(name,calls+1)
        with self.assertRaises(ValueError):recipes.successor_options(C,'/x',['-xattrs','-acl'])
    def test_registry_routes_each_schema_to_its_own_contract(self):
        from current_validation_paths import dng_contract
        self.assertIs(successors.contract(C.SCHEMA),C);self.assertIs(successors.contract(dng_contract.SCHEMA),dng_contract)
        self.assertIsNone(successors.contract('unison-current-named-receiving-execution/1'))
        self.assertEqual(admission.SCHEMAS[C.SCHEMA],'successor')
    def test_phase_passes_the_preference_to_both_endpoints(self):
        scripts=recipes.scripts(recipes.literal_templates(SOURCE),'/repo');rows=C.plan(WORKSPACE,'stock')['rows']
        xattr=recipes.successor_phase(C,rows[3],2,scripts,'/bin/u');acl=recipes.successor_phase(C,rows[5],1,scripts,'/bin/u')
        self.assertEqual((xattr['command'][-1],xattr['server_command'][-1]),('-xattrs','-xattrs'))
        self.assertEqual((acl['command'][-1],acl['server_command'][-1]),('-acl','-acl'))
        off=recipes.successor_phase(C,rows[2],2,scripts,'/bin/u')
        self.assertNotIn('-xattrs',off['command']);self.assertNotIn('designated',off)


class FakePath:
    store={}
    def __init__(self,path):self.path=str(path)
    def __truediv__(self,name):return FakePath(self.path+'/'+name)
    def read_bytes(self):return self.store[self.path]['data']
    def write_bytes(self,data):
        entry=self.store.setdefault(self.path,dict(xattr={},acl=None));entry['data']=data;entry['blocks']=len(data)//512
    def exists(self):return self.path in self.store
    def unlink(self):del self.store[self.path]
    def stat(self):
        entry=self.store[self.path];return type('st',(),dict(st_size=len(entry['data']),st_blocks=entry['blocks']))
    def punch_hole(self,offset,length):
        entry=self.store[self.path];entry['data']=entry['data'][:offset]+bytes(length)+entry['data'][offset+length:];entry['blocks']-=length//512
    def xattr(self,key,data=None,*,remove=False):
        x=self.store[self.path]['xattr']
        if remove:del x[key];return None
        if data is not None:x[key]=data;return len(data)
        return x[key]
    def xattr_names(self):return sorted(self.store[self.path]['xattr'])
    def acl(self,text=None):
        if text is not None:self.store[self.path]['acl']=text or None
        return self.store[self.path]['acl']


def fake_session(propagate):
    """Inert Session; propagate(session, options) applies Unison's chosen outcome."""
    class Session:
        def __init__(self,root,binary):
            self.name=str(root).rsplit('/',1)[1];self.left=FakePath(str(root)+'/left');self.right=FakePath(str(root)+'/right');self.sequence=0
        def calls(self,endpoint='server'):return []
        def sync(self,*,policy,options,success=True,exit=None,designated=None):
            self.sequence+=1;expected=C.call(self.name,self.sequence)
            assert (policy,list(options),success,exit,designated)==(expected[0],expected[1],True,None,None)
            return propagate(self,list(options))
    return Session


def declared(s,options):
    """The current production behavior: content always, xattrs/ACLs only when enabled, holes materialized."""
    changed=False;prefix=s.left.path+'/'
    if any(p.startswith(s.right.path+'/') for p in FakePath.store) and not any(p.startswith(prefix) for p in FakePath.store):
        raise AssertionError('Unison batch aborts when a replica root is emptied (confirmbigdel)')
    for path in [p for p in FakePath.store if p.startswith(s.right.path+'/')]:
        if s.left.path+path[len(s.right.path):] not in FakePath.store:del FakePath.store[path];changed=True
    for path,entry in list(FakePath.store.items()):
        if not path.startswith(prefix):continue
        target=s.right.path+'/'+path[len(prefix):];old=FakePath.store.get(target)
        new=dict(data=entry['data'],blocks=len(entry['data'])//512,
            xattr=dict(entry['xattr']) if '-xattrs' in options else (old or {}).get('xattr',{}),
            acl=entry['acl'] if '-acl' in options else (old or {}).get('acl'))
        if old is None or any(old[k]!=new[k] for k in ('data','xattr','acl')):FakePath.store[target]=new;changed=True
    return 'Synchronization complete' if changed else 'Nothing to do: replicas have not changed since last sync.'


class Cases(unittest.TestCase):
    def setUp(self):FakePath.store.clear()
    def run_all(self,behavior):
        return {name:function(WORKSPACE+'/'+name,'/bin/u') for name,function in bind(fake_session(behavior)).items()}
    def test_declared_behavior_passes_and_records_hole_allocation(self):
        results=self.run_all(declared)
        self.assertEqual(results['holes']['first_receiver_allocated_bytes'],8*MiB+4096)
        self.assertLess(results['holes']['source_allocated_bytes'],3*MiB)
        self.assertEqual(results['acl']['result'],'set-removed')
    def test_dropped_property_or_leaked_default_fails(self):
        def drop_xattr_removal(s,options):
            keep={p:copy.deepcopy(e['xattr']) for p,e in FakePath.store.items() if p.startswith(s.right.path)}
            value=declared(s,options)
            if s.name=='xattr' and s.sequence==4:
                for p,x in keep.items():
                    if p in FakePath.store:FakePath.store[p]['xattr']=x
            return value
        def leak_acl(s,options):return declared(s,[*options,'-acl'])
        def no_empty(s,options):
            value=declared(s,options)
            if s.name=='zero-length' and s.sequence==1:del FakePath.store[s.right.path+'/empty.bin']
            return value
        for behavior,name in ((drop_xattr_removal,'xattr'),(leak_acl,'acl-default-off'),(no_empty,'zero-length')):
            FakePath.store.clear()
            with self.subTest(name=name),self.assertRaises((AssertionError,KeyError)):
                bind(fake_session(behavior))[name](WORKSPACE+'/'+name,'/bin/u')


class Replay(dng_test.Replay):
    """A complete fabricated filesystem properties run replayed under its own schema."""
    def build(self):return dng_test.fabricate(C,WORKSPACE,lambda row,sequence,phase:[])
    def test_complete_d_inventory_replays_to_exact_totals(self):
        value=self.replay(*self.build())
        self.assertTrue(value['complete']);self.assertEqual(value['cli_calls'],17);self.assertEqual(value['fake_validators'],0)
        self.assertEqual(value['original_completed_cases'],6);self.assertFalse(value['resource_release_authorized'])
    def test_designated_line_removed_or_named_schema_refuses(self):
        packet,*rest=self.build();packet['schema']='unison-current-dng-merge-receiving-execution/1'
        with self.assertRaises(ValueError):self.replay(packet,*rest)
        packet,result,records,root_records,states=self.build();del result['calls']['17']
        with self.assertRaises(ValueError):self.replay(packet,result,records,root_records,states)


@unittest.skipUnless(sys.platform=='darwin','Darwin xattr/ACL/hole fixtures')
class OwnedFixtureIO(unittest.TestCase):
    """Tiny private files: declared xattr, extended ACL and a punched hole through held descriptors."""
    def setUp(self):
        from current_validation_paths.files import Files
        self.temp=tempfile.TemporaryDirectory();root=Path(self.temp.name);st=root.lstat()
        self.files=Files(root,(st.st_dev,st.st_ino));self.root=self.files.Path(root)
    def tearDown(self):
        self.files.close();self.temp.cleanup()
    def test_xattr_set_change_remove_and_undeclared_key(self):
        f=self.root/'f';f.write_bytes(b'x')
        self.assertEqual(f.xattr(KEY,b'v1'),2);self.assertEqual(f.xattr(KEY),b'v1');self.assertIn(KEY,f.xattr_names())
        f.xattr(KEY,remove=True);self.assertNotIn(KEY,f.xattr_names())
        for args in (('user.other',b'v'),(KEY,b'')):
            with self.assertRaises(ValueError):f.xattr(*args)
    def test_acl_round_trip_and_clear(self):
        f=self.root/'f';f.write_bytes(b'x');self.assertIsNone(f.acl())
        self.assertEqual(f.acl(ACL_TEXT),ACL_TEXT);self.assertIsNone(f.acl(''))
    def test_punched_hole_keeps_length_and_reads_zero(self):
        f=self.root/'f';f.write_bytes(b'a'*(8*MiB)+b'b'*4096);f.punch_hole(MiB,6*MiB)
        data=f.read_bytes();self.assertEqual(len(data),8*MiB+4096);self.assertEqual(data[MiB:7*MiB],bytes(6*MiB))
        self.assertLess(f.stat().st_blocks*512,3*MiB)
        for offset,length in ((1,4096),(MiB,8*MiB)):
            with self.assertRaises(ValueError):f.punch_hole(offset,length)


if __name__=='__main__':unittest.main()
