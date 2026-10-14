"""Organize reported evidence; does not infer missing patent/topic mappings."""
from pathlib import Path
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data/chapter04'
OUT.mkdir(parents=True, exist_ok=True)
tables_path = 'refs/source-extracts/chapter04-tables.json'
tables = {t['source_table']: t['rows'] for t in json.loads((ROOT / tables_path).read_text())}
source_paths = [
    '论文保留初版-基于动态演化的智能建造领域关键技术识别及预测_副本3.docx',
    tables_path, 'refs/source-extracts/chapter04-original.txt',
    'refs/source-extracts/chapter04-figures/source-paragraph-262.png',
    'refs/source-extracts/chapter04-figures/source-paragraph-269.png',
    'plan/review/chapter04-table-crosscheck.json',
    'tables/chapter04-network-reported-metrics.json',
]
sources = [{'path': p, 'sha256': hashlib.sha256((ROOT / p).read_bytes()).hexdigest()}
           for p in source_paths]

observations = []
for table_id in (13, 14, 15):
    for row_number, row in enumerate(tables[table_id][1:], start=2):
        if row[0] == '-':
            continue
        ipc = re.sub(r'[\s-]', '', row[0])
        observations.append({
            'evidence_id': f'N{table_id-12}-{ipc}',
            'stage_id': f'S{table_id-12}', 'ipc': ipc,
            'values_as_reported': dict(zip(
                ['degree', 'betweenness', 'closeness', 'eccentricity'], row[1:])),
            'source': {'path': tables_path, 'source_table': table_id, 'row_including_header': row_number},
            'status': 'reported_value_not_recomputed',
            'supplement_crosscheck': 'missing_in_supplement' if table_id == 13 and ipc == 'G01B011'
                                    else 'matched_reported_supplement',
        })

# These links are interpretations already discussed in the chapter, NOT joins.
candidate_ipcs = {
    2: ['G06F030', 'G06N003'], 3: ['B25J011'],
    4: ['G01B011'], 6: ['G06N003'], 8: ['B33Y070'],
}
static_groups = [
    {'evidence_id': 'H01', 'topic_ids': ['T02', 'T05', 'T09'], 'cut_height': 1.2,
     'meaning': '图示截断高度下的语义子组，非跨阶段演化或工程协同实测',
     'source': {'path': source_paths[4], 'locator': '原层次聚类图'}},
    {'evidence_id': 'H02', 'topic_ids': ['T04', 'T07'], 'cut_height': 1.2,
     'meaning': '图示截断高度下的语义子组，非跨阶段演化或工程协同实测',
     'source': {'path': source_paths[4], 'locator': '原层次聚类图'}},
]

