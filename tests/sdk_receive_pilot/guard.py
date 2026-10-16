#!/usr/bin/python3
"""Private finite-pilot executable guard; not an installed validator protocol."""
import hashlib,json,os,pathlib,stat,sys
def require(condition):
 if not condition:raise RuntimeError('finite pilot binding check failed')
config=json.loads(pathlib.Path(__file__).with_suffix('.json').read_text())
args=sys.argv[1:]
require(len(args)==9 and args[0]=='--unison-dng-validation-v1')
require(args[1]=='--expected-sha256' and args[3]=='--expected-size')
require(args[5:8]==['--threads','1','--'])
require(os.getpgid(0)==config['group'] and config['group']>1)
candidate=pathlib.Path(args[8]);require(candidate.is_absolute())
require(candidate.is_relative_to(pathlib.Path(config['workspace'])))
with candidate.open('rb') as stream:
 before=os.fstat(stream.fileno());require(stat.S_ISREG(before.st_mode))
 hasher=hashlib.sha256()
 while True:
  chunk=stream.read(1048576)
  if not chunk:break
  hasher.update(chunk)
 digest=hasher.hexdigest();after=os.fstat(stream.fileno())
require((before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns,before.st_ctime_ns)==(after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns,after.st_ctime_ns))
require(digest==args[2] and str(before.st_size)==args[4] and digest in config['allowed_sha256'])
executable=pathlib.Path(config['executable'])
require(hashlib.sha256(executable.read_bytes()).hexdigest()==config['executable_sha256'])
# Claim a finite call slot BEFORE replacing this process with the tool. No
# slot alone proves neither exec nor success: the caller also requires the
# bound return protocol and genuine terminal aggregate closure.
entry={'pid':os.getpid(),'pgid':os.getpgid(0),'candidate':str(candidate),'sha256':digest,'size':before.st_size,'mode':config['mode']}
for number in range(1,11):
 try:fd=os.open(str(pathlib.Path(config['calls'])/f'{number:02d}.json'),os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
 except FileExistsError:continue
 with os.fdopen(fd,'w') as output:json.dump(entry,output);output.flush();os.fsync(output.fileno())
 break
else:raise RuntimeError('finite SDK call cap reached')
os.execv(str(executable),[str(executable),*args])
