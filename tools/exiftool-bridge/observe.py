#!/usr/bin/env python3
"""Read-only DNG interpretation alongside exact component hashes.

Caller coordinates CPU/IO. No admission, source copy, writer or sync policy here.
"""
import argparse,hashlib,importlib.util,json,os,stat,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'tests'),str(ROOT/'bench/sync')]
from component_remote.io import load,sha,identity
from shared_cpu_pool import UnresolvedOwnership,close_descriptors
from shared_process_owner import retain_after_record
from sdk_host_matrix.shared_child import invoke
MAX_INPUT=256*1024*1024
REV='3cd699a2e6633fcf28e39c260c71709b6a6049a7'

def unique(pairs):
 out={}
 for k,v in pairs:
  if k in out:raise ValueError('duplicate helper key')
  out[k]=v
 return out

def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode()

def projection(payload,engine):
 if payload.get('schema')!='unison-exiftool-rs-values/1' or payload.get('exiftool_version')!='13.59':raise ValueError('helper schema/version differs')
 tags=payload['maker_notes'];warnings=payload['warnings']
 if type(tags) is not list or len(tags)>4096 or type(warnings) is not list:raise ValueError('bounded typed observation required')
 groups={}
 for tag in tags:
  if set(tag)!={'group','document','name','id','value'} or any(type(tag[k]) is not str for k in ('group','document','name','id')):raise ValueError('tag shape differs')
  groups.setdefault(tag['group'],[]).append(tag)
 children=[]
 for group,records in sorted(groups.items()):
  records=sorted(records,key=canonical) # duplicates remain, including identical ones
  domain={'schema':'unison-exiftool-rs-projection/1','engine':engine,'group':group,'tags':records}
  fields=[dict(tag=tag,observation_sha256=hashlib.sha256(canonical(dict(
      schema='unison-exiftool-rs-field/1',engine=engine,group=group,tag=tag))).hexdigest()) for tag in records]
  children.append(dict(vendor_group=group,tags=records,field_observations=fields,
                       observation_sha256=hashlib.sha256(canonical(domain)).hexdigest()))
 return dict(plugin='dng/exiftool-rs/makernotes',schema='unison-exiftool-rs-projection/1',engine=engine,
  status='observed' if tags else 'no_makernote_tags_observed',children=children,warnings=warnings,
  library_version=payload.get('engine_version'),upstream_exiftool_version=payload['exiftool_version'],
  value_basis='typed exiftool-rs raw_value observations; not original source field encodings',
  coverage=dict(byte_offsets_available=False,unknown_bytes_excluded=False,complete_makernote_mapping=False),
  transfer_authority=False,semantic_merge_authority=False)

def checked_components(receipt):
 spec=importlib.util.spec_from_file_location('unison_component_inspector',ROOT/'tools/semantic-inspect/run.py')
 module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 build=load(receipt)
 if (build['schema']!='unison-semantic-inspector-build/1' or build['complete'] is not True
     or build['build_only'] is not True or type(build['build_exit']) is not int or build['build_exit']!=0
     or set(build['source_sha256'])!={str(p) for p in module.SOURCES}):raise ValueError('component build differs')
 for name,digest in build['source_sha256'].items():
  if sha(ROOT/name)!=digest:raise ValueError('component source changed')
 binary=Path(build['binary']);workspace=Path(build['workspace']);info=workspace.lstat()
 if (not workspace.is_absolute() or binary!=workspace/'semantic-inspect' or not stat.S_ISDIR(info.st_mode)
     or info.st_uid!=os.getuid() or info.st_mode & 0o077 or sha(binary)!=build['binary_sha256']):raise ValueError('component artifact changed')
 return binary


def observe(source,receipt,*,components_build=None):
 build=load(receipt)
 if build['schema']!='unison-exiftool-rs-build/1' or build['complete'] is not True or build['engine_revision']!=REV:raise ValueError('qualified bridge receipt required')
 binary=Path(build['binary'])
 if sha(binary)!=build['binary_sha256'] or sha(Path(__file__).with_name('main.rs'))!=build['wrapper_sha256']:raise ValueError('bridge executable/source pin changed')
 engine={k:build[k] for k in ('engine_revision','binary_sha256','wrapper_sha256')}
 before=identity(source)
 if before['st_nlink']!=1 or not 0<before['st_size']<=MAX_INPUT:raise ValueError('one bounded regular source required')
 fd=os.open(source,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK|os.O_CLOEXEC)
 calls=[]
 try:
  def stamp():return {k:getattr(os.fstat(fd),k) for k in before}
  if stamp()!=before:raise ValueError('opened source identity differs')
  digest=hashlib.sha256();offset=0
  while offset<before['st_size']:
   data=os.pread(fd,min(1048576,before['st_size']-offset),offset)
   if not data:raise ValueError('short source read')
   digest.update(data);offset+=len(data)
  outcome=invoke([str(binary),'--fd',str(fd)],dict(os.environ),time.monotonic()+60,pass_fds=(fd,))
  calls.append(outcome)
  if outcome['returncode'] or outcome['capture_truncated']:raise ValueError('bridge failed or output truncated')
  payload=json.loads(outcome['stdout'],object_pairs_hook=unique)
  interpreted=projection(payload,engine)
  components=None
  if components_build:
   inspector=checked_components(components_build)
   call=invoke([str(inspector),'--components','/dev/fd/'+str(fd)],dict(os.environ),time.monotonic()+60,pass_fds=(fd,));calls.append(call)
   if call['returncode'] or call['capture_truncated']:raise ValueError('component inspector failed')
   components=json.loads(call['stdout'],object_pairs_hook=unique)['target']
   if components.get('status')=='observed' and components['sha256']!=digest.hexdigest():raise ValueError('component/source hash differs')
  if stamp()!=before or identity(source)!=before:raise ValueError('source changed during interpretation')
  report=dict(schema='unison-dng-knowledge-observation/1',source_identity=before,source_sha256=digest.hexdigest(),
              container_components=components,interpretations=[interpreted],calls=calls)
 except UnresolvedOwnership as error:
  error.retained_fds=tuple(set(error.retained_fds)|{fd});error.exiftool_source_identity=before
  raise
 except BaseException as error:
  error.exiftool_calls=tuple(calls)
  close_descriptors([fd]);raise
 else:
  try:close_descriptors([fd])
  except UnresolvedOwnership as error:
   error.exiftool_observation=report
   raise
  return report

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--bridge-build',required=True,type=Path);p.add_argument('--components-build',type=Path);p.add_argument('source',type=Path);a=p.parse_args()
 print(json.dumps(observe(a.source,a.bridge_build,components_build=a.components_build),indent=2))
if __name__=='__main__':
 try:main()
 except UnresolvedOwnership as error:retain_after_record(lambda:print(repr(error),file=sys.stderr,flush=True))
