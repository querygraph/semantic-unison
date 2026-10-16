#!/usr/bin/env python3
"""Finite offline artifact controls, using historical data; no new measurements."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
from unittest.mock import patch

import merge_partitions as merger
from partitions import COUNT, specification


def refuse(function):
    try:
        function()
    except (ValueError, OSError):
        return
    raise AssertionError('invalid artifact operation accepted')


def main():
    raw = Path(__file__).parent / 'results/warm-128MiB-4files-20261015.json'
    historical = json.loads(raw.read_text())
    with tempfile.TemporaryDirectory(prefix='unison-offline-part-merge-') as temporary:
        work = Path(temporary)
        paths = []
        for index in range(COUNT):
            part = copy.deepcopy(historical)
            part['partition'] = specification(index)
            wanted = {tuple(value) for value in part['partition']['configurations']}
            part['samples'] = [row for row in part['samples'] if
                               (row['label'], row['mode'], row['workers']) in wanted]
            path = work / ('part%d.json' % index)
            path.write_text(json.dumps(part))
            paths.append(path)
        originals = [hashlib.sha256(path.read_bytes()).hexdigest() for path in paths]
        output = work / 'complete.json'
        proof = merger.merge_files(list(reversed(paths)), output)
        combined = json.loads(output.read_text())
        assert (proof['rows'], proof['cli_invocations']) == (108, 324)
        assert combined['summary'] == historical['summary']
        assert len(combined['partition_input_receipts']) == COUNT
        complete_hash = hashlib.sha256(output.read_bytes()).hexdigest()
        refuse(lambda: merger.merge_files(paths, output))
        assert hashlib.sha256(output.read_bytes()).hexdigest() == complete_hash
        refuse(lambda: merger.merge_files(paths, paths[0]))
        refuse(lambda: merger.merge_files(paths[:-1], work / 'missing.json'))
        refuse(lambda: merger.merge_files(paths[:-1] + [paths[0]], work / 'duplicate.json'))
        with patch.object(merger, 'MAX_INPUT_BYTES', 8):
            refuse(lambda: merger.merge_files(paths, work / 'oversized.json'))
        refuse(lambda: merger.read_part(work))
        with patch.object(merger, 'stamp', side_effect=['before', 'changed']):
            refuse(lambda: merger.read_part(paths[0]))
        paths[0].write_text('{incomplete')
        refuse(lambda: merger.merge_files(paths, work / 'malformed.json'))
        # Only the deliberately corrupted owned fixture changed; the merger
        # never writes any of its inputs.
        assert [hashlib.sha256(path.read_bytes()).hexdigest() for path in paths[1:]] == originals[1:]
        for name in ('missing', 'duplicate', 'oversized', 'malformed'):
            assert not (work / (name + '.json')).exists()
    print('PASS offline108-row/324-CLI merge, exclusive output,8 artifact refusals and unchanged inputs; no dispatch')


if __name__ == '__main__':
    main()
