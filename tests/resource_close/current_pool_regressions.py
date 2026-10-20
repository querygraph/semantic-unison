"""Run original fixed duplicate and nested-reader faults on one current epoch."""
import argparse,hashlib,json,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--receipt',action='append',required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
reports={}
for name in ['worker_fault_run.py','reader_fault_run.py']:
 report=a.out/(name+'.json')
 argv=[sys.executable,str(HERE/name),'--report',str(report)]
 for receipt in a.receipt:argv+=['--receipt',receipt]
 subprocess.run(argv,check=True)
 reports[name]={'path':str(report),'bytes':report.stat().st_size,'sha256':hashlib.sha256(report.read_bytes()).hexdigest()}
with (a.out/'RESULT.json').open('x') as f:json.dump({'scope':'Original fixed duplicate+reader controls against current pool epoch, no fuzz/SDK/Photo input','reports':reports,'runner_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},f,indent=2)
