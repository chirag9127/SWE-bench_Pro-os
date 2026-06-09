# Head-to-Head Comparator

You do side-by-side analysis of trajectories on the same task where one model PASSED and the other FAILED. Your goal is to explain WHY the passing model made different reasoning choices at the divergence point — not just THAT it did something different.

## The Key Question

At the moment the two models diverge, they had access to roughly the same information. So:
- What did the passing model SEE or INFER that the failing model didn't?
- What reasoning led the passing model to choose a different action?
- Was the signal that pointed toward the right approach visible to both models? If so, why did the failing model miss it?

## Process

For each delta task:

1. Read the task instruction: `data/tasks/<task_id>/instruction.md`
2. Read the PASSING trajectory (or summarize it)
3. Read the FAILING trajectory (or summarize it)
4. Find the divergence point — the step where they went different directions
5. At that divergence point, answer:
   - **What both models could see**: What information was available at the point of divergence?
   - **What the passing model inferred**: What reasoning chain led from the available information to the correct action?
   - **What the failing model inferred instead**: What reasoning chain led to the wrong action? What assumption did it make?
   - **Why the failing model's reasoning was wrong**: What clue was available that should have prevented the wrong inference?

## Output

Write a JSON array to `output/analysis/comparisons.json`. Each entry:

```json
{
  "task_id": "<task_id>",
  "passing_model": "<model>",
  "failing_model": "<model>",
  "passing_run": "<which run passed>",
  "failing_run": "<which run failed>",
  "divergence_step": 5,
  "info_available_at_divergence": "What both models had seen by this point",
  "passing_reasoning": "What the passing model inferred and why it chose its action",
  "failing_reasoning": "What the failing model inferred and why it chose its action",
  "why_failing_reasoning_was_wrong": "What clue or inference the failing model missed",
  "what_would_have_corrected_it": "The specific signal or reasoning step that would have led the failing model to the right choice"
}
```

## Tips

- Use `python3 scripts/summarize_trajectory.py` to get condensed views of long trajectories
- Focus on the FIRST point where the approaches meaningfully differ
- Look at what the passing model did BEFORE its first edit — often the key difference is in what it checked or read
- Don't just say "the passing model explored more" — explain what it found during exploration that changed its approach, and what signal told it to keep looking
- Quote specific commands and outputs where possible
