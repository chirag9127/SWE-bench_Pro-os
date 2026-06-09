# Auto Loss Analysis — Design Doc

**Status**: Draft v2
**Last updated**: 2026-04-14

---

## 1. What This Is

An agentic framework that takes tasks + model trajectories and produces a structured loss analysis report — the kind found in the NVIDIA and ByteDance examples. It uses a swarm of specialized sub-agents that play different roles (observer, questioner, investigator, critic, writer) and collaborate through an iterative scientific discovery loop.

The framework is **not a rigid pipeline**. It's a team of agents with different roles that a Controller dispatches based on what needs to be understood. Some work in parallel, some build on each other's findings, and a Critic challenges everything before it becomes a finding.

---

## 2. Two Analysis Tracks

Every loss analysis fundamentally answers two questions:

### Track A: Headroom Analysis (multi-model)
*"Where is the delta between models, and what explains it?"*

Find tasks where Model A passes and Model B fails. Understand what Model A did right and what Model B did wrong. This directly tells you what the weaker model needs to learn.

Key outputs:
- Head-to-head pass rate comparison
- Delta tasks (A passes, B fails) with side-by-side trajectory analysis
- Relative gap analysis (ratio to frontier, room to improve)
- Performance stratification (by difficulty, category, LOC, trajectory length)
- Degradation rates (who breaks down under pressure?)

### Track B: Failure Pattern Analysis (per-model or cross-model)
*"How does each model fail, and how fixable is it?"*

Classify every failure into a taxonomy (L1 execution vs reasoning, L2 subcategories). Compare the agent's approach against the golden solution. Determine which failures are mechanically addressable vs requiring deeper capability improvements.

Key outputs:
- L1/L2 failure taxonomy with counts per model
- Execution-vs-reasoning layer split
- Addressability spectrum (high → low fixability)
- Illustrative failure examples with "what happened" + "root cause"
- Side-by-side tables: failing model output vs passing model output
- Per-model deep dives (strengths, weaknesses, unique patterns)

---

## 3. Input Shape

```
data/
├── results.csv                        # SSOT for pass/fail
│   columns: task_id, model, run, result, reward, difficulty, category
│
├── tasks/
│   └── <task-name>/
│       ├── instruction.md             # Problem description given to the agent
│       ├── task.toml                  # Metadata: difficulty, category, tags, timeouts
│       ├── tests/                     # Verifier tests
│       ├── solution/                  # Reference solution (golden patch)
│       └── data/                      # Environment data files (optional)
│
└── evals/
    └── <task-name>/
        └── <model>/
            └── run-<id>/
                ├── trajectory.json    # Full agent trajectory (ATIF schema)
                └── result/
                    ├── reward.txt     # 0 or 1
                    ├── test-stdout.txt
                    └── test-stderr.txt
```

**Key invariants:**
- `results.csv` is the single source of truth. The framework never infers pass/fail.
- Golden solution in `solution/` is critical — diff analysis compares agent output vs golden.
- Trajectory follows ATIF: `{schema_version, session_id, agent, steps[], final_metrics}`.
- Each step: `step_id`, `source` (user/agent), `message`, `tool_calls[]`, `observation`.

---

## 4. Output Shape

```
output/
├── report.md                          # Final loss analysis report (4-20 pages)
├── figures/                           # Generated visualizations
│   ├── headline_pass_rates.png
│   ├── failure_mode_distribution.png
│   ├── l2_heatmap.png
│   ├── execution_vs_reasoning.png
│   ├── pass_rate_by_difficulty.png
│   ├── degradation_rates.png
│   └── ...
├── analysis/                          # Intermediate agent outputs (JSON)
│   ├── statistics.json                # Raw computed stats
│   ├── failure_classifications.json   # Per-trajectory L1/L2 labels
│   ├── headroom_pairs.json            # Delta task analysis
│   ├── hypotheses.json                # Generated + tested hypotheses
│   └── exemplars.json                 # Selected illustrative examples
└── cache/                             # LLM response cache (avoids re-spend)
```

---

## 5. Agent Architecture

### 5.1 Controller (Orchestrator)

The Controller is not an agent — it's the main loop that:
1. Loads data and computes baseline statistics (no LLM)
2. Determines which analysis tracks to run (headroom if multi-model, failure patterns always)
3. Dispatches sub-agents with specific questions
4. Collects findings into a shared context (the "investigation board")
5. Runs the Critic on findings before they're finalized
6. Hands final findings to the Writer

