"""Two continuing arms; pending updates have no invented score."""
from pathlib import Path
import json,hashlib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parent
arms=[(32,'adamw','llm-60: rank-32 AdamW','#1565c0',None),
      (4096,'muon','A100: rank-4096 factorwise Muon','#138d75',None)]
fig,axes=plt.subplots(2,1,figsize=(11,7.5),sharex=True)
sources={};latest={};evaluation_ids=set()
for rank,optimizer,label,color,pending in arms:
    points=[]
    for p in R.glob('*update*.json'):
        row=json.loads(p.read_bytes())
        if row.get('rank')!=rank or row.get('optimizer')!=optimizer:continue
        assert row['status']=='COMPLETE' and row['cases']==864
        points.append(row);sources[p.name]=hashlib.sha256(p.read_bytes()).hexdigest()
    points.sort(key=lambda p:p['source_training_updates'])
    assert len({p['source_training_updates'] for p in points})==len(points)
    assert len({p['runtime_id'] for p in points})==1
    assert all(1<=p['source_training_updates']<=68 for p in points)
    evaluation_ids.update(p['evaluation_id'] for p in points)
    latest[f'rank{rank}_{optimizer}']=dict(update=points[-1]['source_training_updates'],correct=points[-1]['passed'],finished=points[-1]['finished'])
    for ax,key in zip(axes,['passed','finished']):
        ax.plot([p['source_training_updates'] for p in points],[p[key] for p in points],'-o',color=color,label=label,linewidth=2.4)
        last=points[-1];ax.annotate(str(last[key]),(last['source_training_updates'],last[key]),xytext=(8,6),textcoords='offset points',color=color,weight='bold')
    if pending is not None:axes[0].axvline(pending,color=color,linestyle=':',alpha=.6)
assert len(evaluation_ids)==1
for y,(name,color) in zip([.85,.66],[('rank32_adamw','#1565c0'),('rank4096_muon','#138d75')]):
    v=latest[name]
    axes[0].text(.58,y,f"Update {v['update']} scored: {v['correct']}/864",color=color,fontsize=10,transform=axes[0].transAxes)
axes[0].set_ylabel('Correct answers / 864');axes[1].set_ylabel('Naturally finished / 864')
for ax in axes:
    ax.set_ylim(0,900);ax.set_xlim(.7,max(10,max(v['update'] for v in latest.values()))+.5);ax.grid(alpha=.2)
axes[0].legend(loc='upper left');axes[1].set_xlabel('Completed training updates (27 practice presentations per update)')
maximum=max(10,max(v['update'] for v in latest.values()))
axes[1].set_xticks(range(1,maximum+1,max(1,maximum//10)))
fig.suptitle('MiniCPM: the two continuing training arms',fontsize=16)
fig.text(.10,.025,'Only marked points were scored; connecting lines do not supply missing measurements.\nSame 864 questions; learning rates, parameterization and recorded hardware runtimes differ.\nSnapshot: 2026-10-27. Both arms are authorized to continue to update 68.',fontsize=9)
fig.tight_layout(rect=(0,.11,1,.94));fig.savefig(R/'two-continuations.png',dpi=160);plt.close(fig)
(R/'two-continuations-manifest.json').write_text(json.dumps(dict(schema=1,status='MEASURED_PROGRESS',source_sha256=sources,plot_source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),latest_measured=latest,evaluation_id=next(iter(evaluation_ids))),indent=2)+'\n')
