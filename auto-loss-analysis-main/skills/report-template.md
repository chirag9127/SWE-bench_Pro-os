# Loss Analysis Report Template

This is the reference template for how the final `output/report.md` should be structured and formatted. Writers should follow this exactly.

**IMPORTANT**: The report is front-loaded — failure analysis and examples come FIRST (sections 3-4), supported by performance data (section 5). The executive summary and methodology are lean context-setters, not the main event.

---

# Loss Analysis Report: {Dataset Name}

## 1. EXECUTIVE SUMMARY

{1-2 sentence scope: models, task count, runs.}

> *Central finding: {The single most important INSIGHT — not a stat. Why does the weaker model fail? What behavioral pattern explains the gap? This should be actionable, not just "Model A is better.""}*

### Key Headlines

Headlines lead with INSIGHTS, not statistics. The stat supports the insight, not the other way around.

**{Insight about WHY failures happen.}** {Supporting stat and what it means for improvement.} (See §3.)

**{Insight about the most fixable failure mode.}** {Stat + concrete intervention.} (See §3.)

**{Insight about behavioral divergence between models.}** {What the better model does differently.} (See §4.)

**{Insight about improvement leverage.}** {Where to focus effort for maximum ROI.} (See §6.)

### Per-Model Takeaways

| Model | Key Behavioral Pattern | Primary Weakness | Top Intervention |
|-------|----------------------|------------------|-----------------|
| **{Model A}** | {What it does well — behavioral, not just "higher pass rate"} | {Specific failure pattern} | {Concrete action} |
| **{Model B}** | {What it does well} | {Specific failure pattern} | {Concrete action} |

### Actionable Recommendations

| # | Failure Pattern | Concrete Intervention | Expected Impact |
|---|----------------|----------------------|-----------------|
| 1 | **{Pattern}**: {stat} | **{Specific action}**: {detail} | {Quantified impact} |
| 2 | **{Pattern}**: {stat} | **{Specific action}**: {detail} | {Impact} |
| 3 | **{Pattern}**: {stat} | **{Specific action}**: {detail} | {Impact} |

**Every recommendation must be a concrete, implementable action. NEVER use "investigate further", "audit for broken harnesses", or "study patterns for transfer". If you don't know the fix, don't list it.**

---

## 2. METHODOLOGY

{Half-page max. Setup, metrics definitions, sampling approach. This is reference material, not the main content.}

---

## 3. FAILURE MODE ANALYSIS

{THIS IS THE CORE SECTION. Front and center.}

### 3.1 L1 Failure Distribution

{Brief intro: how failures were classified, sample size, caveats.}

Use the discovered taxonomy from `classifications.json["taxonomy"]` — these categories were found in the data, not predefined. Present them in a table:

| Failure Pattern | Count (%) | Layer | What Happens | Fix Strategy |
|----------------|-----------|-------|-------------|-------------|
| {Discovered pattern name} | {N (X%)} | {Layer} | {1-sentence behavioral description} | {Concrete intervention} |

### 3.2 Why These Failures Happen

{Deep analysis of the top 2-3 failure modes. For each, trace the reasoning chain: what information was available → what the model concluded → why that conclusion was wrong → what reasoning would have led to the correct approach.}

**{Task name}**: Both models saw {shared information}. {Passing model} inferred {correct conclusion} because {reasoning chain}. {Failing model} instead assumed {incorrect conclusion} because {reasoning chain} — it missed {specific signal} which was visible at step N in {file/output}.

{This level of "why" analysis is what makes the report actionable. "Agent edited the wrong file" is useless. "Agent saw the error mention postgresql.conf and jumped straight to editing it, without checking whether conf.d/ overrides exist — the include_dir directive was on line 3 of the file it opened" is useful.}

### 3.3 Addressability Spectrum

| Failure Mode | Fix Difficulty | Rate | Intervention |
|-------------|---------------|------|-------------|
| {Most fixable first} | Scaffolding change | {X%} | {Specific action} |

---

## 4. HEADROOM DEEP DIVE & ILLUSTRATIVE EXAMPLES

{Combine headroom analysis with the examples. Don't separate them — the examples ARE the headroom analysis.}

### 4.1 Where the Gap Lives

{Brief headroom table, then immediately into behavioral analysis.}

### 4.2 {Failure Mode}: {task-name}

| | {Failing Model} ({N}/{M} tests) | {Passing Model} ({M}/{M} tests) |
|---|---|---|
| **What it did** | {Specific description with step numbers and commands} | {Specific description} |
| **What it saw** | {What information was available at the decision point} | {Same or similar information} |
| **Why it chose that approach** | {The reasoning chain: what it concluded from the available info and why that was wrong} | {The reasoning chain: what it inferred differently and why that was correct} |

*{Italicized annotation: the specific reasoning gap — what signal was available but missed, and what intervention would close that gap.}*

### 4.3 {Failure Mode}: {task-name}

{Same format. 3-4 examples total, one per major failure category.}

---

## 5. PERFORMANCE CONTEXT

{This section provides supporting numbers. It is NOT the main event — sections 3-4 are.}

### 5.1 Overall Pass Rates

{Compact table + chart. Brief interpretation.}

### 5.2 Difficulty Scaling

{Compact table + chart. Focus on the insight: does the gap widen on harder tasks?}

### 5.3 Consistency

{Brief: how reliable is each model? What fraction of the gap is capability vs. reliability?}

---

## 6. RECOMMENDATIONS

| # | Failure Pattern | Concrete Intervention | Expected Impact |
|---|----------------|----------------------|-----------------|
| 1 | **{Pattern}**: {stat} | **{Specific implementable action}**: {detail} | {Quantified impact} |

**Rules for recommendations:**
- Every recommendation MUST be a concrete, implementable action
- NO "investigate", "study", "audit", "explore" — those are next steps, not recommendations
- Each must tie directly to a finding from §3 or §4
- Order by expected impact (highest first)
- Include quantified expected impact where possible

{1-2 sentence closing on deployment order.}
