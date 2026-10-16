"""Pure functional shared-matrix audit; never authorizes resource release."""
from plan import receipt,telemetry,require
from shared_plan import shared_matrix

def audit(reference,experimental,fixtures,memory_bytes,rows,*,require_complete=True):
    proposal=shared_matrix(reference,experimental,fixtures,memory_bytes)
    require(type(require_complete) is bool,'typed audit scope required')
    require(type(rows) is list and (len(rows)==12 if require_complete else 1<=len(rows)<=12),
            'bounded ordered returned calls required')
    references={};results=[];pids=set()
    for index,(case,row) in enumerate(zip(proposal['cases'],rows),1):
        require(type(row) is dict and set(row)=={'index','command','outcome'}
                and type(row['index']) is int and row['index']==index
                and row['command']==case['command'],'ordered exact call/command binding required')
        out=row['outcome'];require(type(out) is dict,'returned outcome required')
        require(type(out.get('returncode')) is int and out['returncode']==0
                and out.get('timed_out') is False and out.get('capture_truncated') is False,
                'successful nontruncated call required')
        child=out.get('client_cleanup',{})
        require(type(child.get('pid')) is int and child['pid']>0 and child['pid'] not in pids
                and child.get('reaped') is True and type(child.get('returncode')) is int
                and child['returncode']==0 and child.get('hard_kill_required') is False,
                'distinct normally reaped direct child required')
        pids.add(child['pid'])
        require(type(out.get('stdout')) is str and len(out['stdout'])<=16384
                and type(out.get('stderr')) is str and len(out['stderr'])<=262144,
                'bounded captured diagnostic text required')
        value=receipt(out['stdout'],case)
        if case['backend']=='reference':references[case['codec']]=value
        require(value==references[case['codec']],'validation result differs from reference')
        observed=telemetry(out['stderr'],case,memory_bytes) if case['backend']=='experimental' else None
        results.append(dict(index=index,codec=case['codec'],backend=case['backend'],
                            requested_threads=case['threads_including_caller'],receipt=value,observations=observed))
    return dict(functional_results=results,calls=len(rows),experimental_calls=sum(r['backend']=='experimental' for r in results),
        full_matrix_complete=len(rows)==12,
        aggregate_group_settlement_proved=False,parent_terminal_proved=False,
        io_cpu_fd_closure_proved=False,resource_release_authorized=False,
        os_thread_scaling_proved=False,hard_rss_cap_proved=False,pixel_equivalence_proved=False,
        runtime_qualification_requires_actual_owned_receipts=True)
