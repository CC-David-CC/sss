"""Plot measured learning and forgetting; leave every unmeasured gap visible."""
from pathlib import Path
import argparse,json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

r=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--data',type=Path,default=r/'validation/minicpm-native-learning-20261024/shared-learning-block-ax.json')
parser.add_argument('--lora-data',type=Path)
a=parser.parse_args();v=json.loads(a.data.read_text())
assert v['status']=='PARTIAL_CURVE' and v['cases']==864 and v['optimizer_ranking_established'] is False
arms=['adamw-full','muon-standard-full','muon-rms-decay-full','muon-fast-refine-full']
labels=['AdamW','Standard Muon','RMS / decay Muon','Fast-to-refine Muon']
colors=['#245fa4','#d27724','#278768','#9458a5'];markers=['^','o','s','x']
if a.lora_data is not None:
    lora=json.loads(a.lora_data.read_text());bridge=lora['trained_runtime_bridge']
    if (lora['evaluation_id']!=v['evaluation_id'] or lora['cases']!=v['cases']
            or any(lora['baseline'][key]!=v['baseline'][key] for key in ('passed','finished'))
            or bridge['old_runtime_id']!=v['runtime_id'] or bridge['new_runtime_id']!=lora['runtime_id']
            or bridge['different_sampled_sequences'] or bridge['answer_gains'] or bridge['answer_losses']
            or bridge['completion_differences']
            or not any(p['model_sha256']==bridge['model_sha256'] and p['evaluation_evidence_sha256']==bridge['old_result_sha256'] for p in v['points'])
            or not all(lora['baseline_controls']['native_artifacts'].values())
            or any(c['different_sampled_sequences'] or c['answer_gains'] or c['answer_losses'] or c['completion_differences'] for c in lora['baseline_controls']['controls'])):
        raise ValueError('Matching cases, observed original/trained runtime bridges and identical native artifacts required')
    v['points'] += [dict(p,arm='adamw-lora-attached') for p in lora['points']]
    arms.append('adamw-lora-attached');labels.append('AdamW LoRA (attached)');colors.append('#8a4c2e');markers.append('P')
last=max(p['update'] for p in v['points']);spacing=max(1,(last+9)//10)
panels=[('passed','Correct answers / 864',864),('finished','Naturally finished / 864',864),
        ('answer_gains',f"Previously wrong answers gained / {864-v['baseline']['passed']}",864-v['baseline']['passed']),
        ('answer_losses',f"Original successes lost / {v['baseline']['passed']}",v['baseline']['passed'])]
plt.rcParams.update({'font.size':11,'axes.spines.top':False,'axes.spines.right':False,'svg.hashsalt':'sss-shared-learning'})
fig,axes=plt.subplots(2,2,figsize=(12,8),sharex=True)
for ax,(key,title,maximum) in zip(axes.flat,panels):
    initial=v['baseline'].get(key,0)
    ax.scatter([0],[initial],color='#6d7885',marker='D',label='Original',s=45,zorder=4)
    for arm,label,color,marker in zip(arms,labels,colors,markers):
        points=sorted([x for x in v['points'] if x['arm']==arm],key=lambda x:x['update'])
        ax.scatter([x['update'] for x in points],[x[key] for x in points],label=label,color=color,marker=marker,
            s=70 if marker=='x' else 42,zorder=3,alpha=.95)
        for left,right in zip(points,points[1:]):
            if right['update']==left['update']+1:
                ax.plot([left['update'],right['update']],[left[key],right[key]],color=color,linewidth=1,alpha=.7)
    ax.set_ylim(-maximum*.025,maximum*1.06)
    if maximum==864:ax.set_yticks([0,216,432,648,864])
    elif key=='answer_losses':ax.set_yticks([0,10,20,30,40,50,59])
    ax.set_xticks(range(0,last+1,spacing));ax.set_xlim(-.3,last+.5)
    ax.set_title(title);ax.grid(alpha=.18)
for ax in axes[1]:ax.set_xlabel('Completed updates · 27 practice presentations each')
handles,legend_labels=axes[0,0].get_legend_handles_labels()
fig.legend(handles,legend_labels,loc='upper center',bbox_to_anchor=(.5,.945),ncol=len(arms)+1,fontsize=9,frameon=False)
fig.suptitle('Native MiniCPM: measured learning and forgetting',fontsize=16,y=.985)
note='Only complete 864-case development assessments. Gaps are unmeasured; different predeclared settings, no optimizer ranking.\n'
note+=('Attached LoRA has its own runtime identity; original + trained execution bridges matched. Merged deployment remains unqualified.'
       if a.lora_data is not None else 'Direct LoRA is a separate runtime series. Sealed acceptance remains unfinished.')
fig.text(.5,.018,note,ha='center',fontsize=9)
fig.tight_layout(rect=(0,.065,1,.90))
out=r/'docs/images'
for ext in ['svg','png']:fig.savefig(out/('cow-shared-learning.'+ext),dpi=165,metadata={'Creator':'S³ public aggregate report'})
p=out/'cow-shared-learning.svg';p.write_text('\n'.join(line.rstrip() for line in p.read_text().splitlines())+'\n')
