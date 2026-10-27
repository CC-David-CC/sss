"""Plot completed saved precision measurements, never interpolate missing points."""
from pathlib import Path
import csv,json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

root=Path(__file__).resolve().parent
record=json.loads((root/'final-checkpoint-precision.json').read_bytes())
with(root/'original-quantization.csv').open(newline='',encoding='utf8')as f:
    original={row['format']:row for row in csv.DictReader(f)}
formats=['F32','F16','Q8_0','Q5_K_M','Q4_K_M','Q3_K_M','Q2_K','Q1_0']
ticks=['F32','F16','Q8','Q5','Q4','Q3','Q2','Q1']
lookup={(row['arm'],row['format']):row for row in record['rows']}
fig,axes=plt.subplots(2,2,figsize=(15,10),sharex=True)
plt.rcParams.update({'font.size':10})
for col,arms in enumerate([['adamw-full','muon-standard-full'],['adamw-lora-r'+str(rank)for rank in [1,2,3,4,8,16]]]):
    for row,metric in enumerate(['correct','finished']):
        ax=axes[row,col]
        for i,arm in enumerate(arms):
            values=[lookup[(arm,fmt)].get(metric,np.nan)for fmt in formats]
            measured=sum(np.isfinite(values))
            label=('Full AdamW'if arm=='adamw-full'else'Standard Muon'if arm=='muon-standard-full'else'LoRA rank '+arm.split('-r')[-1])
            if measured==0:label+=' (sweep pending)'
            ax.plot(range(8),values,marker=['o','s','^','D','v','P'][i],linewidth=2,
                label=label,color=plt.get_cmap('tab10')(i),markersize=5)
        key='passed'if metric=='correct'else'finished'
        values=[int(original[fmt][key])if fmt in original else np.nan for fmt in formats]
        ax.plot(range(8),values,'k--',marker='x',linewidth=1.6,label='Original at each format (prior runtime)')
        base=59 if metric=='correct' else 415
        ax.axhline(base,color='#888888',linewidth=1,linestyle=':',label='Original F16 reference (59 correct / 415 finished)')
        ax.set_ylim(-20,900 if row else 550);ax.set_xlim(-.2,7.2)
        ax.set_xticks(range(8),ticks)
        ax.set_ylabel(('Correct answers'if row==0 else'Naturally finished responses')+' / 864')
        ax.grid(alpha=.2);ax.spines[['top','right']].set_visible(False)
        if row==1:ax.set_xlabel('Each precision converted directly from that arm’s own F32 master')
axes[0,0].set_title('Full-weight AdamW and standard Muon | all formats complete',fontweight='bold')
axes[0,1].set_title('Six AdamW LoRA ranks | all formats complete',fontweight='bold')
fig.suptitle('MiniCPM5-2B: which trained gains survive quantization?',fontsize=18,fontweight='bold',y=.99)
fig.text(.5,.945,'68 updates · 1,836 ordered practice presentations · 864 fixed questions · F32 + seven inference formats',ha='center',fontsize=11)
fig.text(.5,.018,'Snapshot '+record['captured_utc'][:19].replace('T',' ')+' UTC. Pending is a gap, never zero. Original F32 recovered from existing receipts. Shared A100 load; no isolated speed claim.',ha='center',fontsize=9)
legend={}
for ax in axes[0,:]:
    handles,labels=ax.get_legend_handles_labels()
    legend.update(zip(labels,handles))
fig.legend(legend.values(),legend.keys(),loc='lower center',bbox_to_anchor=(.5,.037),ncol=5,fontsize=9,frameon=False)
fig.tight_layout(rect=(0,.115,1,.925))
fig.savefig(root/'final-checkpoint-precision.png',dpi=150,facecolor='white')
plt.close(fig)
