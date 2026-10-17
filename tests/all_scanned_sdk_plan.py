"""Pure command/accounting proposal. Import and planning perform no IO or exec.

This is not a runtime executor, admission verifier, or ownership audit.
"""
from pathlib import Path
import re

MIB = 1048576
BUILD = 'unison-sdk171-2724-v1-single'


def plan(binary, tool, workspace):
    for item in (binary, tool):
        if (type(item) is not dict or type(item.get('path')) is not str
                or not Path(item['path']).is_absolute()
                or re.fullmatch('[0-9a-f]{64}', item.get('sha256', '')) is None):
            raise ValueError('absolute executable and exact SHA required')
    if (binary.get('label') not in ('stock', 'ox')
            or tool.get('build_id') != BUILD
            or type(tool.get('threads')) is not int or tool['threads'] != 1):
        raise ValueError('qualified compiler and single-thread SDK identity required')
    w = Path(workspace)
    if (not w.is_absolute() or '..' in w.parts
            or len(str(w / 'scan.sock').encode()) >= 100):
        raise ValueError('bounded absolute private namespace required')
    # CandidateValidation.unchanged_file_with_validators reserves SDK+2MiB
    # in its outer loan. Its one-child partition lends SDK+1MiB, independently
    # per endpoint process. No size-proportional receiving publication loan.
    workspace_mib = 2048
    minimum_payload = (workspace_mib + 2) * MIB
    gate_mib = 4096
    common = ['-semanticworkers', '3', '-maxthreads', '3',
              '-semanticpayloadbudget', str(gate_mib),
              '-semanticdescriptorbudget', '64', '-semanticmaxinflight', '2',
              '-adobevalidator', tool['path'], '-adobevalidatorhash', tool['sha256'],
              '-adobevalidatorbuild', BUILD, '-adobevalidatorthreads', '1',
              '-adobevalidatorworkspace', str(workspace_mib),
              '-adobevalidatetimeout', '90',
              '-adobevalidatescanfiles', '1', '-adobevalidatescanpathbytes', '4096',
              '-adobevalidatescanmaxmib', '256',
              '-debug', 'validation-process', '-debug', 'validation-group',
              '-debug', 'validation-input']

    def invocation(policy, scope):
        flags = [*common, '-adobevalidate', policy, '-adobevalidatescope', scope]
        return dict(argv=[binary['path'], str(w / 'left'),
                          'ssh://localhost/' + str(w / 'right'),
                          '-sshcmd', str(w / 'launcher.py'),
                          '-servercmd', binary['path'], '-batch', '-auto',
                          '-fastcheck', 'false', '-times', *flags],
                    server_flags=flags)

    return dict(schema='unison-all-scanned-sdk-proposal/1',
                baseline=invocation('off', 'received'),
                validate=invocation('require', 'all-scanned'),
                calls_per_compiler=2, maximum_sdk_calls_per_compiler=2,
                selected_regular_files_per_endpoint=1,
                minimum_payload_credits_per_endpoint=minimum_payload,
                payload_credits_per_endpoint=gate_mib * MIB,
                minimum_descriptor_credits_per_endpoint=25,
                descriptor_credits_per_endpoint=64,
                cpu_endpoint_credits=[3, 3], cpu_owner_credits=2,
                total_cpu_credits=8, sdk_timeout_seconds=90,
                cli_observation_seconds=240,
                owner_observation_seconds=600,
                requires_identical_clone_only_roots=True,
                requires_empty_transfer_on_validation=True,
                requires_sdk_candidate_hash_equals_private_source=True,
                requires_endpoint_local_staging_outside_roots=True,
                requires_exact_admission_and_existing_exglobal=True,
                runtime_admitted=False, sdk_validation_proved=False,
                physical_clone_sharing_proved=False, hard_rss_cap=False,
                semantic_eligibility_proved=False)