```
Controller
│
├── [Always] Statistician (compute, no LLM)
│   └── Produces: pass rates, distributions, stratifications
│
├── [Track A: Headroom] ──────────────────────────────────
│   ├── Observer → reads delta tasks, extracts factual diffs
│   ├── Comparator → side-by-side trajectory analysis
│   └── Questioner → "why did Model A succeed here?"
│
├── [Track B: Failure Patterns] ──────────────────────────
│   ├── Classifier → assigns L1/L2 failure mode per trajectory
│   ├── Diff Analyst → compares agent patch vs golden patch
│   ├── Investigator → deep-reads trajectories for root cause
│   └── Questioner → generates hypotheses about failure patterns
│
├── [Always] Critic → challenges every finding
├── [Always] Exemplar Curator → picks best illustrative examples
└── [Always] Writer → synthesizes findings into report sections
```

### 5.2 Sub-Agent Roles

| Role | LLM? | What it does | Skill needed |
|------|-------|-------------|-------------|
| **Statistician** | No | Computes pass rates, stratifications, distributions, correlation matrices. Pure Python/pandas. Produces all tables and chart data. | Data computation, chart generation |
| **Observer** | Yes | Reads trajectories and extracts factual observations — no judgment. "The agent ran 15 commands. It read 3 files before editing. It never ran tests." | Trajectory reading, fact extraction |
| **Classifier** | Yes | LLM-as-judge: reads a failing trajectory + task instruction and assigns L1 category (Execution/Reasoning) and L2 subcategory. Returns structured JSON. | Failure taxonomy knowledge, structured output |
| **Diff Analyst** | Yes | Compares agent's final state / patch against the golden solution. Identifies: what was correct, what was missing, what was wrong. | Code diff analysis, patch comparison |
| **Comparator** | Yes | Side-by-side analysis of two trajectories on the same task (pass vs fail, or Model A vs Model B). Finds the divergence point. | Paired trajectory reading |
| **Investigator** | Yes | Deep-reads specific trajectories to answer targeted questions from the Questioner. "Did the agent read the error message before retrying?" | Deep trajectory analysis |
| **Questioner** | Yes | Given statistics + initial findings, generates hypotheses and follow-up questions. "Do build errors correlate with tasks that use Go?" "Is the model looping more on hard tasks?" | Hypothesis generation |
| **Critic** | Yes | Challenges findings. "Is this correlation spurious?" "Is the sample size too small?" "Could there be an alternate explanation?" Flags weak claims. | Critical reasoning |
| **Exemplar Curator** | Yes | From classified failures, picks the 1-2 most illustrative examples per finding. Prefers examples where one model fails and another passes on the same task. | Example selection, annotation |
| **Writer** | Yes | Takes findings + examples + statistics and writes report sections. Follows the report template. Produces markdown with table formatting. | Report writing, data narrative |

### 5.3 Agent Collaboration Flow

This is **not sequential**. The Controller dispatches work in waves:

**Wave 1: Ground truth (parallel, no LLM)**
- Statistician computes everything from results.csv + task metadata
- Data loader indexes all trajectories and golden solutions

**Wave 2: Classification (parallel, LLM)**
- Classifier processes all failing trajectories (in parallel batches)
- Diff Analyst compares agent patches vs golden patches (in parallel)
- Observer extracts trajectory facts (step counts, tool usage, patterns)

**Wave 3: Investigation (depends on Wave 2)**
- Questioner reviews Wave 1+2 outputs, generates targeted questions
- Controller dispatches Investigators to answer each question
- Comparator does head-to-head on delta tasks (parallel)

**Wave 4: Validation**
- Critic reviews all findings from Waves 1-3
- Flags anything with weak evidence or small sample sizes
- Controller may dispatch additional Investigators to resolve

**Wave 5: Synthesis**
- Exemplar Curator selects best examples per finding
- Writer produces report sections from the investigation board
- Statistician generates final charts from confirmed findings

### 5.4 The Investigation Board (Shared State)

All agents read from and write to a shared JSON structure:

```json
{
  "statistics": { ... },           // Wave 1 output
  "classifications": [ ... ],      // Wave 2: per-trajectory L1/L2 labels
  "diffs": [ ... ],                // Wave 2: agent vs golden comparisons
  "observations": [ ... ],         // Wave 2: trajectory facts
  "questions": [ ... ],            // Wave 3: generated questions
  "answers": [ ... ],              // Wave 3: investigation results
  "comparisons": [ ... ],          // Wave 3: head-to-head analyses
  "critiques": [ ... ],            // Wave 4: challenges to findings
  "findings": [ ... ],             // Confirmed findings (post-critique)
  "exemplars": [ ... ],            // Wave 5: selected examples
  "report_sections": { ... }       // Wave 5: written report sections
}
```

