"""Pure one-bit negative fixture for the qualified generated classic-TIFF family.

Not a general TIFF graph/alias proof or camera editor. No IO or SDK invocation.
A later admitted SDK call must establish the actual finding; construction alone
never proves decode failure, a digest mismatch or receiving rejection.
"""
import struct
from sdk_fixture_states import geometry,require

WIDTHS={1:1,2:1,3:2,4:4,5:8,6:1,7:1,8:2,9:4,10:8,11:4,12:8,13:4}


def corrupt_new_raw_digest(data,codec):
    observed=geometry(data,codec)
    order='<' if data[:2]==b'II' else '>'
    primary=struct.unpack_from(order+'I',data,4)[0]
    count=struct.unpack_from(order+'H',data,primary)[0]
    end=primary+2+12*count+4
    entries=[]
    for index in range(count):
        tag,typ,n,at=struct.unpack_from(order+'HHII',data,primary+2+12*index)
        require(typ in WIDTHS and 0<n<=len(data),'bounded known fixture entry required')
        size=n*WIDTHS[typ]
        if size>4:
            require(8<=at and at+size<=len(data),'fixture entry extent out of bounds')
            require(at+size<=primary or at>=end,'fixture entry aliases primary table')
            entries.append((tag,typ,n,at,at+size))
    digest=[entry for entry in entries if entry[0]==51111]
    require(len(digest)==1 and digest[0][1:3]==(1,16),'one BYTE[16] NewRawImageDigest required')
    _,_,_,start,stop=digest[0]
    require(not any(tag!=51111 and start<b and a<stop for tag,_,_,a,b in entries),
            'digest aliases another primary value')
    changed=bytearray(data);changed[start]^=1;changed=bytes(changed)
    require(changed[:start]==data[:start] and changed[start+1:]==data[start+1:]
            and changed[start]^data[start]==1,'exact one-bit fixture mutation required')
    require(geometry(changed,codec)==observed,'fixture geometry changed')
    return dict(data=changed,tag=51111,offset=start,bytes_changed=1,xor_mask=1,
                actual_sdk_finding_proved=False,receiving_rejection_proved=False)
