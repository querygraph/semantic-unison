"""Pure finite real-SDK receiving successor; no payload access or execution."""
import re
from pathlib import Path

BUILD='unison-sdk171-2724-v1-single'


def plan(binary,tool,workspace):
    for item in (binary,tool):
        if type(item) is not dict or type(item.get('path')) is not str or not Path(item['path']).is_absolute() or re.fullmatch('[0-9a-f]{64}',item.get('sha256','')) is None:
            raise ValueError('exact absolute executable/SHA metadata required')
    if binary.get('label') not in ('stock','ox') or tool.get('build_id')!=BUILD or type(tool.get('threads')) is not int or tool['threads']!=1:
        raise ValueError('qualified single-thread reference tool and compiler label required')
    w=Path(workspace)
    if not w.is_absolute() or '..' in w.parts or len(str(w/'seed.sock').encode())>=100:
        raise ValueError('bounded absolute private transport namespace required')
    # Four slots preserve a future source even when two consumers arrive first.
    # CPU credits remain endpoint3 + endpoint3 + owner2, not four native workers.
    source=8*16*1048576+262144
    publication=max(1048576,source)+2048*1048576
    required=source+2*publication
    gate=6144*1048576
    assert required<=gate and 8+2*24<=64
    flags=['-clone','auto','-semanticworkers','3','-maxthreads','3',
           '-semanticmaxinflight','4','-semanticvolumejobs','2',
           '-adobevalidate','require','-adobevalidator',tool['path'],
           '-adobevalidatorhash',tool['sha256'],'-adobevalidatorbuild',BUILD,
           '-adobevalidatorthreads','1','-adobevalidatetimeout','90',
           '-adobevalidatorworkspace','2048','-semanticpayloadbudget','6144',
           '-validationtreememory','0','-semanticdescriptorbudget','64',
           '-debug','validation-process','-debug','validation-group','-debug','validation-live']
    return dict(schema='unison-sdk-multifile-plan/1',
        command=[binary['path'],str(w/'left'),'ssh://localhost/'+str(w/'right'),
                 '-sshcmd',str(w/'launcher.py'),'-servercmd',binary['path'],
                 '-batch','-auto','-fastcheck','false','-times',*flags],
        server_flags=flags,case_count=1,candidates=2,maximum_sdk_calls=2,
        source_headroom_bytes=source,publication_bytes=publication,
        minimum_payload_credits=required,payload_credits=gate,
        minimum_descriptor_credits=56,descriptor_credits=64,transaction_slots=4,
        endpoint_cpu_credits=[3,3],owner_cpu_credits=2,total_cpu_credits=8,
        maximum_single_thread_helpers_at_receiver=2,
        requires_clone_only_generated_inputs=True,
        requires_exact_admission_and_existing_exglobal=True,
        runtime_admitted=False,actual_overlap_proved=False,semantic_eligibility_proved=False,
        sdk_validation_proved=False,hard_rss_cap=False,
        scope='command/accounting preparation only; actual candidate hashes, SDK receipts and all child/group closures must be independently bound')
