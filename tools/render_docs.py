#!/usr/bin/env python3
"""Compile planning views deterministically. No network, dispatch or state writes."""
from pathlib import Path
import argparse
from collections import Counter
import json

ROOT = Path(__file__).resolve().parents[1]

def read(root, path):
    return json.loads((root/path).read_text(encoding='utf-8'))

def table(headers, rows):
    def esc(v): return str(v).replace('|','/').replace('\n',' ')
    lines=['| '+' | '.join(headers)+' |','|'+'|'.join('---' for _ in headers)+'|']
    return '\n'.join(lines+['| '+' | '.join(esc(v) for v in row)+' |' for row in rows])

def expression_text(e):
    for op,label in [('all_of','ALL'),('any_of','ANY')]:
        if op in e: return label+'('+ '; '.join(expression_text(x) for x in e[op])+')'
    k=e.get('kind')
    if k=='task_accepted': return e['task_id']+' accepted'
    if k=='gate_ref': return 'gate:'+e['gate_id']
    if k=='evidence_condition': return 'evidence:'+e['name']
    if k=='host_attribute': return 'host.'+e['attribute']+'='+str(e['equals'])
    if k=='authority_condition': return 'authorization:'+e['name']
    return 'UNKNOWN_EXPRESSION'

def refs(e, kind, field):
    if isinstance(e,dict):
        return ([e.get(field)] if e.get('kind')==kind else []) + sum((refs(x,kind,field) for x in e.values()),[])
    if isinstance(e,list): return sum((refs(x,kind,field) for x in e),[])
    return []

def consumers(data,gid):
    return ([t['id'] for t in data['tasks'] if gid in t['execution_gates']]
        +['gate:'+g for g,e in data['gate_definitions'].items() if gid in refs(e,'gate_ref','gate_id')]
        +data.get('gate_consumers',{}).get(gid,[]))

def gate_table(data):
    return table(['门槛','结构表达式','裁决来源任务','消费方'],[
        [gid,expression_text(e),', '.join(data['gate_policies'][gid].get('decision_owner_tasks',[])) or '可信主机／授权登记',', '.join(consumers(data,gid)) or '—']
        for gid,e in data['gate_definitions'].items()])

def wave_table(data):
    return table(['启动波次','任务（仍须逐项满足依赖）','工作目标'],[
        [w,', '.join(t['id'] for t in data['tasks'] if t['wave']==w),label]
        for w,label in data['wave_definitions'].items()])

def task_table(data,names,board=False):
    heads=['ID','工作','phase / wave','角色／模型候选','直接依赖','额外门槛']+(['状态'] if board else [])
    rows=[]
    for t in data['tasks']:
        rows.append([t['id'],t['title'],t['phase']+' / '+t['wave'],names[t['role']]+' / '+' → '.join(t['model_candidates']),
            ', '.join(t['depends_on']) or '—',', '.join(t['execution_gates']) or '—']+([t['status']] if board else []))
    return table(heads,rows)

