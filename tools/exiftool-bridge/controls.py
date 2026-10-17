"""Actual library helper plus DNG component inspector; original1KiB fixtures."""
import argparse,copy,hashlib,json,struct,tempfile
from pathlib import Path
import observe

def fixture(serial=123456,make=b'Canon\0'):
 data=bytearray(1024);struct.pack_into('<2sHIH',data,0,b'II',42,8,7)
 entries=((271,2,len(make),160),(272,2,10,176),(34665,4,1,128),
          (50706,1,4,1025),(273,4,1,512),(279,4,1,64),(700,1,16,384))
 for i,e in enumerate(entries):struct.pack_into('<HHII',data,10+12*i,*e)
 struct.pack_into('<H',data,128,1);struct.pack_into('<HHII',data,130,37500,7,18,256)
 data[160:160+len(make)]=make;data[176:186]=b'Canon EOS\0'
 struct.pack_into('<H',data,256,1);struct.pack_into('<HHII',data,258,12,4,1,serial)
 data[384:400]=b'<x>one</x>      ';data[512:576]=b'P'*64
 return bytes(data)

def main():
 p=argparse.ArgumentParser();p.add_argument('--bridge-build',type=Path,required=True);p.add_argument('--components-build',type=Path,required=True);p.add_argument('--report',type=Path,required=True);a=p.parse_args()
 out=Path(tempfile.mkdtemp(prefix='unison-exiftool-controls-'));reports=[]
 for i,data in enumerate((fixture(),fixture(654321))):
  source=out/(str(i)+'.dng');source.write_bytes(data);source.chmod(0o400)
  before=observe.identity(source)
  report=observe.observe(source,a.bridge_build,components_build=a.components_build)
  assert before==observe.identity(source) and hashlib.sha256(source.read_bytes()).hexdigest()==report['source_sha256']
  assert report['container_components']['status']=='observed'
  view=report['interpretations'][0]
  assert view['status']=='observed' and view['children'] and not view['transfer_authority']
  assert any(t['name']=='SerialNumber' for c in view['children'] for t in c['tags'])
  reports.append(report)
 left,right=reports
 assert left['source_sha256']!=right['source_sha256']
 assert left['container_components']['projections']['encoded_pixels']==right['container_components']['projections']['encoded_pixels']
 assert left['container_components']['projections']['private_metadata']!=right['container_components']['projections']['private_metadata']
 assert left['interpretations'][0]['children']!=right['interpretations'][0]['children']
 # Existing inspector entry point composes both actual subprocesses.
 import sys,time
 from sdk_host_matrix.shared_child import invoke
 cli=invoke([sys.executable,str(observe.ROOT/'tools/semantic-inspect/run.py'),
  '--use-build',str(a.components_build),'--exiftool-build',str(a.bridge_build),'--','--components',str(out/'0.dng')],
  dict(__import__('os').environ),time.monotonic()+30)
 assert cli['returncode']==0 and not cli['capture_truncated']
 cli_report=json.loads(cli['stdout']);assert cli_report['source_sha256']==left['source_sha256']
 assert cli_report['interpretations']==left['interpretations']
 # Default entry point retains its original schema and component-only behavior.
 default=invoke([sys.executable,str(observe.ROOT/'tools/semantic-inspect/run.py'),
  '--use-build',str(a.components_build),'--','--components',str(out/'0.dng')],dict(__import__('os').environ),time.monotonic()+30)
 assert default['returncode']==0 and json.loads(default['stdout'])['schema']=='unison-dng-components/0'
 # Stable grouping, duplicate preservation and engine-bound composability.
 engine=left['interpretations'][0]['engine'];tag=left['interpretations'][0]['children'][0]['tags'][0]
 base=dict(schema='unison-exiftool-rs-values/1',exiftool_version='13.59',maker_notes=[tag,tag],warnings=[])
 assert len(observe.projection(base,engine)['children'][0]['tags'])==2
 changed=copy.deepcopy(engine);changed['engine_revision']='different'
 assert observe.projection(base,engine)['children'][0]['observation_sha256']!=observe.projection(base,changed)['children'][0]['observation_sha256']
 assert observe.projection(dict(base,maker_notes=[]),engine)['status']=='no_makernote_tags_observed'
 # Adding another decoded field preserves an existing field observation hash.
 extra=copy.deepcopy(tag);extra['name']='OriginalSyntheticField'
 a_view=observe.projection(dict(base,maker_notes=[tag]),engine)['children'][0]
 b_view=observe.projection(dict(base,maker_notes=[tag,extra]),engine)['children'][0]
 preserved=[f for f in b_view['field_observations'] if f['tag']==tag]
 assert preserved==a_view['field_observations']
 assert a_view['observation_sha256']!=b_view['observation_sha256']
 a.report.write_text(json.dumps(dict(passed=True,reports=reports,cli=cli,default_cli=default,fixture_directory=str(out),scope='original tiny TIFF/DNG; actual pinned exiftool-rs library plus existing stock component inspector; no camera/Adobe/SDK/transport'),indent=2)+'\n')
 print('PASS actual Canon MakerNote decoding; changed private values / unchanged encoded pixels; duplicate and engine domains')
if __name__=='__main__':main()
