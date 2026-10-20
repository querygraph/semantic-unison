"""Filesystem property transition cases on the retained Session; no subprocess or bare file IO.

Each call takes its options from `fs_contract.call`, which the parent replay
recomputes independently. Bytes, xattrs and ACLs must match exactly after every
call. Hole allocation is recorded, not asserted: the case map records whether
the remote transfer keeps the source's holes.
"""
import os,pwd
from current_validation_paths.fs_contract import CASES,call

KEY='org.unison.fsprop.tag'
MiB=1048576
# The current user's synthetic member UUID, name and id, as acl_to_text renders it.
ACL_TEXT='!#acl 1\nuser:FFFFEEEE-DDDD-CCCC-BBBB-AAAA%08X:%s:%d:allow:read\n'%(os.getuid(),pwd.getpwuid(os.getuid()).pw_name,os.getuid())


def check(value,message):
    if not value:raise AssertionError(message)


def bind(Session):
    """Return one function per declared case for the given retained Session class."""
    def sync(s,name):
        policy,options,*_=call(name,s.sequence+1)
        return s.sync(policy=policy,options=options)
    def same(s,name):
        left,right=s.left/name,s.right/name
        check(right.read_bytes()==left.read_bytes(),'replica bytes differ')
        return left,right
    def nothing(log):check('Nothing to do: replicas have not changed since last sync.' in log,'default-off property propagated')
    def zero_length(s):
        f=s.left/'empty.bin';f.write_bytes(b'');sync(s,'zero-length')
        _,right=same(s,'empty.bin');check(right.stat().st_size==0,'zero-length file not created empty')
        f.write_bytes(b'z'*4096);sync(s,'zero-length');same(s,'empty.bin')
        f.write_bytes(b'');sync(s,'zero-length');_,right=same(s,'empty.bin');check(right.stat().st_size==0,'shrink to zero not propagated')
        f.unlink();sync(s,'zero-length');check(not (s.right/'empty.bin').exists(),'zero-length deletion not propagated')
        return dict(result='created-grown-shrunk-deleted')
    def holes(s):
        f=s.left/'holes.bin';f.write_bytes(b'a'*(8*MiB)+b'b'*4096);f.punch_hole(MiB,6*MiB)
        data=f.read_bytes();check(data[MiB:7*MiB]==bytes(6*MiB) and data[:MiB]==b'a'*MiB,'punched fixture bytes differ')
        source=f.stat().st_blocks*512;check(source<3*MiB,'fixture holes not allocated as holes')
        sync(s,'holes');_,right=same(s,'holes.bin');first=right.stat().st_blocks*512
        f.write_bytes(data[:8*MiB+10]+b'c'+data[8*MiB+11:]);f.punch_hole(MiB,6*MiB);sync(s,'holes');_,right=same(s,'holes.bin')
        return dict(result='bytes-exact',source_allocated_bytes=source,first_receiver_allocated_bytes=first,
            update_receiver_allocated_bytes=right.stat().st_blocks*512,file_bytes=8*MiB+4096)
    def xattr_default_off(s):
        f=s.left/'tagged.bin';f.write_bytes(b'tagged');sync(s,'xattr-default-off')
        f.xattr(KEY,b'v1');nothing(sync(s,'xattr-default-off'))
        check(KEY not in (s.right/'tagged.bin').xattr_names(),'xattr propagated without -xattrs')
        return dict(result='not-propagated')
    def xattr(s):
        f=s.left/'tagged.bin';r=s.right/'tagged.bin';f.write_bytes(b'tagged');sync(s,'xattr');check(KEY not in r.xattr_names(),'unexpected xattr')
        for value in (b'v1',b'v2-longer'):
            f.xattr(KEY,value);sync(s,'xattr');same(s,'tagged.bin');check(r.xattr(KEY)==value,'xattr value not propagated')
        f.xattr(KEY,remove=True);sync(s,'xattr');check(KEY not in r.xattr_names(),'xattr removal not propagated')
        check(r.xattr_names()==f.xattr_names(),'replica xattr names differ')
        return dict(result='set-changed-removed')
    def acl_default_off(s):
        f=s.left/'guarded.bin';f.write_bytes(b'guarded');sync(s,'acl-default-off')
        check(f.acl(ACL_TEXT)==ACL_TEXT,'fixture ACL not set');nothing(sync(s,'acl-default-off'))
        check((s.right/'guarded.bin').acl() is None,'ACL propagated without -acl')
        return dict(result='not-propagated')
    def acl(s):
        f=s.left/'guarded.bin';r=s.right/'guarded.bin';f.write_bytes(b'guarded');sync(s,'acl');check(r.acl() is None,'unexpected ACL')
        check(f.acl(ACL_TEXT)==ACL_TEXT,'fixture ACL not set');sync(s,'acl');same(s,'guarded.bin');check(r.acl()==ACL_TEXT,'ACL not propagated')
        check(f.acl('') is None,'fixture ACL not cleared');sync(s,'acl');check(r.acl() is None,'ACL removal not propagated')
        return dict(result='set-removed')
    bodies={'zero-length':zero_length,'holes':holes,'xattr-default-off':xattr_default_off,'xattr':xattr,
            'acl-default-off':acl_default_off,'acl':acl}
    def case(name):
        def run(root,binary):
            s=Session(root,binary);result=dict(name=name,**bodies[name](s))
            check(s.sequence==dict(CASES)[name],'case omitted a declared call')
            check(not s.calls('client') and not s.calls('server'),'a non-DNG transition invoked a validator')
            return result
        return run
    return {name:case(name) for name,_ in CASES}