def task_book(data,roles):
    names={r['id']:r['name'] for r in roles};counts=Counter(t['status'] for t in data['tasks'])
    out=['# 调酒师开源版｜项目任务书 v'+data['schema_version'],'','日期：'+data['created_on']+'  ',
        f"任务总数：{len(data['tasks'])}；状态分布："+json.dumps(counts,ensure_ascii=False)+'。',
        '本文件由 coordination/tasks.json 与角色注册表生成。当前为未接入的规划快照，未创建真实远端 PR 或工程运行。','',
        '## 使用与交付规则','',
        'TaskSpec 是 task_spec_fields 的不可变投影。每次派工创建 RunManifest，记录真实仓库、版本、模型、主机、资源阶段和预算；结果为 WorkerResult，审查为 ReviewVerdict，实际集成为 IntegrationReceipt，门槛为 GateDecision。运行状态不改变任务摘要，模板不构成已执行证据。','',
        'depends_on 在可信账本确认依赖 accepted 时满足；execution_gates 单独判定。phase 是工作包，wave 是推荐波次，同波不等于同时就绪。门槛 unknown 与 false 都阻止放行。完整负面研究可以 accepted，能力 verified 和产品 gate passed 另行判断。','',
        '实现与验收资源分段申请。validation_resource_expression 的 all_of 表示检查都要完成，any_of 表示工具链条件成立时任选；不表示编码期一直持有 GUI。动作前置在系统操作前检查，允许先观察并记录 precondition_failed；缺机器、权限或实际观察仍为 blocked/not_run。','',
        '代码和版本化协议通过独立审查、当前基线候选验证、实际合并确认后接受。纯研究／裁决可归档不可变证据后接受，不伪造 merge SHA。作者子 Agent 不充当唯一独立 reviewer；角色默认范围不扩大任务 scope_paths。','',
        '## 波次与启动','',wave_table(data),'',
        '人工 bootstrap 使用同一契约、排他资源登记和已授权 CLI，不等待未完成的调度器。OPS-05 或 OPS-06 一条真实可用即可验收 OPS-07；自动派工另需 automation_runtime_ready。OpenCode 仍是首条 Codex 路线的可选扩展。','',
        '## 首版需求映射','',table(['能力','相关任务'],[[f'F{n:02d}',', '.join(t['id'] for t in data['tasks'] if f'F{n:02d}' in t['feature_ids'] and t['id']!='APP-24')] for n in range(1,13)]),'',
        'APP-24 综合 F01—F12。需求覆盖不证明功能已实现。','',
        '## 任务总览','',task_table(data,names),'','## 完整任务卡','']
    for t in data['tasks']:
        out += ['### '+t['id']+'｜'+t['title'],'',
            '归属工作包 phase：'+t['phase']+'；推荐波次 wave：'+t['wave']+'；角色：'+names[t['role']]+'；模型候选顺序：'+' → '.join(t['model_candidates'])+'；交付类型：'+t['delivery_kind']+'；状态：'+t['status']+'。','',
            '实现资源：'+t['compute_class']+'。验收资源表达式：`'+json.dumps(t['validation_resource_expression'],ensure_ascii=False)+'`。','',
            '直接依赖：'+(', '.join(t['depends_on']) or '无')+'。额外门槛：'+(', '.join(t['execution_gates']) or '无额外 gate；仍须派工通用前置')+'。','',
            '**可修改范围**','']+['- '+x for x in t['scope_paths']]
        if t.get('shared_file_change_requests'): out += ['', '共享文件变更请求（owner 串行处理）：'+', '.join(t['shared_file_change_requests'])+'。']
        if t.get('scope_change_policy'): out += ['',t['scope_change_policy']]
        out += ['','**验收标准**','']+['- '+x for x in t['acceptance_criteria']]
        out += ['','**需要的证据**','']+['- '+x for x in t['evidence_required']]
        if t.get('research_evidence_policy'): out += ['', '通用研究规则：'+t['research_evidence_policy']]
        if t.get('research_task_note'): out += ['', '本卡补充：'+t['research_task_note']]
        if t.get('action_preconditions'): out += ['', '实际动作前置：'+', '.join(t['action_preconditions'])+'。']
        if t['required_environment_notes']: out += ['', '环境说明：'+' '.join(t['required_environment_notes'])]
        if t['blocked_reasons']: out += ['', '接入前置：'+' '.join(t['blocked_reasons'])]
        if t['optional_for_first_lane']: out += ['', '不阻塞已可用的首条执行器路线。']
        out += ['', '审查规则：'+t['review_policy']+'。','','任务规范 SHA-256：`'+t['task_spec_sha256']+'`','']
    out += ['## 门槛定义与签发','',gate_table(data),'',
        '结构见 [依赖视图](dependency-map.md)。M0 由 APP-02 的独立验收签发，M1 产品裁决归 APP-08，M3 汇总裁决归 APP-26。签发主体必须在可信 registry 登记，报告里自称 reviewer 不产生权限。','',
        '## 修复与变更','',
        '发现问题转具体修复卡或回实现者；APP-22 不直接修改生产 UI。新提交或相关基线／契约变化使旧结论重新评估。Grok 不可用时按已列候选顺序选择独立 Astra run，记录 requested/effective 路由。','',
        '新增任务通过同一 Schema、引用、路径和生成检查，不把初始任务总数硬编码为永久规则。发行准备与签名、试用、公开发布的授权按具体动作分别核对。','']
    return '\n'.join(out)