---

## 6. Failure Taxonomy

Borrowed from NVIDIA/ByteDance reports, adapted for generality:

### L1 Categories

| L1 | Layer | Description |
|----|-------|-------------|
| **Build Error** | Execution | Code doesn't compile: syntax errors, type mismatches, undefined symbols, missing toolchain steps |
| **Collapse** | Execution | Process degeneration: edit loops, fixup spirals, gave up, stalled |
| **Timeout** | Execution | Ran out of time or context window |
| **Hallucination** | Reasoning | Fabricated APIs, file paths, codebase assumptions |
| **Logical Failure** | Reasoning | Right location, wrong implementation: edge cases, wrong conditions |
| **Misdiagnosis** | Reasoning | Wrong problem identified: wrong file, symptom fix, under-scoped |
| **Regression** | Reasoning | Fix breaks existing functionality |

### L2 Subcategories (discovered per-dataset)

The Classifier agent proposes L2 labels during classification. Common ones:
- Misread Issue Description, Imagined Codebase Structure, Under-Scoped Fix
- Fabricated File Path, Phantom API/Method, Missed Edge Case
- Edit Loop, Fixup Spiral, Stalled, Duration Timeout, Exceeded Context Limit
- Wrong Condition, Wrong Data Transformation, Broke Existing Test

The taxonomy is **not hardcoded** — the Classifier discovers what's relevant for each dataset.

---

## 7. Key Analysis Techniques

### 7.1 Agent Patch vs Golden Patch Diff
Every task has a `solution/` directory. The Diff Analyst extracts what the agent actually changed (from trajectory tool_calls) and compares it against the golden solution. This reveals:
- Did the agent touch the right files?
- Did it make the right kind of change?
- What did it miss?
- Did it change things it shouldn't have?

### 7.2 Execution-vs-Reasoning Framework
Split failures into two layers:
- **Execution layer** (Build Error + Collapse + Timeout): mechanical failures, often fixable through tooling
- **Reasoning layer** (Hallucination + Logical Failure + Misdiagnosis + Regression): understanding failures, require capability improvements

This split is the most actionable framing: execution failures have concrete fixes, reasoning failures require training improvements.

### 7.3 Addressability Spectrum
Rank failure modes by how fixable they are:

| Addressability | Failure Modes | Intervention |
|----------------|---------------|-------------|
| High | Build Error, Collapse | Toolchain training, loop detection |
| Medium-High | Timeout | Budget allocation, efficiency |
| Medium | Hallucination | Repository-context grounding |
| Medium-Low | Misdiagnosis | Scope verification, pre-fix checklist |
| Low | Logical Failure, Regression | Core reasoning improvement |

### 7.4 Performance Stratification
Stratify results by multiple dimensions to find where models break:
- **Difficulty** (easy/medium/hard)
- **Category** (from task.toml)
- **Complexity** (golden patch LOC as proxy)
- **Trajectory length** (agent message count)
- **Tags** (language, domain, etc.)

Key metric: **degradation rate** — how much does performance drop from easiest to hardest bucket? Models that retain capability under pressure are fundamentally different from ones that collapse.

### 7.5 Retry Value Analysis
When multiple runs exist per task:
- Pass@1 vs Pass@3 lift
- Are failures stochastic (retries help) or systematic (same failure every time)?
- Does retry value differ by failure type?

---

## 8. Report Template

The report follows the structure proven in the NVIDIA/ByteDance examples:

```
# Loss Analysis Report: {dataset_name}

## 1. EXECUTIVE SUMMARY
- Central finding (1 paragraph callout box)
- Key headlines (3-5 bullets, each with a bold stat)
- Per-model takeaways table (strengths, weaknesses, top recommendation)
- Actionable recommendations table (finding → recommendation → expected impact)

## 2. METHODOLOGY
- Evaluation setup (agent, tools, models, task count, runs)
- Task distribution (by dimension: category, difficulty, tags)
- Metrics definitions (Pass@1, Pass@3, rubric if available)
- Failure taxonomy description

## 3. HEADLINE PERFORMANCE
- Pass rate table + bar chart (all models)
- Relative gap analysis (ratio to frontier, room to improve)
- Retry value (Pass@1 → Pass@3 lift)

## 4. FAILURE MODE ANALYSIS
- L1 distribution table + stacked bar chart
- Execution-vs-reasoning framework table + chart
- L2 heatmap across models (if multi-model)
- Addressability spectrum table
- Per-model failure profile summary

## 5. PERFORMANCE BY DIMENSION
- By difficulty (table + line chart showing degradation)
- By category (table)
- By complexity/LOC bucket (if golden patch available)
- By trajectory length bucket
- Degradation rate comparison table

## 6. ILLUSTRATIVE EXAMPLES
- One side-by-side example per major failure mode
  Format: Task description | Failing model output | Passing model output
  With "What happened" + "Root cause" annotation

## 7. PER-MODEL DEEP DIVES (if multi-model)
- Model A: strengths, weaknesses, top L2 failures, tool usage
- Model B: same
- (repeat)

## 8. RECOMMENDATIONS
- Ordered by expected impact
- Each: Finding → Recommendation → Expected Impact
```

