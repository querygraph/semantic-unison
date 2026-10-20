"""Cross-compiler peer cases on the retained Session; no subprocess or bare file IO.

The Session's client runs the plan's compiler and its server the pinned peer.
Each call takes its options and expectation from `cross_contract.call`, which
the parent replay recomputes independently.
"""
from current_validation_paths.cross_contract import CASES,call
from current_validation_paths.dng_cases import BASE,LEFT,RIGHT
from current_validation_paths.fs_cases import KEY,ACL_TEXT

PAYLOAD=bytes((i*131+7)%251 for i in range(300000))


def check(value,message):
    if not value:raise AssertionError(message)


def bind(Session):
    """Return one function per declared case for the given retained Session class."""
    def sync(s,name):
        policy,options,_,_,code,designated=call(name,s.sequence+1)
        return s.sync(policy=policy,options=options,success=code==0,exit=code if code==1 else None,designated=designated)
    def same(s,name,data):
        check((s.left/name).read_bytes()==data and (s.right/name).read_bytes()==data,'replicas differ from the expected bytes')
    def seed_update(s):
        (s.left/'a.txt').write_bytes(b'left seed');(s.right/'b.bin').write_bytes(PAYLOAD);sync(s,'seed-update')
        same(s,'a.txt',b'left seed');same(s,'b.bin',PAYLOAD)
        changed=PAYLOAD[:150000]+b'X'+PAYLOAD[150001:];(s.left/'b.bin').write_bytes(changed);sync(s,'seed-update');same(s,'b.bin',changed)
        check('Nothing to do: replicas have not changed since last sync.' in sync(s,'seed-update'),'no-op call propagated')
        return dict(result='seeded-updated-idle')
    def reverse_deletion(s):
        (s.left/'gone.txt').write_bytes(b'short-lived');sync(s,'reverse-deletion');same(s,'gone.txt',b'short-lived')
        (s.right/'gone.txt').unlink();sync(s,'reverse-deletion')
        check(not (s.left/'gone.txt').exists() and not (s.right/'gone.txt').exists(),'server-side deletion not propagated to the client')
        return dict(result='deleted-from-server')
    def conflict_skip(s):
        (s.left/'c.txt').write_bytes(b'common');sync(s,'conflict-skip');same(s,'c.txt',b'common')
        (s.left/'c.txt').write_bytes(b'client edit');(s.right/'c.txt').write_bytes(b'server edit!');sync(s,'conflict-skip')
        check((s.left/'c.txt').read_bytes()==b'client edit' and (s.right/'c.txt').read_bytes()==b'server edit!','skipped conflict changed a replica')
        return dict(result='conflict-skipped')
    def properties(s):
        f=s.left/'p.bin';f.write_bytes(b'properties');f.xattr(KEY,b'client');check(f.acl(ACL_TEXT)==ACL_TEXT,'fixture ACL not set')
        sync(s,'properties');r=s.right/'p.bin';same(s,'p.bin',b'properties')
        check(r.xattr(KEY)==b'client' and r.acl()==ACL_TEXT,'client properties not received by the peer')
        r.xattr(KEY,b'server-v2');check(r.acl('') is None,'fixture ACL not cleared');sync(s,'properties')
        check(f.xattr(KEY)==b'server-v2' and f.acl() is None,'peer properties not received by the client')
        return dict(result='properties-both-directions')
    def dng_receive(s):
        verify=s.original_assertions['verify_call']
        (s.left/'image.dng').write_bytes(BASE);sync(s,'dng-receive');same(s,'image.dng',BASE)
        (s.left/'image.dng').write_bytes(LEFT);sync(s,'dng-receive');same(s,'image.dng',LEFT)
        check(len(s.calls('server'))==1 and not s.calls('client'),'peer receive gate required')
        verify(s.calls('server')[0],LEFT,previous=BASE)
        (s.right/'image.dng').write_bytes(RIGHT);sync(s,'dng-receive');same(s,'image.dng',RIGHT)
        check(len(s.calls('client'))==1 and len(s.calls('server'))==1,'client receive gate required')
        verify(s.calls('client')[0],RIGHT,previous=LEFT,endpoint='client')
        return dict(result='gated-both-directions')
    bodies={'seed-update':seed_update,'reverse-deletion':reverse_deletion,'conflict-skip':conflict_skip,
            'properties':properties,'dng-receive':dng_receive}
    def case(name):
        def run(root,binary):
            s=Session(root,binary);result=dict(name=name,**bodies[name](s))
            check(s.sequence==dict((n,c) for n,c,_ in CASES)[name],'case omitted a declared call')
            return result
        return run
    return {name:case(name) for name,*_ in CASES}
