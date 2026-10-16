"""Compile the exact receiving collector prefix; no helper or SDK execution."""
import argparse,pathlib,tempfile,subprocess,hashlib,json
p=argparse.ArgumentParser();p.add_argument('--compiler',required=True);p.add_argument('--report',type=pathlib.Path,required=True);a=p.parse_args()
r=pathlib.Path(__file__).resolve().parents[2];source=r/'src/dngCandidateValidation.ml';text=source.read_text();prefix=text[:text.index('open Lwt')];assert prefix.startswith('module LiveSamples = struct')
w=pathlib.Path(tempfile.mkdtemp(prefix='unison-validation-live-'));(w/'control.ml').write_text(prefix+(r/'tests/validation_live/test.ml').read_text())
subprocess.run([a.compiler,'control.ml','-o','control'],cwd=w,check=True,timeout=20);x=subprocess.run([str(w/'control')],capture_output=True,text=True,timeout=10);(w/'test.log').write_text(x.stdout+x.stderr);print(x.stdout+x.stderr,end='')
a.report.write_text(json.dumps({'passed':x.returncode==0,'workspace':str(w),'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'test_sha256':hashlib.sha256((r/'tests/validation_live/test.ml').read_bytes()).hexdigest(),'scope':'exact bounded collector only; no receiving companion, helper, SDK, payload or Photo invocation'},indent=2)+'\n');raise SystemExit(x.returncode)
