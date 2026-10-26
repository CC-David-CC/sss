"""Four intermediate precision panels; comparisons are within each checkpoint."""
import csv
from pathlib import Path
import matplotlib.pyplot as plt
from plot_original_reference import add_original_curve

ROOT=Path(__file__).resolve().parent
with (ROOT/'trained-precision-panels.csv').open(encoding='utf-8',newline='') as f:
    rows=list(csv.DictReader(f))
panels=[('adamw43','AdamW full · update 43 · llm-60'),
        ('muon42','Standard Muon · update 42 · llm-49'),
        ('rms41','RMS/decay Muon · update 41 · llm-60'),
        ('fast41','Fast/refine Muon · update 41 · llm-60')]
formats=['F32','F16','Q8_0','Q5_K_M','Q4_K_M','Q3_K_M','Q2_K','Q1_0']
labels=['FP32','FP16','Q8','Q5','Q4','Q3','Q2','Q1']
fig,axes=plt.subplots(2,2,figsize=(13,9),sharey=True)
fig.subplots_adjust(left=.075,right=.98,top=.80,bottom=.14,hspace=.45,wspace=.16)
for ax,(key,title) in zip(axes.flat,panels):
    data={r['format']:r for r in rows if r['panel']==key}
    correct=[int(data[f]['passed']) for f in formats]
    finished=[int(data[f]['finished']) for f in formats]
    ax.plot(range(8),finished,'s--',color='#147a56',label='Trained natural finishes',linewidth=1.6)
    ax.plot(range(8),correct,'o-',color='#245b91',label='Correct answers',linewidth=2)
    add_original_curve(ax, ROOT, formats, 'passed')
    for i,value in enumerate(correct):ax.annotate(str(value),(i,value),xytext=(0,10),textcoords='offset points',ha='center',fontsize=9)
    ax.set_title(title,loc='left',fontweight='bold',fontsize=11,pad=12)
    ax.set_xticks(range(8),labels);ax.set_ylim(-35,920);ax.set_yticks([0,216,432,648,864])
    ax.grid(axis='y',color='#dddddd');ax.set_axisbelow(True)
    for spine in ('top','right'):ax.spines[spine].set_visible(False)
    ax.set_ylabel('Out of 864 frozen questions')
handles,legend_labels=axes[0,0].get_legend_handles_labels()
fig.legend(handles,legend_labels,loc='upper center',bbox_to_anchor=(.5,.89),ncol=3,fontsize=9,frameon=False)
fig.suptitle('Trained MiniCPM5-2B: all four precision panels complete',fontsize=18,fontweight='bold',y=.97)
fig.text(.5,.91,'28 quantized evaluations × 864 questions = 24,192 attempts; existing FP32 references retained',ha='center',fontsize=11)
fig.text(.5,.065,'Compare precision within each panel. Updates, training exposures and runtimes differ; this is not an optimizer ranking.',ha='center',fontsize=10)
fig.text(.5,.025,'Original per-quant line uses prior runtime, same cases and 64-token limit; original F32 unmeasured. No new model calls.',ha='center',fontsize=9,color='#555555')
fig.savefig(ROOT/'trained-precision-panels.png',dpi=180,facecolor='white')

fig,axes=plt.subplots(2,2,figsize=(13,9),sharex=True)
fig.subplots_adjust(left=.09,right=.98,top=.79,bottom=.13,hspace=.43,wspace=.27)
for ax,(key,title) in zip(axes.flat,panels):
    data={r['format']:r for r in rows if r['panel']==key}
    gains=[int(data[f]['answer_gains']) for f in formats[1:]]
    losses=[-int(data[f]['answer_losses']) for f in formats[1:]]
    ax.barh(range(7),gains,color='#3c8b69',label='Newly correct')
    ax.barh(range(7),losses,color='#b84e53',label='FP32 successes lost')
    for i,(gain,loss) in enumerate(zip(gains,losses)):
        ax.text(gain+7,i,str(gain),va='center',fontsize=9)
        ax.text(loss-7,i,str(-loss),va='center',ha='right',fontsize=9)
    ax.set_yticks(range(7),labels[1:]);ax.invert_yaxis();ax.set_xlim(-540,85)
    ax.axvline(0,color='#666666',linewidth=.7);ax.grid(axis='x',color='#eeeeee');ax.set_axisbelow(True)
    ax.set_title(title,loc='left',fontweight='bold',fontsize=11,pad=12)
    for spine in ('top','right','left'):ax.spines[spine].set_visible(False)
    ax.set_xlabel('Changed answers versus this checkpoint’s FP32 reference')
handles,legend_labels=axes[0,0].get_legend_handles_labels()
fig.legend(handles,legend_labels,loc='upper center',bbox_to_anchor=(.5,.89),ncol=2,fontsize=9,frameon=False)
fig.suptitle('What quantization gained and lost, question by question',fontsize=18,fontweight='bold',y=.97)
fig.text(.5,.91,'Equal total scores can hide different answers. Each bar is paired against its own local FP32 reference.',ha='center',fontsize=11)
fig.text(.5,.045,'One run per format; no repeated seeds. These are frozen-panel observations, not general capability estimates.',ha='center',fontsize=10,color='#555555')
fig.savefig(ROOT/'trained-precision-gains-losses.png',dpi=180,facecolor='white')
print('Rendered four complete panels and their paired gains/losses.')
