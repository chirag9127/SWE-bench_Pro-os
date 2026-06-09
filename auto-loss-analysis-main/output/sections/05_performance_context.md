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
