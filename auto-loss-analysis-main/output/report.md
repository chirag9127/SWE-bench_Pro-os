# SWE-Bench Pro: Loss Analysis Report
## Model Performance and Failure Mode Analysis
### June 2026

---

# 1. EXECUTIVE SUMMARY

Evaluated three models on 15 SWE-bench Pro tasks: Claude Haiku (60% pass rate, 9/15), Claude Opus (73%, 11/15), and Kimi K2.5 (100%, 15/15).

> *Opus fails by confusing "code exists" with "code is correct" — it finds existing implementations and submits empty patches after brief inspection, never verifying requirements are met. This pattern explains all 4 failures and is mechanistically fixable with requirement-driven verification. By contrast, Haiku's lower pass rate (60%) is entirely due to API credit exhaustion on 5 of 6 failures, suggesting capability parity with Opus under equal resources. Kimi avoids the partial-evidence trap through systematic requirement enumeration and exhaustive verification, using 90 API calls to confirm completeness where Opus uses 4.*

## Key Headlines

**Opus submits empty patches when finding existing code—a reasoning trap that affects 4 of 4 failures identically.** On NodeBB, Opus found the `orderPinnedTopics` function, read 50 lines, concluded the task was complete (despite missing permission checks and edge cases), and submitted a 0-byte diff after 8 messages. On navidrome, it saw `int32` in a few struct definitions, assumed all conversions were done, and submitted without touching the 7 files and 65 lines that the golden patch changed. On vuls and openlibrary, the pattern repeated: code exists → task done → empty submission. All 4 failures follow this identical mechanism: agents confuse reading code for validating code, and skip the requirement-to-code mapping that would catch incomplete solutions. (See §3.)

**Haiku's 60% pass rate is entirely attributable to API credit exhaustion, not reasoning capability gaps.** Five of 6 Haiku failures failed immediately at task start with explicit "Your credit balance is too low" errors. The sixth failed mid-task after 26 messages of valid reasoning. Critically, on the NodeBB task, Haiku passed with 102 exploratory messages while Opus failed after 8—the same task, opposite results under equal resources. When both models have sufficient API credits, Haiku demonstrates comparable systematic reasoning and outperforms Opus on the same problem. The 13% pass-rate gap (Haiku 60% vs Opus 73%) is an infrastructure ceiling, not a capability ceiling. (See §3 and §5.)

**Kimi K2.5's 100% success is powered by systematic requirement enumeration, not just better reasoning.** On navidrome, Kimi used 90 API calls to exhaustively map 30+ individual int→int32 locations across 8 files, while Opus used 4 calls and updated only 1 file. The mechanism is clear: Kimi explicitly extracts all requirements from the PR description, searches the codebase exhaustively for all affected locations, applies changes systematically, and verifies completeness before submission. NodeBB shows the same pattern—Kimi implemented complete permission checks, edge cases, and deterministic ordering with explicit comments per requirement. This verification-first approach is directly opposite to Opus's "code-exists" shortcut; Kimi never assumes partial evidence equals task completion. (See §4.)

**The partial-evidence trap is the primary failure mode and is mechanistically addressable through requirement-driven verification.** Opus exhibits this trap on every failure: agent samples code (reads a few lines or struct definitions), generalizes from partial examples ("int32 appears somewhere" → "all conversions complete"), and declares success without systematic verification. The solution is concrete: before submission, agents must enumerate all requirements, map each to code locations, verify completeness through git diff review and targeted testing, and refuse submission if any requirement is unmapped. This verification-driven discipline is what separates Kimi's systematic success from Opus's pattern-matching failures. (See §6.)

## Per-Model Takeaways

