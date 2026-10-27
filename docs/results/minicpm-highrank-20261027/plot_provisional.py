"""Plot only retained scored points; no model execution or missing-point fill."""
from pathlib import Path
import argparse,hashlib,json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def main():
 p=argparse.ArgumentParser();p.add_argument('--input-dir',type=Path,default=Path(__file__).parent)
 p.add_argument('--output-dir',type=Path,default=Path(__file__).parent);a=p.parse_args()
 families={(32,'adamw'):[],(32,'muon'):[],(4096,'adamw'):[],(4096,'muon'):[]};sources={};runtimes={}
 evaluation_ids=set()
 for file in sorted(a.input_dir.glob('*update*.json')):
  row=json.loads(file.read_bytes());key=(row.get('rank'),row.get('optimizer'))
  if key not in families:continue
  if row['status']!='COMPLETE' or row['cases']!=864:raise ValueError('Incomplete panel: '+file.name)
  n=row['source_training_updates']
  if n>10 or any(v['source_training_updates']==n for v in families[key]):raise ValueError('Unexpected or duplicated update')
  families[key].append(row);sources[file.name]=hashlib.sha256(file.read_bytes()).hexdigest()
  runtimes.setdefault(str(key),set()).add(row['runtime_id']);evaluation_ids.add(row['evaluation_id'])
 if len(evaluation_ids)!=1:raise ValueError('One frozen question panel required')
 if any(len(v)>1 for v in runtimes.values()):raise ValueError('Within-arm runtime changed; review before plotting as one trajectory')
 complete=all(any(v['source_training_updates']==5 for v in rows) for rows in families.values())
 fig,axes=plt.subplots(2,1,figsize=(11,8),sharex=True)
 colors=['#1565c0','#e67e22','#8e44ad','#138d75'];markers=['o','s','^','D']
 for (key,rows),color,marker in zip(families.items(),colors,markers):
  if not rows:continue
  rows.sort(key=lambda r:r['source_training_updates']);x=[r['source_training_updates'] for r in rows]
  label=f'Rank {key[0]} '+('AdamW' if key[1]=='adamw' else 'factorwise Muon')
  for ax,field in zip(axes,('passed','finished')):
   ax.plot(x,[r[field] for r in rows],marker=marker,color=color,label=label,linewidth=2,markersize=6)
   last=rows[-1];ax.annotate(str(last[field]),(x[-1],last[field]),xytext=(7,5),textcoords='offset points',color=color,fontsize=10)
 axes[0].axhline(59,color='#777777',linestyle='--',linewidth=1,label='Historical original: 59 correct / 415 finished')
 axes[1].axhline(415,color='#777777',linestyle='--',linewidth=1)
 axes[0].set_ylabel('Correct answers / 864');axes[1].set_ylabel('Naturally finished / 864')
 axes[0].set_ylim(-15,max(400,max(r['passed'] for rows in families.values() for r in rows)*1.15))
 axes[1].set_ylim(-25,920);axes[1].set_xlabel('Completed training updates (27 practice presentations per update)')
 for ax in axes:
  ax.set_xlim(.8,5.65);ax.set_xticks(range(1,6));ax.grid(alpha=.2)
 handles,labels=axes[0].get_legend_handles_labels()
 fig.legend(handles,labels,loc='upper center',bbox_to_anchor=(.5,.94),ncol=2,fontsize=9)
 fig.suptitle('MiniCPM high-rank provisional study — '+('five-update readout' if complete else 'progress snapshot'),fontsize=15)
 fig.text(.08,.025,'Only marked points were measured; connecting lines do not supply missing measurements.\n'
  'Learning rates and cross-host runtimes differ. Original reference uses a historical runtime.\n'
  'Same 864 questions and 64-token output bound; this is not release qualification or an isolated optimizer-effect estimate.',fontsize=9)
 fig.tight_layout(rect=(0,.12,1,.81));a.output_dir.mkdir(parents=True,exist_ok=True)
 fig.savefig(a.output_dir/'provisional-training.png',dpi=160);plt.close(fig)
 manifest=dict(schema=1,status='COMPLETE_FIVE_UPDATE_READOUT' if complete else 'IN_PROGRESS',
  source_sha256=sources,runtime_ids={k:sorted(v) for k,v in runtimes.items()},evaluation_id=next(iter(evaluation_ids)),
  new_model_calls=0,interpolated_measurements=0,original_reference_kind='historical; different recorded runtime',
  plot_source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
 (a.output_dir/'provisional-plot-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
 print(json.dumps(dict(status=manifest['status'],scored_points=sum(map(len,families.values())))))
if __name__=='__main__':main()
