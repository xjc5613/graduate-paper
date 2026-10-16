"""Reproducible scientific figures from supplied report values; no inferred edges."""
from pathlib import Path
import os,csv,json,hashlib,shutil
os.environ['MPLCONFIGDIR']=str(Path('/private/tmp/thesis-mpl-cache'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT if (ROOT/'build_manifest.json').exists() else ROOT/'figures/publication_v1'; DATA=OUT/'data'
OUT.mkdir(exist_ok=True); DATA.mkdir(exist_ok=True)
font='/System/Library/Fonts/STHeiti Light.ttc'
fm.fontManager.addfont(font)
plt.rcParams.update({'font.family':fm.FontProperties(fname=font).get_name(),'font.size':10,'axes.unicode_minus':False,'axes.spines.top':False,'axes.spines.right':False,'axes.linewidth':.7,'axes.labelcolor':'#25364A','text.color':'#25364A','xtick.color':'#536273','ytick.color':'#536273','xtick.major.width':.6,'ytick.major.width':.6,'savefig.dpi':450,'svg.fonttype':'none','pdf.fonttype':42})
BLUE='#36769B'; TEAL='#2D9188'; ORANGE='#C88840'; INK='#25364A'; GRAY='#7D8794'
CMAP=LinearSegmentedColormap.from_list('scientific_teal',['#F5F8FA','#BCD8E1','#68A9B8','#286F86','#163F59'])
TOPICS=['多专业协同平台','参数化与生成式设计','机器人集群协同','施工全过程数字孪生','智能规范审查','建筑工程大模型','装配式建筑','建筑规模增材制造','模块化与可重构设计']
outputs=[]
def save(fig,name):
 for ext in ['png','svg','pdf']:fig.savefig(OUT/f'{name}.{ext}',dpi=450,facecolor='white')
 outputs.append(name);plt.close(fig)
def writecsv(name,header,rows):
 with open(DATA/name,'w',encoding='utf-8-sig',newline='') as f:
  w=csv.writer(f);w.writerow(header);w.writerows(rows)
def clean(ax):
 ax.set_axisbelow(True);ax.grid(axis='y',color='#E7ECF0',lw=.6)
# Figure 4-1: values actually printed in original; absent bins are not imputed.
x=np.array(list(range(1,21))+[22,24,27]); y=np.array([887,1330,1223,881,601,374,211,144,81,55,29,19,18,16,10,10,3,8,5,4,5,1,1])
writecsv('fig4_1_visible_frequencies.csv',['IPC分类号数量','原图可见专利频数'],zip(x,y))
fig,axs=plt.subplots(1,2,figsize=(11.2,4.5),gridspec_kw={'width_ratios':[1.2,1]})
fig.subplots_adjust(left=.075,right=.98,bottom=.23,top=.84,wspace=.28)
a=axs[0];a.bar(x,y,color=BLUE,width=.76);clean(a)
a.set(xlim=(.2,28),ylim=(0,1490),xlabel='单件专利IPC分类号数量',ylabel='专利记录数（件）',xticks=[1,5,10,15,20,25,27]);a.set_title('A  全部可见频数',loc='left',fontweight='bold',pad=12)
for xx,yy in zip(x[:9],y[:9]):a.text(xx,yy+25,str(yy),ha='center',fontsize=8,rotation=90 if xx<6 else 0)
a=axs[1]; m=x>=10;a.bar(x[m],y[m],color=TEAL,width=.72);clean(a)
a.set(xlim=(9.2,28),ylim=(0,64),xlabel='单件专利IPC分类号数量',ylabel='专利记录数（件）',xticks=x[m]);a.tick_params(axis='x',labelsize=8);a.set_title('B  长尾区间放大',loc='left',fontweight='bold',pad=12)
for xx,yy in zip(x[m],y[m]):a.text(xx,yy+1.1,str(yy),ha='center',fontsize=8)
fig.text(.075,.96,'专利样本IPC分类号数量分布',fontsize=15,weight='bold',va='top')
fig.text(.075,.075,'据原图标注转录；可见频数合计5916，与正文5926相差10，待核原统计底表。\n未标注类别不补值；B仅放大长尾区间，不改变计量尺度。',fontsize=9,color=GRAY)
save(fig,'fig4_1_IPC分类号分布')
# Figure 4-5: transcribed full rounded displayed matrix; no re-estimated TF-IDF.
words=['建筑增材制造','机器人协同','物联网','大数据','建筑大模型','云计算','区块链','虚拟现实','机器学习','模块化建筑','装配式建筑','参数化与生成式设计','数字孪生','BIM','智慧工地','工程仿真','施工监测','智能施工']
mat=np.zeros((9,18))
entries=[{10:.21,11:.56,13:.64},{3:.23,11:1,12:.34,13:.63},{1:1},{10:.44,12:1,16:.56,17:.63},{3:.35,6:.18},{4:.63,10:.15},{10:1},{0:1,10:.17},{3:.56,12:.11,13:.25,16:.19}]
for i,d in enumerate(entries):
 for j,v in d.items():mat[i,j]=v
writecsv('fig4_5_displayed_weights.csv',['主题ID','主题名称']+words,[[f'T{i+1}',TOPICS[i]]+list(mat[i]) for i in range(9)])
fig,ax=plt.subplots(figsize=(13.2,6.8));fig.subplots_adjust(left=.25,right=.9,bottom=.27,top=.86)
im=ax.imshow(mat,cmap=CMAP,vmin=0,vmax=1,aspect='auto')
ax.set_xticks(range(18));ax.set_xticklabels(words,rotation=52,ha='right',fontsize=9)
ax.set_yticks(range(9));ax.set_yticklabels([f'T{i+1}  {t}' for i,t in enumerate(TOPICS)],fontsize=10)
ax.tick_params(length=0,pad=8)
ax.set_xticks(np.arange(-.5,18,1),minor=True);ax.set_yticks(np.arange(-.5,9,1),minor=True);ax.grid(which='minor',color='white',lw=1.2);ax.tick_params(which='minor',bottom=False,left=False)
for i in range(9):
 for j in range(18):
  if mat[i,j]>0:ax.text(j,i,f'{mat[i,j]:.2f}',ha='center',va='center',color='white' if mat[i,j]>=.6 else INK,fontsize=9)
for sp in ax.spines.values():sp.set_visible(False)
cax=fig.add_axes([.925,.30,.012,.51]);cb=fig.colorbar(im,cax=cax);cb.set_label('原图显示关联权重',labelpad=10);cb.outline.set_visible(False)
fig.text(.04,.96,'九类技术主题与技术关键词的关联',fontsize=16,weight='bold',va='top')
fig.text(.04,.045,'数值按原图两位小数转录；浅色且无数字的单元格为原图0.00。原始归一化方法待核。\n主题名称沿用第四章；主题5的0.18位于“区块链”列，正文相关表述需同步核对。',fontsize=9,color=GRAY)
save(fig,'fig4_5_主题关键词热力图')
# Figure 4-6: preserve visible topology; digitized heights are APPROXIMATE.
# Read from original axis 0=214px, .2=322px, merge x pixels:714/800/839/885/925/938/1004/1126.
merges=[('T5','T2',.93,'D1'),('T7','T4',1.09,'D2'),('D1','T9',1.16,'D3'),('D2','T6',1.25,'D4'),('D4','T3',1.32,'D5'),('T8','T1',1.34,'D6'),('D6','D5',1.46,'D7'),('D7','D3',1.69,'D8')]
writecsv('fig4_6_approximate_merges.csv',['左分支','右分支','原图近似合并高度','合并ID'],merges)
fig,ax=plt.subplots(figsize=(10.8,6.2));fig.subplots_adjust(left=.30,right=.97,bottom=.23,top=.86)
order=['T8','T1','T7','T4','T6','T3','T5','T2','T9'];pos={t:(0,8-i) for i,t in enumerate(order)}
for a,b,h,key in merges:
 xa,ya=pos[a];xb,yb=pos[b];c=TEAL if key=='D2' else ORANGE if key in ['D1','D3'] else '#647789'
 ax.plot([xa,h,h,xb],[ya,ya,yb,yb],color=c,lw=1.8);pos[key]=(h,(ya+yb)/2)
ax.axvline(1.2,color='#A1AAB4',ls='--',lw=1);ax.text(1.2,8.65,'参考截断 1.20',ha='center',fontsize=9,color=GRAY)
ax.set_yticks(range(9));ax.set_yticklabels([f'{t}  {TOPICS[int(t[1:])-1]}' for t in order[::-1]])
ax.set(xlim=(0,1.76),ylim=(-.6,8.8),xlabel='合并高度（按原图近似转录）');ax.grid(axis='x',color='#E8EDF1',lw=.6);ax.set_axisbelow(True);ax.tick_params(axis='y',length=0,pad=10)
ax.spines['left'].set_visible(False)
fig.text(.04,.96,'九类技术主题的层次关联结构',fontsize=16,weight='bold',va='top')
fig.text(.04,.065,'保留原图叶序与合并关系；高度为图示近似值，不是重新计算的聚类结果。\n精确距离、连接方法与合并矩阵尚待提供；虚线仅用于说明1.20处的分组。',fontsize=9,color=GRAY)
save(fig,'fig4_6_主题层次聚类_近似重绘')
# Supplemental: actual tabulated node trajectories (missing values remain missing).
metric_source=ROOT/'refs/agent-results-2026-10-15/ipc_stage_metrics.csv'
if not metric_source.exists():metric_source=DATA/'source_ipc_stage_metrics.csv'
rows=list(csv.DictReader(open(metric_source,encoding='utf-8-sig')))
select=['B25J11','G06F30','G06N3','B33Y70','G01B11','G01S17'];names=['机器人','设计计算','智能分析','增材制造','传感测量','定位感知']
selected=[r for r in rows if r['ipc'] in select]
writecsv('supp_selected_ipc_metrics.csv',list(rows[0]),[[r[k] for k in rows[0]] for r in selected])
fig,axs=plt.subplots(2,3,figsize=(11.5,6.5),sharex=True,sharey=True);fig.subplots_adjust(left=.085,right=.98,bottom=.22,top=.85,hspace=.35,wspace=.18)
for ax,ipc,name in zip(axs.flat,select,names):
 rr={int(r['stage']):r for r in selected if r['ipc']==ipc}
 for key,c,marker,label in [('degree',BLUE,'o','度中心度'),('betweenness',ORANGE,'s','中介中心度')]:
  yy=[float(rr[s][key]) if s in rr else np.nan for s in [1,2,3]]
  ax.plot([1,2,3],yy,color=c,marker=marker,lw=1.7,markersize=4,label=label)
 ax.set_title(ipc+'  '+name,loc='left',fontsize=11,pad=8);ax.set_xticks([1,2,3]);ax.set_xticklabels(['阶段1','阶段2','阶段3']);ax.set_ylim(-.008,.218);clean(ax)
 if 1 not in rr:ax.text(1.06,.012,'该表未列',color=GRAY,fontsize=8,ha='left')
for ax in axs[:,0]:ax.set_ylabel('报告中心度')
handles,labels=axs.flat[0].get_legend_handles_labels();fig.legend(handles,labels,loc='lower center',bbox_to_anchor=(.55,.09),ncol=2,frameon=False)
fig.text(.05,.96,'关键IPC节点的跨阶段影响力变化',fontsize=16,weight='bold',va='top')
fig.text(.05,.035,'补充图：数值来自既有节点指标表；未提供值留空，不填零。采用原阶段编号，实际年份对应仍待核。',fontsize=9,color=GRAY)
save(fig,'supp_关键IPC节点演化轨迹')
# Supplement: reported node count differences, kept separate from unknown edge topology.
writecsv('supp_network_sizes.csv',['阶段','指标全表节点数','原图最大连通分量标注'],[[1,75,43],[2,518,451],[3,979,919]])
fig,ax=plt.subplots(figsize=(7.5,4.9));fig.subplots_adjust(left=.11,right=.97,bottom=.25,top=.84)
xx=np.arange(3);ax.bar(xx-.18,[75,518,979],.32,color=BLUE,label='指标全表节点');ax.bar(xx+.18,[43,451,919],.32,color=TEAL,label='原图最大连通分量标注')
for offset,vals in [(-.18,[75,518,979]),(.18,[43,451,919])]:
 for i,v in enumerate(vals):ax.text(i+offset,v+15,str(v),ha='center',fontsize=10)
ax.set(xticks=xx,xticklabels=['阶段1','阶段2','阶段3'],ylabel='节点数（个）',ylim=(0,1120));clean(ax);ax.legend(loc='upper left',frameon=False,fontsize=9)
fig.text(.06,.96,'阶段网络规模及统计范围',fontsize=15,weight='bold',va='top')
fig.text(.06,.075,'补充图：两类数量使用不同统计范围，不能相互替代。\n节点数不包含边关系信息，不能据此重建原共现网络。',fontsize=9,color=GRAY)
save(fig,'supp_阶段网络规模比较')
# Thesis framework: conceptual method flow, not an empirical performance claim.
fig=plt.figure(figsize=(12,15));ax=fig.add_axes([0,0,1,1]);ax.set_xlim(0,12);ax.set_ylim(0,15);ax.axis('off')
def box(x,y,w,h,title,body='',fill='#F2F6F9',edge='#BCD0DD',ts=11,bs=9.5):
 p=FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0.01,rounding_size=0.08',linewidth=.9,edgecolor=edge,facecolor=fill);ax.add_patch(p)
 ax.text(x+w/2,y+h-.25,title,ha='center',va='center',fontsize=ts,weight='bold')
 if body:ax.text(x+w/2,y+(h-.4)/2,body,ha='center',va='center',fontsize=bs,linespacing=1.65)
 return (x+w/2,y,x+w/2,y+h)
def arrow(x1,y1,x2,y2,c='#6A7B89',style='-'):
 ax.add_patch(FancyArrowPatch((x1,y1),(x2,y2),arrowstyle='-|>',mutation_scale=11,lw=1.05,color=c,linestyle=style,connectionstyle='arc3,rad=0',shrinkA=3,shrinkB=3))
def band(y,h,label,caption,color):
 ax.add_patch(FancyBboxPatch((.36,y),11.28,h,boxstyle='round,pad=0.01,rounding_size=0.10',linewidth=.7,edgecolor='#D9E2E8',facecolor='#FFFFFF'))
 ax.text(.65,y+h-.30,label,fontsize=11,weight='bold',color=color,va='center');ax.text(11.35,y+h-.30,caption,ha='right',fontsize=9,color=GRAY,va='center')
ax.text(.55,14.60,'智能建造关键技术识别与发展研判',fontsize=22,weight='bold',va='center')
ax.text(.55,14.22,'全篇研究框架  |  时间背景 → 结构识别 → 语义解释 → 条件性发展路径',fontsize=11,color=GRAY)
band(12.35,1.45,'第1—2章  研究问题与理论依据','明确对象、问题与分析逻辑',BLUE)
box(.65,12.57,3.35,.70,'研究问题','发展阶段 · 关键技术 · 未来方向',ts=10.5,bs=9)
box(4.32,12.57,3.35,.70,'理论基础','生命周期 · 知识组合 · 社会网络',ts=10.5,bs=9)
box(7.99,12.57,3.35,.70,'研究边界','技术范围 · 时间范围 · 证据口径',ts=10.5,bs=9)
arrow(6,12.35,6,12.03)
band(9.95,2.05,'第3章  发展态势与生命周期阶段','输出：统一观察窗口与领域背景',BLUE)
box(.65,10.76,3.0,.65,'专利与文献样本','检索 · 清洗 · 统计口径',ts=10.5,bs=9)
box(4.08,10.76,3.68,.65,'总体态势与生命周期分析','数量 · 子领域 · 主体 · 拟合解释',ts=10.5,bs=9)
box(8.20,10.76,3.14,.65,'阶段结构比较','技术构成 · 创新布局',ts=10.5,bs=9)
arrow(3.65,11.08,4.08,11.08);arrow(7.76,11.08,8.20,11.08)
box(1.0,10.13,10,.40,'统一观察窗口：2010—2014  /  2015—2019  /  2020—2025',fill='#E9F1F6',ts=10)
arrow(6,9.95,6,9.63)
band(6.40,3.20,'第4章  关键技术识别与动态演化','输出：关键节点轨迹、九主题与演化证据',TEAL)
box(.65,7.94,3.06,1.02,'分阶段IPC共现网络','统一分类粒度\n共现关系与网络结构',fill='#EFF7F5',edge='#B6D9D2')
box(4.15,7.94,3.34,1.02,'节点影响力与跨期比较','度 · 中介 · 接近中心度\n关键技术与潜在方向',fill='#EFF7F5',edge='#B6D9D2')
box(7.94,7.94,3.4,1.02,'专利文本映射与BERTopic','题名、摘要的主题表示\n九类技术主题及工程内涵',fill='#EFF7F5',edge='#B6D9D2')
arrow(3.71,8.45,4.15,8.45);arrow(7.49,8.45,7.94,8.45)
box(.94,6.64,10.12,.88,'演化解释与研究结果汇总','节点演化规律  +  主题关联及协同解释  +  来源、时间与适用边界',fill='#E6F2EF',edge='#91C4B9',ts=11,bs=10)
arrow(2.2,7.94,2.2,7.52);arrow(5.82,7.94,5.82,7.52);arrow(9.64,7.94,9.64,7.52)
arrow(6,6.40,6,6.08);ax.text(6.15,6.23,'演化证据输入',fontsize=9,color=TEAL,va='center')
band(1.73,4.32,'第5章  证据约束下的多智能体发展研判','输出：发展命题、条件性路线与建议',ORANGE)
box(.65,4.86,10.69,.62,'证据组织与量化分析','来源审核与版本管理 · 年度活动估计 · 网络演化与多源证据融合',fill='#FBF5EC',edge='#E2C9A7',ts=11,bs=9)
arrow(1.82,4.86,1.82,4.62)
box(.65,3.55,2.35,1.05,'演化分析','证据摘要\n观察与缺口',fill='#FBF5EC',edge='#E2C9A7',ts=10.5)
box(3.35,3.55,2.35,1.05,'发展命题生成','对象 · 场景 · 时域\n证据与前置条件',fill='#FBF5EC',edge='#E2C9A7',ts=10.5)
box(6.05,4.13,2.35,.47,'反向审查',fill='#FBF5EC',edge='#E2C9A7',ts=10)
box(6.05,3.55,2.35,.47,'工程审查',fill='#FBF5EC',edge='#E2C9A7',ts=10)
box(8.98,3.55,2.35,1.05,'裁决','接受 / 修订\n降级 / 暂缓',fill='#FBF5EC',edge='#E2C9A7',ts=10.5)
arrow(3,4.075,3.35,4.075);arrow(5.7,4.075,6.05,4.365);arrow(5.7,4.075,6.05,3.785);arrow(8.4,4.365,8.98,4.075);arrow(8.4,3.785,8.98,4.075)
# Feedback loop from adjudication to generation, limited to local revision.
ax.plot([10.15,10.15,4.52],[3.55,3.23,3.23],color=ORANGE,lw=1,ls='--');arrow(4.52,3.23,4.52,3.55,c=ORANGE,style='--');ax.text(7.35,3.28,'局部修订与有限复审',ha='center',va='bottom',fontsize=8.5,color=ORANGE)
box(.65,2.61,10.69,.44,'LangGraph编排 + Harness执行约束：结构化输出 · 确定性校验 · 日志追溯 · 终止条件',fill='#F0F2F4',edge='#CBD3DB',ts=9.4)
box(.65,1.96,10.69,.43,'发展路径与评价：2027—2030 / 2031—2035 / 2036—2040  ·  证据一致性、局限与发展建议',fill='#FBF5EC',edge='#E2C9A7',ts=9.3)
arrow(6,2.61,6,2.39)
arrow(6,1.73,6,1.43)
box(.65,.78,10.69,.62,'第6章  结论与展望','回应研究问题 · 总结贡献 · 说明局限 · 提出后续研究方向',fill='#F0F4F7',edge='#B8C9D5',ts=11,bs=9.5)
ax.text(.65,.35,'实线：分析与信息传递；虚线：受限修订。框架表示研究组织，不代表所有评价环节已有实测结果。',fontsize=8.8,color=GRAY)
save(fig,'fig1_全篇研究框架流程图')
# Compact portrait version for insertion at approximately 16–17 cm width.
fig=plt.figure(figsize=(7.2,10.2));ax=fig.add_axes([0,0,1,1]);ax.set_xlim(0,7.2);ax.set_ylim(0,10.2);ax.axis('off')
ax.text(3.6,9.87,'智能建造关键技术识别与发展研判框架',ha='center',fontsize=14,weight='bold')
box(.35,8.65,6.5,.86,'第1—2章  研究问题与理论基础','技术范围与研究问题｜生命周期、知识组合与社会网络',ts=10.5,bs=9)
arrow(3.6,8.65,3.6,8.39)
box(.35,7.10,6.5,1.26,'第3章  发展态势与生命周期阶段分析','专利与文献 → 总体态势 → 生命周期解释与阶段比较\n观察窗口：2010—2014 / 2015—2019 / 2020—2025',ts=10.5,bs=9)
arrow(3.6,7.10,3.6,6.84)
box(.35,4.86,6.5,1.95,'第4章  关键技术识别与动态演化分析','分阶段IPC共现网络 → 节点影响力及跨期变化\n↓\n关键节点与专利文本映射 → BERTopic九主题\n↓\n演化规律、主题关联及来源边界 → 研究证据汇总',fill='#EFF7F5',edge='#9BCABD',ts=10.5,bs=9)
arrow(3.6,4.86,3.6,4.60)
box(.35,1.88,6.5,2.69,'第5章  证据约束下的多智能体发展研判','证据组织与量化分析 → 演化分析 → 发展命题生成\n↓\n独立双审查：反向审查 + 工程审查 → 裁决\n↓\n接受 / 局部修订与有限复审 / 降级 / 暂缓\n\nLangGraph + Harness：校验、日志、版本及终止条件\n发展路径、证据一致性评价与技术发展建议',fill='#FBF5EC',edge='#DEC49F',ts=10.5,bs=9)
arrow(3.6,1.88,3.6,1.62)
box(.35,.73,6.5,.86,'第6章  结论与展望','回应研究问题 → 总结贡献与局限 → 后续研究方向',ts=10.5,bs=9)
ax.text(.35,.32,'注：框架表示研究组织；未来路径为条件性判断，评价实测范围见正文。',fontsize=8,color=GRAY)
save(fig,'fig1_全篇研究框架_正文精简版')
(OUT/'build_manifest.json').write_text(json.dumps({'figures':outputs,'dpi':450,'formats':['png','svg','pdf'],'font':font,'matplotlib':matplotlib.__version__,'data_notes':{'frequency':'original visible count total 5916, manuscript 5926','heatmap':'rounded displayed values, not raw model matrix','dendrogram':'approximate digitization, original topology','network':'no edges inferred or invented','framework':'conceptual research organization'}},ensure_ascii=False,indent=2))
print(json.dumps(outputs,ensure_ascii=False))
