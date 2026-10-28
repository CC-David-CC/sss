"""Plot paired adjacent-checkpoint answer turnover, from existing public aggregates."""
import json
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
root=Path(__file__).resolve().parent
report=json.loads((root/'paired-update-transitions.json').read_text(encoding='utf8'))
labels={'adamw-full':'Full AdamW','muon-standard-full':'Full standard Muon','muon-rms-decay-full':'Full RMS/decay Muon','muon-fast-refine-full':'Full fast/refine Muon',**{'adamw-lora-r'+str(n):'AdamW LoRA rank '+str(n)for n in [1,2,3,4,8,16]}}
fig,axes=plt.subplots(5,2,figsize=(14,15),sharex=True)
fig.subplots_adjust(top=.90,bottom=.10,left=.075,right=.985,hspace=.45,wspace=.18)
for axis,(arm,name)in zip(axes.flat,labels.items()):
    rows=[r for r in report['transitions']if r['arm']==arm]
    rows.sort(key=lambda r:r['update']);x=[r['update']for r in rows]
    axis.bar(x,[r['answer_gains']for r in rows],color='#18865b',width=.85)
    axis.bar(x,[-r['answer_losses']for r in rows],color='#c23d47',width=.85)
    axis.plot(x,[r['answer_gains']-r['answer_losses']for r in rows],color='#202020',lw=1.1)
    axis.axhline(0,color='#777777',lw=.7);axis.grid(axis='y',alpha=.2)
    axis.set_title(f'{name} | {len(rows)} paired transitions',fontsize=11)
    axis.spines[['top','right']].set_visible(False);axis.set_xlim(0,70)
    axis.set_xticks([0,10,20,30,40,50,60,68]);axis.tick_params(labelsize=9)
for a in axes[-1,:]:a.set_xlabel('New checkpoint update (compared with preceding update)')
for a in axes[:,0]:a.set_ylabel('Answers gained / lost')
fig.suptitle('A flat total score can hide substantial answer turnover',fontsize=18,fontweight='bold',y=.973)
fig.text(.5,.936,f"MiniCPM5-2B | 864 fixed questions | {len(report['transitions'])} observed adjacent transitions | fixed training horizon complete",ha='center',fontsize=11)
fig.legend(handles=[Patch(color='#18865b',label='Newly correct'),Patch(color='#c23d47',label='Previously correct, now wrong'),Line2D([0],[0],color='#202020',label='Net score change')],loc='lower center',bbox_to_anchor=(.5,.047),ncol=3,frameon=False)
fig.text(.5,.018,'Same frozen cases and runtime within each pair. Missing early checkpoints are not inferred.\nFull updates: FP32; LoRA: F16 base + attached adapter. Panel y scales differ. No optimizer ranking or release acceptance.',ha='center',va='bottom',fontsize=10,color='#555555')
fig.savefig(root/'paired-update-turnover.png',dpi=160,facecolor='white')
plt.close(fig)
