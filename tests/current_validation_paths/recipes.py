"""Pure generated-script and exact endpoint recipes; no filesystem/process IO."""
import ast,hashlib
from pathlib import PurePosixPath as Path
from sdk_merge_receiving.admission import PYTHON


def literal_templates(source):
    result={}
    for node in ast.parse(source).body:
        if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name) and node.targets[0].id in ('DRIVER','COPY','MERGE'):
            if node.targets[0].id in result:raise ValueError('duplicate fixture template')
            result[node.targets[0].id]=ast.literal_eval(node.value)
    if set(result)!={'DRIVER','COPY','MERGE'}:raise ValueError('all original fixture templates required')
    return result


def scripts(ns,repository):
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
    qualified=lambda text:text.replace('#!/usr/bin/python3\n','#!'+PYTHON+'\n',1)
    return {'client-validator.py':qualified(templates['DRIVER']),'server-validator.py':qualified(templates['DRIVER']),
        'external-copy.py':qualified(templates['COPY']),'merge.py':qualified(templates['MERGE']),'loopback.py':launcher,
        'abort-loopback.py':launcher.replace('sdk_merge_receiving.child_entry import launcher_main','clone_interruption_transport import launcher_main',1)}


def flags(policy):
    if policy not in ('off','warn','require'):raise ValueError('exact validation policy required')
    return ['-clone','off','-semanticworkers','2','-semanticcpubudget','2','-maxthreads','1',
        '-semanticvolumejobs','1','-semanticmaxinflight','4','-adobevalidate',policy,
        '-adobevalidatescope','received','-debug','copy','-debug','semantic',
        '-debug','validation-process','-debug','validation-group','-debug','validation-input','-debug','external-process']


def options(root,values):
    root=Path(root);values=list(values);i=0
    while i<len(values):
        flag=values[i]
        if flag=='-xferbycopying=false':i+=1;continue
        expected={'-copythreshold':'0','-copyprog':str(root/'external-copy.py'),'-copyprogrest':str(root/'external-copy.py'),
            '-merge':'Name *.dng -> '+str(root/'merge.py')+' CURRENT1 CURRENT2 NEW'}
        if flag not in expected or i+1>=len(values) or values[i+1]!=expected[flag]:raise ValueError('undeclared original case option')
        i+=2
    return values


def config(root,endpoint,script_sources,timeout='30'):
    if endpoint not in ('client','server') or timeout not in ('1','30'):raise ValueError('exact endpoint config required')
    name=endpoint+'-validator.py'
    return dict(adobevalidator=str(Path(root)/name),adobevalidatorhash=hashlib.sha256(script_sources[name].encode()).hexdigest(),
        adobevalidatorbuild='validation-path-'+endpoint+'-v1',adobevalidatorthreads='1',adobevalidatetimeout=timeout)


