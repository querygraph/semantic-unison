"""Original assertions with owned files and trusted retained process adapters.

This module launches nothing. invoke/audit/interrupt are pinned executor source,
never packet callbacks; an admitted owner must supply them and all resource FDs.
"""
import hashlib,json
from shared_cpu_pool import UnresolvedOwnership
from sdk_merge_receiving.admission import PYTHON
from current_validation_paths.cancel_observation import validate_fixture


def factory(legacy,*,files,binary,repository,invoke,audit,interrupt,persist):
    if not all(callable(f) for f in (invoke,audit,interrupt,persist)):raise ValueError('owned source adapters required')
    ns=legacy.__init__.__globals__;ns['ADMISSION_OPTIONS']=['-semanticvolumejobs','1']
    ns['HELPER_CONFIG']={};ns['SERVER_HELPER_DESCRIPTORS']=None
    templates={name:ns[name] for name in ('DRIVER','COPY','MERGE')}
    if not all(text.startswith('#!/usr/bin/python3\n') for text in templates.values()):raise ValueError('qualified original helper template spelling required')
    def replace_once(text,before,after):
        if text.count(before)!=1:raise ValueError('exact original external fixture source binding required')
        return text.replace(before,after,1)
    old_hold="if control['interrupt']!='no':\n    while True:time.sleep(.02)\n"
    templates['COPY']=replace_once(templates['COPY'],old_hold,"if control['interrupt']!='no':\n    while not here.with_suffix('.release').exists():time.sleep(.02)\n")
    templates['COPY']=replace_once(templates['COPY'],'pid=os.getpid(),interrupt=','pid=os.getpid(),group=os.getpgrp(),interrupt=')
    templates['MERGE']=replace_once(templates['MERGE'],'import hashlib,json,pathlib,sys,resource','import hashlib,json,pathlib,sys,resource,os')
    templates['MERGE']=replace_once(templates['MERGE'],"result=hashlib.sha256(result).hexdigest(),output=sys.argv[3],","result=hashlib.sha256(result).hexdigest(),output=sys.argv[3],pid=os.getpid(),group=os.getpgrp(),")
    imports=[str(repository)+'/tests',str(repository)+'/tests/sdk_host_matrix',str(repository)+'/bench/sync']
    launcher='#!'+PYTHON+'\nimport sys\nsys.path[:0]='+repr(imports)+'\nfrom sdk_merge_receiving.child_entry import launcher_main\nraise SystemExit(launcher_main())\n'
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
                self.drivers={}
                for endpoint in ('client','server'):
                    path=self.root/(endpoint+'-validator.py');path.write_text(templates['DRIVER'].replace('#!/usr/bin/python3\n','#!'+PYTHON+'\n',1));path.chmod(0o700)
                    self.drivers[endpoint]=path
                self.copy=self.root/'external-copy.py';self.copy.write_text(templates['COPY'].replace('#!/usr/bin/python3\n','#!'+PYTHON+'\n',1));self.copy.chmod(0o700)
                self.copy.with_suffix('.control.json').write_text(json.dumps(dict(interrupt='no')))
                self.merger=self.root/'merge.py';self.merger.write_text(templates['MERGE'].replace('#!/usr/bin/python3\n','#!'+PYTHON+'\n',1));self.merger.chmod(0o700)
                self.launcher=self.root/'loopback.py';self.launcher.write_text(launcher);self.launcher.chmod(0o700)
                config=self.config('server');config['semanticvolumejobs']='1'
                (self.server_state/'endpoint.prf').write_text(''.join(k+' = '+v+'\n' for k,v in config.items()))
                self.control('image.dng')
                self.prepared_scripts={str(path):hashlib.sha256(path.read_bytes()).hexdigest() for path in (*self.drivers.values(),self.copy,self.merger,self.launcher)}
            except UnresolvedOwnership as error:self._retain(error);raise
            except BaseException as error:raise self._retain(error) from error
        def config(self,endpoint):
            self._ready()
            if endpoint not in ('client','server'):raise ValueError('exact endpoint required')
            driver=self.drivers[endpoint]
            return dict(adobevalidator=str(driver),adobevalidatorhash=hashlib.sha256(driver.read_bytes()).hexdigest(),
                adobevalidatorbuild='validation-path-'+endpoint+'-v1',adobevalidatorthreads='1',adobevalidatetimeout='30')
        def _options(self,options):
            values=list(options);i=0
            while i<len(values):
                flag=values[i]
                if flag=='-xferbycopying=false':i+=1;continue
                expected={'-copythreshold':'0','-copyprog':str(self.copy),'-copyprogrest':str(self.copy),
                    '-merge':'Name *.dng -> '+str(self.merger)+' CURRENT1 CURRENT2 NEW'}
                if flag not in expected or i+1>=len(values) or values[i+1]!=expected[flag]:raise ValueError('undeclared original case option')
                i+=2
            return values
        def common_flags(self,policy):
            if policy not in ('off','warn','require'):raise ValueError('exact validation policy required')
            return ['-clone','off','-semanticworkers','2','-semanticcpubudget','2','-maxthreads','1',
                '-semanticvolumejobs','1','-semanticmaxinflight','4','-adobevalidate',policy,
                '-adobevalidatescope','received','-debug','copy','-debug','semantic',
                '-debug','validation-process','-debug','validation-group','-debug','validation-input','-debug','external-process']
        def command(self,*,policy='require',options=()):
            self._ready();settings=[value for k,v in self.config('client').items() for value in ('-'+k,v)]
            return [self.binary,str(self.left),'ssh://localhost/'+str(self.right),'-sshcmd',str(self.launcher),
                '-servercmd',self.binary,'-batch','-auto','-fastcheck','false',*self.common_flags(policy),*settings,*self._options(options)]
        def sync(self,*,policy='require',options=(),success=True):
            if type(success) is not bool:raise self._retain(ValueError('exact case expectation required'))
            return self._run(policy,options,0 if success else 2)
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
        def _run(self,policy,options,expected_exit):
            self._ready()
            try:
                self.last_outcome=None;self.last_verdict=None
                self.sequence+=1
                before={endpoint:len(self.calls(endpoint)) for endpoint in ('client','server')}
                intent=dict(sequence=self.sequence,case_root=str(self.root),command=self.command(policy=policy,options=options),
                    server_command=[self.binary,'-server','__new-rpc-mode',*self.common_flags(policy),*self._options(options)],
                    expected_client_exit=expected_exit,before_fake_helper_counts=before,
                    before_external_counts={kind:len(ns['records'](path.with_suffix('.calls.jsonl'))) for kind,path in (('copy',self.copy),('merge',self.merger))},
                    helper_controls={endpoint:json.loads(self.drivers[endpoint].with_suffix('.control.json').read_text()) for endpoint in ('client','server')},
                    server_profile_sha256=hashlib.sha256((self.server_state/'endpoint.prf').read_bytes()).hexdigest(),
                    resource_release_authorized=False)
                if self.cancel_fixture is not None:
                    f=self.cancel_fixture
                    intent['cancellation']=dict(name=f['name'],incoming_sha256=hashlib.sha256(f['incoming']).hexdigest(),
                        incoming_bytes=len(f['incoming']),previous_sha256=hashlib.sha256(f['previous']).hexdigest(),previous_bytes=len(f['previous']))
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
                return interrupt(self,name,data,kind)
            except UnresolvedOwnership as error:self._retain(error);raise
            except BaseException as error:raise self._retain(error) from error
    return Session
