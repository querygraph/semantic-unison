"""Interpret the consumed saved timed run via its source-bound Darwin supplement."""
import argparse,hashlib,json
from pathlib import Path
from cached_benchmark.contract import read_bytes
from cached_benchmark.entry import write
from shared_cpu_pool import unique_object
import sync_timed_darwin_audit
import sync_timed_summary
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--input',type=Path,required=True)
p.add_argument('--input-sha256',required=True)
p.add_argument('--output',type=Path,required=True)
a=p.parse_args()
raw=read_bytes(a.input.resolve(),16*1048576);digest=hashlib.sha256(raw).hexdigest()
if digest!=a.input_sha256:raise ValueError('saved result hash differs')
proof,view=sync_timed_darwin_audit.audit(json.loads(raw,object_pairs_hook=unique_object),(ROOT/'bench/sync/ownership.py').read_bytes())
report=sync_timed_summary.summarize(view)
report['input']=dict(path=str(a.input.resolve()),bytes=len(raw),sha256=digest)
report['lifecycle_receipt_interpretation']='Source-derived Darwin census supplement, not raw literal true; parent needed independent recovery, not normal batch reap'
report['darwin_source_supplement']=dict(producer_sha256=proof['producer_sha256'],derived_receipt_locations=len(proof['derived_receipt_locations']),raw_input_unchanged=True)
write(a.output.resolve(),report)
for g in report['groups']:
 print(g['label'],g['mode'],g['workers'],'median',g['update_wall_seconds']['median'],flush=True)