definitions = [
    '围绕同一工程对象组织多专业模型、数据与业务协同的技术方向。',
    '通过参数、规则、目标和约束组织设计方案生成与比较的技术方向。',
    '将机器人机构、驱动、移动与多设备共同作业组织相结合的技术方向。',
    '将施工现场状态感知与数字表达相联系，用于过程监测和分析的技术方向。',
    '将规范条件与工程设计信息建立可处理对应，以辅助核查的技术方向。',
    '将行业知识与语言或多模态信息处理结合，用于工程知识和任务辅助的技术方向。',
    '通过预制构件及连接方式衔接设计、工厂制造与现场安装的技术方向。',
    '以材料逐层堆积形成建筑构件，关联几何、工艺及材料性能的技术方向。',
    '以模块及接口关系组织建筑空间的组装、拆卸与功能调整的技术方向。',
]
records = []
for index, row in enumerate(tables[16][1:], start=1):
    title, keywords = row[1].split('：', 1)
    tid = f'T{index:02d}'
    links = []
    for ipc in candidate_ipcs.get(index, []):
        links.append({
            'ipc': ipc, 'status': 'functional_interpretation_only',
            'network_evidence_ids': [o['evidence_id'] for o in observations if o['ipc'] == ipc],
            'allowed_use': '提出结构与工程内涵的对照问题；不得当作该主题已验证的节点指标',
            'validation_needed': '逐专利IPC—年份—主题对应表',
        })
    records.append({
        'technology_id': tid, 'source_topic_id': row[0], 'name': title,
        'definition': definitions[index-1],
        'definition_status': 'scope_summary_not_verified_implementation',
        'definition_source': {'path': 'refs/source-extracts/chapter04-original.txt', 'paragraph': f'{251+index:04d}'},
        'keywords': keywords.split('、'), 'reported_example': row[2],
        'example_status': 'source_technical_description_not_verified_deployment',
        'topic_evidence_id': f'Q{index:02d}',
        'source': {'path': tables_path, 'source_table': 16, 'row_including_header': index+1},
        'classification': 'reported_key_technology_theme',
        'patent_ids': None, 'verified_ipc_mapping': None,
        'candidate_context_links': links,
        'field_stage_context': ['S1', 'S2', 'S3'],
        'reported_topic_corpus_scope': ['S2', 'S3'],
        'technology_specific_lifecycle': None,
        'stage_topic_counts': None, 'stage_topic_strength': None,
        'temporal_semantic_change': None, 'observed_bottleneck_evidence': None,
        'static_relation_evidence_ids': [g['evidence_id'] for g in static_groups if tid in g['topic_ids']],
        'allowed_claims': ['原报告将相关文本归纳为该主题，并给出所列关键词和典型技术表述'],
        'unsupported_claims': ['主题在特定阶段快速增长', '已经实现工程协同',
                               '已确定技术成熟度或未来突破年份', '网络节点指标等于主题指标'],
        'missing_materials': ['逐专利编号、年份及主题映射', '主题样本量与代表文本',
                              '动态主题分析及参数记录', '实证瓶颈资料与单项生命周期依据'],
    })

supplement_path = 'tables/chapter04-network-reported-metrics.json'
supplement = json.loads((ROOT / supplement_path).read_text())
candidate_specs = [
    ('B28C007', '混凝土智能化搅拌与配送控制', '0239'),
    ('G06Q050', '建造过程数字化管理平台', '0240'),
    ('B66C023', '智能塔吊与吊装机器人', '0241'),
    ('C08L097', '生物质纤维增强可降解建材', '0242'),
    ('G16Y010', '建造物联网通用数据接口标准', '0243'),
    ('E02D033', '地基智能监测与灾害预警', '0244'),
]
candidate_nodes = []
for number, (ipc, label, paragraph) in enumerate(candidate_specs, start=1):
    short = ipc[:4] + str(int(ipc[4:]))
    matches = [
        {'stage_id': f"S{item['stage']}",
         'metrics': {k: item[k] for k in ('degree', 'betweenness', 'closeness', 'eccentricity')},
         'source': {'path': supplement_path, 'row_index_zero_based': i}}
        for i, item in enumerate(supplement) if item['ipc'] == short
    ]
    candidate_nodes.append({
        'candidate_id': f'C{number:02d}', 'ipc': ipc, 'application_label_from_source': label,
        'label_note': '原稿的智能建造应用解释，非IPC官方完整定义',
        'source': {'path': 'refs/source-extracts/chapter04-original.txt', 'paragraph': paragraph},
        'network_observations': matches, 'verified_topic_mapping': None,
        'status': 'candidate_only_not_validated_future_key_technology',
        'unsupported_claims': ['将于3—5年内跃迁', '已实现规模应用', '具有标准必要专利地位'],
    })

