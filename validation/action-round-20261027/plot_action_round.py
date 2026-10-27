"""Plot only saved aggregate results; no model calls or private prompt output."""
from pathlib import Path
import json
import matplotlib.pyplot as plt
root=Path(__file__).resolve().parent
audit=json.loads((root/'audit.json').read_text())
review=json.loads((root/'review-pairs.json').read_text())
assert audit['status']=='AUDITED_ORIGINAL_EVIDENCE'
assert audit['rounds'][0]['native_updates']==4 and audit['rounds'][0]['cases']==868
assert review['candidate_correct']-review['baseline_correct']==review['answer_gains']-review['answer_losses']==-36
fig,axes=plt.subplots(1,3,figsize=(14,5.8),gridspec_kw={'width_ratios':[1.1,1.5,1.4]})
fig.subplots_adjust(left=.065,right=.975,bottom=.21,top=.72,wspace=.36)
for ax,values,maximum,title in [
 (axes[0],[1,2],2,'BW workflow: 2 diagnostic cases'),
 (axes[1],[review['baseline_correct'],review['candidate_correct']],864,'Math/state review: 864 cases')]:
 bars=ax.bar(['Parent','Candidate'],values,color=['#63758a','#2d719b'],width=.58)
 ax.set_ylim(0,maximum*1.16);ax.set_title(title,fontsize=11,fontweight='bold',pad=14)
 ax.set_ylabel('Correct answers');ax.grid(axis='y',alpha=.2);ax.set_axisbelow(True)
 if maximum==2:ax.set_yticks([0,1,2])
 for bar,value in zip(bars,values):ax.text(bar.get_x()+bar.get_width()/2,value+maximum*.025,f'{value}/{maximum}',ha='center',fontsize=12)
axes[2].bar(['Gained','Lost'],[review['answer_gains'],-review['answer_losses']],color=['#17805d','#b64e44'],width=.58)
axes[2].axhline(0,color='#777777',lw=1)
axes[2].set_ylim(-72,40);axes[2].set_ylabel('Changed answer verdicts')
axes[2].set_title('Review turnover: net -36',fontsize=11,fontweight='bold',pad=14)
axes[2].text(0,27,'+23',ha='center',fontsize=12);axes[2].text(1,-65,'-59',ha='center',fontsize=12)
for ax in axes:
 for spine in ('top','right'):ax.spines[spine].set_visible(False)
fig.suptitle('One native action-learning round: a workflow gain with review losses',fontsize=17,fontweight='bold',y=.97)
fig.text(.5,.86,'4 full AdamW updates | 4 verified action lessons + 27 mixed-review lessons | 124 presentations',ha='center',fontsize=11)
fig.text(.5,.10,'Previous working parent retained; candidate preserved for repair. Both review models finished all 864 responses.',ha='center',fontsize=10)
fig.text(.5,.045,'Separate from the frozen 68-update optimizer study. Two workflow cases do not establish broad mastery.',ha='center',fontsize=10,color='#555555')
fig.savefig(root/'action-round.png',dpi=170,facecolor='white');plt.close(fig)
print('Rendered audited four-update action round; no inference or training.')
