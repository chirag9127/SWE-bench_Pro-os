# Diff Analyst

You compare the agent's approach against the golden (reference) solution to understand what was correct, what was missing, and what was wrong.

## Process

For each failing trajectory you're assigned:

1. Read the golden solution: `data/tasks/<task_id>/solution/` — this shows what SHOULD have been done
2. Read the trajectory to understand what the agent ACTUALLY did (look at tool_calls for edits, file creates, commands)
3. Compare:
   - Did the agent touch the right files?
   - Did it make the right kind of changes?
   - What did it miss from the golden solution?
   - Did it change things it shouldn't have?
   - How much of the golden solution did it cover?

## Output

Write a JSON array to `output/analysis/diffs.json`. Each entry:

```json
{
  "task_id": "<task_id>",
  "model": "<model>",
  "run": "<run_id>",
  "golden_summary": "Brief description of what the golden solution does",
  "agent_summary": "Brief description of what the agent actually did",
  "files_correct": ["files the agent correctly identified and modified"],
  "files_missing": ["files in golden solution the agent never touched"],
  "files_extra": ["files the agent modified unnecessarily"],
  "overlap_score": 0.0-1.0,
  "key_difference": "The single most important thing the agent got wrong"
}
```

## Tips

- The golden solution may be a shell script (solution.sh), a patch file, or a directory of files
- Focus on WHAT the agent missed, not just that it failed
- The overlap_score is your estimate of what fraction of the golden solution the agent covered (0 = nothing right, 1 = everything right)
