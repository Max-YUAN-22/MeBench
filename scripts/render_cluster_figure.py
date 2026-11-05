from pathlib import Path
import argparse,json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
parser=argparse.ArgumentParser();parser.add_argument('--analysis',type=Path,default=Path('robustness_output/cluster_bootstrap_analysis.json'));parser.add_argument('--output',type=Path,default=Path('paper/manuscript/figs'));a=parser.parse_args();a.output.mkdir(parents=True,exist_ok=True)
C=json.load(open(a.analysis));names={'GPT-6-Astra':'GPT','Claude-Sonnet-5.5':'Claude','Gemini-3.8-Flash':'Gemini','GLM-5.3-Flash':'GLM','Grok-4.6':'Grok','Biomni':'Biomni'}
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'pdf.fonttype':42,'axes.spines.top':False,'axes.spines.right':False})
fig,ax=plt.subplots(figsize=(6.15,2.9));fig.subplots_adjust(left=.14,right=.97,bottom=.2,top=.79)
for k,offset,col,label in [('pair',-.12,'#236693','Pair clusters (168)'),('study_component',.12,'#b66c28','Source components (31)')]:
 for i,s in enumerate(names):
  r=next(r for r in C['ci'] if r['system']==s and r['metric']=='balanced_joint' and r['cluster']==k)
  ax.errorbar(r['estimate'],5-i+offset,xerr=[[r['estimate']-r['lo']],[r['hi']-r['estimate']]],fmt='o',ms=3.5,capsize=2,color=col,lw=1.3,label=label if i==0 else None)
ax.set(yticks=range(6),yticklabels=list(names.values())[::-1],xlim=(20,100),ylim=(-.5,5.5),xlabel='Task 2 joint balanced accuracy (%)');ax.grid(axis='x',alpha=.2);ax.set_axisbelow(True)
legend=fig.legend(loc='upper center',bbox_to_anchor=(.54,.99),ncol=2,frameon=False)
fig.canvas.draw();assert not legend.get_window_extent().overlaps(ax.get_window_extent()),'Legend overlaps data area'
fig.savefig(a.output/'cluster_intervals.pdf');fig.savefig(a.output/'cluster_intervals.png',dpi=240)
