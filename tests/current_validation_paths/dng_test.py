"""Built-in DNG merge successor controls; fabricated captures and inert sessions only."""
import copy,hashlib,json,os,unittest
from current_validation_paths import dng_contract as C,recipes,parent,successors
from current_validation_paths.dng_cases import bind,TARGET,LEFT,RIGHT,BASE,FORK_BYTES,INPUTS
from current_validation_paths.evidence import audit
from current_validation_paths.evidence_test import bundle,lines
from current_validation_paths.parent_full_test import child,helper_lines,RESOURCES
from current_validation_paths.parent_test import SOURCE,encode
from current_validation_paths.runtime import case_summary
from sdk_merge_receiving.admission import PYTHON
WORKSPACE='/private/tmp/u-dmerge-0123456789abcdef'


class Contract(unittest.TestCase):
    def test_thirteen_cases_twenty_nine_calls_nine_validators(self):
        rows=C.plan(WORKSPACE,'stock')['rows']
        self.assertEqual(len(rows),13);self.assertEqual(sum(r['max_CLI_calls'] for r in rows),29)
        self.assertEqual(sum(r['max_fake_validator_calls'] for r in rows),9)
        for bad in ('/private/tmp/u-vpath-0123456789abcdef','/tmp/u-dmerge-0123456789abcdef'):
            with self.assertRaises(ValueError):C.plan(bad,'stock')
    def test_every_zero_validator_failure_names_its_designated_decline(self):
        for name,calls,helpers in C.CASES:
            for sequence in range(1,calls+1):
                policy,options,client,server,code,designated=C.call(name,sequence)
                recipes.dng_options('/x',options)
                if code and name not in ('first-receiver-reject','second-receiver-reject'):self.assertGreaterEqual(len(designated),20)
                if code==0:self.assertIsNone(designated)
            with self.assertRaises(ValueError):C.call(name,calls+1)
        with self.assertRaises(ValueError):recipes.dng_options('/x',['-merge','Name *.dng -> /bin/sh'])
    def test_phase_binds_exact_command_controls_and_designated_line(self):
        scripts=recipes.scripts(recipes.literal_templates(SOURCE),'/repo');row=C.plan(WORKSPACE,'ox')['rows'][11]
        value=recipes.dng_phase(row,2,scripts,'/bin/u')
        self.assertEqual(value['expected_client_exit'],1);self.assertEqual(value['designated'],C.DESIGNATED['policy-disabled'])
        self.assertEqual(value['command'][-2:],C.DISABLED);self.assertNotIn('designated',recipes.dng_phase(row,1,scripts,'/bin/u'))


class Designated(unittest.TestCase):
    LINE='Failed [image.dng]: DNG scalar merge requires a saved common version; enable backupcurrent before synchronization'
    def check(self,code,designated,stderr):
        row,pair,_=bundle('pass',code);pair['proxy']['stderr']='';pair['client']['stderr']=stderr
        return audit(pair,client_command=row['command'],proxy_command=pair['proxy']['command'],server_command=row['server_command'],
            raw_proxy_bytes=json.dumps(pair['raw_proxy']).encode(),expected_client_exit=code,expected_helpers=[],designated=designated)
    def test_failed_or_skipped_without_validator_needs_the_exact_client_line(self):
        self.assertEqual(self.check(2,self.LINE,self.LINE+'\n')['designated_decline'],self.LINE)
        self.assertEqual(self.check(1,self.LINE,'x '+self.LINE+' y\n')['client_returncode'],1)
        for code,designated,stderr in ((2,self.LINE,'other failure\n'),(2,None,self.LINE),(1,None,self.LINE),(0,self.LINE,self.LINE),(2,'short',self.LINE)):
            with self.subTest(code=code,designated=designated),self.assertRaises(ValueError):self.check(code,designated,stderr)
    def test_server_side_copy_of_the_line_does_not_count(self):
        row,pair,_=bundle('pass',2);pair['proxy']['stderr']=self.LINE;pair['client']['stderr']=''
        with self.assertRaises(ValueError):
            audit(pair,client_command=row['command'],proxy_command=pair['proxy']['command'],server_command=row['server_command'],
                raw_proxy_bytes=json.dumps(pair['raw_proxy']).encode(),expected_client_exit=2,expected_helpers=[],designated=self.LINE)


