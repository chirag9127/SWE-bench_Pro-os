#!/usr/bin/env python3
"""Generate a clean, aesthetic architecture diagram for Auto Loss Analysis.

Usage: python3 scripts/generate_architecture_diagram.py --output output/figures/architecture.png
"""

import argparse
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import numpy as np

# ── Palette ──────────────────────────────────────────────────────────────────
BG = "#FAFAFA"
PURPLE = "#674EA7"
PURPLE_MED = "#9B8EC4"
PURPLE_LIGHT = "#D9D2E9"
PURPLE_FAINT = "#F0EDF7"
CORAL = "#E07A5F"
CORAL_LIGHT = "#F5CFC2"
SAGE = "#81B29A"
SAGE_LIGHT = "#D4E8DC"
GOLD = "#D4A843"
GOLD_LIGHT = "#F5E6C0"
SLATE = "#3D405B"
SLATE_LIGHT = "#E8E8EE"
WHITE = "#FFFFFF"
GRAY = "#AAAAAA"
DARK = "#333333"


def pill(ax, cx, cy, w, h, label, color, text_color=WHITE, fontsize=9.5,
         sublabel=None, bold=True, radius=0.015):
    """Draw a pill-shaped box centered at (cx, cy)."""
    x = cx - w / 2
    y = cy - h / 2
    box = FancyBboxPatch(
        (x, y), w, h,
        boxstyle=f"round,pad={radius}",
        facecolor=color, edgecolor="none", zorder=3,
    )
    ax.add_patch(box)
    ty = cy + (0.012 if sublabel else 0)
    ax.text(cx, ty, label, ha="center", va="center", fontsize=fontsize,
            color=text_color, fontweight="bold" if bold else "normal", zorder=4)
    if sublabel:
        ax.text(cx, cy - 0.016, sublabel, ha="center", va="center",
                fontsize=7, color=text_color, alpha=0.8, zorder=4)


def zone(ax, x, y, w, h, color, alpha=0.08, border_alpha=0.25):
    """Draw a soft background zone."""
    box = FancyBboxPatch(
        (x, y), w, h, boxstyle="round,pad=0.008",
        facecolor=color, edgecolor=color, alpha=alpha, linewidth=0, zorder=1,
    )
    ax.add_patch(box)
    # Subtle border
    border = FancyBboxPatch(
        (x, y), w, h, boxstyle="round,pad=0.008",
        facecolor="none", edgecolor=color, alpha=border_alpha,
        linewidth=1.0, zorder=1,
    )
    ax.add_patch(border)


def flow_arrow(ax, x1, y1, x2, y2, color=GRAY, lw=1.5, head=0.008):
    """Simple straight arrow."""
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle=f"-|>,head_width={head},head_length={head*0.8}",
                                color=color, lw=lw),
                zorder=2)


def wave_label(ax, x, y, num, title, color):
    """Wave badge + title."""
    # Badge
    badge = FancyBboxPatch(
        (x, y - 0.012), 0.055, 0.024, boxstyle="round,pad=0.004",
        facecolor=color, edgecolor="none", zorder=3,
    )
    ax.add_patch(badge)
    ax.text(x + 0.0275, y, f"W{num}", ha="center", va="center",
            fontsize=7.5, color=WHITE, fontweight="bold", zorder=4)
    ax.text(x + 0.065, y, title, ha="left", va="center",
            fontsize=8.5, color=DARK, zorder=4)


