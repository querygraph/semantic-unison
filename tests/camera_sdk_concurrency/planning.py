"""Accounting feasibility for a future two-file SDK receiving control; no admission."""
MIB = 1048576
GIB = 1024 * MIB
MAX_PAYLOAD = 16 * MIB


def plan(*, consumers=2, workspace_mib=2048, gate_mib=6144,
         descriptor_credits=64, endpoint_workers=3, owner_credits=2,
         cpu_grant=8, project_memory_gib=32):
    values = locals().copy()
    if any(type(value) is not int or value <= 0 for value in values.values()):
        raise ValueError('positive integer accounting declarations required')
    if consumers != 2:
        raise ValueError('this finite successor covers exactly two receiving candidates')
    if cpu_grant > 8 or endpoint_workers * 2 + owner_credits > cpu_grant:
        raise ValueError('both endpoints and owners must fit standing Unison8')
    if endpoint_workers < consumers:
        raise ValueError('endpoint cannot admit both single-thread validators')
    if max(gate_mib, workspace_mib) > 32768 or project_memory_gib > 32:
        raise ValueError('declared project memory exceeds standing envelope')
    source = 8 * MAX_PAYLOAD + 262144
    publication = max(MIB, source) + workspace_mib * MIB
    required = source + consumers * publication
    descriptors = 8 + consumers * 24
    if required > gate_mib * MIB:
        raise ValueError('concurrent publications and reserved source exceed gate')
    if descriptors > descriptor_credits:
        raise ValueError('concurrent publications and source exceed descriptor credits')
    if 2 * gate_mib * MIB > project_memory_gib * GIB:
        raise ValueError('both endpoint gates exceed declared project memory')
    return dict(consumers=consumers, minimum_gate_bytes=required,
                source_headroom_bytes=source, publication_bytes=publication,
                gate_mib=gate_mib, minimum_descriptor_credits=descriptors,
                transaction_slots=consumers + 1, endpoint_workers=endpoint_workers,
                helper_threads=1, maximum_helpers_per_receiving_endpoint=consumers,
                configured_endpoint_cpu_total=2 * endpoint_workers,
                owner_credits=owner_credits, cpu_grant=cpu_grant,
                declared_endpoint_memory_total_bytes=2 * gate_mib * MIB,
                runtime_admitted=False, hard_rss_cap=False,
                physical_io_cap=False, actual_concurrency_qualified=False)
