"""Rebind existing parser command cases to both actual logs; metadata only.

Does not open fixture payloads, rerun inspectors, or infer SDK/pixel semantics.
"""
import collections,hashlib,json,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tests'),str(ROOT/'tests/sdk_host_matrix')]
from cached_benchmark.contract import read_bytes
from final_profile_owner import closed,log_sha


def load(path,digest=None,limit=2*1048576):
    raw=read_bytes(str(path),limit)
    if digest is not None and hashlib.sha256(raw).hexdigest()!=digest:raise ValueError('metadata pin changed '+str(path))
    return json.loads(raw),dict(path=str(path),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())


def main():
    actual_path=ROOT/'tests/qualification/final-extended-profile-pair-actual-20261019.json'
    actual,actual_pin=load(actual_path)
    assert actual['state']=='PASS_CLOSED' and actual['owning_tool']==dict(session=88003,initial_chunk='cd9153',terminal_chunk='d7e7af',exit_code=0,running_session=None)
    current_bindings={};historical_support=[]
    for name,digest in actual['source_sha256'].items():
        data=read_bytes(str(ROOT/name),4*1048576);current=hashlib.sha256(data).hexdigest();current_bindings[name]=current
        if current!=digest:
            assert name=='tests/sdk_host_matrix/shared_child.py'
            assert digest=='408097836323a1131921ceb9439201ce76b267f02b9187e81689db86aaf82783'
            assert current=='b4491baf26abecc3a38796529f0fb132a22994e18cbb83537502c4f51e1d8712'
            inverse=data.decode()
            for addition in ('    started_ns=time.monotonic_ns()\n','    owner.started_ns=started_ns\n','            owner.terminal_observed_ns=time.monotonic_ns()\n','            owner.reaped_ns=time.monotonic_ns();owner.last_wait4_usage=usage\n'):
                assert inverse.count(addition)==1;inverse=inverse.replace(addition,'',1)
            assert hashlib.sha256(inverse.encode()).hexdigest()==digest
            historical_support.append(dict(path=name,executed_sha256=digest,current_sha256=current,exact_inverse_additions=4,scope='Timestamp and wait4-usage observations only; executed source preserved, no current helper rerun claimed'))
    for ref in actual['top_artifacts']:load(ref['path'],ref['sha256'])
    rows=[];common=None;command_rows=None
    for audit in actual['audits']:
        record,record_pin=load(audit['receipt']['path'],audit['receipt']['sha256'])
        assert record['terminal']=='passed' and record['current_sources_match_snapshot'] is True
        assert record['source_sha256'].items()<=actual['source_sha256'].items()
        historical_snapshots=[]
        for historical in historical_support:
            name=historical['path'];snapshot=Path(record['artifact_directory'])/'sources'/name
            data=read_bytes(str(snapshot),1048576)
            assert hashlib.sha256(data).hexdigest()==historical['executed_sha256']
            historical_snapshots.append(dict(path=str(snapshot),sha256=historical['executed_sha256']))
        metadata=record['commands'];assert len(metadata)==1253
        names=[x['name'] for x in metadata];assert len(set(names))==len(names)
        if common is None:common=metadata
        else:assert common==metadata,'different compiler case vectors'
        directory=Path(record['artifact_directory']);raw=read_bytes(str(directory/'commands.tsv'),1048576)
        assert hashlib.sha256(raw).hexdigest()==record['commands_sha256']
        fields=[line.split('\t') for line in raw.decode().splitlines() if line]
        assert [(r[0],r[1]) for r in fields]==[(r['operation'],r['name']) for r in metadata]
        if command_rows is None:command_rows=fields
        manifest,manifest_pin=load(record['artifact_manifest'],record['artifact_manifest_sha256'])
        oracles,oracle_pin=load(directory/'fixture-oracles.json',record['fixture_oracles_sha256'])
        assert len(oracles)==33 and [x['name'] for x in oracles]==[x['name'] for x in metadata if x['operation']=='inspect']
        nested=[]
        for probe in record['compiler_probes']:
            closed(probe['outcome'],0);assert probe['argv']==probe['outcome']['command'];nested.append(probe['outcome']['client_cleanup']['pid'])
        for run in record['runs']:
            for key in ('compile','test'):
                call=run[key];code=2 if call.get('detected_assertion') else 0
                closed(call['outcome'],code);assert call['exit_code']==code and call['argv']==call['outcome']['command']
                assert log_sha(call['log'])==call['log_sha256'];nested.append(call['outcome']['client_cleanup']['pid'])
        assert len(nested)==10 and len(set(nested))==10
        test=record['runs'][0]['test'];assert record['runs'][0]['mode']=='fixed' and test['cases']==1253 and test['assertions']==6288
        text=test['outcome']['stdout'];assert text==test['stdout']
        assert re.findall(r'^CASE (.+)$',text,re.M)==names
        assert re.findall(r'^PASS (.+)$',text,re.M)==names
        assert 'All 1253 DNG /1 cases passed; 6288 assertions;' in text and not test['outcome']['stderr']
        assert [x['name'] for x in record['sparse_inspector_only']]==[x['name'] for x in metadata if x['operation']=='sparse']
        rows.append(dict(compiler=audit['compiler'],record=record_pin,command_file=dict(path=str(directory/'commands.tsv'),sha256=record['commands_sha256']),test_log=dict(path=test['log'],sha256=test['log_sha256']),artifact_manifest=manifest_pin,independent_oracles=oracle_pin,nested_children=nested,cases=1253,assertions=6288,parser_fixture_sources_match_current=True,all_harness_sources_match_current=False,historical_support_snapshots=historical_snapshots))
    assert [x['compiler'] for x in rows]==['stock','ox']
    def select(operation,pattern):
        found=[x['name'] for x in common if x['operation']==operation and re.search(pattern,x['name'])]
        assert found,(operation,pattern)
        return found
    groups={
        'classic_little_endian_valid':select('inspect',r'^classic-le-'),
        'classic_big_endian_valid':select('inspect',r'^classic-be-'),
        'bigtiff_little_endian_valid':select('inspect',r'^big-le-'),
        'bigtiff_big_endian_valid':select('inspect',r'^big-be-'),
        'independent_exact_wire_and_apply':select('golden',r'.'),
        'raw_strips_protected':select('opaque',r'-(main|sub)-strip-'),
        'raw_tiles_protected':select('opaque',r'-sub-tile-'),
        'jpeg_preview_protected':select('opaque',r'-jpeg-preview$'),
        'embedded_original_protected':select('opaque',r'-value-50828$'),
        'opcode_lists_protected':select('opaque',r'-value-(51008|51009|51022)$'),
        'undeclared_trailer_protected':select('opaque',r'-unreferenced-tail$'),
        'xmp_alias_rejections':select('reject',r'(XMP-alias|alias-XMP|alias-CR-list)'),
        'cyclic_or_repeated_graph_rejections':select('reject',r'(cycle|repeated|next-chain)'),
        'overflow_or_unsigned_rejections':select('reject',r'(overflow|922337203685477580[78]|18446744073709551615|unsigned)'),
        'count_type_and_size_rejections':select('reject',r'(count|type|header|length-outside|offset-98305)'),
        'unknown_tag_refusals':select('reject',r'(unknown|unsupported|unqualified)'),
        'sparse_above_uint32_inspector_only':select('sparse',r'.'),
    }
    result=dict(schema='unison-final-parser-case-inventory/1',actual_receipt=actual_pin,executed_source_sha256=actual['source_sha256'],current_source_sha256=current_bindings,historical_support_changes=historical_support,compiler_bindings=rows,counts=dict(collections.Counter(x['operation'] for x in common)),cases=common,groups=groups,v0_inspection_acceptance_counts=dict(collections.Counter(x[-1] for x in command_rows if x[0]=='inspect')),new_native_execution=False,fixture_payload_opened=False,limitations=['Named structural/layout/protected-byte cases only; no universal camera grammar or opaque tag interpretation','Opcode and embedded original bytes protected; no instruction execution or embedded raw decoding','Sparse files inspected above uint32 only; no full SHA, SDE materialization or receiving test on those sparse files','XMP observation/XML depth and scalar merge policies require separate case evidence','Does not establish final receiving/Adobe/decoded pixels/crash durability/corpus qualification'])
    out=ROOT/'doc/final-parser-case-inventory-20261019.json';out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(output=str(out),sha256=hashlib.sha256(out.read_bytes()).hexdigest(),cases_per_compiler=1253,assertions_per_compiler=6288,counts=result['counts'],groups={k:len(v) for k,v in groups.items()},new_native_execution=False,fixture_payload_opened=False)))

if __name__=='__main__':main()
