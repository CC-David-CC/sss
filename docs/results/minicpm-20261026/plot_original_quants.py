"""Plot the seven completed original-model precision evaluations."""
import csv
from pathlib import Path

import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parent
with (ROOT / 'original-quantization.csv').open(encoding='utf-8', newline='') as stream:
    data = {row['format']: row for row in csv.DictReader(stream)}
order = ['Q1_0', 'Q2_K', 'Q3_K_M', 'Q4_K_M', 'Q5_K_M', 'Q8_0', 'F16']
labels = ['Q1_0', 'Q2_K', 'Q3_K_M', 'Q4_K_M', 'Q5_K_M', 'Q8_0', 'FP16']
if set(data) != set(order) or any(int(r['cases']) != 864 for r in data.values()):
    raise ValueError('All seven complete 864-case precision results required')

fig, axes = plt.subplots(1, 2, figsize=(13, 6.6))
fig.subplots_adjust(left=.12, right=.96, top=.78, bottom=.20, wspace=.28)
colors = ['#4c78a8'] * 6 + ['#243b5a']
for axis, metric, title, limit, ticks in [
    (axes[0], 'passed', 'Correct answers', 72, [0, 16, 32, 48, 64]),
    (axes[1], 'finished', 'Responses that stopped naturally', 960, [0, 216, 432, 648, 864]),
]:
    values = [int(data[fmt][metric]) for fmt in order]
    bars = axis.barh(labels, values, color=colors, height=.62)
    axis.invert_yaxis()
    axis.set_title(title, loc='left', fontsize=13, fontweight='bold', pad=12)
    axis.set_xlim(0, limit)
    axis.set_xticks(ticks)
    axis.grid(axis='x', color='#dddddd', alpha=.8)
    axis.set_axisbelow(True)
    axis.tick_params(axis='y', length=0, labelsize=11)
    for spine in ('top', 'right', 'left'):
        axis.spines[spine].set_visible(False)
    for bar, value in zip(bars, values):
        axis.text(value + limit*.018, bar.get_y()+bar.get_height()/2,
            f'{value}/864  ({value/864:.1%})', va='center', fontsize=10)
axes[0].set_xlabel('Number correct (axis zoomed to 0-72; 864 questions total)')
axes[1].set_xlabel('Number with natural EOS within 64 generated tokens')
fig.suptitle('Original MiniCPM5-2B: all seven precision formats',
             fontsize=19, fontweight='bold', y=.96)
fig.text(.5, .875, 'Each format attempted the same 864 frozen questions | one completed run per format',
         ha='center', fontsize=12)
fig.text(.5, .09, 'These are original-model results. Trained-model quantization comparisons are pending.',
         ha='center', fontsize=11, fontweight='bold')
fig.text(.5, .035, 'Shared A100 server. Exact-answer scoring and a 64-token response limit; these are bounded suite scores, not general model ratings.',
         ha='center', fontsize=9, color='#555555')
fig.savefig(ROOT / 'original-quantization.png', dpi=200, facecolor='white')
print('Rendered original-quantization.png: 7 formats, 6,048 scored attempts.')