package = {
    'schema_version': '0.1', 'created_date': '2026-10-13',
    'status': 'partial_reported_evidence_not_complete_dynamic_analysis',
    'purpose': '第4章已有证据组织及第5章输入准备；缺项保留null，不补造动态结果',
    'data_cutoff_as_reported': '2025-10-01',
    'cutoff_note': '该日期为样本检索截止日，不等于所有方法说明及整理记录在当日已可获得',
    'sample_counts_as_reported': {'patents': 5926, 'topic_input_patents': 926, 'topics': 9},
    'sample_linkage_status': '926条输入与总样本/主题的逐项映射待核实',
    'reported_clustering_evaluation': {
        'evidence_id': 'M01',
        'default': {'silhouette': 0.415, 'calinski_harabasz': 1245.7},
        'reported_optimized': {'silhouette': 0.682, 'calinski_harabasz': 2896.3},
        'source': {'path': 'refs/source-extracts/chapter04-original.txt', 'paragraph': '0248'},
        'status': 'reported_only_comparability_and_repeated_runs_unverified',
    },
    'stages': [
        {'id': 'S1', 'years': [2010, 2014]},
        {'id': 'S2', 'years': [2015, 2019]},
        {'id': 'S3', 'years': [2020, 2025], 'partial_final_year': True},
    ],
    'stage_note': '网络观察窗口；不等同于已拟合的生命周期拐点或单项技术成熟阶段',
    'sources': sources, 'network_observations': observations,
    'static_theme_relations': static_groups, 'technology_records': records,
    'potential_technology_candidates': candidate_nodes,
    'global_limits': [
        '未重新运行网络构建或BERTopic，报告值保留原精度',
        '主题映射未经逐专利验证，候选功能联系不作定量映射',
        '阈值口径、连通分量及主题输入须核实',
        '静态层次关系不能证明技术协同效果，未实施独立稳健性与外部验证',
        '不含各技术的概率、TRL或已验证预测成绩',
    ],
}

ids = [o['evidence_id'] for o in observations] + [g['evidence_id'] for g in static_groups] + [r['topic_evidence_id'] for r in records]
assert len(ids) == len(set(ids))
assert len(observations) == 30 and len(records) == 9
for r in records:
    for link in r['candidate_context_links']:
        assert link['network_evidence_ids'] and set(link['network_evidence_ids']) <= set(ids)
    assert set(r['static_relation_evidence_ids']) <= set(ids)

out = OUT / 'evolution-evidence-v0.1.json'
out.write_text(json.dumps(package, ensure_ascii=False, indent=2)+'\n')
lines = ['# 第4章演化证据包初版', '',
         '本文件为JSON证据包的可读索引。整理已提供的真实报告，不代表重新完成实验。', '',
         '九主题对应原表16，30条网络记录对应原表13—15。候选IPC联系是功能解释，尚无逐专利映射；阶段主题强度、语义变化、单项生命周期和实证瓶颈均保留空值。', '',
         '| 对象ID | 技术主题 | 原报告典型技术 | 候选IPC（仅功能对应） |',
         '|---|---|---|---|']
for r in records:
    ipcs = '、'.join(l['ipc'] for l in r['candidate_context_links']) or '待核实'
    lines.append(f"| {r['technology_id']} | {r['name']} | {r['reported_example']} | {ipcs} |")
lines += ['', '引用主题事实使用Q01—Q09，引用节点指标使用网络记录的N前缀编号，静态语义子组使用H01/H02。不要将候选IPC关联写成主题指标。每条记录包含来源表、行号、缺失材料和结论边界。', '',
          'JSON文件：evolution-evidence-v0.1.json。生成脚本：scripts/build_chapter04_evidence.py。', '',
          '证据不足时仅能形成有限的条件性问题或判断，不能因多智能体一致同意而将其升级为已验证结论。']
lines += ['', '## 潜在关键技术候选', '',
          '以下候选保留原稿提出的方向；指标来自补充网络记录，不作未来跃迁已验证结论。与九主题的逐专利对应仍待核实。', '',
          '| 候选ID | IPC | 原稿应用解释 | 有记录的阶段 |', '|---|---|---|---|']
for c in candidate_nodes:
    stages = '、'.join(o['stage_id'] for o in c['network_observations'])
    lines.append(f"| {c['candidate_id']} | {c['ipc']} | {c['application_label_from_source']} | {stages} |")
(OUT / 'README.md').write_text('\n'.join(lines)+'\n')
print(f'Created {out.relative_to(ROOT)}: {len(records)} topics, {len(observations)} reported node records; missing fields retained.')
