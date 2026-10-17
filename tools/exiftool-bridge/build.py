#!/usr/bin/env python3
"""Build a private read-only bridge from an exact local exiftool-rs git commit."""
import argparse,hashlib,io,json,os
from pathlib import Path
import subprocess,tarfile
REV='3cd699a2e6633fcf28e39c260c71709b6a6049a7'
HERE=Path(__file__).resolve().parent

def main():
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 a.output.mkdir(mode=0o700) # consumed once; never repair/reuse a failed build
 snapshot=a.output/'engine';snapshot.mkdir(mode=0o700)
 archive=subprocess.check_output(['git','-C',str(a.source),'archive',REV,'Cargo.toml','Cargo.lock','build.rs','src','locales'])
 with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
  if any(not (m.isfile() or m.isdir()) or Path(m.name).is_absolute() or '..' in Path(m.name).parts for m in tar):raise ValueError('unsafe source archive')
  tar.extractall(snapshot,filter='data')
 app=a.output/'bridge';(app/'src').mkdir(parents=True,mode=0o700)
 (app/'src/main.rs').write_bytes((HERE/'main.rs').read_bytes())
 (app/'Cargo.toml').write_text('[package]\nname="unison-exiftool-bridge"\nversion="0.1.0"\nedition="2021"\n[dependencies]\nexiftool-rs={path="../engine",default-features=false}\n')
 # Start from the engine's pinned dependency graph; Cargo adds only this root.
 (app/'Cargo.lock').write_bytes((snapshot/'Cargo.lock').read_bytes())
 env=dict(os.environ,CARGO_TARGET_DIR=str(a.output/'target'))
 subprocess.run(['cargo','generate-lockfile','--offline','--manifest-path',str(app/'Cargo.toml')],env=env,check=True)
 subprocess.run(['cargo','build','--offline','--locked','--jobs','2','--manifest-path',str(app/'Cargo.toml')],env=env,check=True)
 binary=a.output/'target/debug/unison-exiftool-bridge'
 sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
 receipt=dict(schema='unison-exiftool-rs-build/1',complete=True,engine_revision=REV,
  binary=str(binary),binary_sha256=sha(binary),wrapper_sha256=sha(HERE/'main.rs'),
  build_driver_sha256=sha(Path(__file__)),lock_sha256=sha(app/'Cargo.lock'),
  source_sha256={str(f.relative_to(snapshot)):sha(f) for f in sorted(snapshot.rglob('*')) if f.is_file()},
  rustc=subprocess.check_output(['rustc','--version'],text=True).strip(),
  cargo=subprocess.check_output(['cargo','--version'],text=True).strip(),native_executions=0)
 (a.output/'BUILD.json').write_text(json.dumps(receipt,indent=2)+'\n')
if __name__=='__main__':main()
