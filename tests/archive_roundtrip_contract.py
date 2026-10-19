"""Exact ten-stage private archive downgrade scenario; no process or IO grants.

The owning driver must separately prove every child, server and descriptor closed.
A designated missing-base refusal is functional evidence, never a closure proof.
"""
import hashlib
import struct

STAGES = ('seed', 'merge-before-downgrade', 'baseline-noop', 'baseline-update',
          'current-reopen', 'missing-base-refusal', 'restore-known-common',
          'captured-common-update', 'merge-after-baseline', 'final-noop')
EXPECTED = (('1','Blue'),('2','Gold'),('2','Gold'),('3','Gold'),('3','Gold'),
            None,('3','Gold'),('4','Gold'),('5','Rose'),('5','Rose'))
WRITES = {0:{'left':('1','Blue')},
          1:{'left':('2','Blue'),'right':('1','Gold')},
          3:{'left':('3','Gold')},
          5:{'left':('4','Gold'),'right':('3','Rose')},
          6:{'left':('3','Gold'),'right':('3','Gold')},
          7:{'left':('4','Gold')},
          8:{'left':('5','Gold'),'right':('4','Rose')}}


def fixture(rating='1',label='Blue'):
    if rating not in ('1','2','3','4','5') or label not in ('Blue','Gold','Rose'):
        raise ValueError('fixed original scalar fixture values required')
    data=bytearray(bytes((i*71+19)%256 for i in range(65536)))
    struct.pack_into('<2sHIH',data,0,b'II',42,8,4)
    entries=[(273,4,1,12288),(279,4,1,len(data)-12288),(700,1,8192,1024),(50706,1,4,1025)]
    for i,entry in enumerate(entries):struct.pack_into('<HHII',data,10+12*i,*entry)
    struct.pack_into('<I',data,58,0)
    packet=(f'<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" xmlns:xmp="http://ns.adobe.com/xap/1.0/"><rdf:Description rdf:about="" xmp:Rating="{rating}" xmp:Label="{label}"/></rdf:RDF>').encode()
    data[1024:9216]=packet+b' '*(8192-len(packet))
    return bytes(data)


def stage(index):
    if type(index) is not int or not 0<=index<len(STAGES):raise ValueError('exact ten-stage index required')
    return dict(index=index,name=STAGES[index],generation='baseline' if index in (2,3) else 'current',
                writes={k:fixture(*v) for k,v in WRITES.get(index,{}).items()},
                expected=None if EXPECTED[index] is None else fixture(*EXPECTED[index]),
                designated_refusal=index==5,expected_merge=index in (1,8))


def verify(index, *, returncode, log, left, right, archives_before, archives_after,
           target_before, target_after):
    row=stage(index)
    if type(returncode) is not int or type(log) is not str or type(left) is not bytes or type(right) is not bytes:
        raise ValueError('exact observed exit/log/payload required')
    # Archive identities/names must come from the same retained roots/states.
    for inventory in (archives_before,archives_after):
        if type(inventory) is not dict or set(inventory)!={'client','server'}:
            raise ValueError('both endpoint archive inventories required')
        for entries in inventory.values():
            if type(entries) is not dict or any(type(k) is not str or not k.startswith('ar') or
                    type(v) is not str or len(v)!=64 or any(c not in '0123456789abcdef' for c in v)
                    for k,v in entries.items()):raise ValueError('exact archive name/hash inventory required')
    if not all(archives_after.values()):raise ValueError('both endpoint archives must survive')
    if index and (not all(archives_before.values()) or any(set(archives_before[k])!=set(archives_after[k]) for k in archives_before)):
        raise ValueError('archive deletion/reset/renaming is not downgrade compatibility')
    lower=log.lower()
    if index in (2,3) and ('no archive files were found' in lower or 'archive format mismatch' in lower):
        raise ValueError('baseline rebuilt or refused archives')
    if row['designated_refusal']:
        # Actual nonzero status is retained; historical evidence never established
        # one exact numeric code. Signals and arbitrary failures do not qualify.
        if returncode not in (1,2) or 'no saved common base is available' not in log or 'Uncaught unix error' in log:
            raise ValueError('specific normal missing-base refusal required')
        if left!=fixture('4','Gold') or right!=fixture('3','Rose'):
            raise ValueError('missing-base refusal changed an edited replica')
    else:
        if returncode!=0 or left!=row['expected'] or right!=row['expected']:
            raise ValueError('exact successful archive-stage bytes required')
        if ('Built-in DNG scalar merge verified' in log)!=row['expected_merge']:
            raise ValueError('actual scalar merge observation differs')
    if index in (2,9) and (not target_before or target_before!=target_after):
        raise ValueError('noop replaced or touched receiver')
    return dict(stage=row['name'],returncode=returncode,left_sha256=hashlib.sha256(left).hexdigest(),
                right_sha256=hashlib.sha256(right).hexdigest(),functional_only=True,
                process_or_resource_closure_proved=False)
