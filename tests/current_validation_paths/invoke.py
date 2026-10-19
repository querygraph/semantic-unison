"""Retained normal-call actor; call only inside an admitted IO/CPU worker.

No resource acquisition or standalone CLI. All callbacks are trusted source seams
for original controls. This actor cannot release inherited CPU/IO descriptors.
"""
from copy import deepcopy
import hashlib,json,os,time
from pathlib import Path
from cached_benchmark.contract import read_bytes
from shared_cpu_pool import UnresolvedOwnership
from sdk_merge_receiving.admission import PYTHON,exact
from sdk_merge_receiving.store import Store
from sdk_negative_receiving.bound_call import call
from current_validation_paths.evidence import audit as audit_pair
from current_validation_paths.cancel_call import call as cancel_call
from current_validation_paths.cancel_observation import wait as observe_cancel,validate_fixture
from current_validation_paths.cancel_evidence import audit as audit_cancel


def artifacts(packet):
    for ref in (packet['binary'],packet['interpreter']):
        if hashlib.sha256(read_bytes(ref['path'],256*1048576)).hexdigest()!=ref['sha256']:raise ValueError('named-path execution artifact changed')


class Actor:
    def __init__(self,packet,resources,deadline,*,pair_call=call,cancellation_call=cancel_call,artifact_check=artifacts):
        if len(resources)!=9 or len({r['fd'] for r in resources})!=9:raise ValueError('exact previously verified inherited nine-resource rows required')
        self.packet=deepcopy(packet);self.resources=deepcopy(resources);self.deadline=deadline
        self.pair_call=pair_call;self.cancellation_call=cancellation_call;self.artifact_check=artifact_check;self.stores={};self.calls={}
        self.attempts=0;self.active=None;self.retained=None;self.closed=False;self.normal_sequences={}
        self.allowed={r['directory'] for r in packet['rows']}
    def _ready(self):
        if self.retained is not None:raise self.retained
        if self.closed:raise ValueError('actor already retired')
    def _retain(self,error):
        retained=error if isinstance(error,UnresolvedOwnership) else UnresolvedOwnership('named call unresolved; retain every child/store/resource owner')
        if retained is not error:retained.original_failure=error
        retained.named_call_actor=self
        excluded=set(getattr(retained,'uncertain_fds',()))
        known=[*retained.retained_fds,*[r['fd'] for r in self.resources],*[s.fd for s in self.stores.values() if not s.closed]]
        retained.retained_fds=tuple(dict.fromkeys(fd for fd in known if fd not in excluded))
        self.retained=retained;return retained
    def invoke(self,session,intent):
        self._ready()
        try:
            root=str(session.root)
            if (self.active is not None or root not in self.allowed or intent['case_root']!=root
                or type(intent['sequence']) is not int or intent['sequence']!=self.normal_sequences.get(root,0)+1
                or self.attempts>=self.packet['limits']['CLI_calls']):raise ValueError('one exact ordered case call within declared budget required')
            if intent['command'][:8]!=[self.packet['binary']['path'],str(session.left),'ssh://localhost/'+str(session.right),
                '-sshcmd',str(session.launcher),'-servercmd',self.packet['binary']['path'],'-batch']:
                raise ValueError('exact current endpoint/launcher command required')
            if intent['server_command'][:3]!=[self.packet['binary']['path'],'-server','__new-rpc-mode']:raise ValueError('exact current server required')
            now=time.monotonic();phase=min(self.deadline,now+self.packet['limits']['per_CLI_observation_seconds'])
            if not now<phase:raise TimeoutError('no new call after observation deadline')
            self.attempts+=1;number=self.attempts;stem='call-%03d'%number
            self.normal_sequences[root]=intent['sequence'];self.active=dict(number=number,root=root,intent=deepcopy(intent),stem=stem)
            if root not in self.stores:
                for name in ('home','tmp'):(session.root/name).mkdir()
                native=session.root.lstat();self.stores[root]=Store(root,dict(device=native.st_dev,inode=native.st_ino))
            store=self.stores[root]
            store.write(stem+'-INTENT.json',dict(intent=deepcopy(intent),global_call=number,resource_release_authorized=False))
            self.artifact_check(self.packet)
            expected_scripts={str(path) for path in (*session.drivers.values(),session.copy,session.merger,session.launcher)}
            if set(session.prepared_scripts)!=expected_scripts:raise ValueError('exact generated script inventory required')
            for path,digest in session.prepared_scripts.items():
                if hashlib.sha256(session.root.__class__(path).read_bytes()).hexdigest()!=digest:raise ValueError('generated helper/launcher script changed')
            if hashlib.sha256((session.server_state/'endpoint.prf').read_bytes()).hexdigest()!=intent['server_profile_sha256']:
                raise ValueError('server endpoint profile changed after intent')
            for endpoint,control in intent['helper_controls'].items():
                if not exact(json.loads(session.drivers[endpoint].with_suffix('.control.json').read_text()),control):raise ValueError('fake helper control changed after intent')
            native=session.root.lstat();config=dict(directory=root,identity=dict(device=native.st_dev,inode=native.st_ino),stage=stem,
                binary=self.packet['binary']['path'],flags=intent['server_command'][3:],deadline=phase,worker_pid=os.getpid(),resource_fds=self.resources)
            imports=[self.packet['repository']+'/tests',self.packet['repository']+'/tests/sdk_host_matrix',self.packet['repository']+'/bench/sync']
            source='#!'+PYTHON+'\nimport sys\nsys.path[:0]='+repr(imports)+'\nfrom sdk_merge_receiving.child_entry import proxy_main\nraise SystemExit(proxy_main('+repr(config)+'))\n'
            compile(source,root+'/'+stem+'-proxy.py','exec')
            script=session.root/(stem+'-proxy.py');script.write_text(source);script.chmod(0o700)
            proxy=[PYTHON,'-B',str(script)]
            store.write(stem+'-CONFIG.json',dict(proxy=config,script_sha256=hashlib.sha256(script.read_bytes()).hexdigest(),resource_release_authorized=False))
            socket=str(session.root/(stem+'.sock'))
            if len(os.fsencode(socket))>=100:raise ValueError('bounded local socket path required')
            env=dict(PATH='/usr/bin:/bin:/usr/sbin:/sbin',LANG='C',LC_ALL='C',HOME=str(session.root/'home'),TMPDIR=str(session.root/'tmp'),PYTHONNOUSERSITE='1',PYTHONDONTWRITEBYTECODE='1')
            client_env=dict(env,UNISON=str(session.client_state),UNISON_MERGE_BINARY=self.packet['binary']['path'],UNISON_MERGE_SOCKET=socket,UNISON_MERGE_DEADLINE=str(phase))
            def persist(row,pair,raw):
                if 'pair_pin' in self.active:raise ValueError('one-use pair already persisted')
                self.active['pair_pin']=store.write(stem+'-PAIR.json',dict(pair=pair,raw_proxy_hex=raw.hex(),resource_release_authorized=False))
            arguments=dict(proxy_command=proxy,proxy_environment=dict(env,UNISON=str(session.server_state)),
                socket_path=socket,deadline=phase,pass_fds=tuple(r['fd'] for r in self.resources),
                read_proxy_bytes=lambda:store.read(stem+'-PROXY.json',maximum=65536),persist=persist)
            if 'cancellation' in intent:
                fixture=session.cancel_fixture
                if type(fixture) is not dict or intent['expected_client_exit']!=3 or not exact(intent['cancellation'],dict(
                    name=fixture['name'],incoming_sha256=hashlib.sha256(fixture['incoming']).hexdigest(),incoming_bytes=len(fixture['incoming']),
                    previous_sha256=hashlib.sha256(fixture['previous']).hexdigest(),previous_bytes=len(fixture['previous']))):
                    raise ValueError('exact source-owned cancellation fixture required')
                before=intent['before_fake_helper_counts']['client']
                validate_fixture(fixture['name'],fixture['incoming'],fixture['previous'],before)
                control=intent['helper_controls']['client']
                if control['mode']!='hang' or control['destination']!=str(session.left/fixture['name']):
                    raise ValueError('declared receiving-client hang control required before any child')
                value=self.cancellation_call(dict(command=intent['command']),client_env,**arguments,
                    before_interrupt=lambda child,limit:observe_cancel(session,fixture['name'],fixture['incoming'],fixture['previous'],before,child,limit))
                result=value[:2];self.active['cancellation_pin']=store.write(stem+'-CANCELLATION.json',value[2])
            else:
                if intent['expected_client_exit'] not in (0,2):raise ValueError('normal call cannot claim cancellation')
                result=self.pair_call(dict(command=intent['command']),client_env,**arguments)
            self.active.update(returned=result,proxy_command=proxy)
            return dict(global_call=number,pair_pin=deepcopy(self.active['pair_pin']),resource_release_authorized=False)
        except UnresolvedOwnership as error:self._retain(error);raise
        except BaseException as error:raise self._retain(error) from error
    def _helpers(self,session,intent,*,hang_outcome='timed-out'):
        result=[]
        for endpoint in ('client','server'):
            before=intent['before_fake_helper_counts'][endpoint];values=session.calls(endpoint)
            if type(before) is not int or not 0<=before<=len(values) or len(values)-before>6:raise ValueError('bounded fake-helper counter prefix required')
            control=intent['helper_controls'][endpoint]
            for value in values[before:]:
                if value['endpoint']!=endpoint or value['mode']!=control['mode']:raise ValueError('helper counter/control binding differs')
                candidate=Path(value['candidate']);destination=Path(value['destination']);base=Path(session.left if endpoint=='client' else session.right)
                if '..' in candidate.parts or '..' in destination.parts or not candidate.is_relative_to(base) or not destination.is_relative_to(base) or candidate==destination:
                    raise ValueError('fake receiving candidate/destination escaped exact endpoint')
                expected_destination=Path(control['destination'])/(candidate.name) if control.get('directory') is True else Path(control['destination'])
                if destination!=expected_destination or value['argv']!=['--unison-dng-validation-v1','--expected-sha256',value['sha256'],
                    '--expected-size',str(value['size']),'--threads','1','--',str(candidate)]:raise ValueError('exact helper invocation/destination counter required')
                result.append(dict(endpoint=endpoint,pid=value['pid'],candidate_sha256=value['sha256'],candidate_bytes=value['size'],
                    mode=control['mode'],outcome=hang_outcome if control['mode']=='hang' else 'completed'))
        return result
    def audit(self,session,intent,outcome):
        self._ready()
        try:
            active=self.active
            if active is None or not exact(active['intent'],intent) or not exact(outcome,dict(global_call=active['number'],pair_pin=active['pair_pin'],resource_release_authorized=False)):
                raise ValueError('exact active returned call/pin required')
            store=self.stores[active['root']];pin=active['pair_pin'];record=store.read_json(pin['name'],expected_sha256=pin['sha256'])
            raw=bytes.fromhex(record['raw_proxy_hex'])
            if raw.hex()!=record['raw_proxy_hex'] or not exact(record['pair'],active['returned'][0]) or raw!=active['returned'][1]:raise ValueError('independently read pair differs')
            arguments=dict(client_command=intent['command'],proxy_command=active['proxy_command'],server_command=intent['server_command'],raw_proxy_bytes=raw)
            if 'cancellation' in intent:
                pin=active['cancellation_pin'];cancellation=store.read_json(pin['name'],expected_sha256=pin['sha256'])
                verdict=audit_cancel(record['pair'],**arguments,cancellation=cancellation,
                    expected_helpers=self._helpers(session,intent,hang_outcome='cancelled'))
            else:
                verdict=audit_pair(record['pair'],**arguments,expected_client_exit=intent['expected_client_exit'],expected_helpers=self._helpers(session,intent))
            store.write(active['stem']+'-AUDIT.json',verdict)
            self.calls[active['number']]=dict(root=active['root'],intent=deepcopy(intent),pair_pin=active['pair_pin'],verdict=verdict)
            if 'cancellation_pin' in active:self.calls[active['number']]['cancellation_pin']=active['cancellation_pin']
            self.active=None;return verdict
        except UnresolvedOwnership as error:self._retain(error);raise
        except BaseException as error:raise self._retain(error) from error
    def close(self):
        self._ready()
        if self.active is not None or len(self.calls)!=self.attempts:raise ValueError('cannot close actor with unaccepted invocation')
        try:
            for store in self.stores.values():store.close()
        except UnresolvedOwnership as error:self._retain(error);raise
        self.closed=True
