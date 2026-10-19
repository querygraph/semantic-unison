"""Original inert command vectors; never opens DNGs or invokes a validator."""
import copy
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sdk_merge_receiving.plan import schedule, LIMITS, CODECS, STAGES, BUILD


def inputs():
    return (dict(stock=dict(label='stock', path='/qualified/stock', sha256='a'*64),
                 ox=dict(label='ox', path='/qualified/ox', sha256='b'*64)),
            dict(path='/qualified/sdk', sha256='c'*64, build_id=BUILD, threads=1),
            '/private/tmp/u-smg-'+'a'*16)


class Plan(unittest.TestCase):
    def test_exact_stages_peers_and_helper_count(self):
        binaries, tool, workspace = inputs(); before = copy.deepcopy((binaries, tool))
        value = schedule(binaries, tool, workspace)
        self.assertEqual([(r['codec'], r['stage']) for r in value['rows']],
                         [(c,s) for c in CODECS for s in STAGES])
        self.assertEqual(sum(r['expected_sdk_helpers'] for r in value['rows']), 6)
        self.assertEqual(len(value['rows']), 9)
        for row in value['rows']:
            argv = row['command']; flags = row['server_flags']
            self.assertEqual(argv[0], binaries['stock']['path'])
            self.assertEqual(argv[argv.index('-servercmd')+1], binaries['ox']['path'])
            self.assertEqual(argv[-len(flags):], flags)
            self.assertEqual(flags[flags.index('-adobevalidatescope')+1], 'received')
            self.assertEqual(flags[flags.index('-adobevalidate')+1],
                             'off' if row['stage'] == 'seed' else 'require')
            self.assertEqual(row['requires_unchanged_noop'], row['stage'] == 'noop')
        self.assertEqual((binaries, tool), before)

    def test_budgets_include_both_endpoints_and_source_headroom(self):
        value = schedule(*inputs())
        self.assertEqual(value['limits'], LIMITS)
        self.assertEqual(value['token_indexes'], list(range(8)))
        self.assertEqual(value['declared_endpoint_plus_owner_credits'], 6)
        self.assertLessEqual(value['minimum_payload_credits'], value['payload_credits'])
        self.assertLessEqual(value['minimum_descriptor_credits'], value['descriptor_credits'])
        for row in value['rows']:
            flags = row['server_flags']
            for option, expected in [('-semanticworkers','2'),('-semanticcpubudget','2'),
                    ('-semanticpayloadbudget','6144'),('-adobevalidatorworkspace','2048'),
                    ('-semanticmaxinflight','4'),('-validationtreememory','0')]:
                self.assertEqual(flags[flags.index(option)+1], expected)
        for field in ('runtime_admitted','sdk_invoked','hard_rss_cap','os_thread_cap'):
            self.assertIs(value[field], False)

    def test_refuses_unqualified_or_ambiguous_input(self):
        for mutation in ('role','same-peer','thread-bool','parallel-tool','tool-build',
                         'hash','relative','escape','namespace','extra'):
            binaries, tool, workspace = inputs()
            if mutation == 'role': binaries['ox']['label']='stock'
            if mutation == 'same-peer': binaries['ox']['path']=binaries['stock']['path']
            if mutation == 'thread-bool': tool['threads']=True
            if mutation == 'parallel-tool': tool['threads']=2
            if mutation == 'tool-build': tool['build_id']='unqualified'
            if mutation == 'hash': tool['sha256']='A'*64
            if mutation == 'relative': binaries['stock']['path']='relative'
            if mutation == 'escape': workspace='/private/tmp/../u-smg-'+'a'*16
            if mutation == 'namespace': workspace='/private/tmp/reused-name'
            if mutation == 'extra': tool['fallback']=True
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                schedule(binaries, tool, workspace)


if __name__ == '__main__':
    unittest.main()
