"""Exercise pinned complete inspectors on original tiny TIFFs and Unicode paths."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import struct
import subprocess
import tempfile

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--build-receipt', type=Path, action='append', required=True)
p.add_argument('--report', type=Path, required=True)
a = p.parse_args()
spec = importlib.util.spec_from_file_location('inspector_driver', Path(__file__).with_name('run.py'))
driver = importlib.util.module_from_spec(spec)
spec.loader.exec_module(driver)
w = Path(tempfile.mkdtemp(prefix='unison-inspector-integration-'))
os.chmod(w, 0o700)
def fixture(packet):
    data = bytearray(256)
    struct.pack_into('<2sHIH', data, 0, b'II', 42, 8, 4)
    for i, entry in enumerate(((273,4,1,160),(279,4,1,64),(700,1,16,96),(50706,1,4,257))):
        struct.pack_into('<HHII', data, 10+12*i, *entry)
    data[96:112] = packet.ljust(16, b' ')
    data[160:224] = bytes(range(64))
    return bytes(data)
base = w/'basis-é漢字"\n.dng'
target = w/'target-😀.dng'
other = w/'other.dng'
unsupported = w/'unsupported.dng'
base.write_bytes(fixture(b'<x>old</x>'))
target.write_bytes(fixture(b'<x>new</x>'))
data = bytearray(target.read_bytes()); data[170] ^= 1; other.write_bytes(data)
unsupported.write_bytes(b'original unsupported tiny fixture')
opaque = w/'opaque-change.dng'
data = bytearray(target.read_bytes()); data[250] ^= 1; opaque.write_bytes(data)
paths = [base,target,other,unsupported,opaque]
def identity(path):
    s = path.lstat()
    return [s.st_dev,s.st_ino,s.st_mode,s.st_size,s.st_mtime_ns,s.st_ctime_ns,s.st_nlink]
before = {str(path):(identity(path),hashlib.sha256(path.read_bytes()).hexdigest()) for path in paths}
runs = []
for receipt in a.build_receipt:
    binary = driver.checked_inspector(receipt)
    for label, argv, classification in [
        ('same',['--base',str(base),str(base)],'exact_bytes'),
        ('metadata',['--base',str(base),str(target)],'editable_metadata'),
        ('complement',['--base',str(base),str(other)],'other_bytes'),
        ('unsupported',[str(unsupported)],None),
    ]:
        r = subprocess.run([str(binary),*argv],capture_output=True,timeout=10)
        assert r.returncode == 0, r.stderr
        value = json.loads(r.stdout.decode('utf-8',errors='strict'))
        expected = argv[-1]
        assert bytes.fromhex(value['target']['path_bytes_hex']) == os.fsencode(expected)
        assert value['target']['path'] == expected
        if classification:
            assert value['classification'] == classification, value
            assert value['target']['status'] == value['basis']['status'] == 'supported'
            assert bytes.fromhex(value['basis']['path_bytes_hex']) == os.fsencode(argv[1])
        else:
            assert value['target']['status'] == 'unsupported'
        log = w/(str(len(runs))+'.json'); log.write_bytes(r.stdout)
        runs.append({'binary':str(binary),'binary_sha256':driver.sha(binary),'label':label,
                     'exit_code':r.returncode,'report':str(log),'report_sha256':driver.sha(log)})
# Exercise the newer layout view and advisory component forest independently
# of the unchanged strict-profile cases above. Every byte remains covered.
for receipt in a.build_receipt:
    binary=driver.checked_inspector(receipt)
    layout=subprocess.run([str(binary),'--profile','org.firstpair.dng-layout/0',
        '--base',str(base),str(target)],capture_output=True,timeout=10)
    assert layout.returncode==0,layout.stderr
    value=json.loads(layout.stdout)
    assert value['classification']=='uninterpreted_regions' and value['patch_eligible'] is True,value
    log=w/(str(len(runs))+'.json');log.write_bytes(layout.stdout)
    runs.append(dict(binary=str(binary),binary_sha256=driver.sha(binary),label='layout-profile',
        exit_code=0,report=str(log),report_sha256=driver.sha(log)))
    for label,changed,lane in [('component-metadata',target,'standard_metadata'),
                               ('component-pixels',other,'encoded_pixels'),
                               ('component-opaque',opaque,'opaque')]:
        basis=base if changed==target else target
        result=subprocess.run([str(binary),'--components','--base',str(basis),str(changed)],
            capture_output=True,timeout=10)
        assert result.returncode==0,result.stderr
        value=json.loads(result.stdout);left=value['basis'];right=value['target']
        assert left['status']==right['status']=='observed'
        assert left['sha256']==hashlib.sha256(basis.read_bytes()).hexdigest()
        assert right['sha256']==hashlib.sha256(changed.read_bytes()).hexdigest()
        assert left['sha256']!=right['sha256']
        assert left['projections'][lane]['sha256']!=right['projections'][lane]['sha256']
        for stable in set(left['projections'])-{lane}:
            assert left['projections'][stable]==right['projections'][stable],(label,stable)
        assert left['hash_bytes_requested']==right['hash_bytes_requested']==256
        log=w/(str(len(runs))+'.json');log.write_bytes(result.stdout)
        runs.append(dict(binary=str(binary),binary_sha256=driver.sha(binary),label=label,
            exit_code=0,report=str(log),report_sha256=driver.sha(log)))
for path in paths:
    assert before[str(path)] == (identity(path),hashlib.sha256(path.read_bytes()).hexdigest())
a.report.write_text(json.dumps({'passed':True,'workspace':str(w),'calls':len(runs),'runs':runs,
    'source_epoch_and_bytes_unchanged':True,'fixture_bytes':sum(p.stat().st_size for p in paths),
    'test_sha256':driver.sha(Path(__file__)),
    'scope':'original tiny TIFFs; full pinned inspector path/classification output; no Photo/camera/SDK/Adobe/EXglobal'},indent=2)+'\n')
print('PASS',len(runs),'complete inspector calls; original fixtures unchanged',flush=True)
