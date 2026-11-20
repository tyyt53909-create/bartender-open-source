#!/usr/bin/env python3
"""Check the portable starter, contracts, dependency semantics and generated views."""
from pathlib import Path, PurePosixPath
import argparse
import hashlib
import json
import re
import sys
from jsonschema import Draft202012Validator
from gate_eval import dependency_graph
from render_docs import render_all, refs

ROOT=Path(__file__).resolve().parents[1]
def read(root,p): return json.loads((root/p).read_text(encoding='utf-8'))
def digest(value):
    return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def matches(path,scope): return path.startswith(scope) if scope.endswith('/') else path==scope
def safe(path):
    return bool(path) and not path.startswith('/') and '..' not in PurePosixPath(path).parts and not any(c in path for c in '\\\x00\r\n:')
def files(root):
    return [p for p in sorted(root.rglob('*')) if p.is_file() and not any(x in p.parts for x in ['__pycache__','.git','.venv','.build']) and p.suffix not in ['.pyc','.zip']]
def resources(expr):
    if isinstance(expr,dict):
        return ({expr['resource_class']} if 'resource_class' in expr else set()) | set().union(*(resources(x) for x in expr.values()))
    if isinstance(expr,list): return set().union(*(resources(x) for x in expr))
    return set()

def validate_catalog(data,root=ROOT):
    errors=[]
    def ck(value,message):
        if not value: errors.append(message)
    tasks=data['tasks'];by_id={t['id']:t for t in tasks}
    roles={r['id'] for r in read(root,'coordination/roles.json')['roles']}
    models={m['alias'] for m in read(root,'coordination/models.json')['models']}
    resource_ids={r['id'] for r in read(root,'coordination/hosts.json')['resource_classes']}
    ck(len(by_id)==len(tasks),'Duplicate task ID')
    schema=Draft202012Validator(read(root,'contracts/task.schema.json'))
    runtime=['assigned_run_id','actual_model_id','runner_version','host_id','base_sha','head_sha','candidate_sha','contract_sha','pr_url','reviewer_run_id','merge_commit_sha']
    for t in tasks:
        tid=t['id']
        errors += [f'{tid}: schema {e.json_path}: {e.message}' for e in schema.iter_errors(t)]
        ck(t['role'] in roles,tid+': unknown role')
        ck(t['phase'] in data['phase_definitions'],tid+': unknown phase')
        ck(t['wave'] in data['wave_definitions'],tid+': unknown wave')
        ck(t['model_candidates'][0]==t['model_alias'],tid+': primary model differs from candidate order')
        ck(set(t['model_candidates'])<=models,tid+': unregistered model candidate')
        ck(t['compute_class'] in resource_ids,tid+': unknown implementation resource')
        ck(set(t['validation_compute_classes'])==resources(t['validation_resource_expression']),tid+': validation resource summary differs from expression')
        ck(set(t['validation_compute_classes'])<=resource_ids,tid+': unknown validation resource')
        ck(bool(t['acceptance_criteria']) and bool(t['evidence_required']),tid+': missing acceptance or evidence')
        ck(t['task_spec_sha256']==digest({k:t[k] for k in data['task_spec_fields'] if k in t}),tid+': stale TaskSpec hash')
        for s in t['scope_paths']+t.get('shared_file_change_requests',[]): ck(safe(s),tid+': unsafe scope '+s)
        ck(tid not in t['depends_on'],tid+': direct self dependency')
        if t['delivery_kind']=='validation':
            ck(not any(s.startswith(('Apps/','Packages/')) for s in t['scope_paths']),tid+': validation owns production source')
        if t['delivery_kind']=='code': ck(t['compute_class']!='macos_gui_exclusive',tid+': coding holds GUI for entire task')
        if tid!='APP-02': ck('APP-02 的构建/基线失败' not in t.get('research_evidence_policy',''),tid+': leaked M0-specific research rule')
        if not data['runtime']['connected']:
            ck(t['status']=='planned',tid+': disconnected initial snapshot claims progress')
            ck(all(t.get(k) is None for k in runtime),tid+': fabricated runtime identity')
            ck(t['evidence_refs']==[],tid+': unexplained live evidence')
    graph=dependency_graph(data)
    errors += ['Dependency '+json.dumps(e,ensure_ascii=False) for e in graph['errors']]
    ck(not graph['conservative_cycles'],'Conditional dependency cycle')
    def check_expr(e,label):
        if not isinstance(e,dict): errors.append(label+': expression is not an object');return
        operators=[x for x in ['all_of','any_of','kind'] if x in e]
        ck(len(operators)==1,label+': expression must have exactly one operator')
        if len(operators)!=1:return
        op=operators[0]
        if op!='kind':
            ck(isinstance(e[op],list) and bool(e[op]),label+': empty or invalid boolean group')
            if isinstance(e[op],list):
                for child in e[op]:check_expr(child,label)
        else: ck(e[op] in ['task_accepted','gate_ref','host_attribute','evidence_condition','authority_condition'],label+': unknown expression kind')
    for gid,expr in data['gate_definitions'].items():
        check_expr(expr,gid);p=data['gate_policies'].get(gid,{})
        for tid in p.get('permitted_source_tasks',[])+p.get('required_subject_tasks',[]): ck(tid in by_id,gid+': unknown source/subject task')
        if refs(expr,'evidence_condition','name'):
            ck(p.get('decision_required') is True and p.get('require_independent_run') is True,gid+': evidence gate lacks independent decision policy')
            ck(set(p.get('required_bindings',[]))>={'source','scope','context'},gid+': incomplete current binding policy')
        for condition,ids in p.get('condition_source_tasks',{}).items():
            ck(condition in refs(expr,'evidence_condition','name') and set(ids)<=set(p.get('permitted_source_tasks',[])),gid+': invalid condition/source mapping')
    features=set().union(*(set(t['feature_ids']) for t in tasks))
    ck(features=={f'F{n:02d}' for n in range(1,13)},'F01-F12 mapping incomplete')
    # Regression invariants exposed by the external review, not a fixed task count.
    for tid in ['APP-03','APP-12','APP-13']:
        ck('M0_BASELINE_VERIFIED' in by_id[tid]['execution_gates'],tid+': M0 baseline gate missing')
    ck({'APP-18','APP-25'}<=set(by_id['APP-22']['depends_on']),'APP-22: permissions/UI implementation missing from dependencies')
    ck('F01' in by_id['APP-14']['feature_ids'],'APP-14: manual organization mapping missing')
    ck({'F06','F07'}<=set(by_id['APP-07']['feature_ids']),'APP-07: input/recovery mapping missing')
    for tid in ['OPS-03','OPS-05','OPS-06']:ck(by_id[tid]['role']=='integrator',tid+': CLI tooling wrongly assigned to macOS platform')
    for tid in ['APP-17','APP-18']:ck(by_id[tid]['compute_class']=='macos_build',tid+': coding resource is not macos_build')
    for tid in ['APP-08','APP-26']:ck(by_id[tid]['model_candidates']==['grok4.7','gpt6.2astra'],tid+': reviewer routing differs from policy')
    ck('APP-26' in refs(data['gate_definitions']['M3_PRODUCT_GATE_PASSED'],'task_accepted','task_id'),'M3: no explicit adjudication task')
    ck(set(data['gate_policies']['M3_PRODUCT_GATE_PASSED'].get('required_subject_tasks',[]))=={'APP-18','APP-19','APP-20','APP-21'},'M3: subject-author binding policy missing')
    return errors

