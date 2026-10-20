"""Pure ordered call ledger. It never establishes process or FD settlement.

The executor must independently audit the referenced raw transport/helper records.
An unfinished intent is deliberately distinguishable from a known failed prefix.
"""
from copy import deepcopy
from sdk_merge_receiving.plan import CODECS, STAGES, require, digest


class Ledger:
    def __init__(self):
        self.entries = []

    def begin(self, codec, stage, command_sha256):
        require(not self.entries or 'outcome' in self.entries[-1],
                'unfinished intent retains ownership; no successor')
        index = len(self.entries)
        require(index < 9 and (codec, stage) == (CODECS[index//3], STAGES[index%3]),
                'exact serial codec/stage order required')
        require(not self.entries or self.entries[-1]['outcome']['returncode'] == 0,
                'failed prefix cannot start a successor or retry')
        digest(command_sha256)
        self.entries.append(dict(index=index, codec=codec, stage=stage,
                                 command_sha256=command_sha256))
        return index

    def finish(self, index, *, returncode, transport_record_sha256, helper_record_sha256s):
        require(type(index) is int and index == len(self.entries)-1 and index >= 0,
                'only current intent may finish')
        entry = self.entries[index]
        require('outcome' not in entry, 'outcome is immutable; no replacement')
        require(type(returncode) is int, 'typed terminal return code required')
        digest(transport_record_sha256)
        require(type(helper_record_sha256s) is list and len(helper_record_sha256s) <= 2,
                'bounded raw helper references required')
        for value in helper_record_sha256s:
            digest(value)
        require(len(set(helper_record_sha256s)) == len(helper_record_sha256s),
                'distinct endpoint helper records required')
        # A failure may occur before either helper, between them, or after both.
        # Counts alone cannot turn a missing helper into a no-creation proof.
        if returncode == 0:
            expected = 2 if entry['stage'] == 'update' else 0
            require(len(helper_record_sha256s) == expected,
                    'successful phase has incorrect helper count')
        entry['outcome'] = dict(returncode=returncode,
            transport_record_sha256=transport_record_sha256,
            helper_record_sha256s=list(helper_record_sha256s))

    def report(self):
        pending = bool(self.entries and 'outcome' not in self.entries[-1])
        failed = bool(self.entries and not pending
                      and self.entries[-1]['outcome']['returncode'] != 0)
        complete = len(self.entries) == 9 and not pending and not failed
        return dict(schema='unison-sdk-merge-call-ledger/1',
            entries=deepcopy(self.entries), complete=complete,
            state=('UNRESOLVED_INTENT' if pending else 'FAILED_PREFIX_REQUIRES_AUDIT'
                   if failed else 'COMPLETE_REQUIRES_AUDIT' if complete else 'READY'),
            raw_process_audit_required=True, helper_noncreation_proved=False,
            worker_settlement_proved=False, resource_release_authorized=False)