def phase(row,sequence,script_sources,binary):
    if type(sequence) is not int or not 1<=sequence<=row['max_CLI_calls']:raise ValueError('bounded exact original case sequence required')
    root=Path(row['directory']);family=row['family'];args=row['arguments'];policy='require';code=0;opts=[]
    client=server='pass';directory=False
    names={'resumed':'resumed.DNG','external':'external.dng','moved':'a-moved.dng','merged':'merge.dng','timed_out':'timed.dng','cancelled':'cancelled.dng','directory_admission':'image.dng'}
    name=names[family]
    copyopts=['-copythreshold','0','-copyprog',str(root/'external-copy.py'),'-copyprogrest',str(root/'external-copy.py'),'-xferbycopying=false']
    mergeopts=['-merge','Name *.dng -> '+str(root/'merge.py')+' CURRENT1 CURRENT2 NEW']
    if family=='resumed':
        if sequence==1:opts=copyopts;code='connection-failure'
        else:
            server=args[1] if sequence==2 else 'pass'
            opts=['-xferbycopying=false'] if sequence==2 or sequence==3 and args[1]!='pass' else []
            if sequence==2 and args[1]!='pass':code=2
    elif family=='external':
        rejected=args[1]=='require' and args[0]!='pass' or args[0]=='mutate'
        server=args[0] if sequence==1 or not rejected else 'pass'
        if sequence==1:policy=args[1];opts=copyopts;code=2 if rejected else 0
        elif sequence==2 and rejected:opts=['-xferbycopying=false']
    elif family=='moved':
        if sequence==1:name='z-original.dng'
        else:server=args[0] if sequence==2 or not(args[0]!='pass' and args[1]=='require') else 'pass'
        if sequence==2:policy=args[1];code=2 if args[0]!='pass' and policy=='require' else 0
    elif family=='merged':
        if sequence==2:client,server=args;opts=mergeopts;code=0 if args==['pass','pass'] else 2
        elif sequence==3 and args!=['pass','pass']:opts=mergeopts
    elif family=='timed_out' and sequence==2:server='hang';policy=args[0];code=0 if policy=='warn' else 2
    elif family=='cancelled' and sequence==2:client='hang';policy=args[0];code=3
    elif family=='directory_admission':server='delay';directory=True
    controls={endpoint:dict(endpoint=endpoint,build='validation-path-'+endpoint+'-v1',mode=mode,
        destination=str(root/('left' if endpoint=='client' else 'right')/name)) for endpoint,mode in (('client',client),('server',server))}
    if directory:controls['server'].update(destination=str(root/'right/parallel-directory'),directory=True)
    settings=[value for key,setting in config(root,'client',script_sources).items() for value in ('-'+key,setting)]
    launcher=root/('abort-loopback.py' if family=='resumed' and sequence==1 else 'loopback.py')
    command=[binary,str(root/'left'),'ssh://localhost/'+str(root/'right'),'-sshcmd',str(launcher),'-servercmd',binary,
        '-batch','-auto','-fastcheck','false',*flags(policy),*settings,*opts]
    server_config=config(root,'server',script_sources,'1' if family=='timed_out' and sequence>=2 else '30')
    server_config['semanticvolumejobs']='1'
    profile=''.join(key+' = '+value+'\n' for key,value in server_config.items())
    return dict(command=command,server_command=[binary,'-server','__new-rpc-mode',*flags(policy),*opts],
        expected_client_exit=code,helper_controls=controls,server_profile_text=profile,
        server_profile_sha256=hashlib.sha256(profile.encode()).hexdigest(),
        prepared_scripts={str(root/name):hashlib.sha256(text.encode()).hexdigest() for name,text in script_sources.items()})


def proxy_source(repository,config):
    import json
    module='current_validation_paths.producer_proxy' if 'producer_observer' in config else 'sdk_merge_receiving.child_entry'
    imports=[repository+'/tests',repository+'/tests/sdk_host_matrix',repository+'/bench/sync']
    literal=json.dumps(config,sort_keys=True,allow_nan=False,separators=(',',':'))
    return '#!'+PYTHON+'\nimport json,sys\nsys.path[:0]='+repr(imports)+'\nfrom '+module+' import proxy_main\nraise SystemExit(proxy_main(json.loads('+repr(literal)+')))\n'


def producer_observer(row,identity):
    data=bytes(range(256))*8192+b'synthetic resume tail\n';kind=row['arguments'][0]
    staged=data if kind=='complete' else data[:len(data)//2]
    return dict(root=row['directory'],identity=list(identity),name='resumed.DNG',kind=kind,source_bytes=len(data),
        source_sha256=hashlib.sha256(data).hexdigest(),staged_bytes=len(staged),staged_sha256=hashlib.sha256(staged).hexdigest())


def cancellation_fixture():
    previous=b'previous live cancellation fixture\n'*128
    incoming=previous+b'reverse receive that must never commit after cancellation'
    return dict(name='cancelled.dng',incoming_sha256=hashlib.sha256(incoming).hexdigest(),incoming_bytes=len(incoming),
        previous_sha256=hashlib.sha256(previous).hexdigest(),previous_bytes=len(previous))
