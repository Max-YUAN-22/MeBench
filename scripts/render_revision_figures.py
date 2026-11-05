import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap
import argparse
parser=argparse.ArgumentParser(description='Render supplementary figures S1 and S2.')
parser.add_argument('--audit',type=Path,default=Path('audit_output/independent_audit.json'))
parser.add_argument('--modules',type=Path,default=Path('family_analysis/claim_audit.json'))
parser.add_argument('--output',type=Path,default=Path('paper/manuscript/figs'))
args=parser.parse_args()
O=args.output;O.mkdir(parents=True,exist_ok=True);A=json.load(open(args.audit))
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.titlesize':11,'axes.labelsize':10,'xtick.labelsize':9,'ytick.labelsize':9,'pdf.fonttype':42,'ps.fonttype':42,'axes.linewidth':0.65})
rows=[r for r in A['summary'] if r['task']==2];names=['GPT','Claude','Gemini','GLM','Grok','Biomni*'];keys=['mechanism_correct','mediator_correct','causal_role_order_correct','intervention_outcome_link_correct','no_material_contradiction']
fig=plt.figure(figsize=(9.6,4.3),facecolor='white')
gs=fig.add_gridspec(1,2,left=.085,right=.985,bottom=.27,top=.78,wspace=.43,width_ratios=[1.06,1])
a,b=fig.add_subplot(gs[0]),fig.add_subplot(gs[1])
v=np.array([[100-r[k] for k in keys] for r in rows]);cm=LinearSegmentedColormap.from_list('fail',['#f7fafc','#b9d1df','#487a98','#163e59'])
im=a.imshow(v,cmap=cm,vmin=0,vmax=40,aspect='auto')
a.set_yticks(range(6),names);a.set_xticks(range(5),['Mechanism','Mediator','Role / order','Outcome link','Evidence'],rotation=32,ha='right',rotation_mode='anchor');a.tick_params(length=0,pad=6)
for sp in a.spines.values():sp.set_visible(False)
a.set_xticks(np.arange(-.5,5,1),minor=True);a.set_yticks(np.arange(-.5,6,1),minor=True);a.grid(which='minor',color='white',linewidth=1.2);a.tick_params(which='minor',length=0)
for i in range(6):
 for j in range(5):a.text(j,i,f'{v[i,j]:.1f}',ha='center',va='center',color='white' if v[i,j]>=23 else '#18364a',fontsize=9)
cax=fig.add_axes([.10,.085,.34,.022]);cb=fig.colorbar(im,cax=cax,orientation='horizontal',ticks=[0,10,20,30,40]);cb.outline.set_visible(False);cb.ax.tick_params(length=0,labelsize=8);cb.set_label('Criterion failure (%)',fontsize=9,labelpad=3)
x=np.arange(6);w=.24;colors=['#315c78','#70a7b4','#b8c6cc']
for off,k,label,color in zip([-w,0,w],['answer','chain','joint'],['Answer','Chain','Joint'],colors):b.bar(x+off,[r[k] for r in rows],w,label=label,color=color,edgecolor='white',linewidth=.4,zorder=3)
b.set_xticks(x,names,rotation=32,ha='right',rotation_mode='anchor');b.set_ylabel('Pass rate (%)',labelpad=4);b.set_ylim(0,105);b.set_yticks([0,25,50,75,100]);b.grid(axis='y',color='#dde4e9',linewidth=.65,zorder=0);b.tick_params(length=0,pad=5)
for sp in ['top','right','left']:b.spines[sp].set_visible(False)
b.spines['bottom'].set_color('#b9c4cb')
# The legend occupies a separate strip ABOVE the data axes.
leg=b.legend(loc='lower left',bbox_to_anchor=(-.025,1.025),ncol=3,frameon=False,fontsize=9,columnspacing=.85,handlelength=1.15,handletextpad=.35,borderaxespad=0)
fig.text(.04,.94,'A',fontweight='bold',fontsize=13);fig.text(.085,.94,'Where explanations fail',fontsize=11)
fig.text(.545,.94,'B',fontweight='bold',fontsize=13);fig.text(.59,.94,'Answer, explanation and joint pass',fontsize=11)
fig.canvas.draw();renderer=fig.canvas.get_renderer();assert not leg.get_window_extent(renderer).overlaps(b.get_window_extent(renderer)), 'Legend overlaps data axes'
fig.savefig(O/'diagnostic_landscape.pdf',bbox_inches='tight',pad_inches=.06);fig.savefig(O/'diagnostic_landscape.png',dpi=220,bbox_inches='tight',pad_inches=.06);plt.close(fig)
# The second figure shows descriptive within-module intervention contrasts.
M=json.load(open(args.modules))
fig,axs=plt.subplots(1,2,figsize=(8.7,3.2),sharex=True)
fig.subplots_adjust(left=.05,right=.985,bottom=.17,top=.68,wspace=.3)
for ax,groups,title in zip(axs,[['PPARA_activation','BHLHE40_depletion'],['TP63_TF_loss','FOXK1_loss']],['PPARA-BHLHE40','TP63-FOXK1']):
 y=np.arange(2)
 for d,key,col,lab in [(-.16,'direction_correct','#315c78','Correct direction'),(.16,'chain_pass','#70a7b4','Chain pass')]:
  vals=[100*M[g][key]/M[g]['n'] for g in groups];ax.barh(y+d,vals,.27,color=col,label=lab,zorder=3)
  for yy,val,g in zip(y+d,vals,groups):ax.text(max(val,0)+1.2,yy,f"{M[g][key]}/{M[g]['n']}",va='center',fontsize=8.5,color='#253e50')
 labels=['PPARA activation','BHLHE40 depletion'] if groups[0].startswith('PPARA') else ['TP63 depletion','FOXK1 depletion']
 ax.set_yticks(y,labels);ax.invert_yaxis();ax.set_xlim(0,125);ax.set_xticks([0,25,50,75,100]);ax.set_xlabel('Percentage of unit-run records');ax.set_title(title,loc='left',fontsize=11,pad=16);ax.grid(axis='x',color='#e2e8ed',linewidth=.7,zorder=0);ax.tick_params(length=0)
 for sp in ax.spines.values():sp.set_visible(False)
 ax.set_yticklabels(labels,fontsize=9)
# Room for left labels requires independent margin in each panel.
fig.subplots_adjust(left=.18,right=.94,wspace=.70)
handles,labels=axs[0].get_legend_handles_labels();fig.legend(handles,labels,loc='upper center',bbox_to_anchor=(.55,.98),ncol=2,frameon=False,fontsize=10)
fig.savefig(O/'intervention_contrasts.pdf',bbox_inches='tight',pad_inches=.08);fig.savefig(O/'intervention_contrasts.png',dpi=220,bbox_inches='tight',pad_inches=.08)
print('Redrawn vector figures. S1 panel B legend verified outside data axes.')
