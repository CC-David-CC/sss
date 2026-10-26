"""Render the latest nine S3 skill scores, retaining unequal update counts."""
import csv
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parent
with (ROOT/'latest-skill-scores.csv').open(encoding='utf-8',newline='') as f: rows=list(csv.DictReader(f))
arms=[('adamw-full','AdamW full'),('muon-standard-full','Muon standard'),
      ('muon-rms-decay-full','Muon RMS/decay'),('muon-fast-refine-full','Muon fast/refine'),
      *[('adamw-lora-r'+str(n),'LoRA rank '+str(n)) for n in (1,2,3,4,8,16)]]
skills=[('math.place_value','Place\nvalue'),('math.add.no_carry','Add\nno carry'),
        ('math.add.carry','Add\ncarry'),('math.add.signed','Signed\naddition'),
        ('math.multiply','Multiply'),('math.divide','Divide'),('math.fraction','Fraction'),
        ('math.fraction.add','Fraction\naddition'),('state.registers','Register\nstate')]
index={(r['arm'],r['skill_id']):r for r in rows}
if len(index)!=90 or any(int(r['cases'])!=96 for r in rows):raise ValueError('Complete 10-arm, 9-skill, 96-case matrix required')
values=np.array([[int(index[a,s]['passed']) for s,_ in skills] for a,_ in arms])
labels=[f"{label}  (update {index[a,skills[0][0]]['update']})" for a,label in arms]
fig,ax=plt.subplots(figsize=(13,6.6));fig.subplots_adjust(left=.23,right=.92,top=.82,bottom=.22)
im=ax.imshow(values,vmin=0,vmax=96,cmap='viridis',aspect='auto')
ax.set_xticks(range(9),[s for _,s in skills],fontsize=10)
ax.set_yticks(range(10),labels,fontsize=10)
for y in range(10):
    for x in range(9):ax.text(x,y,str(values[y,x]),ha='center',va='center',fontsize=10,color='white' if values[y,x]<50 else 'black')
fig.colorbar(im,ax=ax,fraction=.03,pad=.025,label='Correct out of 96')
fig.suptitle('MiniCPM5-2B: latest S3 skill results',fontsize=18,fontweight='bold',y=.96)
fig.text(.5,.88,'Each cell is correct answers out of 96 frozen questions for that skill',ha='center',fontsize=12)
fig.text(.5,.09,'Checkpoints have different update counts. This is a progress snapshot, not a matched-exposure optimizer ranking.',ha='center',fontsize=10)
fig.text(.5,.035,'These nine arithmetic/state skills do not establish BW shell ability, tool use, or autonomous research performance.',ha='center',fontsize=9,color='#555555')
fig.savefig(ROOT/'latest-skill-scores.png',dpi=200,facecolor='white')
print('Rendered latest-skill-scores.png: 90 exact aggregate cells.')
