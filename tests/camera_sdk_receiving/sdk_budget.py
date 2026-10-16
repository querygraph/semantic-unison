"""Pure accounting preflight, not a physical-memory/RSS or runtime admission cap."""
MIB=1048576
GATE_MIB=4096
WORKSPACE_MIB=2048
MAX_PAYLOAD=16*MIB


def validate(*,gate_mib=GATE_MIB,workspace_mib=WORKSPACE_MIB):
    if type(gate_mib) is not int or type(workspace_mib) is not int:
        raise ValueError('typed explicit memory accounting budgets required')
    if not 0<workspace_mib<=gate_mib<=32768:
        raise ValueError('SDK workspace must fit bounded declared gate')
    # Match SemanticRuntime source and publication envelopes. The transport
    # explicitly disables validation-tree manifest accounting for one file.
    source=8*MAX_PAYLOAD+262144
    consumer=max(MIB,source)+workspace_mib*MIB
    if source+consumer>gate_mib*MIB:
        raise ValueError('SDK publication workspace plus reserved source exceeds semantic gate')
    return {'semantic_payload_mib':gate_mib,'sdk_workspace_mib':workspace_mib,
            'source_headroom_bytes':source,'publication_bytes':consumer,
            'minimum_gate_bytes':source+consumer,'descriptor_credits':32,
            'hard_rss_cap':False,'validation_tree_memory_mib':0}
