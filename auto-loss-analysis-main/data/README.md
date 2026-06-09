# Prepared SWE-bench Pro Mini Run Data

This data directory was prepared from `runs/swepro-15task-mini-20260608`.

The source artifacts contain generation status and submitted patches, but not
verifier pass/fail rewards. `results.csv` and each `result/reward.txt` therefore
use a provisional proxy:

- `pass`: `exit_status == "Submitted"` and `has_diff == "True"`
- `fail`: any retry/error state, missing diff, or empty submitted diff

Use these results for trajectory/process loss analysis only. Replace
`results.csv` and `result/reward.txt` with verifier results before treating the
statistics as benchmark correctness.

Layout:

- `results.csv`: one row per task and one run column per model.
- `evals/<instance_id>/<model>/run-v1/trajectory.json`: copied trajectory.
- `evals/<instance_id>/<model>/run-v1/prediction.patch`: submitted patch.
- `evals/<instance_id>/<model>/run-v1/result/reward.txt`: provisional reward.
- `tasks/<instance_id>/instruction.md`: task prompt from local JSONL metadata.
- `tasks/<instance_id>/solution/gold.patch`: reference patch from local JSONL metadata.
