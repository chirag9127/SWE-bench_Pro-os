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