class FakePath:
    store={}
    def __init__(self,path):self.path=str(path)
    def __truediv__(self,name):return FakePath(self.path+'/'+name)
    def read_bytes(self):return self.store[self.path]
    def write_bytes(self,data):self.store[self.path]=data
    def owned_names(self):return sorted({k[len(self.path)+1:].split('/')[0] for k in self.store if k.startswith(self.path+'/')})
    def resource_fork(self,data=None):
        if data is not None:self.store[self.path+'#rsrc']=data
        return self.store.get(self.path+'#rsrc')


def fake_session(behavior):
    """Inert Session that applies a chosen Unison outcome per call, never a process."""
    class Session:
        original_assertions=dict(verify_call=lambda call,data,previous=None,endpoint='server':None)
        def __init__(self,root,binary):
            self.name=str(root).rsplit('/',1)[1];self.left=FakePath(str(root)+'/left');self.right=FakePath(str(root)+'/right')
            self.client_state=FakePath(str(root)+'/client-state');self.sequence=0;self.helpers=dict(client=[],server=[]);self.controls=('pass','pass')
        def control(self,name,client='pass',server='pass'):self.controls=(client,server)
        def calls(self,endpoint='server'):return self.helpers[endpoint]
        def sync(self,*,policy,options,success=True,exit=None,designated=None):
            self.sequence+=1;expected=C.call(self.name,self.sequence)
            assert (policy,list(options))==(expected[0],expected[1]) and ((0 if success else 2) if exit is None else exit)==expected[4] and designated==expected[5]
            return behavior(self,self.sequence)
    return Session


def correct(s,sequence):
    """What the current production behavior is declared to do for each call."""
    name=s.name
    if sequence==1:
        (s.right/'image.dng').write_bytes((s.left/'image.dng').read_bytes())
        if s.name!='missing-base':(s.client_state/'backup'/'image.dng').write_bytes(BASE)
        return ''
    if name in ('disjoint','swapped') and sequence==2 or name=='second-receiver-reject' and sequence==3:
        (s.left/'image.dng').write_bytes(TARGET);(s.right/'image.dng').write_bytes(TARGET)
        s.helpers['client'].append({});s.helpers['server'].append({});return 'Built-in DNG scalar merge verified'
    if name=='second-receiver-reject':
        (s.left/'image.dng').write_bytes(TARGET);s.helpers['client'].append({});s.helpers['server'].append({});return ''
    if name=='first-receiver-reject':s.helpers['client'].append({})
    return ''


class Cases(unittest.TestCase):
    def setUp(self):FakePath.store.clear()
    def test_declared_behavior_passes_every_translated_case(self):
        functions=bind(fake_session(correct))
        self.assertEqual(set(functions),{n for n,*_ in C.CASES})
        for name,function in functions.items():
            with self.subTest(name=name):self.assertIn(function(WORKSPACE+'/'+name,'/bin/u')['result'],('converged','rejected','rejected-then-converged'))
    def test_declined_merge_that_changes_a_replica_or_leaves_temporaries_fails(self):
        def leaky(s,sequence):
            value=correct(s,sequence)
            if s.name=='competing' and sequence==2:(s.right/'image.dng').write_bytes(TARGET)
            if s.name=='unknown-field' and sequence==2:(s.left/'.unison.merge1-image.dng').write_bytes(b'x')
            return value
        functions=bind(fake_session(leaky))
        for name in ('competing','unknown-field'):
            with self.subTest(name=name),self.assertRaises(AssertionError):functions[name](WORKSPACE+'/'+name,'/bin/u')
    def test_second_receiver_retry_must_regate_both_replicas(self):
        def lazy(s,sequence):
            if s.name=='second-receiver-reject' and sequence==3:
                (s.left/'image.dng').write_bytes(TARGET);(s.right/'image.dng').write_bytes(TARGET);return 'Built-in DNG scalar merge verified'
            return correct(s,sequence)
        with self.assertRaises(AssertionError):bind(fake_session(lazy))['second-receiver-reject'](WORKSPACE+'/second-receiver-reject','/bin/u')


