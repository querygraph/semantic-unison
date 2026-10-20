"""Original assertions with owned files and trusted retained process adapters.

This module launches nothing. invoke/audit/interrupt are pinned executor source,
never packet callbacks; an admitted owner must supply them and all resource FDs.
"""
import hashlib,json
from shared_cpu_pool import UnresolvedOwnership
from sdk_merge_receiving.admission import PYTHON
from current_validation_paths.cancel_observation import validate_fixture
from current_validation_paths import recipes


def factory(legacy,*,files,binary,repository,invoke,audit,interrupt,persist,options=recipes.options):
    if not all(callable(f) for f in (invoke,audit,interrupt,persist,options)):raise ValueError('owned source adapters required')
    ns=legacy.__init__.__globals__;ns['ADMISSION_OPTIONS']=['-semanticvolumejobs','1']
    ns['HELPER_CONFIG']={};ns['SERVER_HELPER_DESCRIPTORS']=None
    generated=recipes.scripts(ns,repository)
    class Session(legacy):
        original_assertions=ns
        def _ready(self):
            if self.retained is not None:raise self.retained
            files._ready()
        def _retain(self,error):
            retained=error if isinstance(error,UnresolvedOwnership) else UnresolvedOwnership('named receiving session incomplete; retain all owners')
            if retained is not error:retained.original_failure=error
            retained.named_validation_session=self;retained.named_fixture_files=files
            retained.named_invocation_outcome=getattr(self,'last_outcome',None)
            retained.named_invocation_verdict=getattr(self,'last_verdict',None)
            files._retain(retained)
            self.retained=retained
            return retained
        def __init__(self,root,selected_binary):
            self.retained=None;self.sequence=0;self.active_intent=None
            self.last_outcome=None;self.last_verdict=None;self.cancel_fixture=None
            self.invoke_adapter=invoke;self.audit_adapter=audit;self.interrupt_adapter=interrupt;self.persist_adapter=persist
            try:
                if selected_binary!=binary:raise ValueError('exact prepared compiler binary required')
                self.root=files.Path(root);self.binary=binary;self.root.mkdir()
                self.left,self.right,self.client_state,self.server_state=(self.root/name for name in ('left','right','client-state','server-state'))
                for path in (self.left,self.right,self.client_state,self.server_state):path.mkdir()
                for name,text in generated.items():
                    path=self.root/name;path.write_text(text);path.chmod(0o700)
                self.drivers={endpoint:self.root/(endpoint+'-validator.py') for endpoint in ('client','server')}
                self.copy=self.root/'external-copy.py';self.copy.with_suffix('.control.json').write_text(json.dumps(dict(interrupt='no')))
                self.merger=self.root/'merge.py';self.launcher=self.root/'loopback.py';self.abort_launcher=self.root/'abort-loopback.py'
                config=self.config('server');config['semanticvolumejobs']='1'
                (self.server_state/'endpoint.prf').write_text(''.join(k+' = '+v+'\n' for k,v in config.items()))
                self.control('image.dng')
                self.prepared_scripts={str(path):hashlib.sha256(path.read_bytes()).hexdigest() for path in (*self.drivers.values(),self.copy,self.merger,self.launcher,self.abort_launcher)}
            except UnresolvedOwnership as error:self._retain(error);raise
            except BaseException as error:raise self._retain(error) from error
        def config(self,endpoint):
            self._ready()
            if endpoint not in ('client','server'):raise ValueError('exact endpoint required')
            driver=self.drivers[endpoint]
            return dict(adobevalidator=str(driver),adobevalidatorhash=hashlib.sha256(driver.read_bytes()).hexdigest(),
                adobevalidatorbuild='validation-path-'+endpoint+'-v1',adobevalidatorthreads='1',adobevalidatetimeout='30')
        def _options(self,values):return options(self.root,values)
        def common_flags(self,policy):return recipes.flags(policy)
        def command(self,*,policy='require',options=()):
            self._ready();settings=[value for k,v in self.config('client').items() for value in ('-'+k,v)]
            return [self.binary,str(self.left),'ssh://localhost/'+str(self.right),'-sshcmd',str(self.launcher),
                '-servercmd',self.binary,'-batch','-auto','-fastcheck','false',*self.common_flags(policy),*settings,*self._options(options)]
        def sync(self,*,policy='require',options=(),success=True,exit=None,designated=None):
            # Explicit exit/designated serve source-owned successor cases; the
            # original assertions only ever pass success.
            if (type(success) is not bool or exit not in (None,0,1,2) or exit is not None and (exit==0)!=success
                or designated is not None and (type(designated) is not str or len(designated)<20 or success)):
                raise self._retain(ValueError('exact case expectation required'))
            return self._run(policy,options,(0 if success else 2) if exit is None else exit,designated)
        def cancel(self,name,incoming,previous,*,policy):
            self._ready()
            try:
                validate_fixture(name,incoming,previous,len(self.calls('client')))
                if policy not in ('require','warn') or self.cancel_fixture is not None:raise ValueError('one exact require/warn cancellation fixture required')
            except BaseException as error:raise self._retain(error) from error
            self.cancel_fixture=dict(name=name,incoming=incoming,previous=previous)
            result=self._run(policy,(),3)
            self.cancel_fixture=None
            return result
        def _intent(self,policy,options,expected_exit,designated=None):
            self.sequence+=1
            profile=(self.server_state/'endpoint.prf').read_text()
            before={endpoint:len(self.calls(endpoint)) for endpoint in ('client','server')}
            intent=dict(sequence=self.sequence,case_root=str(self.root),command=self.command(policy=policy,options=options),
                server_command=[self.binary,'-server','__new-rpc-mode',*self.common_flags(policy),*self._options(options)],
                expected_client_exit=expected_exit,before_fake_helper_counts=before,
                before_external_counts={kind:len(ns['records'](path.with_suffix('.calls.jsonl'))) for kind,path in (('copy',self.copy),('merge',self.merger))},
                helper_controls={endpoint:json.loads(self.drivers[endpoint].with_suffix('.control.json').read_text()) for endpoint in ('client','server')},
                server_profile_text=profile,server_profile_sha256=hashlib.sha256(profile.encode()).hexdigest(),
                prepared_scripts=dict(self.prepared_scripts),
                resource_release_authorized=False)
            if designated is not None:intent['designated']=designated
            if self.cancel_fixture is not None:
                f=self.cancel_fixture
                intent['cancellation']=dict(name=f['name'],incoming_sha256=hashlib.sha256(f['incoming']).hexdigest(),
                    incoming_bytes=len(f['incoming']),previous_sha256=hashlib.sha256(f['previous']).hexdigest(),previous_bytes=len(f['previous']))
            return intent
        def _run(self,policy,options,expected_exit,designated=None):
            self._ready()
            try:
                self.last_outcome=None;self.last_verdict=None
                intent=self._intent(policy,options,expected_exit,designated)
                before=intent['before_fake_helper_counts']
                self.active_intent=intent
                persist('INTENT',self,intent) # Must finish before any child adapter.
                outcome=invoke(self,intent);self.last_outcome=outcome
                verdict=audit(self,intent,outcome);self.last_verdict=verdict
                if (type(verdict) is not dict or verdict.get('external_children_settled') is not True
                    or verdict.get('resource_release_authorized') is not False
                    or type(verdict.get('client_returncode')) is not int
                    or verdict['client_returncode']!=intent['expected_client_exit']
                    or verdict.get('command')!=intent['command'] or type(verdict.get('log')) is not str):
                    raise ValueError('independent exact invocation/settlement verdict required')
                log=verdict['log'];(self.root/('run-%02d.log'%self.sequence)).write_text(log)
                for endpoint in ('client','server'):
                    if len(self.calls(endpoint))>before[endpoint]:
                        prefix='[semantic]' if endpoint=='client' else '[server: semantic]'
                        if not any(line.startswith(prefix) and '1 jobs per filesystem' in line for line in log.splitlines()):
                            raise ValueError('actual endpoint filesystem execution declaration missing')
                persist('ACCEPTED',self,dict(intent=intent,verdict=verdict,resource_release_authorized=False))
                self.active_intent=None
                return log
            except UnresolvedOwnership as error:self._retain(error);raise
            except BaseException as error:raise self._retain(error) from error
        def interruption(self,name,data,kind):
            self._ready()
            try:
                if kind not in ('complete','partial'):raise ValueError('two original owned producer-interruption controls only')
                return self.interrupt_adapter(self,name,data,kind)
            except UnresolvedOwnership as error:self._retain(error);raise
            except BaseException as error:raise self._retain(error) from error
    return Session
