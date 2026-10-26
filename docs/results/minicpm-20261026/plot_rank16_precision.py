"""Render completed precision measurements; pending formats stay unscored."""
import json
from pathlib import Path
import matplotlib.pyplot as plt
from plot_original_reference import add_original_curve

root = Path(__file__).resolve().parent
report = json.loads((root / 'rank16-final-precision.json').read_text(encoding='utf8'))
rows = report['rows']
fig, axes = plt.subplots(2, 1, figsize=(12, 8), sharex=True,
                         gridspec_kw={'height_ratios': [2, 1]})
fig.subplots_adjust(top=.79, bottom=.17, left=.09, right=.97, hspace=.18)
for axis, field, title, color in [(axes[0], 'correct', 'Correct answers / 864', '#2457a6'),
                                   (axes[1], 'finished', 'Naturally finished / 864', '#147a56')]:
    x = [i for i, r in enumerate(rows) if r['status'] == 'COMPLETE']
    y = [r[field] for r in rows if r['status'] == 'COMPLETE']
    axis.plot(x, y, marker='o', color=color, lw=2.2, label='Trained rank 16, update 68')
    add_original_curve(axis, root, [r['format'] for r in rows],
                       'passed' if field == 'correct' else 'finished', horizontal=True)
    for i, r in enumerate(rows):
        if r['status'] == 'COMPLETE':
            axis.annotate(str(r[field]), (i, r[field]), xytext=(0, 9),
                          textcoords='offset points', ha='center', fontsize=11)
        else:
            axis.axvspan(i - .3, i + .3, color='#f1f1f1', zorder=-1)
            axis.text(i, .08, 'pending', ha='center', transform=axis.get_xaxis_transform(),
                      color='#666666', fontsize=10)
    axis.set_ylabel(title)
    axis.set_ylim(0, 920)
    axis.set_yticks([0, 216, 432, 648, 864])
    axis.grid(axis='y', alpha=.25)
    axis.spines[['top', 'right']].set_visible(False)
axes[0].axhline(rows[0]['correct'], color='#2457a6', ls=':', lw=.8, alpha=.6)
axes[1].set_xticks(range(len(rows)), [r['format'] for r in rows])
axes[1].set_xlabel('Requested GGUF format (K formats use mixed tensor types)')
fig.suptitle('MiniCPM5-2B: preserving learned behavior after quantization',
             fontsize=17, fontweight='bold', y=.965)
fig.text(.5, .895, 'AdamW LoRA rank 16, update 68 | one merged master | 864 fixed questions',
         ha='center', fontsize=11)
handles, labels = axes[0].get_legend_handles_labels()
fig.legend(handles, labels, loc='upper center', bbox_to_anchor=(.5,.87), ncol=1,
           fontsize=9, frameon=False)
fig.text(.5, .035, 'Original sweep: prior runtime, same frozen cases; original F32 not measured.\n'
         'Dashed orange = original per quant; gray dots = original F16 level. Shared A100 loads; no release acceptance.',
         ha='center', fontsize=10, color='#555555')
fig.savefig(root / 'rank16-final-precision.png', dpi=160, facecolor='white')
plt.close(fig)