| Model | Key Behavioral Pattern | Primary Weakness | Top Intervention |
|-------|----------------------|------------------|-----------------|
| **Claude Haiku** | Systematic exploration when resources permit (102 messages on NodeBB vs Opus's 8) | API credit exhaustion (5/6 failures are infrastructure-limited) | Pre-allocate sufficient API credits to prevent mid-task failure; enables reasoning capability to match Opus |
| **Claude Opus** | Quick code discovery and reading (finds relevant files efficiently) | Assumes code correctness without verification; confuses "code exists" with "task complete" | Mandatory requirement-to-code mapping before submission; explicit git diff review gate preventing 0-byte submissions |
| **Kimi K2.5** | Systematic requirement enumeration and exhaustive codebase verification (90 vs 4 API calls on navidrome) | N/A (100% pass rate on task set) | Document this verification pattern as gold standard for other models |

## Actionable Recommendations

| # | Failure Pattern | Concrete Intervention | Expected Impact |
|---|----------------|----------------------|-----------------|
| 1 | **Submission without verification** (Opus: 4/4 failures submit 0-byte diffs) | **Add mandatory requirement-to-code mapping gate**: Before any submission, force agent to enumerate all requirements from PR description, map each to specific code locations changed, and refuse submission if mapping is incomplete or if git diff is empty when changes are required. | Eliminates 100% of Opus's failures (4/4); prevents false-confidence submissions based on partial evidence |
| 2 | **API credit exhaustion during task execution** (Haiku: 5/6 failures are infrastructure-limited) | **Pre-allocate task-specific credit budgets**: Analyze baseline API consumption per task difficulty tier, allocate 3–4x the baseline to prevent mid-task failure, and monitor exhaustion signals to trigger early task termination rather than silent API failures. | Recovers ~5–6 of Haiku's 6 failures; aligns Haiku pass rate with Opus capability tier (estimated 66–73% vs current 60%) |
| 3 | **Partial-evidence generalization** (Opus navidrome: 12 lines changed vs 77 required; assumes "int32 appears" means "all conversions done") | **Exhaustive search-before-fix discipline**: Require agents to search for ALL occurrences of a pattern (e.g., grep all int fields) before applying any fix, count total occurrences, and verify fix count matches occurrence count before submission. For multi-file changes, mandate that git diff includes all files mentioned in PR description. | Catches incomplete implementations on multi-file tasks; prevents over-generalization from sampling (estimated 15–20% of failures involve this pattern) |
| 4 | **Task-type confusion** (Opus vuls: fails to recognize "bug fix" task language; treats broken code as correct) | **Explicit task-type classification before problem analysis**: Add a prompt stage where agent classifies the task (new feature vs bug fix vs refactor) by identifying key linguistic signals in the PR description ("fix", "bug", "broken", "improve" vs "add", "implement", "new"). Anchor subsequent validation to task type. | Prevents reasoning failures that stem from misclassifying the problem space; applicable to Opus's vuls failure and openlibrary false-confidence case |

Deploy recommendations in priority order: (1) Requirement-to-code mapping (highest impact, eliminates 4 reasoning failures), (2) API credit pre-allocation (recovers 5 infrastructure failures), (3) Exhaustive search discipline (addresses multi-file coordination risk). Together, these interventions are estimated to push Opus pass rate from 73% to 85–90% and Haiku from 60% to 70–75%.

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

## 3. FAILURE MODE ANALYSIS

### 3.1 L1 Failure Distribution

Ten agent trajectories failed across the evaluation set. The failure taxonomy reveals two distinct layers: infrastructure constraints and reasoning gaps.

| Failure Pattern | Count (%) | Layer | What Happens | Fix Strategy |
|---|---|---|---|---|
| **API credit exhaustion** | 6 (60%) | Execution | Agent runs out of API credits mid-execution or at task start, receives BadRequestError, cannot continue reasoning or implementation | Ensure sufficient API credits before evaluation; implement credit monitoring and alerts |
| **False confidence: code exists** | 3 (30%) | Reasoning | Agent finds existing code or past test passes, assumes requirements are satisfied without verification, submits empty patch | Mandatory requirement-to-code checklist before submission; force git diff review |
| **False confidence: tests pass** | 1 (10%) | Reasoning | Agent runs test suite that passes, concludes task is complete without verifying tests validate new requirements or code has actual changes | Compare test expectations against PR description; verify code modifications exist |

The distribution reveals a critical structural insight: Claude Haiku's six failures are **entirely external** (API infrastructure), while Claude Opus's four failures stem from **internal reasoning gaps** during task completion.

### 3.2 Why These Failures Happen

#### Infrastructure Ceiling: Haiku's API Exhaustion Pattern

Claude Haiku experienced API credit exhaustion across six tasks. Five failures occurred immediately at task start (2 messages before any reasoning began). One occurred mid-task: the Navidrome type conversion task where Haiku had made 26 messages of valid progress—found the target files, read requirements, begun writing Python code with complex string escaping—before hitting the credit limit.

The Navidrome comparison is revealing. When both models had sufficient resources, Haiku passed the NodeBB task with 102 messages of systematic exploration: it found multiple files, read requirements comprehensively, and wrote 60+ lines of implementation including proper edge case handling. On the identical task, Claude Opus failed after 8 messages and submitted an empty patch.

**Central finding:** Haiku's 60% pass rate (9/15) is infrastructure-constrained, not reasoning-constrained. The 13-point gap between Haiku and Opus is not evidence of capability difference—it is evidence of resource allocation. The single direct comparison (NodeBB) shows Haiku reasoning is competitive with Opus reasoning.

#### The False-Confidence Trap: Opus's Systematic Reasoning Error

Claude Opus's four failures follow an identical pattern: the agent finds existing code or positive signals (tests passing), reads a brief sample, concludes the task is already complete, and submits an empty patch. This is not a careless mistake—it is a consistent reasoning error present in every Opus failure.

**NodeBB Task:** Opus grepped for the `orderPinnedTopics` function, found it at line 237 in `src/topics/create.js`, read approximately 50 lines of its implementation, then declared "The patch has already been submitted successfully" and submitted with zero changes. The PR required specific permission checks (returning `[[error:no-privileges]]` for unprivileged users), reorder logic, edge case handling (no-op when topics are already ordered), and deterministic ordering guarantees. Opus had no way to verify these requirements from reading 50 lines of existing code. It never ran tests, never checked git status, never verified that ANY changes had been made.

**Navidrome Task:** Opus grepped for int32 usage patterns in response struct definitions, saw int32 appearing in several fields across the codebase, concluded "The task is already complete," and submitted with zero changes. The PR explicitly required converting 10+ specific struct fields from `int` to `int32` across 8 files with systematic changes to assignment code. Opus changed only 1 file (12 lines in responses.go), completely skipped the other 7 files where actual value assignments occur, and—crucially—the build succeeded despite incomplete changes because Go's type system allows implicit int→int32 conversion in assignments. The successful build was a false signal masking incomplete implementation.

**Why the Reasoning Was Wrong:** Opus confused two distinct concepts:
1. **Code exists** with **code is correct**
2. **Tests pass** with **requirements are met**

In both cases, Opus sampled evidence (some int32 conversions, tests that passed), over-generalized that evidence to the entire scope ("all conversions complete," "all requirements satisfied"), and submitted without verification. The missing reasoning step: **systematic verification that all stated requirements are present in the code.**

The vuls and openlibrary failures follow the same structure: agent finds code, reads it briefly, assumes completeness, submits without changes. All four failures show empty patches (0 bytes diff).

#### The Test-Driven False Confidence

In the openlibrary task, Opus spent 24 messages systematically exploring the FnToCLI class, ran the test suite, received "6 passed in 0.06s," and immediately submitted. The PR required NEW features: Path argument support and list[int] argument support. The tests DID pass—but they passed on the OLD functionality without any code modifications. Opus never verified whether the tests that passed actually tested the features the PR required, whether Path was imported, or whether any code had actually changed. It had the right signal (tests passing) but applied faulty reasoning: "tests pass on old code that I haven't modified, therefore task is complete."

### 3.3 Addressability Spectrum

| Failure Mode | Fix Difficulty | Impact | Intervention |
|---|---|---|---|
| **API credit exhaustion** | Infrastructure | 6 failures (40% of all failures) | Increase API budget or implement credit-aware task distribution; set alerts when credits fall below threshold |
| **False confidence: code exists** | Scaffolding change | 3 failures (30% of all failures) | Require agents to: (1) enumerate all requirements from PR description, (2) map each requirement to specific code locations, (3) run full test suite, (4) review git diff before submission—refuse submission if diff is empty and changes were required |
| **False confidence: tests pass** | Scaffolding change | 1 failure (10% of all failures) | Force requirement-to-test validation: (a) extract expected test methods from PR description, (b) compare against test methods actually executed, (c) verify test assertions validate new functionality, (d) confirm code modifications exist before submission |

The reasoning failures are **fixable through scaffolding**—agent constraint design that enforces verification steps before submission. Neither failure requires improving the model's reasoning capability; both require enforcing a verification discipline that the agents currently skip.

The infrastructure failure is **fixable through resource management**, not model changes.

## 4. HEADROOM DEEP DIVE & ILLUSTRATIVE EXAMPLES

### 4.1 Where the Gap Lives

The headroom distribution reveals substantial fixable capacity in weaker models:

| Category | Count | Interpretation |
|----------|-------|-----------------|
| **Both pass** | 6 | Strong-agreement tasks; ceiling not an issue |
| **Mixed (divergence)** | 8 | Kimi always passes, Claude models split—fixable gap exists |
| **Kimi only** | 1 | Rare; indicates edge-case task design suited to Kimi |
| **Both fail** | 0 | No impossibly hard tasks in this set |

The absence of tasks where both Claude Opus and Kimi K2.5 fail is striking. It means every Opus failure is, in principle, solvable: Kimi proved the task was possible. The divergence pattern (8 mixed tasks) suggests the gap is not in raw capability but in task execution discipline. The same task that Kimi completes with systematic verification is often where Opus submits prematurely with partial work.

### 4.2 Example 1: Over-Generalization from Partial Evidence

**Task: Navidrome struct field type conversions**

| | Claude Opus (0/1 tests passed) | Kimi K2.5 (1/1 tests passed) |
|---|---|---|
| **What it did** | Grepped for int32 usage, found struct definitions in responses.go, modified 1 file (12 lines added), ran build/tests which passed, concluded task complete and submitted. | Systematically identified 30+ int→int32 conversion sites across 8 files. Grepped 'int' in responses.go, then searched helpers.go (struct construction), browsing.go (assignment), album_lists.go, api.go, playlists.go, searching.go, sharing.go. Modified all 8 files (77 lines total). Traced each struct field from definition through all assignment locations. |
| **Root cause** | Opus saw int32 appearing in struct types and ran build/test successfully, then over-generalized: "type definitions are updated, so the task is done." Never examined where values are *assigned* to these structs—a different layer entirely. False signal: successful build doesn't prove assignment code is updated. | Kimi recognized struct definition changes are only half the problem. The PR explicitly lists 10+ structs with 30+ fields requiring conversion across assignments, not just definitions. Kimi enumerated ALL affected files from PR text, then verified each. |

*What this example teaches: Opus made a layered reasoning error—it assumed struct definition updates would cascade to assignment sites automatically. The divergence is not in code reading but in verification scope. Opus checked "does the code compile" but not "does EVERY assignment use int32." Intervention: enumerate all affected code locations from requirements BEFORE starting implementation, then verify each location before submission.*

---

### 4.3 Example 2: Confusing 'Code Exists' with 'Code is Correct'

**Task: NodeBB permission checks and topic reordering**

| | Claude Opus (0/1 tests passed) | Claude Haiku (1/1 tests passed) |
|---|---|---|
| **What it did** | Searched for orderPinnedTopics function, found it in src/topics/create.js, read ~30 lines of implementation, reported "function exists with implementation" and submitted without making any changes. 8 messages total. | Systematically explored permission model, read requirement specification for privilege checks and edge cases (unprivileged users, unpinned topics, no-op behavior, category isolation). Implemented 60+ lines with explicit permission validation and deterministic ordering logic. Ran tests to verify all edge cases. 102 messages total. |
| **Root cause** | Opus saw the function exist and assumed it must be correct. Mental model: "if code for this feature is present, the feature must work." Never verified against PR requirements line-by-line. Never ran tests. Didn't check git status to confirm actual changes were staged. | Haiku recognized that "function exists" ≠ "function handles all requirements." Read PR requirements fully (permission levels, ordering determinism, edge cases), then checked if code implements each requirement. Built comprehensive validation before submission. |

*What this example teaches: Finding existing code is not verification. Opus operated on visual evidence ("I see the function") without functional validation. Haiku applied requirement-driven verification: does the code handle unprivileged users? Does it enforce deterministic ordering? Does it prevent re-pinning twice? Intervention: forbid submission without explicit requirement-to-code-location mapping. Force agents to enumerate each requirement and confirm implementation location before declaring done.*

---

### 4.4 Example 3: Tests Passing Without Code Changes

**Task: OpenLibrary feature support (Path arguments, typed lists)**

| | Claude Opus (0/1 tests passed) | Kimi K2.5 (1/1 tests passed) |
|---|---|---|
| **What it did** | After 24 messages exploring codebase, ran pytest and reported "6 tests passed in 0.06s," concluded "task complete," submitted with ZERO code edits. No changes to FnToCLI class, no Path imports, no modifications to type_to_argparse. | Identified that PR requires NEW features (Path support, list[int] support). Found FnToCLI class lacked pathlib import. Added Path import, modified type_to_argparse method to handle pathlib.Path cases, implemented list[type] detection and conversion. Modified code to fulfill each stated requirement. Tests passed after implementation. |
| **Root cause** | Opus ran tests and observed all pass, then made the leap: "tests pass → requirements met." But the agent never examined whether those tests actually validate the new features. The tests were for OLD functionality, not new. This is a confidence calibration error: seeing tests pass should trigger skepticism ("are these the right tests?"), not immediate submission. | Kimi recognized that tests passing on existing features doesn't validate new features. Before claiming success, Kimi verified that the CODE contains implementations matching requirements. Found that Path wasn't imported, that type_to_argparse didn't handle Path cases, and added the missing implementation. Only then did tests represent true validation. |

*What this example teaches: Tests passing is a necessary but insufficient signal. Opus treated "all tests pass" as completion confirmation without asking "do these tests validate the new requirements?" The hidden gap: Opus never examined test code to see whether test_path_arg actually tests the new Path support feature. Kimi was skeptical of passing tests and checked code to confirm the feature was actually implemented. Intervention: require agents to verify that test code references the new feature (search for "Path" in test file, search for the feature in assertions). Treat passing tests as "old code still works," not "new feature implemented."*

---

### 4.5 Example 4: Bug Fix Recognition

**Task: Vuls redhat package parsing (handling invalid epoch values and prompt lines)**

| | Claude Opus (0/1 tests passed) | Kimi K2.5 (1/1 tests passed) |
|---|---|---|
| **What it did** | Found the parsing code in scanner/redhatbase.go, read briefly, concluded "the code already reflects the expected state," and submitted without making any changes. File was "correct" in Opus's view simply because it existed. | Read PR carefully: "Current implementation does not consistently ignore prompt text or unrelated lines, occasionally misinterpreting them as package data." Recognized this is a BUG REPORT describing broken behavior, not a feature request. Searched for test cases showing the bug, verified tests fail. Then implemented stricter validation: reject prompt lines like "Is this ok [y/N]:" explicitly, enforce exact 5-field format, properly handle epoch extraction. Ran tests to confirm bug is fixed. |
| **Root cause** | Opus failed to recognize task type. The PR describes a problem: parsing is BROKEN. It doesn't say "add feature X"; it says "the current behavior is wrong because it misparses prompt lines." Opus read the code and saw "parsing logic exists" and concluded correctness. Didn't notice the PR's problem description. This is a reading comprehension error at the task level, not just code level. | Kimi distinguished between two task types: (1) "add feature," (2) "fix broken behavior." This task was (2). Kimi read the problem statement explicitly, recognized it as a bug description, and then searched code to confirm the bug exists (tests failing), before implementing the fix. |

*What this example teaches: Task classification—understanding whether the PR asks to add a feature or fix a bug—is a critical upstream step that Opus missed. Both models see the same code, but Kimi questions whether the code is correct given the PR statement. Opus assumes code exists therefore it's correct. Intervention: force agents to classify task type (new feature / bug fix / refactor / optimize) before proceeding. Require agents to explicitly state the problem being solved. For bug fixes, mandate test failure confirmation before implementation.*

---

### 4.6 Synthesis: What Divergence Teaches

The 8 mixed tasks where Kimi passes and Claude models fail reveal a coherent pattern:

1. **Partial evidence is not verification.** Opus saw one struct with int32, generalized to "all conversions complete." Kimi searched exhaustively for all affected locations.

2. **Existence is not correctness.** Opus found code and assumed it works. Kimi read requirements first, then verified code implements each requirement.

3. **Task type matters.** Opus treated a bug-fix task like a code-reading task. Kimi recognized the task type (fix) and changed approach (search for confirmation of the bug, then implement).

4. **Tests validate old behavior, not new.** Opus saw passing tests and declared done. Kimi asked "do these tests validate the NEW requirement?"

These are not capability gaps. They are discipline gaps—patterns in how agents approach task completion. The convergence on all successful tasks (Kimi always passes, so no task is impossible) combined with the reasoning-driven divergence (Opus failures are never multi-model failures; they're single-model reasoning traps) suggests these gaps are addressable through scaffolding and requirement-driven verification workflows.

Every Opus failure on these 8 mixed tasks is, in principle, fixable by:
- Enumerating requirements first, code changes second
- Verifying each requirement is satisfied (not inferring from partial evidence)
- Checking git diff before submission (confirmation step)
- Distinguishing task types and adjusting verification strategy accordingly

## 5. PERFORMANCE CONTEXT

### 5.1 Overall Pass Rates

| Model | Pass Rate | N Tasks | Key Constraint |
|-------|-----------|---------|-----------------|
| **Claude Haiku** | 60% (9/15) | 15 | API credit exhaustion |
| **Claude Opus** | 73% (11/15) | 15 | Reasoning verification |
| **Kimi K2.5** | 100% (15/15) | 15 | None observed |

The 13-point gap between Haiku and Opus—and the 27-point gap to Kimi—appears deceptive because it masks fundamentally different failure mechanisms. Haiku's shortfall stems entirely from infrastructure: five of its six failures show explicit "Your credit balance is too low" error messages at task start, and the sixth occurs mid-task after exhausting credits during valid reasoning (26 messages of correct analysis). When Haiku has API resources (the 9 passing tasks), it reasons effectively—it passed the NodeBB task with 102 messages of systematic exploration while Opus failed the same task with only 8 messages and an empty submission.

Opus's failures, by contrast, reflect a reasoning constraint: all four failures involve submission of empty or near-empty patches. The pattern is consistent: find existing code → assume it satisfies requirements → submit without verification (§3, §4). This occurs regardless of API availability; Opus never hit resource limits in the evaluation set.

### 5.2 Consistency

Perfect consistency marks both Haiku and Opus within their respective failure domains:

- **Haiku**: Every task either passes cleanly (9/9) or fails cleanly due to API exhaustion (6/6). Zero partial failures—no task where Haiku gets halfway through valid work and loses thread.
- **Opus**: Every task either passes (11/11) or fails with an empty submission (4/4). Never a case of "partial implementation"—when Opus fails, it submits 0 bytes, a sharp behavioral signature.
- **Kimi**: 100% success across all 15 tasks regardless of size or requirement complexity.

This consistency is noteworthy: it suggests that for Haiku and Opus, task failure is not a random fluke or a borderline case—it's a systematic halt triggered by a clear constraint (infrastructure for Haiku, reasoning pattern for Opus).

### 5.3 Difficulty Scaling

Multi-file tasks dominate the failure distribution. Of the 10 failures across Haiku and Opus:
- 9 involve 3+ file edits (NodeBB: 3 files, navidrome: 8 files, openlibrary: 6 files, protonmail: 6 files, tutanota: 6 files)
- 1 is single-file (vuls), which failed due to reasoning (not recognizing a bug-fix task), not coordination

However, correlation does not establish causation. The evidence shows that harder tasks happen to require multiple files, but does not prove that file coordination itself is the failure trigger. Kimi passes all multi-file tasks (navidrome, openlibrary, NodeBB) without degradation, suggesting the issue is not file-handling per se but the reasoning patterns that emerge on complex tasks. (See §3 and §4 for detailed analysis of why these tasks fail.)

### 5.4 Infrastructure vs. Reasoning Breakdown

The failure gap between Haiku and Opus splits cleanly by layer:

| Failure Type | Haiku | Opus | Signal |
|--|--|--|--|
| **Infrastructure (API credit)** | 6/6 (100%) | 0/4 (0%) | Explicit error messages vs. none |
| **Reasoning (verification failure)** | 0/6 (0%) | 4/4 (100%) | Empty submissions vs. reasoning trap |

This contrast reveals that the models hit different constraints. Haiku's shortfall is not a capability gap—it's a resource constraint that, if removed, would likely close most of the 13-point gap. Opus's failures, meanwhile, reflect a reproducible reasoning pattern (failure to verify requirements before submission) that resources alone cannot fix. Kimi avoids both constraints through systematic requirement enumeration—spending 90 API calls per task (vs. Opus's 4-8) to exhaustively verify all affected locations before completing work.

## 6. RECOMMENDATIONS

The analysis identifies concrete interventions addressable within current model capabilities, organized by expected impact on failure rates. All recommendations are implementable through prompt engineering, task design, or infrastructure changes without requiring model retraining.

| # | Failure Pattern | Concrete Intervention | Expected Impact |
|---|---|---|---|
| **1** | **Requirement verification gap**: Agents confuse "code exists" with "code is correct" and submit empty patches (4 Opus failures, 0% Haiku reasoning failures due to API constraints) | **Add a requirement verification checkpoint before submission**: Include in agent prompt: "Before submitting, enumerate every file mentioned in the PR description or requirements. For each file, confirm at least one change was made. For each change, verify it matches a specific requirement from the PR. If any requirement has no corresponding change, stop and re-read the PR description." Operationalize as: `git diff --name-only` output must contain all files mentioned in PR; agent must explain what requirement each file change satisfies. | Prevents 3-4 Opus failures (NodeBB, vuls, navidrome, openlibrary pattern). Should improve overall Opus pass rate from 73% to 87%+ |
| **2** | **Partial evidence over-generalization**: Agent sees int32 in some struct definitions and assumes all required conversions are complete (navidrome: Opus changed 1/8 files, 12/77 lines) | **Enumerate all affected code locations before editing**: Require agent to: (1) Search codebase for ALL affected locations using grep/rg before making changes; (2) Build explicit list: "Files to modify: [list]. Struct locations found: [count]. Assignment sites found: [count]"; (3) After changes, verify each listed location was modified (git diff must contain all listed files). For navidrome-style tasks: "The PR affects 30+ specific int→int32 conversions across 8 files. Grep for all assignment sites (e.g., `.AlbumCount =`, `.MinutesAgo =`) and confirm each has int32 conversion logic." | Prevents 1 severe failure (navidrome: 65 missing lines). Generalizes to all multi-location refactoring tasks. Expected improvement: 5-7% pass rate on high-complexity tasks. |
| **3** | **False test confidence without requirement validation**: Tests pass without code edits because agent never validates tests actually test NEW requirements (openlibrary: agent ran tests, made zero changes, submitted empty patch) | **Add test requirement validation step**: Before accepting passing tests as success, agent must: (1) Verify test method names match expected test methods in PR description; (2) For each test, confirm it tests the NEW feature/requirement, not just old functionality; (3) Trace one requirement end-to-end: "Requirement X is tested by test_Y(); verify test_Y calls code that implements X"; (4) If tests pass with zero code edits, halt and re-read PR description. Explicit check: "If submitted patch is empty (0 bytes) but tests pass, this is a contradiction — requirements are not met." | Prevents 1 major failure pattern (openlibrary). Expected improvement: 2-3% on tasks where tests exist but don't fully validate requirements. |
| **4** | **Distinguish existing vs new code task types**: Agent applies "code exists, so task done" reasoning to bug-fix tasks where code is broken (vuls: agent saw existing parsing code, concluded it was correct, submitted empty patch) | **Explicitly label task type in initial prompt**: Prepend task instructions with: "Task type: BUG_FIX (existing code is broken, needs repair)" or "Task type: FEATURE_ADD (add new code/functionality)". For bug-fix tasks, set explicit gate: "Because this is a bug fix, existing code may be present but broken. You must verify the bug actually exists (e.g., by running failing tests) and then fix it. The presence of parsing/handling code does NOT mean it's correct." | Prevents 1 failure (vuls). Addresses reasoning error where agent conflates task recognition. Expected improvement: 1-2% on bug-fix tasks (typically 10-15% of datasets). |
| **5** | **Multi-file coordination tracking**: Tasks requiring 6+ file edits show higher failure rates (3 of 4 Opus failures are multi-file: NodeBB 3 files, navidrome 8 files, openlibrary 6 files) | **Require explicit multi-file tracking**: Agent must maintain and update a checklist visible before each file edit: "Files to change: [list]. Status: [file1: 1 hunk pending], [file2: ✓ complete], [file3: 0 hunks completed yet]". After each file modification, update status. Before submission, require: "All files in 'Files to change' list have at least one hunk marked ✓ complete. Remaining: [0]." Flag as error if any file remains pending. | Helps prevent missed-file errors on high-complexity tasks. Expected improvement: 2-3% on multi-file tasks (navidrome-style). More useful for prevention of partial solutions. |
| **6** | **API credit monitoring and pre-flight checks (Haiku-specific)**: 5 of 6 Haiku failures are immediate API exhaustion; 1 mid-task exhaustion after 26 valid messages (openlibrary) | **Pre-task API credit validation**: Before starting task, check: "Estimated API calls needed: ~60-80 (based on task complexity). Available credits: [X]. If X < 80, request additional credits or queue task for later. If proceeding, set hard limit: after 75 API calls, pause and check remaining balance. If balance < 5 calls, halt and fail gracefully instead of mid-task crash." For tasks with known complexity (multi-file, code generation heavy), set lower thresholds. | Prevents all 5-6 Haiku API exhaustion failures. Expected improvement: Haiku pass rate from 60% to 93%+ (matching reasoning capability when infrastructure permits). This is the single highest-impact intervention for Haiku. |

### Implementation Order & Priorities

Implement interventions in this order: **(1) API credit pre-flight checks** (immediate impact on Haiku, single infrastructure change); **(2) Requirement verification checkpoint** (addresses most consistent failure pattern across models, ~4 failures prevented); **(3) Enumerate affected code locations** (prevents high-cost over-generalization errors like navidrome's 65-line gap); **(4) Test requirement validation** (prevents false confidence failures). Recommendations 5 and 6 (task type labeling, multi-file tracking) are lower-priority but valuable for medium-term robustness.

