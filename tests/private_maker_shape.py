"""Pure candidate classic-IFD shape diagnostic, never a MakerNote safety proof."""
import struct

WIDTHS={1:1,2:1,3:2,4:4,5:8,6:1,7:1,8:2,9:4,10:8,11:4,12:8,13:4}
MAX_ENTRIES=256
MAX_READ=2+MAX_ENTRIES*12+4


def inspect(read,*,length,original_offset,byte_order,ifd_offset=0):
    """Caller supplies a separately admitted payload-relative bounded reader.

    This assumes a candidate classic TIFF directory shape only. It does not
    recognize a maker/model, interpret inline fields or prove pointer semantics.
    Values are not emitted or dereferenced; external extents are diagnostics.
    """
    if (any(type(v) is not int for v in (length,original_offset,ifd_offset))
            or not 6<=length<=64*1048576 or not 0<=original_offset<2**32
            or not 0<=ifd_offset<=length-2 or byte_order not in ('little','big')):
        raise ValueError('bounded explicit candidate layout required')
    endian='<' if byte_order=='little' else '>'
    requested=0
    def get(offset,count):
        nonlocal requested
        if not 0<=offset<=length or not 0<=count<=length-offset or requested+count>MAX_READ:
            raise ValueError('candidate directory read outside bounds/budget')
        requested+=count;raw=read(offset,count)
        if type(raw) is not bytes or len(raw)!=count:raise ValueError('exact candidate read required')
        return raw
    count=struct.unpack(endian+'H',get(ifd_offset,2))[0]
    if not 1<=count<=MAX_ENTRIES:raise ValueError('bounded nonempty candidate directory required')
    table=get(ifd_offset+2,count*12+4)
    rows=[];tags=set()
    for index in range(count):
        tag,kind,elements,value=struct.unpack_from(endian+'HHII',table,index*12)
        if tag in tags:raise ValueError('ambiguous duplicate candidate tag')
        tags.add(tag)
        if kind not in WIDTHS:raise ValueError('unknown candidate TIFF value type')
        extent=elements*WIDTHS[kind]
        outlined=extent>4
        relative=value-original_offset if outlined else None
        within=(0<=relative<=length and extent<=length-relative) if outlined else None
        rows.append(dict(tag=tag,type=kind,count=elements,value_bytes=extent,
                         out_of_line=outlined,payload_relative_offset=relative,
                         declared_extent_within_payload=within,
                         private_pointer_semantics_verified=False))
    next_value=struct.unpack_from(endian+'I',table,count*12)[0]
    return dict(schema='unison-private-maker-candidate-shape/1',entries=rows,
                next_ifd_zero=next_value==0,requested_read_bytes=requested,
                read_budget_bytes=MAX_READ,maker_format_recognized=False,
                private_reference_closure_proved=False,semantic_eligibility=False,
                inline_values_disclosed=False,pointed_values_read=False,
                scope='Candidate directory geometry only; no vendor grammar, pointer or XMP independence proof.')