def dng_endpoints(row,sequence,phase):
    if row['family']=='first-receiver-reject' and sequence==2:return ['client']
    if row['family']=='second-receiver-reject' and sequence==2:return ['client','server']
    if phase['expected_client_exit']==0 and sequence>1 and not (row['family'] in ('disjoint','swapped') and sequence==3):return ['client','server']
    return []


def fabricate(contract,workspace,endpoints_of):
    """A complete successor run's raw records, as the worker would pin them."""
    packet=dict(contract.plan(workspace,'stock'),schema=contract.SCHEMA,
        repository='/source-only/current-repository',binary=dict(path='/inert/current-unison',sha256='a'*64))
    if successors.peered(contract.SCHEMA):packet['peer']=dict(compiler='ox',binary=dict(path='/inert/peer-unison',sha256='b'*64))
    server=successors.server_binary(packet)
    scripts=recipes.scripts(recipes.literal_templates(SOURCE),packet['repository'])
    records={};root_records={};states={};calls={};summaries=[];number=0
    for row in packet['rows']:
        root=row['directory'];identity=dict(device=1,inode=100+row['index']);streams=dict(client=[],server=[],copy=[],merge=[]);verdicts=[]
        root_records['case-%02d-START.json'%row['index']]=dict(row=row,resource_release_authorized=False)
        helpers_left=row['max_fake_validator_calls']
        for sequence in range(1,row['max_CLI_calls']+1):
            number+=1;stem='call-%03d'%number;base=10000+20*number
            phase=recipes.successor_phase(contract,row,sequence,scripts,packet['binary']['path'],server_binary=server)
            intent=dict(sequence=sequence,case_root=root,**phase,before_fake_helper_counts=dict(client=len(streams['client']),server=len(streams['server'])),
                before_external_counts=dict(copy=0,merge=0),resource_release_authorized=False)
            endpoints=endpoints_of(row,sequence,phase)
            stderr={'client':'','server':''};values=[]
            for k,endpoint in enumerate(endpoints):
                control=phase['helper_controls'][endpoint];destination=control['destination'];candidate=destination.rsplit('/',1)[0]+'/.image.dng.%03d.unison.tmp'%number
                sha=hashlib.sha256((stem+endpoint).encode()).hexdigest()
                value=dict(candidate=candidate,destination=destination,sha256=sha,size=4096,device=1,inode=base+50+k,
                    argv=['--unison-dng-validation-v1','--expected-sha256',sha,'--expected-size','4096','--threads','1','--',candidate],
                    pid=base+4+k,destination_sha256=None,mode=control['mode'],endpoint=endpoint,nofile_hard=256)
                streams[endpoint].append(value);values.append(value);stderr[endpoint]+=helper_lines(value,'completed')
            if 'designated' in phase:stderr['client']+=phase['designated']+'\n'
            proxy=[PYTHON,'-B',root+'/'+stem+'-proxy.py']
            raw=dict(schema='unison-retained-merge-proxy/1',server_command=phase['server_command'],server_pid=base+3,server_returncode=0,server_reaped=True,
                server_group=base+2,input_eof_forwarded=True,output_eof_forwarded=True,forwarded_protocol_bytes=dict(client_to_server_bytes=7,server_to_client_bytes=9),
                parent_group_audit_required=True,sdk_helper_audit_required=True,resource_release_authorized=False)
            pair=dict(client=child(phase['command'],phase['expected_client_exit'],base+1,stderr['client']),proxy=child(proxy,0,base+2,stderr['server']),
                raw_proxy=raw,external_sdk_audit_required=True,resource_release_authorized=False)
            arguments=dict(client_command=phase['command'],proxy_command=proxy,server_command=phase['server_command'],raw_proxy_bytes=json.dumps(raw).encode())
            if 'designated' in phase:arguments['designated']=phase['designated']
            expected=[dict(endpoint=v['endpoint'],pid=v['pid'],candidate_sha256=v['sha256'],candidate_bytes=4096,mode=v['mode'],outcome='completed') for v in values]
            verdict=json.loads(json.dumps(audit(pair,**arguments,expected_client_exit=phase['expected_client_exit'],expected_helpers=expected,expected_external=[])))
            config=dict(directory=root,identity=identity,stage=stem,binary=server,flags=phase['server_command'][3:],deadline=900.,worker_pid=500,resource_fds=RESOURCES)
            item=dict(root=root)
            for key,name,value in (('intent_pin','INTENT',dict(intent=intent,global_call=number,resource_release_authorized=False)),
                ('config_pin','CONFIG',dict(proxy=config,script_sha256=hashlib.sha256(recipes.proxy_source(packet['repository'],config).encode()).hexdigest(),resource_release_authorized=False)),
                ('pair_pin','PAIR',dict(pair=pair,raw_proxy_hex=json.dumps(raw).encode().hex(),resource_release_authorized=False)),('audit_pin','AUDIT',verdict)):
                data=encode(value);records[root,stem+'-'+name+'.json']=data;item[key]=dict(name=stem+'-'+name+'.json',sha256=hashlib.sha256(data).hexdigest(),bytes=len(data))
            records[root,stem+'-INHERITED.json']=encode(dict(proxy_pid=base+2,worker_pid=500,resource_fds=RESOURCES,
                binding=dict(inherited_fds=[r['fd'] for r in RESOURCES],canonical_metadata_bound=True,lock_ownership_independently_proved=False,resource_release_authorized=False)))
            prefix='case-%02d-seq-%03d-'%(row['index'],sequence)
            root_records[prefix+'INTENT.json']=copy.deepcopy(intent);root_records[prefix+'ACCEPTED.json']=dict(intent=copy.deepcopy(intent),verdict=verdict,resource_release_authorized=False)
            calls[str(number)]=item;verdicts.append(dict(root=root,verdict=verdict))
        states[root]=dict(identity=identity,counters=streams,scripts_current=True,profile_current=True)
        summary=case_summary(row,verdicts,dict(name=row['name']));summaries.append(summary);root_records['case-%02d-RESULT.json'%row['index']]=summary
    result=dict(complete=True,cases=summaries,failed_case=None,calls=calls,attempted_CLI_calls=number,actual_SDK_calls=0,actual_Photo_calls=0,
        parent_terminal_proved=False,resource_release_authorized=False,independent_parent_raw_audit_required=True)
    return packet,result,records,root_records,states


