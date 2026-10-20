"""Built-in DNG merge cases on the retained Session; no subprocess or bare file IO.

A translation of `tests/dng_merge/run.py`: same synthetic containers, merge
policies and assertions. Each call takes its options, expected exit and
designated decline line from `dng_contract.call`, which the parent replay
recomputes independently.
"""
import struct
from current_validation_paths.dng_contract import OPTS,CASES,call


def fixture(rating='1',label='Blue',extra='',opaque=False,delete=False):
    b=bytearray(bytes((i*71+19)%256 for i in range(65536)));struct.pack_into('<2sHIH',b,0,b'II',42,8,4)
    packet=(f'<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" xmlns:xmp="http://ns.adobe.com/xap/1.0/"><rdf:Description rdf:about="" xmp:Rating="{rating}" xmp:Label="{label}" {extra}/></rdf:RDF>').encode()
    packet=packet.replace(b'xmp:Rating="'+rating.encode()+b'"',b'') if delete else packet;packet+=b' '*(8192-len(packet))
    for i,e in enumerate([(273,4,1,12288),(279,4,1,len(b)-12288),(700,1,8192,1024),(50706,1,4,1025)]):struct.pack_into('<HHII',b,10+12*i,*e)
    struct.pack_into('<I',b,58,0);b[1024:9216]=packet
    if opaque:b[-1]^=1
    return bytes(b)


BASE,LEFT,RIGHT,TARGET=fixture(),fixture('2'),fixture(label='Gold'),fixture('2','Gold')
INPUTS={'disjoint':(LEFT,RIGHT),'swapped':(RIGHT,LEFT),'competing':(LEFT,fixture('3')),
    'opaque-payload':(LEFT,fixture(label='Gold',opaque=True)),'unknown-field':(LEFT,fixture(label='Gold',extra='xmp:CreatorTool="other"')),
    'missing-base':(LEFT,RIGHT),'first-receiver-reject':(LEFT,RIGHT),'deleted-field':(LEFT,fixture(label='Gold',delete=True)),
    'stale-base':(LEFT,RIGHT),'second-receiver-reject':(LEFT,RIGHT),'policy-mismatch':(LEFT,RIGHT),
    'policy-disabled':(LEFT,RIGHT),'resource-fork':(LEFT,RIGHT)}
FORK_BYTES=b'private resource fork control'


def check(value,message):
    if not value:raise AssertionError(message)


def bind(Session):
    """Return one function per declared case for the given retained Session class."""
    def merge_call(s,name):
        policy,options,client,server,code,designated=call(name,2)
        s.control('image.dng',client=client,server=server)
        return s.sync(policy=policy,options=options,success=code==0,exit=code if code==1 else None,designated=designated)
    def case(name):
        def run(root,binary):
            s=Session(root,binary);verify=s.original_assertions['verify_call'];lft,rgt=INPUTS[name]
            policy,options,*_=call(name,1)
            (s.left/'image.dng').write_bytes(BASE);s.sync(policy=policy,options=options)
            check((s.right/'image.dng').read_bytes()==BASE,'seed common version differs')
            (s.left/'image.dng').write_bytes(lft);(s.right/'image.dng').write_bytes(rgt)
            if name=='stale-base':
                saved=s.client_state/'backup'/'image.dng'
                check(saved.read_bytes()==BASE,'saved common version absent');saved.write_bytes(fixture('5'))
            if name=='resource-fork':(s.left/'image.dng').resource_fork(FORK_BYTES)
            log=merge_call(s,name);result=dict(name=name)
            if name in ('disjoint','swapped'):
                check((s.left/'image.dng').read_bytes()==TARGET and (s.right/'image.dng').read_bytes()==TARGET,'merge did not converge')
                check('Built-in DNG scalar merge verified' in log,'built-in merge not reported')
                check(len(s.calls('client'))==1 and len(s.calls('server'))==1,'one receive gate per replica required')
                verify(s.calls('client')[0],TARGET,previous=lft,endpoint='client');verify(s.calls('server')[0],TARGET,previous=rgt)
                policy,options,*_=call(name,3);s.sync(policy=policy,options=options)
                check(len(s.calls('client'))==1 and len(s.calls('server'))==1,'no-op invoked a validator')
                result['result']='converged'
            elif name=='second-receiver-reject':
                check((s.left/'image.dng').read_bytes()==TARGET and (s.right/'image.dng').read_bytes()==rgt,'first replica must hold the merge, second its own bytes')
                check(len(s.calls('client'))==1 and len(s.calls('server'))==1,'both receive gates required')
                s.control('image.dng');policy,options,*_=call(name,3);retry=s.sync(policy=policy,options=options)
                check('Built-in DNG scalar merge verified' in retry,'retry did not merge again')
                check((s.left/'image.dng').read_bytes()==TARGET and (s.right/'image.dng').read_bytes()==TARGET,'retry did not converge')
                check(len(s.calls('client'))==2 and len(s.calls('server'))==2,'retry bypassed a receive gate')
                result.update(result='rejected-then-converged',first_committed=True)
            else:
                check((s.left/'image.dng').read_bytes()==lft and (s.right/'image.dng').read_bytes()==rgt,'declined merge changed a replica')
                if name=='resource-fork':check((s.left/'image.dng').resource_fork()==FORK_BYTES,'resource fork changed')
                result['result']='rejected'
            for replica in (s.left,s.right):
                check(not [n for n in replica.owned_names() if n.startswith('.unison.merge')],'merge temporary left behind')
            return result
        return run
    return {name:case(name) for name,*_ in CASES}
