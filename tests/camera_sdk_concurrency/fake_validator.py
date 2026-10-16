#!/Users/alexy/.local/share/uv/python/cpython-3.14.6-macos-x86_64-none/bin/python3.14
"""Original tiny-fixture validator only; no SDK and no photographic validity."""
import hashlib,os,re,stat,sys,time
from pathlib import Path

def main():
    args=sys.argv[1:]
    if len(args)!=9 or args[0]!='--unison-dng-validation-v1' or args[1]!='--expected-sha256' or args[3]!='--expected-size' or args[5:8]!=['--threads','1','--']:
        raise ValueError('exact synthetic protocol required')
    candidate=Path(args[8])
    if not candidate.is_absolute() or candidate.resolve()!=candidate:
        raise ValueError('canonical private candidate required')
    # Production helpers intentionally inherit only LANG/LC_ALL/PATH. Bind the
    # disposable namespace from the candidate, never a caller environment hint.
    roots=[p for p in candidate.parents if p.name=='right' and p.parent.name in ('stock','ox')
           and p.parent.parent.parent==Path('/private/tmp')
           and re.fullmatch(r'u-crs-[a-z0-9-]{3,26}',p.parent.parent.name)]
    if len(roots)!=1:raise ValueError('private synthetic receiving namespace required')
    right=roots[0]
    for path in (right,right.parent,right.parent.parent):
        st=os.lstat(path)
        if not stat.S_ISDIR(st.st_mode) or st.st_uid!=os.getuid() or stat.S_IMODE(st.st_mode)!=0o700:
            raise ValueError('owned private synthetic directories required')
    allowed={hashlib.sha256(data).hexdigest():len(data) for data in
        [b'original first synthetic candidate\0'*32,b'independent second synthetic candidate\0'*32]}
    if args[2] not in allowed or str(allowed[args[2]])!=args[4]:raise ValueError('original fixture identity required')
    fd=os.open(candidate,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK|os.O_CLOEXEC)
    try:
        st=os.fstat(fd)
        if not stat.S_ISREG(st.st_mode) or st.st_uid!=os.getuid() or st.st_nlink!=1 or st.st_size!=allowed[args[2]]:
            raise ValueError('bounded private synthetic candidate required')
        data=b''
        while len(data)<st.st_size:
            part=os.read(fd,st.st_size-len(data))
            if not part:raise ValueError('short synthetic read')
            data+=part
        if os.read(fd,1) or hashlib.sha256(data).hexdigest()!=args[2]:raise ValueError('synthetic bytes differ')
    finally:os.close(fd) # Any failure is a failed helper; its supervising owner must reap it.
    time.sleep(.2)
    print('UNISON-DNG-VALIDATION 1\ncandidate-sha256 '+args[2]+'\ncandidate-size '+args[4]+
          '\ndriver-build unison-concurrency-synthetic-v1\nstructure valid\ndecode success\nraw-digest valid\nerrors 0\nwarnings 0\nEND')
if __name__=='__main__':main()
