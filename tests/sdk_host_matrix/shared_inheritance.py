"""Actual disposable9FD inheritance controls; canonical inventory is a test double."""
import argparse,fcntl,json,os,sys,time
from pathlib import Path
from unittest.mock import patch
import shared_binding
from shared_child import invoke
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tests'))
from private_camera_receiving.close import close_descriptors
from shared_cpu_pool import UnresolvedOwnership
from shared_process_owner import retain_after_record

def child(path):
    packet=json.loads(Path(path).read_text());rows=packet['rows']
    start=dict(owner_pid=packet['parent_pid'],child_pid=os.getpid(),target=shared_binding.TARGET,
        command=packet['command'],cpu_credits=8,token_indexes=list(range(8)),io_mode='EX_GLOBAL',inherited_resource_fds=rows)
    # Inventory is deliberately disposable. Actual fstat and inherited handles
    # are real; no canonical pool or fabricated parent START is claimed.
    with patch.object(shared_binding,'inventory',return_value=tuple(tuple(x) for x in packet['identities'])):
        try:proof=shared_binding.verify(start,packet['command'],parent_pid=os.getppid(),worker_pid=os.getpid())
        except (ValueError,OSError) as error:
            print(json.dumps(dict(refused=repr(error))));return 7
    for row,lock in zip(rows,packet['paths']):
        fd=os.open(lock,os.O_RDWR|os.O_NOFOLLOW|os.O_CLOEXEC)
        try:
            try:fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except BlockingIOError:pass
            else:raise AssertionError('fresh description bypassed inherited lock')
        finally:close_descriptors([fd])
    print(json.dumps(dict(inherited_descriptions=len(proof['inherited_fds']),all_fresh_contenders_busy=True,canonical_inventory_double=True)))
    return 0

def controls(root):
    root=Path(root)
    if root.exists():raise ValueError('fresh disposable namespace required')
    root.mkdir(mode=0o700);summaries=[]
    for count in [9,8]:
        w=root/str(count);w.mkdir(mode=0o700);fds=[];paths=[];rows=[];identities=[];retained=False
        try:
            for i in range(9):
                p=w/('lock-'+str(i));fd=os.open(p,os.O_CREAT|os.O_EXCL|os.O_RDWR|os.O_CLOEXEC,0o600)
                fds.append(fd);paths.append(str(p));fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
                st=os.fstat(fd);identities.append((st.st_dev,st.st_ino));rows.append(dict(fd=fd,device=st.st_dev,inode=st.st_ino))
            argv=[sys.executable,str(Path(__file__).resolve()),'--child',str(w/'packet.json')]
            packet=dict(rows=rows,identities=identities,paths=paths,parent_pid=os.getpid(),command=argv)
            (w/'packet.json').write_text(json.dumps(packet)+'\n')
            out=invoke(argv,dict(os.environ),time.monotonic()+10,pass_fds=tuple(fds[:count]))
            assert out['returncode']==(0 if count==9 else 7),out
            assert out['client_cleanup']['reaped'] and out['client_cleanup']['other_group_members_absent_before_reap']
            observed=json.loads(out['stdout']);assert (observed.get('inherited_descriptions')==9)==(count==9)
        except UnresolvedOwnership as error:
            retained=True
            excluded=set(getattr(error,'uncertain_fds',()))
            error.retained_fds=tuple(dict.fromkeys(error.retained_fds+tuple(fd for fd in fds if fd not in excluded)))
            raise
        finally:
            if not retained:close_descriptors(fds)
        for p in paths:
            fd=os.open(p,os.O_RDWR|os.O_NOFOLLOW|os.O_CLOEXEC)
            try:fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
            finally:close_descriptors([fd])
        summaries.append(dict(passed_fds=count,outcome=out,all_parent_copies_closed_after_child_reap=True,all_fresh_locks_reacquired_after_closure=True))
    (root/'RESULT.json').write_text(json.dumps(dict(cases=summaries,scope='2actualPythonchildren/disposable9FDflock inherited/realfstat +canonicalinventory and childSTARTrecord doubles; no canonical IO/admission/SDK/Photo/payload'),indent=2)+'\n')
    print(json.dumps(dict(workspace=str(root),cases=2,actual_children_reaped=True,disposable_fds_closed=True)))
if __name__=='__main__':
    p=argparse.ArgumentParser();g=p.add_mutually_exclusive_group(required=True);g.add_argument('--child',type=Path);g.add_argument('--controls',type=Path);a=p.parse_args()
    if a.child:raise SystemExit(child(a.child))
    try:controls(a.controls)
    except UnresolvedOwnership as error:
        retain_after_record(lambda:print(json.dumps(dict(state='DISPOSABLE_OWNERSHIP_RETAINED',error=repr(error),retained_fds=error.retained_fds)),flush=True))
