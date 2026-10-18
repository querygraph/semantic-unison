"""Keep original helper-launcher behavior qualified after endpoint-mode addition."""
import argparse,hashlib,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--compiler',action='append',required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
records=[]
for index,compiler in enumerate(a.compiler):
 report=a.out/('helper-'+str(index)+'.json')
 subprocess.run([sys.executable,str(ROOT/'tests/helper_limits/run.py'),'--compiler',compiler,'--receipt',str(report)],check=True)
 records.append({'compiler':compiler,'path':str(report),'sha256':hashlib.sha256(report.read_bytes()).hexdigest()})
with (a.out/'RESULT.json').open('x') as f:json.dump({'scope':'Original helper control regression after endpoint alias; no real SDK/Photo','records':records},f,indent=2)
