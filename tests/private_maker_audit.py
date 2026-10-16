"""Independent metadata consistency audit; no payload reads or release authority."""


def require(condition,message):
    if not condition:raise ValueError(message)


def integer(n,low,high):return type(n) is int and low<=n<=high


def audit_worker(result,geometry,*,parent_pid,worker_pid):
    require(type(result) is dict and set(result)=={'schema','complete','diagnostic','failure',
        'parent_pid','worker_pid','canonical_metadata_bound','external_children_started'},
        'exact worker result fields required')
    require(result['schema']=='unison-private-maker-worker/1'
        and type(result['complete']) is bool and result['canonical_metadata_bound'] is True
        and type(result['parent_pid']) is int and result['parent_pid']==parent_pid
        and type(result['worker_pid']) is int and result['worker_pid']==worker_pid
        and type(result['external_children_started']) is int and result['external_children_started']==0,
        'exact actual worker/parent and zero external children required')
    if result['complete']:
        require(result['failure'] is None,'complete worker cannot hide a failure')
        proof=audit(result['diagnostic'],geometry)
    else:
        require(result['diagnostic'] is None and type(result['failure']) is str
                and 0<len(result['failure'])<=4096,'known failed worker must preserve error')
        proof={'metadata_consistent':True,'candidate_shape':False,'semantic_eligibility':False}
    return dict(proof,worker_complete=result['complete'],external_children_started=0,
                resource_release_authorized=False)


def audit(result,geometry):
    keys={'schema','diagnostic_complete','outcome','reason','shape','read_ranges',
          'requested_read_bytes','received_read_bytes','max_requested_read_bytes',
          'source_epoch_unchanged','semantic_eligibility','private_reference_closure_proved',
          'full_input_hash_computed','raw_payload_disclosed','fd_closure_proved_by_return','scope'}
    require(type(result) is dict and set(result)==keys,'exact diagnostic fields required')
    require(result['schema']=='unison-private-maker-slice/1'
        and all(result[k] is True for k in ('diagnostic_complete','source_epoch_unchanged','fd_closure_proved_by_return'))
        and all(result[k] is False for k in ('semantic_eligibility','private_reference_closure_proved',
                    'full_input_hash_computed','raw_payload_disclosed')),'diagnostic claims differ')
    require(type(geometry) is dict and set(geometry)=={'payload_offset','payload_length',
        'original_offset','byte_order','ifd_offset','max_requested_read_bytes'}
        and all(type(geometry[k]) is int for k in geometry if k!='byte_order')
        and geometry['max_requested_read_bytes']==3078
        and geometry['byte_order'] in ('little','big')
        and 6<=geometry['payload_length']<=64*1048576
        and geometry['payload_offset']>=0
        and 0<=geometry['original_offset']<2**32
        and 0<=geometry['ifd_offset']<=geometry['payload_length']-2,'bounded geometry required')
    require(result['scope']=='Bounded candidate geometry only; return occurs only after qualified descriptor close.',
            'exact diagnostic scope required')
    ranges=result['read_ranges'];base=geometry['payload_offset'];length=geometry['payload_length']
    require(type(ranges) is list and 1<=len(ranges)<=2,'one count and at most one directory read required')
    for row in ranges:
        require(type(row) is dict and set(row)=={'offset','requested','received'}
            and integer(row['offset'],base,base+length)
            and integer(row['requested'],0,base+length-row['offset'])
            and integer(row['received'],0,row['requested']),'read range outside admitted payload')
    require(ranges[0]['offset']==base+geometry['ifd_offset'] and ranges[0]['requested']==2,
            'candidate count read differs')
    if len(ranges)==2:
        require(ranges[0]['received']==2 and ranges[1]['offset']==ranges[0]['offset']+2
            and integer(ranges[1]['requested'],16,3076)
            and (ranges[1]['requested']-4)%12==0,'single bounded candidate table required')
    for name,field in (('requested_read_bytes','requested'),('received_read_bytes','received')):
        require(integer(result[name],0,3078) and result[name]==sum(r[field] for r in ranges),
                'read accounting differs')
    require(type(result['max_requested_read_bytes']) is int and result['max_requested_read_bytes']==3078,
            'requested read ceiling differs')
    if result['outcome']=='DECLINED_CANDIDATE_SHAPE':
        require(result['shape'] is None and type(result['reason']) is str and result['reason'] in {
            'bounded nonempty candidate directory required','candidate directory read outside bounds/budget',
            'exact candidate read required','ambiguous duplicate candidate tag','unknown candidate TIFF value type'},
            'decline must preserve a known sanitized parser reason')
        return {'metadata_consistent':True,'candidate_shape':False,'semantic_eligibility':False}
    require(result['outcome']=='CANDIDATE_SHAPE' and result['reason'] is None,'known diagnostic outcome required')
    shape=result['shape']
    require(type(shape) is dict and set(shape)=={'schema','entries','next_ifd_zero','requested_read_bytes',
        'read_budget_bytes','maker_format_recognized','private_reference_closure_proved','semantic_eligibility',
        'inline_values_disclosed','pointed_values_read','scope'},'exact shape fields required')
    require(shape['schema']=='unison-private-maker-candidate-shape/1'
        and type(shape['next_ifd_zero']) is bool
        and all(shape[k] is False for k in ('maker_format_recognized','private_reference_closure_proved',
            'semantic_eligibility','inline_values_disclosed','pointed_values_read'))
        and shape['scope']=='Candidate directory geometry only; no vendor grammar, pointer or XMP independence proof.',
        'shape safety claims differ')
    rows=shape['entries'];widths={1:1,2:1,3:2,4:4,5:8,6:1,7:1,8:2,9:4,10:8,11:4,12:8,13:4}
    require(type(rows) is list and 1<=len(rows)<=256 and len(ranges)==2
        and ranges[1]['requested']==12*len(rows)+4
        and all(r['received']==r['requested'] for r in ranges),'complete candidate table reads required')
    require(type(shape['requested_read_bytes']) is int
        and shape['requested_read_bytes']==result['requested_read_bytes']
        and type(shape['read_budget_bytes']) is int and shape['read_budget_bytes']==3078,
        'shape read accounting differs')
    seen=set()
    for row in rows:
        require(type(row) is dict and set(row)=={'tag','type','count','value_bytes','out_of_line',
            'payload_relative_offset','declared_extent_within_payload','private_pointer_semantics_verified'},
            'exact sanitized candidate entry required')
        require(integer(row['tag'],0,65535) and row['tag'] not in seen
            and integer(row['type'],1,13) and integer(row['count'],0,2**32-1)
            and type(row['value_bytes']) is int and row['value_bytes']==row['count']*widths[row['type']]
            and row['out_of_line'] is (row['value_bytes']>4)
            and row['private_pointer_semantics_verified'] is False,'candidate entry arithmetic/claims differ')
        seen.add(row['tag']);relative=row['payload_relative_offset']
        if row['out_of_line']:
            require(integer(relative,-geometry['original_offset'],2**32-1-geometry['original_offset'])
                and row['declared_extent_within_payload'] is
                    (0<=relative<=length and row['value_bytes']<=length-relative),
                'candidate extent arithmetic differs')
        else:
            require(relative is None and row['declared_extent_within_payload'] is None,
                    'inline values must not be disclosed')
    return {'metadata_consistent':True,'candidate_shape':True,'semantic_eligibility':False}
