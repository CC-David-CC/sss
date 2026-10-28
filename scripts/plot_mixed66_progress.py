"""Render the measured mixed-curriculum development and diagnostic summary."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / 'docs/results'
foundation = json.loads((RESULTS / 'mixed66-development-summary-20261028.json').read_text(encoding='utf-8'))
admin = json.loads((RESULTS / 'mixed66-admin-summary-20261028.json').read_text(encoding='utf-8'))
names = ['Original\nMiniCPM5-2B', 'Remix 2\nparent', 'Candidate\n17 updates']
colors = ['#8b9bae', '#5296d8', '#43bb93']
keys = ['original', 'parent', 'candidate']
assert foundation['cases'] == 396 and admin['cases'] == 11
assert foundation['candidate']['sha256'] == admin['candidate_sha256']
plt.rcParams.update({'font.family':'DejaVu Sans', 'font.size':11,
                     'axes.spines.top':False, 'axes.spines.right':False,
                     'axes.labelcolor':'#243348', 'text.color':'#17263a',
                     'xtick.color':'#33465d', 'ytick.color':'#33465d'})
fig, axes = plt.subplots(1, 3, figsize=(15, 5.9), gridspec_kw={'width_ratios':[1.15,1,1]})
fig.patch.set_facecolor('#f6f8fb')
for ax in axes:
    ax.set_facecolor('#f6f8fb')
    ax.set_axisbelow(True)
    ax.grid(axis='y', color='#dbe3ec', linewidth=.8)

def bars(ax, values, maximum, title, subtitle):
    ax.bar(range(3), [v / maximum * 100 for v in values], color=colors, width=.62, zorder=3)
    ax.set_ylim(0, 125)
    ax.yaxis.set_major_formatter(PercentFormatter(100))
    ax.set_yticks([0,25,50,75,100])
    ax.set_xticks(range(3),names,fontsize=9)
    ax.set_title(title, loc='left', fontsize=13, fontweight='bold', pad=25)
    ax.text(0,1.02,subtitle,transform=ax.transAxes,fontsize=9,color='#5a6d83')
    for i, v in enumerate(values):
        ax.text(i,v/maximum*100+2, f'{v}/{maximum}\n{v/maximum:.1%}',
                ha='center',va='bottom',fontsize=10,fontweight='bold')

bars(axes[0], [foundation[k]['correct'] for k in keys], 396,
     'Foundation answers correct', 'Same 396-case development panel')
bars(axes[1], [foundation[k]['finished'] for k in keys], 396,
     'Responses finished', 'Stopped naturally within the output limit')
bars(axes[2], [admin['original_passed'],admin['parent_passed'],admin['passed']], 11,
     'Tool + code diagnostic', 'Small, simulated / isolated tasks')
fig.suptitle('MiniCPM: early learning and retention', x=.065, y=.98, ha='left',
             fontsize=19, fontweight='bold')
fig.text(.065,.905,'The new candidate gains answers on the foundation panel; the admin diagnostic remains unchanged from its parent.',fontsize=10.5,color='#42566f')
fig.text(.065,.115, f"Candidate vs parent:  +{foundation['gained_vs_parent']} answers gained   |   −{foundation['lost_vs_parent']} answers lost   |   136 practice presentations",
         fontsize=11,fontweight='bold',color='#264e6e')
fig.text(.065,.052,'Development results, not a mastery or release score. Some Boolean inputs overlap semantically across splits.\nThe 11-case diagnostic is not a general Linux-admin or native BW tool-use benchmark.',fontsize=9,color='#566a80',linespacing=1.5)
fig.subplots_adjust(left=.065,right=.98,top=.79,bottom=.27,wspace=.38)
out=RESULTS/'mixed66-progress-20261028.png'
fig.savefig(out,dpi=180,facecolor=fig.get_facecolor())
print(out)
