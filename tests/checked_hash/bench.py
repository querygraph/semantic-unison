#!/usr/bin/env python3
import argparse,pathlib,subprocess,tempfile,hashlib,json,statistics,shutil
p=argparse.ArgumentParser();p.add_argument('--compiler',required=True);p.add_argument('--receipt',type=pathlib.Path,required=True);a=p.parse_args()
r=pathlib.Path(__file__).resolve().parents[2];w=pathlib.Path(tempfile.mkdtemp(prefix='unison-hash-lookup-bench-',dir='/private/tmp'))
for n in ['semanticHash.ml','semanticHash.mli','semanticHash_stubs.c']:shutil.copyfile(r/'src'/n,w/n)
old=subprocess.check_output(['git','show','e519dda:src/semanticHash.ml'],cwd=r);(w/'oldHash.ml').write_bytes(old);shutil.copyfile(r/'src/semanticHash.mli',w/'oldHash.mli');shutil.copyfile(r/'tests/checked_hash/bench.ml',w/'bench.ml')
x=subprocess.run([a.compiler,'-I','+unix','unix.cmxa','semanticHash_stubs.c','oldHash.mli','oldHash.ml','semanticHash.mli','semanticHash.ml','bench.ml','-o','bench'],cwd=w,capture_output=True,text=True);(w/'compile.log').write_text(x.stdout+x.stderr);x.check_returncode()
x=subprocess.run([str(w/'bench')],cwd=w,capture_output=True,text=True,timeout=60);(w/'bench.log').write_text(x.stdout+x.stderr);x.check_returncode();rows={}
for line in x.stdout.splitlines():
 label,cpu,wall=line.split();rows.setdefault(label,[]).append(dict(cpu=float(cpu),wall=float(wall)))
assert all(len(v)==9 for v in rows.values())
medians={k:{field:statistics.median(v[field] for v in values) for field in ['cpu','wall']} for k,values in rows.items()}
H=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
j=dict(schema='unison-hash-round-lookup-microbench/1',compiler=a.compiler,version=subprocess.check_output([a.compiler,'-version'],text=True).strip(),workspace=str(w),samples=rows,medians=medians,newToOldCpuRatio={kind:medians['new-'+kind]['cpu']/medians['old-'+kind]['cpu'] for kind in ['reference','native']},inputBytesPerSample=1048576,oldSourceCommit='e519dda',compiledInputs={p.name:H(p) for p in w.iterdir() if p.suffix in ['.ml','.mli','.c']},binarySha256=H(w/'bench'),logSha256=H(w/'bench.log'),scope='Cached string microbenchmark,9samples,alternating reference order; not full worker/sync/storage performance')
a.receipt.write_text(json.dumps(j,indent=2)+'\n');print(j['version'],j['newToOldCpuRatio'],w)