class Replay(unittest.TestCase):
    """A complete fabricated D run replayed by the parent under the D schema."""
    def build(self):return fabricate(C,WORKSPACE,dng_endpoints)
    def replay(self,packet,result,records,root_records,states):
        return parent.replay(packet,result,source=SOURCE,worker_pid=500,resources=RESOURCES,owner_deadline=1000.,
            read_case=lambda root,name:records[root,name],read_root=lambda name:copy.deepcopy(root_records[name]),
            case_state=lambda root,scripts,profile,proxies:copy.deepcopy(states[root]))
    def test_complete_d_inventory_replays_to_exact_totals(self):
        value=self.replay(*self.build())
        self.assertTrue(value['complete']);self.assertEqual(value['cli_calls'],29);self.assertEqual(value['fake_validators'],9)
        self.assertEqual(value['original_completed_cases'],13);self.assertFalse(value['resource_release_authorized'])
    def test_designated_line_removed_or_named_schema_refuses(self):
        packet,result,records,root_records,states=self.build();root=packet['rows'][2]['directory']
        pair=json.loads(records[root,'call-008-PAIR.json']);pair['pair']['client']['stderr']='';data=encode(pair)
        records[root,'call-008-PAIR.json']=data;result['calls']['8']['pair_pin']=dict(name='call-008-PAIR.json',sha256=hashlib.sha256(data).hexdigest(),bytes=len(data))
        with self.assertRaisesRegex(ValueError,'designated'):self.replay(packet,result,records,root_records,states)
        packet,*rest=self.build();packet['schema']='unison-current-named-receiving-execution/1'
        with self.assertRaises(ValueError):self.replay(packet,*rest)