def validate_package(root=ROOT,data=None,check_docs=True):
    data=data or read(root,'coordination/tasks.json');errors=validate_catalog(data,root)
    def ck(value,message):
        if not value: errors.append(message)
    by_id={t['id']:t for t in data['tasks']};ownership=read(root,'coordination/path-ownership.json')
    for p in files(root):
        rel=p.relative_to(root).as_posix();ck(p.resolve().is_relative_to(root.resolve()),'Path escapes package: '+rel)
        owners=[e for e in ownership['entries'] if matches(rel,e['path'])]
        ck(len(owners)==1,'Path must have exactly one owner classification: '+rel)
        if len(owners)==1:
            o=owners[0]
            if o['mode']!='archived':
                tid=o['owner_task'];ck(tid in by_id,'Unknown owner '+str(tid))
                if tid in by_id: ck(any(matches(rel,s) for s in by_id[tid]['scope_paths']),'Owner scope cannot write '+rel)
            if o['mode']=='generated':ck((root/o['generator']).is_file(),'Missing generator for '+rel)
        if p.suffix in ['.md','.json','.py','.txt']:
            text=p.read_text(encoding='utf-8')
            ck(not re.search(r'https?://chatgpt[.]com/library[?]',text),'Private account link in distributable: '+rel)
    for tid,paths in ownership['required_existing_paths'].items():
        for path in paths:
            ck((root/path).is_file(),'Expected existing source missing: '+path)
            ck(any(matches(path,s) for s in by_id[tid]['scope_paths']),tid+': cannot write required existing source '+path)
    for path in (root/'contracts').glob('*.schema.json'):
        try:Draft202012Validator.check_schema(json.loads(path.read_text()))
        except Exception as e: errors.append(path.name+': invalid JSON Schema '+str(e))
    policy=read(root,'coordination/policies.json');hosts=read(root,'coordination/hosts.json')
    ck(policy['limits']['implementation_runs']<policy['limits']['global_model_sessions'],'No independent review capacity reserved')
    ck(policy['limits']['gui_runs_per_host']==1,'GUI exclusivity missing')
    ck(policy['git']['integration_lease_held_until_terminal_outcome'],'Integration lease ends before terminal result')
    ck(not policy['git']['integration_identity_may_bypass_rules'],'Integration identity can bypass branch rules')
    ck(policy['deployment']['activation_gate']=='automation_runtime_ready','Automatic dispatch activation is unbound')
    ck(data['gate_consumers'].get('automation_runtime_ready')==['policy:deployment.activation_gate'],'OPS-07 output has no explicit consumer')
    if not data['runtime']['connected']:
        ck(not policy['deployment']['enabled'] and hosts['hosts']==[],'Planning snapshot invents connected service/host')
        for model in read(root,'coordination/models.json')['models']:
            ck(model['effective_model_id'] is None and model['effective_provider'] is None,'Planning snapshot invents effective model')
    bs=root/'docs/baselines';provenance=read(bs,'provenance.json')
    for item in provenance['files']:
        p=bs/item['path'];ck(p.is_file(),'Missing archived baseline: '+item['path'])
        if p.is_file():ck(len(p.read_bytes())==item['archived_bytes'] and hashlib.sha256(p.read_bytes()).hexdigest()==item['archived_sha256'],'Archived baseline digest changed: '+item['path'])
    lab=root/'menubar-validation-lab';lm=lab/'PACKAGE-MANIFEST.json'
    ck(hashlib.sha256(lm.read_bytes()).hexdigest()==provenance['lab_snapshot']['sha256'],'Historical Lab manifest changed')
    for item in read(lab,'PACKAGE-MANIFEST.json')['files']:
        p=lab/item['path'];ck(p.is_file(),'Missing historical Lab file: '+item['path'])
        if p.is_file():ck(len(p.read_bytes())==item['bytes'] and hashlib.sha256(p.read_bytes()).hexdigest()==item['sha256'],'Historical Lab bytes changed: '+item['path'])
    # Check repository-local Markdown links in our authored docs. Vendor snapshots
    # retain original-site navigation and are not relinked or presented as inputs.
    docs=list((root/'docs').rglob('*.md'))+[root/'README.md',root/'contracts/README.md']
    for p in docs:
        if not p.exists():continue
        text=p.read_text();links=re.findall(r'\]\(([^\s)]+)\)',text)+re.findall(r'^\[[^\]]+\]:\s+(\S+)',text,re.M)
        for url in links:
            if re.match(r'^[a-zA-Z]+:',url) or url.startswith('#'):continue
            target=(p.parent/url.split('#')[0]).resolve()
            ck(target.is_relative_to(root.resolve()) and target.exists(),'Unresolved local link: '+p.relative_to(root).as_posix()+' -> '+url)
    if check_docs:
        for name,content in render_all(root).items():
            ck((root/name).exists() and (root/name).read_text()==content,'Generated document drift: '+name)
    return errors

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--root',type=Path,default=ROOT);args=parser.parse_args()
    try:
        data=read(args.root,'coordination/tasks.json');errors=validate_package(args.root,data)
    except (OSError,ValueError,KeyError,TypeError) as e:
        errors=['Input error: '+str(e)];data={'tasks':[]}
    print(json.dumps({'status':'invalid' if errors else 'portable_planning_package_valid','tasks':len(data['tasks']),'errors':errors,'proves':'offline structure, local bytes, contracts, ownership and document consistency only','does_not_prove':'remote runners, Mac build/GUI, trustworthy live ledger, merge enforcement or release readiness'},ensure_ascii=False,indent=2))
    return 1 if errors else 0

if __name__=='__main__':raise SystemExit(main())
