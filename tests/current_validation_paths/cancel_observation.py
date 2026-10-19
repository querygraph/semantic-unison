"""Pre-SIGINT fence for the original receiving-into-client fixture.

Counter bytes are observations, not child-settlement proof. The caller owns the
unreaped direct client; later raw process/group records must independently bind
this exact helper observation before any resource release is considered.
"""
import hashlib,time


def validate_fixture(name,incoming,previous,before):
    if (type(name) is not str or '/' in name or name in ('','.','..')
        or type(incoming) is not bytes or type(previous) is not bytes
        or not 0<len(previous)<len(incoming)<=16*1048576
        or type(before) is not int or before<0):raise ValueError('bounded original cancellation fixture required')


def wait(session,name,incoming,previous,before,client,deadline):
    validate_fixture(name,incoming,previous,before)
    expected=hashlib.sha256(incoming).hexdigest();old=hashlib.sha256(previous).hexdigest()
    phase=min(deadline,time.monotonic()+30)
    while time.monotonic()<phase:
        if client.owner.reaped or client.owner.terminal():raise ValueError('client ended before observed active receiving fixture')
        values=session.calls('client')
        if len(values)!=before:
            if len(values)!=before+1:raise ValueError('exactly one new receiving helper required')
            value=values[-1];candidate=session.root.__class__(value['candidate']);destination=session.left/name
            if (value['endpoint']!='client' or value['mode']!='hang' or type(value['pid']) is not int
                or not 0<value['pid']<2**31 or value['pid']==client.owner.pid
                or candidate==destination or candidate.parent!=session.left or value['destination']!=str(destination)
                or value['sha256']!=expected or value['size']!=len(incoming) or value['destination_sha256']!=old
                or value['argv']!=['--unison-dng-validation-v1','--expected-sha256',expected,'--expected-size',
                    str(len(incoming)),'--threads','1','--',str(candidate)]):
                raise ValueError('exact owned receiving helper/candidate/destination binding required')
            st=candidate.lstat()
            if (st.st_dev,st.st_ino)!=(value['device'],value['inode']) or candidate.read_bytes()!=incoming:
                raise ValueError('receiving stage identity/bytes changed before cancellation')
            if destination.read_bytes()!=previous or (session.right/name).read_bytes()!=incoming:
                raise ValueError('source or old live receiver changed before cancellation')
            return dict(helper=value,client_pid=client.owner.pid,candidate_bytes_verified=True,
                previous_destination_preserved=True,source_preserved=True,
                helper_settlement_proved=False,resource_release_authorized=False)
        time.sleep(.01)
    raise TimeoutError('active receiving fixture observation expired; retain without signal')