if __name__=='__main__':unittest.main()


class OwnedFixtureIO(unittest.TestCase):
    """Actual tiny private files: listing and a fd-anchored Darwin resource fork."""
    def setUp(self):
        import tempfile
        from pathlib import Path
        from current_validation_paths.files import Files
        self.temp=tempfile.TemporaryDirectory();root=Path(self.temp.name);st=root.lstat()
        self.files=Files(root,(st.st_dev,st.st_ino));self.root=self.files.Path(root)
    def tearDown(self):
        self.files.close();self.temp.cleanup()
    def test_listing_and_resource_fork_through_owned_descriptors(self):
        import sys
        (self.root/'left').mkdir();image=self.root/'left'/'image.dng';image.write_bytes(LEFT)
        (self.root/'left'/'.unison.merge1-image.dng').write_bytes(b'x')
        self.assertEqual((self.root/'left').owned_names(),['.unison.merge1-image.dng','image.dng'])
        if sys.platform=='darwin':
            self.assertEqual(image.resource_fork(FORK_BYTES),len(FORK_BYTES));self.assertEqual(image.resource_fork(),FORK_BYTES)
            self.assertEqual(image.read_bytes(),LEFT)
        with self.assertRaises(ValueError):image.resource_fork(b'')
        with self.assertRaises(ValueError):(self.root/'..'/'escape').owned_names()


class SessionGuards(unittest.TestCase):
    def session(self,temp,seen):
        from pathlib import Path
        from current_validation_paths.files import Files
        from current_validation_paths.original import load
        from current_validation_paths.session import factory
        root=Path(temp);st=root.lstat();files=Files(root,(st.st_dev,st.st_ino))
        def release():
            # Retention here is a refused expectation, not an unknown close: the
            # remaining descriptors are known test-owned and closed once.
            if files.closed:return
            if files.retained is None:files.close();return
            for fd in files.retained.retained_fds:os.close(fd)
            files.closed=True
        self.addCleanup(release)
        def invoke(session,intent):seen.append(intent);return {}
        def audit(session,intent,outcome):
            return dict(command=intent['command'],client_returncode=intent['expected_client_exit'],log='',external_children_settled=True,resource_release_authorized=False)
        selected=[]
        def make(legacy):
            selected.append(factory(legacy,files=files,binary='/original/current-unison',repository='/repo',invoke=invoke,audit=audit,
                interrupt=lambda *a:None,persist=lambda *a:None,options=recipes.dng_options));return selected[-1]
        load(SOURCE,session_factory=make,path_factory=lambda _:files.Path,cancel_actor=lambda *a:None,filename='/source-only/run.py')
        return selected[0](files.Path(root/'case'),'/original/current-unison')
    def test_explicit_exit_and_designated_reach_the_intent(self):
        import tempfile
        with tempfile.TemporaryDirectory() as temp:
            seen=[];s=self.session(temp,seen)
            s.sync(policy='require',options=C.DISABLED,success=False,exit=1,designated=C.DESIGNATED['policy-disabled'])
            self.assertEqual((seen[-1]['expected_client_exit'],seen[-1]['designated']),(1,C.DESIGNATED['policy-disabled']))
            s.sync(policy='off',options=C.OPTS);self.assertNotIn('designated',seen[-1])
    def test_inconsistent_expectation_or_option_retains_instead_of_running(self):
        import tempfile
        from shared_cpu_pool import UnresolvedOwnership
        for kwargs in (dict(success=True,exit=2),dict(success=True,designated=C.BASE),dict(success=False,designated='short'),
                       dict(success=False,exit=3),dict(options=['-merge','x'])):
            with tempfile.TemporaryDirectory() as temp,self.subTest(kwargs=kwargs):
                seen=[];s=self.session(temp,seen);arguments=dict(policy='require',options=C.OPTS);arguments.update(kwargs)
                with self.assertRaises(UnresolvedOwnership):s.sync(**arguments)
                self.assertEqual(seen,[])
