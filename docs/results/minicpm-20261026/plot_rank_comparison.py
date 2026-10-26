"""Plot standard full optimizers and six AdamW LoRA ranks from saved CSV scores."""
import csv
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from plot_original_reference import original_scores

root=Path(__file__).resolve().parent
with (root/'intermediate-training-curves.csv').open(newline='',encoding='utf8') as f:
    rows=list(csv.DictReader(f))
labels={'adamw-full':'Full AdamW','muon-standard-full':'Full standard Muon',
    **{'adamw-lora-r'+str(n):'AdamW LoRA rank '+str(n) for n in (1,2,3,4,8,16)}}
groups={arm:sorted([r for r in rows if r['arm']==arm],key=lambda r:int(r['update'])) for arm in labels}
asof=max(datetime.fromisoformat(r['scored_at_utc'])for arm in groups for r in groups[arm] if r['scored_at_utc'])
fig,axes=plt.subplots(2,1,figsize=(13,9),sharex=True)
fig.subplots_adjust(left=.09,right=.98,top=.86,bottom=.22,hspace=.16)
colors=['#111111','#7c3aed','#e66101','#d95f9d','#1b9e77','#0088bb','#b8860b','#355cbd']
markers=['o','s','^','D','v','P','X','*']
original=original_scores(root)['F16']
for axis,metric,title,baseline in [(axes[0],'correct_out_of_864','Correct answers / 864',int(original['passed'])),
        (axes[1],'natural_finishes_out_of_864','Naturally finished / 864',int(original['finished']))]:
    axis.axhline(baseline,color='#d06b1f',ls='--',lw=1.8,label=f'Original F16: {baseline}/864')
    axis.axvline(68,color='#888888',ls='--',lw=1)
    for i,(arm,label) in enumerate(labels.items()):
        points=groups[arm];last=points[-1]
        axis.plot([int(r['update'])for r in points],[int(r[metric])for r in points],
            label=f"{label} ({last['update']}: {last[metric]})",color=colors[i],marker=markers[i],
            markevery=max(1,len(points)//12),ms=4,lw=2.2 if i<2 else 1.7)
    axis.set_ylabel(title);axis.grid(axis='y',alpha=.28)
    axis.spines[['top','right']].set_visible(False)
axes[0].set_ylim(0,864);axes[0].set_yticks(range(0,865,144))
axes[1].set_ylim(380,880);axes[1].set_yticks([415,500,600,700,800,864])
axes[1].set_xlim(0,70);axes[1].set_xticks([0,10,20,30,40,50,60,68])
axes[1].set_xlabel('Training updates (27 example presentations per update)')
fig.suptitle('MiniCPM5-2B: full updates versus AdamW LoRA ranks',fontsize=16,fontweight='bold',y=.965)
fig.text(.5,.915,f"864 frozen questions per checkpoint | saved results through {asof:%Y-%m-%d %H:%M UTC}",ha='center',fontsize=10)
handles,names=axes[0].get_legend_handles_labels()
fig.legend(handles,names,loc='lower center',bbox_to_anchor=(.5,.065),ncol=3,frameon=False,fontsize=9)
fig.text(.5,.022,'Legend: (latest update: correct answers). Full AdamW and LoRA ranks 1, 3, 4 and 16 have completed update 68.\n'
    'Full updates: FP32; LoRA: F16 base + adapter. Recorded execution paths differ. Shared A100; interim results.',
    ha='center',fontsize=8.5,color='#555555')
fig.savefig(root/'rank-comparison.png',dpi=220,facecolor='white')
print('Rendered rank-comparison.png')
