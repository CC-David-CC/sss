"""Plot only measured points from the checked public shared-root snapshot."""
from pathlib import Path
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

r=Path(__file__).resolve().parents[1]
v=json.loads((r/'validation/minicpm-native-learning-20261024/shared-learning-block-z.json').read_text())
arms=['adamw-full','muon-standard-full','muon-rms-decay-full','muon-fast-refine-full']
labels=['AdamW','Standard Muon','RMS / decay Muon','Fast-to-refine Muon']
colors=['#245fa4','#d27724','#278768','#9458a5']
plt.rcParams.update({'font.size':11,'axes.spines.top':False,'axes.spines.right':False,'svg.hashsalt':'sss-shared-learning'})
fig,axes=plt.subplots(1,2,figsize=(11,5.2),sharex=True)
for ax,key,title in zip(axes,['passed','finished'],['Correct answers / 864','Naturally finished responses / 864']):
    ax.scatter([0],[v['baseline'][key]],color='#6d7885',marker='D',label='Original',s=45)
    for arm,label,color in zip(arms,labels,colors):
        points=sorted([x for x in v['points'] if x['arm']==arm],key=lambda x:x['update'])
        ax.scatter([x['update'] for x in points],[x[key] for x in points],label=label,color=color,
            marker='x' if arm=='muon-fast-refine-full' else 'o',s=70 if arm=='muon-fast-refine-full' else 38,zorder=3)
        for left,right in zip(points,points[1:]):
            if right['update']==left['update']+1:ax.plot([left['update'],right['update']],[left[key],right[key]],color=color)
    ax.set_ylim(0,900);ax.set_yticks([0,216,432,648,864]);ax.set_xticks(range(7));ax.set_xlim(-.3,6.4)
    ax.set_title(title);ax.set_xlabel('Completed updates · 27 practice presentations each');ax.grid(alpha=.18)
axes[0].legend(loc='upper left',fontsize=9)
fig.suptitle('First completed observations under the shared-root A100 runtime',fontsize=14,y=.985)
fig.text(.5,.025,'Gaps are unmeasured, not interpolated. Early checkpoints are being backfilled.\nDifferent regimens and update counts; no optimizer ranking. Development data, not sealed acceptance.',ha='center',fontsize=9)
fig.tight_layout(rect=(0,.085,1,.95))
out=r/'docs/images'
for ext in ['svg','png']:fig.savefig(out/('cow-shared-learning.'+ext),dpi=165,metadata={'Creator':'S³ public aggregate report'})
p=out/'cow-shared-learning.svg';p.write_text('\n'.join(line.rstrip() for line in p.read_text().splitlines())+'\n')
