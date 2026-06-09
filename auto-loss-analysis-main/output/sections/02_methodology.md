## 2. METHODOLOGY

This analysis examined 15 software engineering tasks evaluated across three models: Claude Haiku (60% pass rate), Claude Opus (73% pass rate), and Kimi K2.5 (100% pass rate). The dataset included 10 failures across 9 tasks (6 Haiku, 4 Opus, 0 Kimi).

**Analysis pipeline:**

1. **Statistics** — Computed ground truth pass rates, headroom distribution (both_pass, both_fail, mixed), and consistency patterns.

2. **Failure Classification** — Examined 10 failing trajectories to discover natural failure mode categories. For each trajectory, analyzed: what information the agent had available → what conclusion it drew → why that reasoning was wrong → what signals would have led to the correct approach.

3. **Solution Comparison** — Compared agent submissions against golden solutions to quantify overlap (0 = nothing correct, 1 = everything correct) and identify missing files/changes.

4. **Hypothesis Generation** — Formulated 10 testable hypotheses about why patterns existed, prioritizing high-impact questions on model divergence.

5. **Investigation** — Verified hypotheses by examining trajectories, test outputs, and code diffs. Answers were validated by a Critic agent for evidence quality and sample sufficiency.

6. **Synthesis** — Curated exemplary examples, synthesized findings into actionable insights, and validated claims against evidence before reporting.

**Sample scope:** With 10 failures total (small sample), findings are marked by confidence level. Claims with N < 5 examples are flagged as medium/low confidence even if consistent. All major findings are based on direct trajectory inspection, not statistical inference alone.

**Key distinction:** Failures are classified into reasoning-layer (agent had information but drew wrong conclusion) vs execution-layer (infrastructure or capability constraint prevented completion). This distinction guides interventions: reasoning failures are addressable through prompting; infrastructure failures require resource allocation.
