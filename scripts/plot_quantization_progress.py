"""Plot completed public precision assessments; leave missing variants missing."""
from pathlib import Path
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

r=Path(__file__).resolve().parents[1]
v=json.loads((r/'validation/minicpm-native-learning-20261024/quantization-progress.json').read_text())
formats=v['declared_formats'];rows={(x['family'],x['format']):x for x in v['rows']}
out=r/'docs/images';out.mkdir(exist_ok=True)
plt.rcParams.update({'font.size':11,'axes.spines.top':False,'axes.spines.right':False,'svg.hashsalt':'sss-quantization'})
fig,axes=plt.subplots(2,1,figsize=(11,7.8),sharex=True)
x=np.arange(len(formats))
for ax,key,title in zip(axes,['passed','finished'],['Correct answers / 864','Naturally finished responses / 864']):
    for family,shift,color in [('original',-.2,'#8c98a5'),('trained',.2,'#158578')]:
        values=[rows[family,f].get(key,np.nan) if rows[family,f]['status']=='COMPLETE' else np.nan for f in formats]
        bars=ax.bar(x+shift,values,width=.38,label=family.title(),color=color)
        ax.bar_label(bars,labels=[str(int(y)) if np.isfinite(y) else '' for y in values],padding=3,fontsize=10)
        for i,y in enumerate(values):
            if not np.isfinite(y):ax.text(i+shift,40,'pending',ha='center',rotation=90,fontsize=9)
    ax.set_ylim(0,945);ax.set_yticks([0,216,432,648,864]);ax.set_ylabel(title)
    ax.grid(axis='y',alpha=.18);ax.set_axisbelow(True)
axes[0].legend(loc='upper right');axes[1].set_xticks(x,formats)
axes[1].set_xlabel('Stored model precision · same model family, questions, limits and RTX 4090 runtime')
fig.suptitle('Does AnswerStop-01 learning survive quantization?',fontsize=16,y=.985)
fig.text(.5,.018,f"{v['measured_variants']}/{v['expected_variants']} completed assessments · 864 development questions each · missing results are not zero scores.\nHistorical trained checkpoint; not the ongoing 68-update optimizer study or a general-capability benchmark.",ha='center',fontsize=9)
fig.tight_layout(rect=(0,.065,1,.96))
for ext in ['svg','png']:fig.savefig(out/('minicpm-quantization-behavior.'+ext),dpi=160,metadata={'Creator':'S³ public aggregate report'})
p=out/'minicpm-quantization-behavior.svg';p.write_text('\n'.join(line.rstrip() for line in p.read_text().splitlines())+'\n')
