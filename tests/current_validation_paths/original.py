"""Trusted source adapter for all original default assertions, never old main.

Callbacks are executor source, not remotely selected packet fields. Returned
functions remain UNADMITTED and may run only under a retained owner. This does
not make a session implementation or child lifetime safe by declaration.
"""
import ast,hashlib
from current_validation_paths.contract import legacy_case_inventory,CASES


def load(source,*,session_factory,cancel_actor,path_factory,filename):
    legacy_case_inventory(source)
    if not callable(session_factory) or not callable(cancel_actor) or not callable(path_factory):raise ValueError('trusted source adapters required')
    tree=ast.parse(source);body=[]
    for node in tree.body:
        if isinstance(node,ast.If):
            test=node.test
            if not (isinstance(test,ast.Compare) and isinstance(test.left,ast.Name) and test.left.id=='__name__'
                and len(test.ops)==1 and isinstance(test.ops[0],ast.Eq) and len(test.comparators)==1
                and isinstance(test.comparators[0],ast.Constant) and test.comparators[0].value=='__main__'
                and not node.orelse and len(node.body)==1 and isinstance(node.body[0],ast.Expr)
                and isinstance(node.body[0].value,ast.Call) and isinstance(node.body[0].value.func,ast.Name)
                and node.body[0].value.func.id=='main' and not node.body[0].value.args and not node.body[0].value.keywords):
                raise ValueError('unexpected top-level source execution guard')
            continue # Original CLI main is never exposed or executed.
        if isinstance(node,(ast.Import,ast.ImportFrom)):
            names={a.name.split('.')[0] for a in node.names} if isinstance(node,ast.Import) else {node.module}
            if not names<={'argparse','hashlib','json','os','pathlib','signal','subprocess','tempfile','time'}:
                raise ValueError('unexpected legacy source import')
        elif isinstance(node,ast.Assign):
            try:ast.literal_eval(node.value)
            except (ValueError,TypeError):raise ValueError('unexpected top-level source initializer')
        elif isinstance(node,ast.Expr):
            if not isinstance(node.value,ast.Constant) or not isinstance(node.value.value,str):
                raise ValueError('unexpected top-level source expression')
        elif isinstance(node,(ast.FunctionDef,ast.ClassDef)):
            if node.decorator_list:raise ValueError('legacy decorators cannot execute in adapter')
        else:raise ValueError('unexpected legacy top-level source node')
        body.append(node)
    def definitions(nodes):
        for node in nodes:
            if isinstance(node,ast.FunctionDef):
                args=node.args
                if (node.decorator_list or node.returns is not None
                    or any(arg.annotation is not None for arg in [*args.posonlyargs,*args.args,*args.kwonlyargs]
                        +([args.vararg] if args.vararg else [])+([args.kwarg] if args.kwarg else []))):
                    raise ValueError('legacy callable definition expressions refused')
                for default in [*args.defaults,*[x for x in args.kw_defaults if x is not None]]:
                    try:ast.literal_eval(default)
                    except (ValueError,TypeError):raise ValueError('legacy callable default execution refused')
            elif isinstance(node,ast.ClassDef):
                if node.bases or node.keywords or node.decorator_list:raise ValueError('legacy class construction expressions refused')
                if any(not isinstance(x,ast.FunctionDef) and not (isinstance(x,ast.Expr) and isinstance(x.value,ast.Constant) and isinstance(x.value.value,str)) for x in node.body):
                    raise ValueError('legacy class body execution refused')
                definitions(node.body)
    definitions(body)
    module=ast.Module(body=body,type_ignores=[])
    ns=dict(__name__='unison_owned_original_validation_cases',__file__=filename)
    exec(compile(module,filename,'exec'),ns)
    legacy=ns['Session'];session=session_factory(legacy)
    if not isinstance(session,type) or session is legacy or not issubclass(session,legacy):raise ValueError('explicit retained Session successor required')
    for name in ('__init__','sync','command','interruption'):
        if name not in session.__dict__ or not callable(session.__dict__[name]) or session.__dict__[name] is legacy.__dict__[name]:
            raise ValueError('retained Session must override '+name)
    legacy_path=ns['Path'];owned_path=path_factory(legacy_path)
    if not isinstance(owned_path,type) or owned_path is legacy_path or not issubclass(owned_path,legacy_path):
        raise ValueError('explicit owned private-file Path successor required')
    for name in ('read_bytes','read_text','write_bytes','write_text','open'):
        if name not in owned_path.__dict__ or not callable(owned_path.__dict__[name]) or owned_path.__dict__[name] is getattr(legacy_path,name):
            raise ValueError('owned Path must replace bare close lifecycle for '+name)
    ns['Session']=session;ns['Path']=owned_path;ns['cancelled']=cancel_actor;ns.pop('main',None)
    functions={family:ns[family] for family,*_ in CASES}
    return dict(functions=functions,source_sha256=hashlib.sha256(source.encode()).hexdigest(),
        original_main_exposed=False,legacy_bare_cancellation_exposed=False,legacy_bare_Path_IO_exposed=False,
        runtime_admitted=False,SDK_calls=0)
