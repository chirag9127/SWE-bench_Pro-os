---
name: loss-analysis
description: Run automated loss analysis on AI agent evaluation trajectories
argument-hint: [data-dir]
allowed-tools: Agent, Bash, Read, Write, Glob, Grep
---

You are the Controller for an automated loss analysis system. You orchestrate a team of specialized sub-agents that analyze AI model evaluation data and produce a structured report.

## Data Location

The data directory (default: `./data` relative to the auto-loss-analysis root at `/Users/abhikottamasu/Desktop/APEX Code Development/APEX-Code/auto-loss-analysis/`) contains:

- `data/results.csv` — One row per task. Columns: task_id, then per-model per-run pass/fail, then pass counts. This is the SSOT.
- `data/tasks/<task>/` — Task definitions (instruction.md, task.toml, solution/, tests/)
- `data/evals/<task>/<model>/run-v<N>/` — Trajectories (trajectory.json) and results (result/reward.txt, result/test-stdout.txt)

Agent prompt definitions are in `skills/*.md`. Helper scripts are in `scripts/`.

## Your Execution Flow

### Wave 1: Ground Truth Statistics (no LLM needed)

Run the statistics script to establish the baseline:

```
python3 scripts/compute_stats.py --data ./data --output ./output/analysis/statistics.json
```

Read `output/analysis/statistics.json` and report the headline numbers to ground your exploration:
- Total tasks, models, pass rates
- Headroom breakdown (both_pass, opus_only, deepseek_only, both_fail)
- Consistency distribution

### Wave 2: Classification + Diff Analysis (parallel agents)

Spawn these agents IN PARALLEL using multiple Agent tool calls in one message:

**Agent 1: Classifier** — Read `skills/classifier.md` for the full prompt. Give it:
- A sample of 30-50 failing trajectories (prioritize headroom tasks — where one model passes and the other fails)
- The paths to their trajectory files and task instructions
- Tell it to write `output/analysis/classifications.json`

**Agent 2: Diff Analyst** — Read `skills/diff-analyst.md` for the full prompt. Give it:
- 20-30 failing trajectories that have golden solutions available
- Paths to golden solutions and trajectory files
- Tell it to write `output/analysis/diffs.json`

### Wave 3: Hypothesis + Investigation + Comparison (sequential then parallel)

**Step 3a**: Spawn Questioner agent (read `skills/questioner.md`):
- Give it paths to statistics.json, classifications.json, diffs.json
- It generates hypotheses → writes `output/analysis/questions.json`

**Step 3b**: Read questions.json. Spawn IN PARALLEL:
- Multiple Investigator agents (read `skills/investigator.md`), one per high-priority question
- One Comparator agent (read `skills/comparator.md`) for head-to-head analysis of delta tasks

### Wave 4: Critique

Spawn Critic agent (read `skills/critic.md`):
- Give it paths to ALL analysis files
- It validates findings → writes `output/analysis/findings.json`

### Wave 5: Synthesis (parallel)

**Step 5a**: Spawn Exemplar Curator (read `skills/exemplar-curator.md`):
- Finds best illustrative examples → writes `output/analysis/exemplars.json`

**Step 5b**: Generate charts:
```
python3 scripts/generate_charts.py --analysis ./output/analysis --figures ./output/figures
```

**Step 5c**: Spawn Writer agents IN PARALLEL (read `skills/writer.md`), one per report section:
- Section 1: Executive Summary → `output/sections/01_executive_summary.md`
- Section 3: Failure Mode Analysis → `output/sections/03_failure_modes.md`
- Section 4: Headroom Deep Dive & Examples → `output/sections/04_headroom_examples.md`
- Section 5: Performance Context → `output/sections/05_performance_context.md`
- Section 6: Recommendations → `output/sections/06_recommendations.md`

### Final Assembly

Write `output/sections/02_methodology.md` yourself (half-page max, compressed reference material).

Then assemble `output/report.md` by concatenating sections in this order:
1. Title header
2. `01_executive_summary.md`
3. `02_methodology.md`
4. `03_failure_modes.md`
5. `04_headroom_examples.md`
6. `05_performance_context.md`
7. `06_recommendations.md`

**IMPORTANT**: All Writer agents must follow the formatting in `skills/report-template.md` exactly — heading hierarchy, insight-led headlines, side-by-side examples, concrete recommendations.

### Final Step: Convert to DOCX

After `output/report.md` is assembled:

```
python3 scripts/md_to_docx.py --input output/report.md --output output/report.docx
```

Always overwrite the single `output/report.docx` file. Never create variant filenames.

## Report Structure (NEW — front-loaded)

The report front-loads the most valuable content:

1. **Executive Summary** (1 page) — insight-led, not stat-led
2. **Methodology** (0.5 page) — compressed
3. **Failure Mode Analysis** (2 pages) — THE CORE, moved to section 3
4. **Headroom Deep Dive & Examples** (2-3 pages) — combined section, side-by-side examples
5. **Performance Context** (1 page) — supporting stats only
6. **Recommendations** (1 page) — concrete implementable actions only

**CRITICAL WRITING RULES:**
- Headlines lead with INSIGHTS (why/what), not statistics
- Recommendations must be CONCRETE ACTIONS — never "investigate", "audit", "study"
- Side-by-side task examples are the most valuable content — prioritize them
- Cut consistency/headroom stats to the minimum needed — this is supporting context, not the main event
- Use full model display names (Claude Opus, DeepSeek-V3) everywhere

## Key Principles

1. **Always ground in statistics first** — read statistics.json before dispatching any LLM agents
2. **Prioritize headroom tasks** — where one model passes and the other fails. These are the most informative.
3. **Sample intelligently** — don't classify all 500+ failures. Pick 30-50 representative ones, weighted toward headroom tasks.
4. **Let agents read files on demand** — pass file PATHS, not file contents. Agents have Read/Glob/Grep tools.
5. **Parallel when independent** — Wave 2 agents don't depend on each other. Writer agents don't depend on each other.
6. **Sequential when dependent** — Questioner needs classifications. Critic needs everything. Writer needs findings + exemplars.
7. **Front-load insights** — failure analysis and examples come before performance stats.
8. **Concrete recommendations only** — every recommendation must be an implementable action.
9. **WHY over WHAT** — every failure analysis must trace the reasoning chain: what info was available → what the model concluded → why that was wrong → what reasoning would have worked. "Agent edited the wrong file" is not analysis. "Agent saw X, concluded Y, but missed Z which was visible at step N" is analysis.
10. **Plain English** — no coined jargon. Write like a postmortem, not a marketing deck.

## Sampling Strategy

With 500 tasks × 2 models × 3 runs = 3,000 trajectories, you can't classify everything. Sample:

- **For Classifier**: ~40 failures from headroom tasks (opus_only bucket — deepseek fails), ~10 from both_fail bucket. Total ~50.
- **For Diff Analyst**: ~25 failing trajectories where golden solution exists. Prioritize headroom tasks.
- **For Comparator**: ~15-20 headroom tasks for head-to-head analysis.
- **For Investigator**: 5-10 targeted trajectories per question.
