"""Plot an exact saved-matrix geometry block alongside its matched-update scores."""
from pathlib import Path
import argparse, json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

root=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--data',type=Path,default=root/'validation/minicpm-native-learning-20261024/optimizer-geometry-au.json')
parser.add_argument('--output-prefix',type=Path,default=root/'docs/images/optimizer-geometry-update8')
args=parser.parse_args();data=json.loads(args.data.read_text())
assert data['status']=='COMPLETE' and data['update']==8 and len(data['results'])==45
arms=['adamw-full','muon-standard-full','muon-rms-decay-full','muon-fast-refine-full']
labels=['AdamW','Standard Muon','RMS / decay Muon','Fast-to-refine Muon']
colors=['#245fa4','#d27724','#278768','#9458a5'];markers=['^','o','s','x']
names=data['matrix_names'];assert len(names)==9 and len(set(names))==9
base={row['matrix_name']:row for row in data['results'] if row['arm']=='original'}
scores={row['arm']:row for row in data['behavior']}
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'svg.hashsalt':'sss-optimizer-geometry'})
fig,axes=plt.subplots(2,2,figsize=(12,8.5))
for index,(arm,label,color,marker) in enumerate(zip(arms,labels,colors,markers)):
    rows={row['matrix_name']:row for row in data['results'] if row['arm']==arm}
    assert rows.keys()==base.keys() and all(row['model_sha256']==scores[arm]['model_sha256'] for row in rows.values())
    x=[i+(index-1.5)*.09 for i in range(len(names))]
    values=[rows[name] for name in names]
    axes[0,0].scatter(x,[row['weights']['entropy_effective_rank']-base[row['matrix_name']]['weights']['entropy_effective_rank'] for row in values],label=label,color=color,marker=marker,s=46)
    axes[0,1].scatter(x,[row['change_from_base']['entropy_effective_rank'] for row in values],color=color,marker=marker,s=46)
    axes[1,0].scatter(x,[row['change_from_base']['frobenius_norm']/base[row['matrix_name']]['weights']['frobenius_norm'] for row in values],color=color,marker=marker,s=46)
    axes[1,1].bar(index,scores[arm]['passed'],color=color,width=.63)
    axes[1,1].text(index,scores[arm]['passed']+12,str(scores[arm]['passed']),ha='center')
axes[0,0].axhline(0,color='#777777',linewidth=.8)
axes[0,0].set_title('Weight entropy-rank change from initial values')
axes[0,1].set_title('Entropy rank of accumulated weight change')
axes[0,1].set_ylim(0,2048);axes[0,1].set_yticks([0,512,1024,1536,2048])
axes[1,0].set_title('Relative accumulated change: ||W8 − W0||F / ||W0||F')
axes[1,0].set_yscale('log')
axes[1,1].set_title('Correct development answers / 864 at update 8')
axes[1,1].set_ylim(0,864);axes[1,1].set_yticks([0,216,432,648,864])
axes[1,1].axhline(59,color='#777777',linewidth=1,linestyle='--')
axes[1,1].text(3.45,72,'Original: 59',ha='right',color='#555555',fontsize=9)
axes[1,1].set_xticks(range(4),['AdamW','Muon','RMS / decay','Fast / refine'])
ticks=[name.split('.')[1]+'\n'+{'attn_q':'Q','attn_output':'O','ffn_down':'FFN↓'}[name.split('.')[2]] for name in names]
for ax in [axes[0,0],axes[0,1],axes[1,0]]:
    ax.set_xticks(range(9),ticks);ax.set_xlabel('Layer and projection');ax.grid(alpha=.18)
axes[1,1].grid(axis='y',alpha=.18);axes[1,1].set_axisbelow(True)
handles,legend=axes[0,0].get_legend_handles_labels()
fig.legend(handles,legend,loc='upper center',bbox_to_anchor=(.5,.947),ncol=4,frameon=False)
fig.suptitle('Native MiniCPM: geometry after eight updates',fontsize=16,y=.985)
fig.text(.5,.022,'216 practice presentations per arm · Nine selected complete hidden matrices · Exact float64 SVD of saved F32 values\nAccumulated change is not a single update. Activation/feature rank and per-step orthogonality were not measured.',ha='center',fontsize=9)
fig.tight_layout(rect=(0,.075,1,.90))
args.output_prefix.parent.mkdir(parents=True,exist_ok=True)
for extension in ['png','svg']:
    fig.savefig(args.output_prefix.with_suffix('.'+extension),dpi=165,metadata={'Creator':'S³ exact saved-matrix report'})
p=args.output_prefix.with_suffix('.svg');p.write_text('\n'.join(line.rstrip() for line in p.read_text().splitlines())+'\n')
