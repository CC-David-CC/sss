"""Export measured per-update learning/forgetting plots and CSV; no model loads."""
from pathlib import Path
import argparse,csv,hashlib,json
from sss.curves import measured_curves

def plot(protocol_path,input_path,prefix):
    protocol=json.loads(Path(protocol_path).read_text());document=json.loads(Path(input_path).read_text())
    curves=measured_curves(protocol,document)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.ticker import MaxNLocator
    prefix=Path(prefix);prefix.parent.mkdir(parents=True,exist_ok=True)
    labels={'adamw-full':'Full AdamW','muon-standard-full':'Full standard Muon',
        'muon-rms-decay-full':'Full RMS/decay Muon','muon-fast-refine-full':'Full fast-to-refine Muon',
        'adamw-lora-r16':'LoRA AdamW, rank16'}
    fig,axes=plt.subplots(2,2,figsize=(12,8),sharex=True)
    panels=[('original_answers_gained','Original wrong answers now correct'),
            ('original_answers_lost','Original correct answers now wrong'),
            ('passed','Exact answers correct'),('finished','Naturally finished responses')]
    rows=[]
    for index,(name,points) in enumerate(curves.items()):
        style=dict(color='black' if 'lora' in name else 'C'+str(index),
            linestyle='--' if 'lora' in name else '-',marker='o',markersize=2.5,
            label=labels.get(name,name),linewidth=1.4)
        for axis,(field,title) in zip(axes.flat,panels):
            axis.plot([p['update'] for p in points],[p[field] for p in points],**style)
        rows.extend(points)
    cases=protocol['cases_per_evaluation'];reference=document['reference_passed']
    for axis,(field,title) in zip(axes.flat,panels):
        axis.set_title(title);axis.grid(alpha=.25);axis.set_xlim(0,max(protocol['checkpoint_updates']))
        axis.set_ylim(bottom=0);axis.set_ylabel('Questions / '+str(cases));axis.yaxis.set_major_locator(MaxNLocator(integer=True))
        if field=='original_answers_gained':axis.set_ylim(0,max(1,max((p[field] for values in curves.values() for p in values),default=0)+1))
        if field=='original_answers_lost':axis.set_ylim(0,max(1,reference));axis.set_ylabel('Lost / '+str(reference)+' original passes')
        if field in ('passed','finished'):axis.set_ylim(0,cases)
    for axis in axes[-1]:axis.set_xlabel('Completed optimizer updates; same ordered practice')
    handles,names=axes[0,0].get_legend_handles_labels();fig.legend(handles,names,loc='lower center',ncol=3,fontsize=9)
    fig.suptitle(protocol.get('display_title','MiniCPM learning and forgetting at equal practice exposure')+'\nMeasured points only; '+str(protocol['batch_size'])+' presentations per update',fontsize=13)
    coverage=', '.join(labels.get(name,name)+': '+str(max((p['update'] for p in values),default='none')) for name,values in curves.items())
    fig.text(.5,.915,'Measured through update '+coverage,ha='center',fontsize=8)
    fig.tight_layout(rect=(0,.09,1,.92))
    fig.savefig(str(prefix)+'.png',dpi=160);fig.savefig(str(prefix)+'.svg');plt.close(fig)
    fields=['arm','update','presentations','original_answers_gained','original_answers_lost','passed','finished','model_sha256']
    with Path(str(prefix)+'.csv').open('w',newline='') as out:
        writer=csv.DictWriter(out,fieldnames=fields,extrasaction='ignore');writer.writeheader();writer.writerows(rows)
    record=dict(schema=1,status='RENDERED_MEASUREMENTS',protocol_id=protocol['protocol_id'],
        measured_points=len(rows),maximum_update_by_arm={name:max((p['update'] for p in points),default=None) for name,points in curves.items()},
        source_data_sha256=hashlib.sha256(Path(input_path).read_bytes()).hexdigest(),
        protocol_file_sha256=hashlib.sha256(Path(protocol_path).read_bytes()).hexdigest(),matplotlib=matplotlib.__version__,
        complete=document.get('status')=='COMPLETE',weights_published=False)
    Path(str(prefix)+'.json').write_text(json.dumps(record,indent=2)+'\n');return record

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--protocol',type=Path,required=True)
    parser.add_argument('--input',type=Path,required=True);parser.add_argument('--output-prefix',type=Path,required=True)
    args=parser.parse_args();print(json.dumps(plot(args.protocol,args.input,args.output_prefix)))
