"""Compose SDK-child ownership with separately settled pinned OS probes.

This callable grants no SDK execution permission. The entrypoint must bind its
contract in an exact admitted plan and own CPU/IO before calling it.
"""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tests'))
from process_observation.probe import Probe
from process_observation.retained import RetainedSamples
from process_observation.audit import audit
from shared_child import invoke


def checked_contract(contract):
    if type(contract) is not dict or set(contract)!={'path','sha256','sample_limit','interval_seconds'}:
        raise ValueError('exact observation contract required')
    path=contract['path'];sha=contract['sha256'];limit=contract['sample_limit'];interval=contract['interval_seconds']
    if type(path) is not str or not Path(path).is_absolute() or Path(path).resolve()!=Path(path):
        raise ValueError('canonical probe path required')
    if type(sha) is not str or len(sha)!=64 or any(c not in '0123456789abcdef' for c in sha):
        raise ValueError('exact probe SHA required')
    if type(limit) is not int or not 1<=limit<=128 or type(interval) not in (int,float) or not .05<=interval<=1:
        raise ValueError('bounded probe fanout/interval required')
    return contract


def invoke_observed(command,environment,deadline,*,contract,pass_fds=()):
    c=checked_contract(contract)
    probe=Probe(c['path'],c['sha256'],pass_fds=pass_fds,limit=c['sample_limit'])
    class Observer(RetainedSamples):
        def report(self):
            report=super().report()
            report.update(probe_children=list(probe.outcomes),probe_sha256=c['sha256'])
            return report
    return invoke(command,environment,deadline,pass_fds=pass_fds,
                  observation_factory=lambda owner:Observer(owner,probe,limit=c['sample_limit']),
                  observation_interval=c['interval_seconds'])


def audit_observed(outcome,contract):
    c=checked_contract(contract);report=outcome.get('process_observations',{})
    if report.get('sample_limit')!=c['sample_limit']:
        raise ValueError('returned observation budget differs')
    return audit(outcome,report.get('probe_children'),probe_path=c['path'],
                 probe_sha256=c['sha256'],recorded_probe_sha256=report.get('probe_sha256'))