def generate(output_path):
    fig, ax = plt.subplots(figsize=(14, 18))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)

    # ── Title ────────────────────────────────────────────────────────────
    ax.text(0.50, 0.975, "Auto Loss Analysis", ha="center", va="top",
            fontsize=24, fontweight="bold", color=SLATE)
    ax.text(0.50, 0.955, "System Architecture", ha="center", va="top",
            fontsize=14, color=PURPLE_MED)
    ax.text(0.50, 0.938, "Claude Code Native  ·  Sub-Agent Orchestration  ·  Iterative Discovery",
            ha="center", va="top", fontsize=9, color=GRAY)

    # ── INPUT ────────────────────────────────────────────────────────────
    y_input = 0.895
    zone(ax, 0.08, y_input - 0.035, 0.84, 0.055, SAGE)
    ax.text(0.10, y_input, "INPUT", ha="left", va="center",
            fontsize=8, fontweight="bold", color=SAGE, alpha=0.7)

    pill(ax, 0.28, y_input, 0.14, 0.032, "results.csv", SAGE,
         sublabel="task × model × run", fontsize=8)
    pill(ax, 0.50, y_input, 0.14, 0.032, "data/tasks/", SAGE,
         sublabel="instruction · solution", fontsize=8)
    pill(ax, 0.72, y_input, 0.14, 0.032, "data/evals/", SAGE,
         sublabel="trajectory · reward", fontsize=8)

    # ── CONTROLLER ───────────────────────────────────────────────────────
    y_ctrl = 0.825
    pill(ax, 0.50, y_ctrl, 0.50, 0.045, "/loss-analysis", SLATE,
         sublabel="Controller Skill — orchestrates all agents", fontsize=14)
    flow_arrow(ax, 0.50, y_input - 0.035, 0.50, y_ctrl + 0.025, color=SAGE)

    # ── WAVE 1 ───────────────────────────────────────────────────────────
    y_w1 = 0.745
    zone(ax, 0.12, y_w1 - 0.032, 0.76, 0.065, "#4A86C8")
    wave_label(ax, 0.135, y_w1 + 0.02, "1", "Ground Truth", "#4A86C8")

    pill(ax, 0.38, y_w1 - 0.005, 0.22, 0.035, "Statistician", "#4A86C8",
         sublabel="compute_stats.py → statistics.json", fontsize=9)
    pill(ax, 0.66, y_w1 - 0.005, 0.22, 0.035, "Chart Generator", "#4A86C8",
         sublabel="generate_charts.py → PNGs", fontsize=9)

    ax.text(0.87, y_w1 - 0.005, "no LLM", ha="right", va="center",
            fontsize=7, color="#4A86C8", fontstyle="italic")

    flow_arrow(ax, 0.50, y_ctrl - 0.025, 0.50, y_w1 + 0.035, color=SLATE)

    # ── WAVE 2 ───────────────────────────────────────────────────────────
    y_w2 = 0.645
    zone(ax, 0.12, y_w2 - 0.042, 0.76, 0.08, CORAL)
    wave_label(ax, 0.135, y_w2 + 0.025, "2", "Classification & Diff", CORAL)

    pill(ax, 0.38, y_w2 - 0.01, 0.24, 0.04, "Classifier Agent", CORAL,
         sublabel="Discovers failure taxonomy · traces WHY", fontsize=9)
    pill(ax, 0.66, y_w2 - 0.01, 0.24, 0.04, "Diff Analyst Agent", CORAL,
         sublabel="Agent patch vs golden solution", fontsize=9)

    # parallel indicator
    ax.text(0.52, y_w2 + 0.027, "parallel", ha="center", va="center",
            fontsize=6.5, color=CORAL, fontstyle="italic",
            bbox=dict(boxstyle="round,pad=0.15", facecolor=CORAL_LIGHT, edgecolor="none"))

    flow_arrow(ax, 0.50, y_w1 - 0.035, 0.50, y_w2 + 0.04, color="#4A86C8")

    # ── WAVE 3 ───────────────────────────────────────────────────────────
    y_w3 = 0.53
    zone(ax, 0.12, y_w3 - 0.047, 0.76, 0.09, PURPLE)
    wave_label(ax, 0.135, y_w3 + 0.03, "3", "Hypothesis → Investigation", PURPLE)

    pill(ax, 0.30, y_w3 - 0.012, 0.18, 0.04, "Questioner", PURPLE,
         sublabel="Generates hypotheses", fontsize=9)
    pill(ax, 0.52, y_w3 - 0.012, 0.18, 0.04, "Investigator", PURPLE,
         sublabel="Deep-reads trajectories", fontsize=9)
    pill(ax, 0.74, y_w3 - 0.012, 0.18, 0.04, "Comparator", PURPLE,
         sublabel="Head-to-head analysis", fontsize=9)

    # arrows between agents
    flow_arrow(ax, 0.39, y_w3 - 0.012, 0.43, y_w3 - 0.012, color=PURPLE_MED, lw=1.0)
    flow_arrow(ax, 0.61, y_w3 - 0.012, 0.65, y_w3 - 0.012, color=PURPLE_MED, lw=1.0)

    flow_arrow(ax, 0.50, y_w2 - 0.045, 0.50, y_w3 + 0.045, color=CORAL)

    # ── WAVE 4 ───────────────────────────────────────────────────────────
    y_w4 = 0.425
    zone(ax, 0.22, y_w4 - 0.028, 0.56, 0.055, GOLD)
    wave_label(ax, 0.235, y_w4 + 0.015, "4", "Validation", GOLD)

    pill(ax, 0.50, y_w4 - 0.006, 0.30, 0.035, "Critic Agent", GOLD,
         text_color=SLATE, sublabel="Challenges findings · confirms or rejects", fontsize=9)

    flow_arrow(ax, 0.50, y_w3 - 0.05, 0.50, y_w4 + 0.03, color=PURPLE_MED)

    # ── WAVE 5 ───────────────────────────────────────────────────────────
    y_w5 = 0.32
    zone(ax, 0.12, y_w5 - 0.047, 0.76, 0.09, PURPLE)
    wave_label(ax, 0.135, y_w5 + 0.03, "5", "Synthesis & Report Writing", PURPLE)

    pill(ax, 0.30, y_w5 - 0.012, 0.18, 0.04, "Exemplar Curator", PURPLE,
         sublabel="Selects best examples", fontsize=9)
    pill(ax, 0.52, y_w5 - 0.012, 0.18, 0.04, "Writer Agents", PURPLE,
         sublabel="1 per section · parallel", fontsize=9)
    pill(ax, 0.74, y_w5 - 0.012, 0.18, 0.04, "Style Enforcer", PURPLE_MED,
         sublabel="md_to_docx.py", fontsize=9)

    ax.text(0.52, y_w5 + 0.027, "parallel", ha="center", va="center",
            fontsize=6.5, color=PURPLE, fontstyle="italic",
            bbox=dict(boxstyle="round,pad=0.15", facecolor=PURPLE_FAINT, edgecolor="none"))

    flow_arrow(ax, 0.50, y_w4 - 0.03, 0.50, y_w5 + 0.045, color=GOLD)

    # ── OUTPUT ───────────────────────────────────────────────────────────
    y_out = 0.225
    pill(ax, 0.50, y_out, 0.50, 0.045, "output/report.md  →  report.docx", SLATE,
         sublabel="NVIDIA/Mercor styled  ·  <10 pages  ·  insight-led analysis", fontsize=12)

    flow_arrow(ax, 0.50, y_w5 - 0.05, 0.50, y_out + 0.025, color=PURPLE_MED)

    # ── INVESTIGATION BOARD (right annotation) ───────────────────────────
    y_board = 0.56
    x_board = 0.945

    ax.text(x_board, y_board + 0.14, "Investigation Board", ha="center", va="center",
            fontsize=9, fontweight="bold", color=PURPLE, rotation=0)
    ax.text(x_board, y_board + 0.115, "output/analysis/", ha="center", va="center",
            fontsize=7, color=GRAY)

    files = [
        "statistics.json", "classifications.json", "comparisons.json",
        "questions.json", "answers.json", "findings.json",
        "exemplars.json", "sections/*.md",
    ]
    for i, f in enumerate(files):
        y = y_board + 0.08 - i * 0.028
        ax.text(x_board, y, f"  {f}", ha="center", va="center",
                fontsize=6.5, color=PURPLE_MED,
                bbox=dict(boxstyle="round,pad=0.2", facecolor=PURPLE_FAINT,
                          edgecolor=PURPLE_LIGHT, linewidth=0.5))

    # Connecting dots from waves to board
    for y in [y_w1, y_w2, y_w3, y_w4, y_w5]:
        ax.plot([0.88, 0.90], [y, y], color=PURPLE_LIGHT, lw=0.8,
                ls="dotted", zorder=1)

    # ── SKILLS INVENTORY (bottom) ────────────────────────────────────────
    y_skills = 0.135
    zone(ax, 0.08, y_skills - 0.055, 0.84, 0.075, PURPLE)

    ax.text(0.12, y_skills, "Agent Prompts", ha="left", va="center",
            fontsize=8, fontweight="bold", color=PURPLE, alpha=0.7)

    skills = ["classifier", "comparator", "critic", "diff-analyst",
              "exemplar-curator", "investigator", "questioner", "writer"]
    for i, s in enumerate(skills):
        x = 0.26 + i * 0.085
        ax.text(x, y_skills, s, ha="center", va="center", fontsize=6.5,
                color=PURPLE,
                bbox=dict(boxstyle="round,pad=0.2", facecolor=PURPLE_FAINT,
                          edgecolor=PURPLE_LIGHT, linewidth=0.5))

    y_scripts = y_skills - 0.035
    ax.text(0.12, y_scripts, "Helper Scripts", ha="left", va="center",
            fontsize=8, fontweight="bold", color=PURPLE, alpha=0.7)

    scripts = ["compute_stats.py", "generate_charts.py", "summarize_trajectory.py", "md_to_docx.py"]
    for i, s in enumerate(scripts):
        x = 0.32 + i * 0.15
        ax.text(x, y_scripts, s, ha="center", va="center", fontsize=6.5,
                color="#4A86C8",
                bbox=dict(boxstyle="round,pad=0.2", facecolor="#EBF0F8",
                          edgecolor="#B8CBE4", linewidth=0.5))

    # ── Subtle watermark ─────────────────────────────────────────────────
    ax.text(0.50, 0.015, "Claude Code Native  ·  No Python Framework  ·  Agents All the Way Down",
            ha="center", va="center", fontsize=8, color=GRAY, alpha=0.5)

    plt.savefig(output_path, dpi=300, bbox_inches="tight", facecolor=BG, pad_inches=0.3)
    plt.close()
    print(f"Saved to {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="./output/figures/architecture.png")
    args = parser.parse_args()
    generate(args.output)
