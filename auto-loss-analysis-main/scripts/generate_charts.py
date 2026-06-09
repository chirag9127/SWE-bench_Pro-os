#!/usr/bin/env python3
"""Generate charts from analysis JSON files → output/figures/*.png

Styled to match the NVIDIA/Mercor report aesthetic:
- Clean, minimal design
- Purple palette (#674EA7 primary, #B4A7D6 secondary)
- Full model names
- No chartjunk (no gridlines clutter, no 3D, no excessive decoration)
- 300 DPI for print quality

Usage: python3 scripts/generate_charts.py --analysis ./output/analysis --figures ./output/figures
"""

import argparse
import json
import os
from collections import Counter

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np

# ── NVIDIA/Mercor Color Palette ────────────────────────────────────────────────
PURPLE_PRIMARY = "#674EA7"
PURPLE_LIGHT = "#B4A7D6"
PURPLE_LIGHTER = "#D9D2E9"
CORAL = "#E07A5F"
SAGE = "#81B29A"
SAND = "#F2CC8F"
DARK_GRAY = "#333333"
LIGHT_GRAY = "#E8E8E8"

# Model name mapping (short → full display name)
MODEL_DISPLAY_NAMES = {
    "opus": "Claude Opus",
    "deepseek": "DeepSeek-V3",
    "claude": "Claude Opus",
    "gpt": "GPT-5.1 Codex",
    "nemotron": "Nemotron Super",
    "claude-haiku-4-5": "Claude Haiku 4.5",
    "claude-opus-4-8": "Claude Opus 4.8",
    "kimi-k2.5": "Kimi K2.5",
}

MODEL_COLORS = {
    "opus": PURPLE_PRIMARY,
    "deepseek": CORAL,
    "claude": PURPLE_PRIMARY,
    "gpt": SAGE,
    "nemotron": SAND,
    "claude-haiku-4-5": PURPLE_LIGHT,
    "claude-opus-4-8": PURPLE_PRIMARY,
    "kimi-k2.5": SAGE,
}


def get_display_name(model_key):
    return MODEL_DISPLAY_NAMES.get(model_key, model_key.replace("_", " ").title())


def get_color(model_key):
    return MODEL_COLORS.get(model_key, PURPLE_LIGHT)


def apply_style():
    """Set global matplotlib style to match NVIDIA report."""
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
        "font.size": 11,
        "axes.titlesize": 13,
        "axes.titleweight": "bold",
        "axes.labelsize": 11,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.edgecolor": DARK_GRAY,
        "axes.labelcolor": DARK_GRAY,
        "xtick.color": DARK_GRAY,
        "ytick.color": DARK_GRAY,
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "axes.grid": False,
        "figure.dpi": 150,
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.2,
    })


def load_json(path):
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f)


def chart_headline_pass_rates(stats, fig_dir):
    """Horizontal bar chart of pass rates per model."""
    models = stats["models"]
    display_names = [get_display_name(m) for m in models]
    rates = [stats["model_stats"][m]["pass_rate"] * 100 for m in models]
    colors = [get_color(m) for m in models]

    fig, ax = plt.subplots(figsize=(9, 3.5))
    bars = ax.barh(display_names, rates, color=colors, height=0.5, edgecolor="white", linewidth=0.5)
    ax.set_xlabel("Pass Rate (%)")
    ax.set_title("Overall Pass Rate by Model")
    ax.set_xlim(0, 105)
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)

    for bar, rate in zip(bars, rates):
        ax.text(bar.get_width() + 1.5, bar.get_y() + bar.get_height() / 2,
                f"{rate:.1f}%", va="center", fontweight="bold", fontsize=12, color=DARK_GRAY)

    plt.tight_layout()
    path = os.path.join(fig_dir, "headline_pass_rates.png")
    plt.savefig(path)
    plt.close()
    print(f"  {path}")


