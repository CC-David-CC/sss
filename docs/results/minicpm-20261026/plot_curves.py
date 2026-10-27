"""Render the intermediate MiniCPM training curves from the adjacent CSV."""

import csv
from datetime import datetime, timezone
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from plot_original_reference import original_scores


ROOT = Path(__file__).resolve().parent
CSV_PATH = ROOT / "intermediate-training-curves.csv"
PNG_PATH = ROOT / "intermediate-training-curves.png"

with CSV_PATH.open(newline="", encoding="utf-8") as handle:
    rows = [row for row in csv.DictReader(handle) if row["arm"] != "original-baseline"]

by_arm = {}
for row in rows:
    by_arm.setdefault(row["arm"], []).append(row)
for points in by_arm.values():
    points.sort(key=lambda row: int(row["training_presentations"]))

as_of = max(datetime.fromisoformat(row["scored_at_utc"]) for row in rows if row["scored_at_utc"])
as_of = as_of.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

labels = {
    "adamw-full": "AdamW - full update",
    "muon-standard-full": "Muon - standard full update",
    "muon-rms-decay-full": "Muon - RMS/decay full update",
    "muon-fast-refine-full": "Muon - fast/refine full update",
    "adamw-lora-r1": "AdamW LoRA - rank 1",
    "adamw-lora-r2": "AdamW LoRA - rank 2",
    "adamw-lora-r3": "AdamW LoRA - rank 3",
    "adamw-lora-r4": "AdamW LoRA - rank 4",
    "adamw-lora-r8": "AdamW LoRA - rank 8",
    "adamw-lora-r16": "AdamW LoRA - rank 16",
}
order = list(labels)
colors = plt.get_cmap("tab10").colors
markers = ["o", "s", "+", "x", "^", "D", "v", "P", "X", "*"]

fig, axes = plt.subplots(2, 1, figsize=(12.8, 9.0), sharex=True)
fig.subplots_adjust(left=0.09, right=0.98, top=0.86, bottom=0.24, hspace=0.15)

original = original_scores(ROOT)['F16']
panels = [
    (axes[0], "correct_out_of_864", "Correct held-out cases (of 864)", int(original['passed'])),
    (axes[1], "natural_finishes_out_of_864", "Naturally finished responses (of 864)", int(original['finished'])),
]
for axis, metric, ylabel, baseline in panels:
    axis.axhline(
        baseline,
        color="#d06b1f",
        linestyle="--",
        linewidth=1.8,
        label="Original F16: 59 correct / 415 finished",
    )
    axis.axvline(
        1836,
        color="#777777",
        linestyle="--",
        linewidth=1.2,
        label="68-update target" if axis is axes[0] else None,
    )
    for index, arm in enumerate(order):
        points = by_arm.get(arm, [])
        if not points:
            continue
        x = [int(row["training_presentations"]) for row in points]
        y = [int(row[metric]) for row in points]
        axis.plot(
            x,
            y,
            color=colors[index],
            marker=markers[index],
            markevery=max(1, len(x) // 12),
            markersize=4,
            linewidth=1.8,
            label=labels[arm],
            alpha=0.94,
        )
    axis.set_ylabel(ylabel)
    axis.grid(True, axis="y", color="#d7d7d7", linewidth=0.7)
    axis.spines["top"].set_visible(False)
    axis.spines["right"].set_visible(False)

axes[0].set_ylim(0, 864)
axes[0].set_yticks(range(0, 865, 144))
axes[1].set_ylim(380, 864)
axes[1].set_yticks([400, 500, 600, 700, 800, 864])
axes[1].set_xlabel("Cumulative training presentations (27 per update)")
axes[1].set_xlim(0, 1900)
axes[1].set_xticks(range(0, 1901, 270))
axes[1].xaxis.set_major_formatter(mticker.StrMethodFormatter("{x:,.0f}"))

fig.suptitle("MiniCPM5-2B: completed 68-update comparison", fontsize=16, fontweight="bold", y=0.96)
fig.text(
    0.5,
    0.91,
    f"673 retained scores | 864 frozen cases per checkpoint | data through {as_of}",
    ha="center",
    fontsize=10,
)
handles, legend_labels = axes[0].get_legend_handles_labels()
fig.legend(
    handles,
    legend_labels,
    loc="lower center",
    bbox_to_anchor=(0.5, 0.095),
    ncol=3,
    frameon=False,
    fontsize=9,
    columnspacing=1.4,
    handlelength=2.4,
)
fig.text(
    0.5,
    0.025,
    "Baseline: 59 correct / 415 naturally finished. Target: 68 updates = 1,836 presentations.\n"
    "Full updates: FP32 weights. LoRA: F16 base plus adapters. Recorded execution paths differ; "
    "same frozen cases. Shared A100 load.",
    ha="center",
    fontsize=8.5,
    color="#555555",
)
fig.savefig(PNG_PATH, dpi=220, facecolor="white")
print(f"Rendered {PNG_PATH} from {len(rows)} completed checkpoints across {len(by_arm)} arms.")
