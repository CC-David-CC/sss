"""Plot completed final-rank precision measurements; gaps remain unmeasured."""
from pathlib import Path
import json
import numpy as np
import matplotlib.pyplot as plt
from plot_original_reference import add_original_curve

root=Path(__file__).resolve().parent
report=json.loads((root/'final-rank-precision.json').read_text(encoding='utf8'))
formats=['F32','F16','Q8_0','Q5_K_M','Q4_K_M','Q3_K_M','Q2_K','Q1_0']
fig,axes=plt.subplots(2,1,figsize=(13,9),sharex=True)
fig.subplots_adjust(top=.77,bottom=.15,left=.09,right=.97,hspace=.18)
for axis,field,title in [(axes[0],'correct','Correct answers / 864'),(axes[1],'finished','Naturally finished / 864')]:
    for rank,color,marker in [(3,'#7b4ab5','s'),(4,'#0086a8','^'),(16,'#2457a6','o')]:
        rows={r['format']:r for r in report['rows']if r['rank']==rank}
        values=[rows[f][field]if rows[f]['status']=='COMPLETE'else np.nan for f in formats]
        axis.plot(range(len(formats)),values,color=color,marker=marker,lw=2,label=f'LoRA rank {rank}, update 68')
    add_original_curve(axis,root,formats,'passed'if field=='correct'else'finished',horizontal=True)
    axis.set_ylabel(title);axis.set_ylim(-15,915);axis.set_yticks([0,216,432,648,864])
    axis.grid(axis='y',alpha=.25);axis.spines[['top','right']].set_visible(False)
axes[1].set_xticks(range(len(formats)),formats)
axes[1].set_xlabel('GGUF format; each quant converted directly from its own trained F32 master')
fig.suptitle('MiniCPM5-2B: how much learning survives quantization?',y=.97,fontsize=18,fontweight='bold')
fig.text(.5,.92,'Final 68-update checkpoints | 1,836 training presentations | 864 frozen questions per measured point',ha='center',fontsize=11)
fig.text(.5,.887,'Saved receipts through '+report['captured_utc'][:16].replace('T',' ')+' UTC',ha='center',fontsize=10)
handles,labels=axes[0].get_legend_handles_labels()
fig.legend(handles,labels,loc='upper center',bbox_to_anchor=(.5,.865),ncol=2,frameon=False,fontsize=10)
fig.text(.5,.055,'Rank 3 Q5 remains a gap until its full panel settles. Original F32: verified existing run.\n'
    'Orange = original per quant; gray = original F16 level. Original runtime differs; historical comparison only.\n'
    'Shared A100 loads. These three ranks are a subset of the unfinished study; no release acceptance.',
    ha='center',fontsize=9,color='#555555')
fig.savefig(root/'final-rank-precision.png',dpi=160,facecolor='white')
plt.close(fig)