def board(data,roles,models,hosts):
    counts=Counter(t['status'] for t in data['tasks']);names={r['id']:r['name'] for r in roles}
    out=['# 调酒师开源版｜Agent 协调板 v'+data['schema_version'],'','快照日期：'+data['created_on']+'  ',
        '连接状态：'+str(data['runtime']['connected']).lower()+'；任务状态来源：'+data['status']+'。','',
        f"{len(data['tasks'])} 张任务；{len(data['runtime']['active_runs'])} 个活动工程运行；{sum(t.get('pr_url') is not None for t in data['tasks'])} 个登记 PR；{counts.get('accepted',0)} 张 accepted。模型候选不是已验证实际路由。",'',
        '## 任务视图','',task_table(data,names,True),'','## 推荐启动波次','',wave_table(data),'',
        '资源与具体 scope 见任务书。建议全局上限 4 个模型会话、3 个实现写入任务，每台 Mac GUI 1 个任务；协调、审查与子 Agent 都计入。人工调度同样保留资源和运行记录。','',
        '## 门槛及其消费关系','',gate_table(data),'',
        '没有真实 RuntimeSnapshot 与证据时，不宣称任何产品 gate passed。失败研究可以 accepted；这不打开 M0/M1/M3。','',
        '## 模型登记','',table(['别名','实际 provider','实际 model ID','可用状态'],[[m['alias'],m.get('effective_provider') or '未解析',m.get('effective_model_id') or '未解析',m.get('availability','未核验')] for m in models]),'',
        f"实际登记主机数：{len(hosts['hosts'])}。ocra 候选确认状态：{str(hosts['orchestrator']['confirmed']).lower()}。",'',
        '## 更新入口','',
        '协调者提交版本化任务变化；运行事实未来由单写账本导出。python3 tools/render_docs.py 生成全部视图，--check 检查漂移。生成器不派工、不改状态、不连接远端。','']
    return '\n'.join(out)

def dependencies(data):
    out=['# 结构化依赖与门槛视图','',
        '由 coordination/tasks.json 生成。ALL 表示全部，ANY 表示任一分支满足；表达式保留替代路径。保守环检查遍历所有可能边，不代表所有备选都成为运行前置。路线、资源和时长未确定时，不生成虚构的数值关键路径。','',
        '## 任务直接依赖','',table(['任务','直接依赖','额外 gate'],[[t['id'],', '.join(t['depends_on']) or '—',', '.join(t['execution_gates']) or '—'] for t in data['tasks']]),'','## 门槛表达式','']
    for gid,e in data['gate_definitions'].items():
        explanation=data['gate_explanations'].get(gid,'')
        if not isinstance(explanation,str): explanation=json.dumps(explanation,ensure_ascii=False)
        out += ['### '+gid,'',explanation,'','消费方：'+', '.join(consumers(data,gid))+'。','',
            '```json',json.dumps({'expression':e,'policy':data['gate_policies'][gid]},ensure_ascii=False,indent=2),'```','']
    return '\n'.join(out)

def render_all(root=ROOT):
    data=read(root,'coordination/tasks.json');roles=read(root,'coordination/roles.json')['roles']
    values={'TASK_COUNT':str(len(data['tasks'])),'WAVE_TABLE':wave_table(data),'GATE_TABLE':gate_table(data),
        'ROLE_TABLE':table(['角色','职责','模型候选','输出'],[[r['id'],r['responsibility'],' → '.join([r['model_alias']]+r.get('fallback_aliases',[])),r['output']] for r in roles])}
    out={}
    for name in ['project-plan','agent-team-architecture']:
        s=(root/'coordination/document-templates'/f'{name}.md').read_text(encoding='utf-8')
        for key,value in values.items(): s=s.replace('{{'+key+'}}',value)
        out[f'docs/{name}.md']=s.rstrip()+'\n'
    out['docs/task-book.md']=task_book(data,roles).rstrip()+'\n'
    out['docs/coordination-board.md']=board(data,roles,read(root,'coordination/models.json')['models'],read(root,'coordination/hosts.json')).rstrip()+'\n'
    out['docs/dependency-map.md']=dependencies(data).rstrip()+'\n'
    return out

def main(only=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');p.add_argument('--root',type=Path,default=ROOT)
    args=p.parse_args();out=render_all(args.root);different=[]
    for name,s in out.items():
        if only and name not in only: continue
        path=args.root/name
        if args.check:
            if not path.exists() or path.read_text(encoding='utf-8')!=s: different.append(name)
        else: path.parent.mkdir(parents=True,exist_ok=True);path.write_text(s,encoding='utf-8')
    print(json.dumps({'status':'drift' if different else ('documents_match' if args.check else 'rendered'),'documents':sorted(only or out.keys()),'different':different},ensure_ascii=False))
    return 1 if different else 0

if __name__=='__main__':
    raise SystemExit(main())