def chart_headroom(stats, fig_dir):
    """Horizontal bar showing headroom buckets with clean labels."""
    headroom = stats["headroom"]

    # Prettier labels
    label_map = {
        "both_pass": "Both Solve",
        "opus_only": "Claude Opus Only",
        "deepseek_only": "DeepSeek-V3 Only",
        "both_fail": "Neither Solves",
    }
    color_map = {
        "both_pass": SAGE,
        "opus_only": PURPLE_PRIMARY,
        "deepseek_only": CORAL,
        "both_fail": LIGHT_GRAY,
    }

    # Order: both_pass, opus_only, deepseek_only, both_fail
    order = ["both_pass", "opus_only", "deepseek_only", "both_fail"]
    labels = [label_map.get(k, k) for k in order]
    values = [headroom.get(k, 0) for k in order]
    colors = [color_map.get(k, PURPLE_LIGHT) for k in order]

    fig, ax = plt.subplots(figsize=(9, 3.5))
    bars = ax.barh(labels, values, color=colors, height=0.55, edgecolor="white", linewidth=0.5)
    ax.set_xlabel("Number of Tasks")
    ax.set_title("Headroom Analysis: Task Solvability by Model")
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)
    ax.invert_yaxis()

    for bar, v in zip(bars, values):
        pct = v / stats["total_tasks"] * 100
        ax.text(bar.get_width() + 3, bar.get_y() + bar.get_height() / 2,
                f"{v} ({pct:.0f}%)", va="center", fontsize=10, color=DARK_GRAY)

    plt.tight_layout()
    path = os.path.join(fig_dir, "headroom.png")
    plt.savefig(path)
    plt.close()
    print(f"  {path}")


def chart_consistency(stats, fig_dir):
    """Side-by-side grouped bar chart of consistency distribution."""
    consistency = stats["consistency"]
    models = stats["models"]
    display_names = [get_display_name(m) for m in models]
    colors = [get_color(m) for m in models]

    max_runs = 0
    for model_counts in consistency.values():
        for key in model_counts:
            if "_of_" in key:
                max_runs = max(max_runs, int(key.split("_of_", 1)[1]))
    max_runs = max_runs or 1
    categories = [f"{i}/{max_runs}" for i in range(max_runs + 1)]
    key_map = {cat: cat.replace("/", "_of_") for cat in categories}

    x = np.arange(len(categories))
    width = 0.35
    fig, ax = plt.subplots(figsize=(9, 4.5))

    for i, m in enumerate(models):
        values = [consistency[m].get(key_map[cat], 0) for cat in categories]
        offset = (i - len(models) / 2 + 0.5) * width
        bars = ax.bar(x + offset, values, width, label=display_names[i],
                       color=colors[i], edgecolor="white", linewidth=0.5)
        for bar, val in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 3,
                    str(val), ha="center", fontsize=9, color=DARK_GRAY)

    ax.set_xticks(x)
    ax.set_xticklabels(categories)
    ax.set_xlabel(f"Runs Passed (out of {max_runs})")
    ax.set_ylabel("Number of Tasks")
    ax.set_title("Run Consistency Distribution")
    ax.legend(frameon=False, loc="upper left")
    plt.tight_layout()

    path = os.path.join(fig_dir, "consistency.png")
    plt.savefig(path)
    plt.close()
    print(f"  {path}")