---

## 9. LLM Usage Strategy

### Model Selection
- **Classifier, Comparator, Investigator**: Claude Sonnet (high throughput, good enough)
- **Critic, Writer**: Claude Opus (needs best reasoning/writing)
- **Statistician, Observer**: No LLM (compute only, or simple extraction)

### Cost Control
- **Trajectory summarization**: Don't send full trajectories. Condense to:
  - First 2 agent steps (initial approach/plan)
  - Last 3 agent steps (final state/outcome)
  - All error messages and test output
  - Command list (what tools were used, in what order)
  - ~1000-2000 tokens per trajectory
- **Batch classification**: Group 5-10 trajectories per LLM call
- **Caching**: All LLM responses cached to `output/cache/` keyed by input hash
- **Budget**: Configurable max spend per analysis run

### Structured Output
All LLM agents return structured JSON, not free text. This enables:
- Programmatic aggregation of classifications
- Automatic chart generation from findings
- Critic can mechanically verify claims against data

---

## 10. Skills & Tools Available to Agents

Each agent has access to specific tools:

| Agent | Tools |
|-------|-------|
| Statistician | Python (pandas, matplotlib), results.csv, task metadata |
| Observer | Trajectory reader, command extractor, step counter |
| Classifier | LLM (with taxonomy prompt), trajectory summary, task instruction |
| Diff Analyst | Golden solution reader, trajectory patch extractor, diff tool |
| Comparator | Paired trajectory reader, step-by-step alignment |
| Investigator | Full trajectory reader, file reader (task files), LLM |
| Questioner | Investigation board reader, LLM |
| Critic | Investigation board reader, statistics verifier, LLM |
| Exemplar Curator | Classification results, trajectory summaries, LLM |
| Writer | Investigation board, chart generator, markdown templates, LLM |

---

## 11. Implementation Plan

| Step | What | Details |
|------|------|---------|
| 1 | **Data loader** | Read results.csv + trajectory JSONs + task metadata into common schema |
| 2 | **Statistician** | Pure Python: pass rates, stratifications, distributions. Matplotlib charts. |
| 3 | **Classifier agent** | LLM-as-judge: classify each failure into L1/L2. Batch processing. |
| 4 | **Diff Analyst agent** | Compare agent output vs golden solution per failing task. |
| 5 | **Comparator agent** | Head-to-head on delta tasks (if multi-model). |
| 6 | **Investigator + Questioner** | Hypothesis-driven deep dives. |
| 7 | **Critic** | Challenge all findings. |
| 8 | **Writer + Exemplar Curator** | Produce final report. |
| 9 | **CLI** | `python -m ala run --data ./data --output ./output --config config.yaml` |

---

## 12. What Makes This Different from a Script

A static script could compute pass rates and make charts. What the agent swarm adds:

1. **Discovery**: The Questioner generates hypotheses a human analyst might not think of. "Is there a correlation between the agent's first tool call and success?"
2. **Deep reading**: Agents can read full trajectories and understand *why* a model did what it did — something no regex or heuristic can do.
3. **Critique**: The Critic catches spurious correlations, small-sample claims, and alternate explanations before they enter the report.
4. **Examples**: The Exemplar Curator finds the *most illustrative* failure, not just any failure — the one that best communicates the pattern to a reader.
5. **Narrative**: The Writer produces coherent prose connecting statistics to examples to recommendations, not just data dumps.

---

## 13. Open Questions

- **Iteration depth**: Should the Questioner → Investigator loop repeat? Start with one pass, add iteration if findings are thin.
- **Golden solution availability**: Not all datasets have golden solutions. Diff analysis is optional but highly valuable.
- **Rubric scoring**: Some datasets have rubric grades beyond binary pass/fail. When available, enables richer analysis (partial credit, criterion-level breakdown).
- **Cost budget**: How to handle a 1000-task dataset without spending $100 on LLM calls? Sampling strategies need tuning.
- **Visualization library**: Matplotlib for now. Could upgrade to Plotly for interactive HTML reports.
