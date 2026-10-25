"""Rebuild report figures from public aggregates (optional matplotlib dependency)."""
from pathlib import Path
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

repo=Path(__file__).resolve().parents[1]
data=repo/'validation/minicpm-native-learning-20261024'
out=repo/'docs/images';out.mkdir(exist_ok=True)
read=lambda name:json.loads((data/name).read_text())
original=read('cow-first-block.json');trained=read('cow-trained-first-block.json')
plt.rcParams.update({'font.size':11,'axes.spines.top':False,'axes.spines.right':False,'svg.hashsalt':'sss-cow-first-block'})
fig,axes=plt.subplots(1,2,figsize=(11,4.8))
for ax,label,values,ratio in [
    (axes[0],'Original F32',[original['fresh']['execution_wall_seconds']/60,original['cow']['execution_wall_seconds']/60],original['evaluation_wall_speedup']),
    (axes[1],'Trained F32 · AdamW update 1',[trained['fresh_wall_seconds']/60,trained['cow_wall_seconds']/60],trained['observed_wall_ratio'])]:
    bars=ax.bar(['Fresh reference','COW'],values,color=['#8c98a5','#158578'],width=.58)
    ax.bar_label(bars,labels=[f'{v:.1f} min' for v in values],padding=5)
    ax.set_ylim(0,max(values)*1.24);ax.set_ylabel('Evaluation wall time (minutes)')
    ax.set_title(f'{label}\nObserved {ratio:.1f}× faster',pad=12)
    ax.grid(axis='y',alpha=.18);ax.set_axisbelow(True)
fig.suptitle('864 questions · identical generated tokens and outcomes',fontsize=15,y=.99)
fig.text(.5,.025,'Shared A100s; different cards and uncontrolled other loads. Evaluation timing, not whole-loop speedup.',ha='center',fontsize=9)
fig.tight_layout(rect=(0,.07,1,.95))
for ext in ['svg','png']:fig.savefig(out/('cow-evaluation-timings.'+ext),dpi=170,metadata={'Creator':'S³ public aggregate report'})
plt.close(fig)

points=read('cow-pre-migration-learning-points.json')['points']
existing=read('cpu-execution-analysis.json')['assessments']
arms=['adamw-full','muon-standard-full','muon-rms-decay-full','muon-fast-refine-full']
labels=['AdamW','Standard Muon','RMS / decay Muon','Fast-to-refine Muon']
colors=['#245fa4','#d27724','#278768','#9458a5']
fig,axes=plt.subplots(1,2,figsize=(11,5.1),sharex=True)
for arm,label,color in zip(arms,labels,colors):
    rows={p['update']:p for p in points if p['arm']==arm}
    first=next(p for p in existing if p['assessment']==arm+'-u001')
    rows[1]=first;rows[0]={'passed':original['fresh']['passed'],'finished':original['fresh']['finished']}
    steps=sorted(rows)
    for ax,key in zip(axes,['passed','finished']):
        ax.plot(steps,[rows[n][key] for n in steps],marker='o',color=color,label=label,
                linestyle='--' if arm=='muon-fast-refine-full' else '-')
for ax,title in zip(axes,['Correct answers / 864','Naturally finished responses / 864']):
    ax.set_title(title);ax.set_xlabel('Completed updates · 27 practice examples per update')
    ax.set_ylim(0,900);ax.set_yticks([0,216,432,648,864]);ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    ax.grid(alpha=.18)
axes[0].legend(loc='upper left',fontsize=9)
fig.suptitle('Early learning points · original frozen A100 evaluation runtime',fontsize=15,y=.99)
fig.text(.5,.025,'Incomplete curves; repeatedly observed development set. Different regimens, not an optimizer ranking.\nRMS/decay and fast-to-refine overlap here. The full 68-update study is still running.',ha='center',fontsize=9)
fig.tight_layout(rect=(0,.09,1,.95))
for ext in ['svg','png']:fig.savefig(out/('cow-early-learning.'+ext),dpi=170,metadata={'Creator':'S³ public aggregate report'})
plt.close(fig)
for name in ['cow-evaluation-timings.svg','cow-early-learning.svg']:
    p=out/name;p.write_text('\n'.join(line.rstrip() for line in p.read_text().splitlines())+'\n')