def chart_by_difficulty(stats, fig_dir):
    """Grouped bar chart of pass rates by difficulty tier."""
    by_diff = stats.get("by_difficulty", {})
    if not by_diff:
        return

    models = stats["models"]
    display_names = [get_display_name(m) for m in models]
    colors = [get_color(m) for m in models]
    difficulties = sorted(by_diff.keys(), key=lambda d: {"easy": 0, "medium": 1, "hard": 2}.get(d, 3))
    diff_labels = [d.capitalize() for d in difficulties]

    x = np.arange(len(difficulties))
    width = 0.35
    fig, ax = plt.subplots(figsize=(9, 4.5))

    for i, m in enumerate(models):
        rates = [by_diff[d].get(m, {}).get("pass_rate", 0) * 100 for d in difficulties]
        offset = (i - len(models) / 2 + 0.5) * width
        bars = ax.bar(x + offset, rates, width, label=display_names[i],
                       color=colors[i], edgecolor="white", linewidth=0.5)
        for bar, rate in zip(bars, rates):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1.5,
                    f"{rate:.0f}%", ha="center", fontsize=9, color=DARK_GRAY)

    ax.set_xticks(x)
    ax.set_xticklabels(diff_labels)
    ax.set_ylabel("Pass Rate (%)")
    ax.set_title("Pass Rate by Difficulty Tier")
    ax.legend(frameon=False)
    ax.set_ylim(0, 105)
    plt.tight_layout()

    path = os.path.join(fig_dir, "pass_rate_by_difficulty.png")
    plt.savefig(path)
    plt.close()
    print(f"  {path}")


def chart_failure_modes(analysis_dir, fig_dir):
    """Horizontal bar chart of L1 failure mode distribution."""
    classifications = load_json(os.path.join(analysis_dir, "classifications.json"))
    if not classifications:
        return

    if isinstance(classifications, dict):
        taxonomy = classifications.get("taxonomy", [])
        records = classifications.get("classifications", [])
    else:
        taxonomy = []
        records = classifications

    if taxonomy:
        l1_counts = Counter({t.get("l1", "Unknown"): t.get("count", 0) for t in taxonomy})
        layer_map = {t.get("l1", "Unknown"): t.get("layer", "reasoning") for t in taxonomy}
    else:
        l1_counts = Counter(c.get("l1", "Unknown") for c in records)
        layer_map = {}
        for c in records:
            layer_map[c.get("l1", "Unknown")] = c.get("layer", "reasoning")

    total = sum(l1_counts.values())

    # Sort by count descending
    sorted_items = l1_counts.most_common()
    labels = [item[0] for item in sorted_items]
    values = [item[1] for item in sorted_items]

    color_map = {"reasoning": PURPLE_PRIMARY, "execution": CORAL}
    colors = [color_map.get(layer_map.get(l, "reasoning"), PURPLE_LIGHT) for l in labels]

    fig, ax = plt.subplots(figsize=(9, 4))
    bars = ax.barh(labels, values, color=colors, height=0.55, edgecolor="white", linewidth=0.5)
    ax.set_xlabel(f"Count (n={total} sampled trajectories)")
    ax.set_title("Failure Mode Distribution")
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)
    ax.invert_yaxis()

    for bar, v in zip(bars, values):
        pct = v / total * 100
        ax.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height() / 2,
                f"{v} ({pct:.0f}%)", va="center", fontsize=10, color=DARK_GRAY)

    # Legend for layer
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor=PURPLE_PRIMARY, label="Reasoning"),
        Patch(facecolor=CORAL, label="Execution"),
    ]
    ax.legend(handles=legend_elements, frameon=False, loc="lower right")

    plt.tight_layout()
    path = os.path.join(fig_dir, "failure_mode_distribution.png")
    plt.savefig(path)
    plt.close()
    print(f"  {path}")


def main(analysis_dir, fig_dir):
    os.makedirs(fig_dir, exist_ok=True)
    apply_style()

    stats = load_json(os.path.join(analysis_dir, "statistics.json"))

    if stats:
        print("Generating charts from statistics.json:")
        chart_headline_pass_rates(stats, fig_dir)
        chart_headroom(stats, fig_dir)
        chart_consistency(stats, fig_dir)
        chart_by_difficulty(stats, fig_dir)

    print("Generating charts from classifications.json:")
    chart_failure_modes(analysis_dir, fig_dir)

    print("Done.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--analysis", default="./output/analysis")
    parser.add_argument("--figures", default="./output/figures")
    args = parser.parse_args()
    main(args.analysis, args.figures)
