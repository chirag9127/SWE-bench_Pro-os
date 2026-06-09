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
