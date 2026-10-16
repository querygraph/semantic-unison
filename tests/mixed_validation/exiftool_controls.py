"""Actual pinned Perl ExifTool version/readonly generated-XMP compatibility controls."""
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import time

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'tests'),str(ROOT/'tests/sdk_host_matrix')]
from mixed_validation.metadata_dependencies import capture,verify,SCRIPT,VERSION
from mixed_validation.artifacts import verified_hash
from private_maker_execute import save
from shared_child import invoke
from shared_cpu_pool import UnresolvedOwnership
from shared_process_owner import retain_after_record


def main():
    root=Path(tempfile.mkdtemp(prefix='unison-exiftool-1359-',dir='/private/tmp'))
    inventory=ROOT/'doc/mixed-exiftool-package-inventory-v2.json'
    record=json.loads(inventory.read_text())
    item=lambda p:dict(path=str(p),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
    contract=dict(version=VERSION,executable=record['executable'],inventory=item(inventory))
    before=verify(contract)
    source=root/'-generated Unicode é.xmp'
    source.write_text('''<?xml version="1.0" encoding="UTF-8"?>
<x:xmpmeta xmlns:x="adobe:ns:meta/"><rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
<rdf:Description rdf:about="" xmlns:xmp="http://ns.adobe.com/xap/1.0/" xmp:Rating="3" xmp:Label="Unison é"/>
</rdf:RDF></x:xmpmeta>''')
    binding=item(source);epoch=verified_hash(binding)
    commands=[[str(SCRIPT),'-config','','-ver'],[str(SCRIPT),'-config','','-j','-s','-XMP:Rating','-XMP:Label','-ExifToolVersion','--',str(source)]]
    calls=[]
    for command in commands:
        out=invoke(command,dict(PATH='/usr/bin:/bin',LANG='C',LC_ALL='C'),time.monotonic()+20)
        calls.append(out);save(root/('CALL-'+str(len(calls))+'.json'),out)
        proof=out['client_cleanup']
        assert proof['reaped'] and proof['other_group_members_absent_before_reap']
        assert out['returncode']==0 and not out['capture_truncated'] and not out['timed_out']
    assert calls[0]['stdout'].strip()==VERSION
    rows=json.loads(calls[1]['stdout'])
    assert len(rows)==1 and rows[0]['SourceFile']==str(source)
    assert str(rows[0]['ExifToolVersion'])==VERSION and rows[0]['Rating']==3 and rows[0]['Label']=='Unison é'
    verified_hash(binding,expected_epoch=epoch)
    after=verify(contract);assert before==after
    result=dict(calls=calls,package=contract,package_proof=after,generated_input=binding,
                source_pins={str(p):item(p) for p in (Path(__file__).resolve(),ROOT/'tests/mixed_validation/metadata_dependencies.py')},
                SDK_invoked=False,photo_payload_opened=False,shared_system_installation_changed=False,
                scope='Pinned Perl13.59 direct version and readonly generated Unicode XMP, exact mixed-probe argv. No SDK/mixed native run or new camera/semantic/pixel qualification.')
    save(root/'RESULT.json',result);print(json.dumps(result),flush=True)


if __name__=='__main__':
    try:main()
    except UnresolvedOwnership as error:retain_after_record(lambda:print(repr(error),flush=True))
