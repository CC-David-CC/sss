"""Render completed trained precision results, showing unfinished rows explicitly."""
import csv
from pathlib import Path
import matplotlib.pyplot as plt
from plot_original_reference import original_scores

ROOT=Path(__file__).resolve().parent
with (ROOT/'trained-quantization-progress.csv').open(encoding='utf-8',newline='') as f: data={r['format']:r for r in csv.DictReader(f)}
order=['F32','F16','Q8_0','Q5_K_M','Q4_K_M','Q3_K_M','Q2_K','Q1_0']
original=original_scores(ROOT)
labels=['FP32 reference','FP16','Q8_0','Q5_K_M','Q4_K_M','Q3_K_M','Q2_K','Q1_0']
fig,axes=plt.subplots(1,2,figsize=(13,7.2));fig.subplots_adjust(left=.16,right=.97,top=.78,bottom=.20,wspace=.22)
for ax,metric,title in [(axes[0],'passed','Correct answers'),(axes[1],'finished','Naturally finished responses')]:
    indices=[i for i,f in enumerate(order) if f in original]
    ax.plot([int(original[order[i]][metric]) for i in indices],indices,'d--',
            color='#d06b1f',lw=1.8,label='Original per quant (prior runtime)',zorder=5)
    for i,fmt in enumerate(order):
        row=data[fmt]
        if row['status']=='COMPLETE':
            value=int(row[metric]);ax.barh(i,value,height=.6,color='#243b5a' if fmt=='F32' else '#4c78a8')
            inside=value>760
            ax.text(value-14 if inside else value+14,i,f'{value}/864 ({value/864:.1%})',
                    va='center',ha='right' if inside else 'left',fontsize=10,
                    color='white' if inside else 'black')
        else:ax.text(20,i,row['status'].replace('_',' '),va='center',fontsize=10,color='#777777')
    ax.set_yticks(range(8),labels);ax.invert_yaxis();ax.set_xlim(0,970);ax.set_xticks([0,216,432,648,864])
    ax.set_title(title,fontsize=13,fontweight='bold',loc='left',pad=12)
    ax.grid(axis='x',color='#dddddd');ax.set_axisbelow(True);ax.tick_params(axis='y',length=0)
    for spine in ('top','right','left'):ax.spines[spine].set_visible(False)
    ax.set_xlabel('Out of 864 frozen questions')
    ax.legend(loc='lower right',fontsize=8,frameon=False)
count=sum(data[f]['status']=='COMPLETE' for f in order[1:])
fig.suptitle('Trained MiniCPM5-2B: seven-format quantization comparison',fontsize=18,fontweight='bold',y=.96)
fig.text(.5,.875,f'AdamW full update 43 | {count}/7 formats complete | same local PCC/COW runtime and 64-token limit',ha='center',fontsize=11)
fig.text(.5,.09,'This intermediate checkpoint is separate from the ten A100 training curves. No additional training was performed.',ha='center',fontsize=10)
note=('Orange line: historical original-model scores on the same cases; prior runtime, original F32 not measured.' if count==7
      else 'Blank rows are unfinished measurements, not zero model scores. Individual answers can change even when totals match.')
fig.text(.5,.035,note,ha='center',fontsize=9,color='#555555')
fig.savefig(ROOT/'trained-quantization-progress.png',dpi=200,facecolor='white')
print(f'Rendered trained-quantization-progress.png: {count}/7 formats complete.')
