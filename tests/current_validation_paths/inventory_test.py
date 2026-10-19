"""Static first-party import closure; parses source, never imports or executes it."""
import ast,unittest
from pathlib import Path
from current_validation_paths import inventory
from current_validation_paths.admission import REPOSITORY

ROOTS=('tests','tests/sdk_host_matrix','bench/sync')
# The generic multi-harness dispatcher is imported only for manifest constants;
# its dispatch functions lazily import every other harness and are never called.
UNCALLED={('tests/shared_dispatch.py','checked_io_request'),('tests/shared_dispatch.py','run')}


def resolve(name):
    for root in ROOTS:
        base=Path(REPOSITORY)/root/name.replace('.','/')
        for candidate in (base.with_suffix('.py'),base/'__init__.py'):
            if candidate.is_file():return str(candidate.relative_to(REPOSITORY))
    return None


def closure(starts):
    seen=set();pending=list(starts)
    while pending:
        name=pending.pop()
        if name in seen:continue
        seen.add(name)
        tree=ast.parse((Path(REPOSITORY)/name).read_text())
        skipped={id(n) for f in tree.body if isinstance(f,ast.FunctionDef) and (name,f.name) in UNCALLED for n in ast.walk(f)}
        for node in ast.walk(tree):
            if id(node) in skipped:continue
            modules=[]
            if isinstance(node,ast.Import):modules=[a.name for a in node.names]
            elif isinstance(node,ast.ImportFrom) and node.module and node.level==0:
                modules=[node.module]+[node.module+'.'+a.name for a in node.names]
            for module in modules:
                found=resolve(module)
                if found:pending.append(found)
    return seen


class Inventory(unittest.TestCase):
    def test_execution_pins_cover_every_first_party_module_the_run_imports(self):
        starts=['tests/current_validation_paths/'+n for n in ('entry.py','freeze.py','producer_proxy.py')]
        starts+=['tests/sdk_merge_receiving/child_entry.py','tests/clone_interruption_transport.py']
        needed=closure(starts);pinned=set(inventory.execution())
        self.assertGreater(len(needed),40);self.assertEqual(needed-pinned,set())
        self.assertIn('tests/validation_paths/run.py',pinned)

if __name__=='__main__':unittest.main()
