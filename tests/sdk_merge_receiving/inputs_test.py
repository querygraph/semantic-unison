"""Original fabricated metadata only; no source file, clone or SDK access."""
import copy
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sdk_merge_receiving.inputs import bind, STATES
from sdk_merge_receiving.plan import CODECS


def fixture():
    cases = []; observed = {}; index = 0
    for codec in CODECS:
        states = {}
        for state in STATES:
            index += 1; name = '/private/tmp/generated-'+codec+'-'+state+'.dng'
            states[state] = dict(path=name, sha256=('%064x' % index), bytes=256)
            observed[name] = dict(st_dev=1, st_ino=index, st_mode=0o100400,
                st_size=256, st_mtime_ns=100, st_ctime_ns=101, st_nlink=1, st_uid=501)
        cases.append(dict(codec=codec, xmp_offset=32, xmp_size=64, states=states))
    return cases, observed


class Inputs(unittest.TestCase):
    def test_exact_twelve_states_without_mutation(self):
        cases, epochs = fixture(); before = copy.deepcopy((cases, epochs))
        rows = bind(cases, epochs, expected_uid=501)
        self.assertEqual([(r['codec'],r['state']) for r in rows],
                         [(c,s) for c in CODECS for s in STATES])
        self.assertEqual(len(rows),12); self.assertEqual((cases,epochs),before)
        rows[0]['identity']['st_size'] = 0
        self.assertEqual((cases,epochs),before)

    def test_refuses_every_unbound_or_ambiguous_metadata_form(self):
        for mutation in ('uid','mode','links','size','boolean','missing','extra',
                         'alias','hash','extent','geometry','outside','state','order'):
            cases, epochs = fixture(); first = cases[0]['states']['base']; name=first['path']
            if mutation == 'uid': epochs[name]['st_uid']=0
            if mutation == 'mode': epochs[name]['st_mode']=0o120777
            if mutation == 'links': epochs[name]['st_nlink']=2
            if mutation == 'size': epochs[name]['st_size']=255
            if mutation == 'boolean': epochs[name]['st_ino']=True
            if mutation == 'missing': del epochs[name]['st_ctime_ns']
            if mutation == 'extra': epochs['/private/tmp/unexpected']=dict(epochs[name])
            if mutation == 'alias': epochs[cases[0]['states']['left']['path']]['st_ino']=epochs[name]['st_ino']
            if mutation == 'hash': cases[0]['states']['left']['sha256']=first['sha256']
            if mutation == 'extent': cases[0]['xmp_offset']=255
            if mutation == 'geometry': cases[0]['xmp_size']=True
            if mutation == 'outside':
                first['path']='/Users/not-an-admitted-source.dng';epochs[first['path']]=epochs.pop(name)
            if mutation == 'state': del cases[0]['states']['target']
            if mutation == 'order': cases.reverse()
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                bind(cases, epochs, expected_uid=501)


if __name__ == '__main__':
    unittest.main()
