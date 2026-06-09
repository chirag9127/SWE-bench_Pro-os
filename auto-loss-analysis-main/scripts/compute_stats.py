#!/usr/bin/env python3
"""Compute baseline statistics from results.csv → output/analysis/statistics.json

Usage: python3 scripts/compute_stats.py --data ./data --output ./output/analysis/statistics.json
"""

import argparse
import csv
import json
import os
from collections import defaultdict


def load_results(csv_path):
    with open(csv_path) as f:
        return list(csv.DictReader(f))


def compute(data_dir, output_path):
    csv_path = os.path.join(data_dir, "results.csv")
    rows = load_results(csv_path)

    # Extract models and runs from column headers
    # Format: task_id, opus_runv1, opus_runv2, opus_runv3, deepseek_runv1, ..., opus_pass_count, deepseek_pass_count
    if not rows:
        print("No data in results.csv")
        return

    # Detect models from column names
    sample = rows[0]
    models = set()
    for col in sample.keys():
        if col.endswith("_pass_count"):
            models.add(col.replace("_pass_count", ""))
    models = sorted(models)

    runs_per_model = {}
    for m in models:
        run_cols = [c for c in sample.keys() if c.startswith(f"{m}_runv")]
        runs_per_model[m] = sorted(run_cols)

    total_tasks = len(rows)

    # --- Per-model pass rates ---
    model_stats = {}
    for m in models:
        run_cols = runs_per_model[m]
        total_runs = 0
        total_pass = 0
        for row in rows:
            for rc in run_cols:
                val = row.get(rc, "")
                if val in ("pass", "fail"):
                    total_runs += 1
                    if val == "pass":
                        total_pass += 1

        pass_count_col = f"{m}_pass_count"
        tasks_with_any_pass = sum(1 for r in rows if int(r.get(pass_count_col, 0)) > 0)

        model_stats[m] = {
            "total_runs": total_runs,
            "total_pass": total_pass,
            "total_fail": total_runs - total_pass,
            "pass_rate": round(total_pass / total_runs, 4) if total_runs else 0,
            "tasks_with_any_pass": tasks_with_any_pass,
            "pass_at_1_approx": round(tasks_with_any_pass / total_tasks, 4),
        }

    # --- Headroom analysis ---
    headroom = {"both_pass": 0, "both_fail": 0}
    for m in models:
        headroom[f"{m}_only"] = 0

    per_task = {}
    for row in rows:
        task_id = row["task_id"]
        task_entry = {}
        model_passed = {}
        for m in models:
            pc = int(row.get(f"{m}_pass_count", 0))
            task_entry[m] = {
                "pass_count": pc,
                "runs": {rc: row.get(rc, "") for rc in runs_per_model[m]},
            }
            model_passed[m] = pc > 0

        # Classify headroom bucket
        all_pass = all(model_passed.values())
        none_pass = not any(model_passed.values())

        if all_pass:
            bucket = "both_pass"
        elif none_pass:
            bucket = "both_fail"
        else:
            winners = [m for m, p in model_passed.items() if p]
            if len(winners) == 1:
                bucket = f"{winners[0]}_only"
            else:
                bucket = "mixed"

        task_entry["headroom_bucket"] = bucket
        headroom[bucket] = headroom.get(bucket, 0) + 1
        per_task[task_id] = task_entry

    # --- Consistency analysis ---
    # How often does the model pass all runs vs some vs none?
    consistency = {}
    for m in models:
        n_runs = len(runs_per_model[m])
        dist = defaultdict(int)
        for row in rows:
            pc = int(row.get(f"{m}_pass_count", 0))
            dist[pc] += 1
        consistency[m] = {f"{k}_of_{n_runs}": v for k, v in sorted(dist.items())}

    # --- Task metadata stats (if task.toml available) ---
    tasks_dir = os.path.join(data_dir, "tasks")
    difficulty_dist = defaultdict(int)
    category_dist = defaultdict(int)
    difficulty_pass_rates = defaultdict(lambda: defaultdict(lambda: {"pass": 0, "total": 0}))
    category_pass_rates = defaultdict(lambda: defaultdict(lambda: {"pass": 0, "total": 0}))

    for row in rows:
        task_id = row["task_id"]
        toml_path = os.path.join(tasks_dir, task_id, "task.toml")
        difficulty = ""
        category = ""
        if os.path.exists(toml_path):
            try:
                import toml as toml_lib
                meta = toml_lib.load(toml_path).get("metadata", {})
                difficulty = meta.get("difficulty", "")
                category = meta.get("category", "")
            except Exception:
                pass

        if difficulty:
            difficulty_dist[difficulty] += 1
        if category:
            category_dist[category] += 1

        for m in models:
            for rc in runs_per_model[m]:
                val = row.get(rc, "")
                if val in ("pass", "fail"):
                    if difficulty:
                        difficulty_pass_rates[difficulty][m]["total"] += 1
                        if val == "pass":
                            difficulty_pass_rates[difficulty][m]["pass"] += 1
                    if category:
                        category_pass_rates[category][m]["total"] += 1
                        if val == "pass":
                            category_pass_rates[category][m]["pass"] += 1

    # Compute rates
    def rates_from_counts(counts_dict):
        result = {}
        for key, models_data in counts_dict.items():
            result[key] = {}
            for m, counts in models_data.items():
                t = counts["total"]
                p = counts["pass"]
                result[key][m] = {
                    "pass": p, "total": t,
                    "pass_rate": round(p / t, 4) if t else 0,
                }
        return result

    stats = {
        "total_tasks": total_tasks,
        "models": models,
        "model_stats": model_stats,
        "headroom": headroom,
        "consistency": consistency,
        "difficulty_distribution": dict(difficulty_dist),
        "category_distribution": dict(category_dist),
        "by_difficulty": rates_from_counts(difficulty_pass_rates),
        "by_category": rates_from_counts(category_pass_rates),
    }

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(stats, f, indent=2)

    # Print summary
    print(f"Dataset: {total_tasks} tasks, {len(models)} models")
    for m in models:
        s = model_stats[m]
        print(f"  {m}: {s['pass_rate']*100:.1f}% pass rate ({s['total_pass']}/{s['total_runs']})")
    print(f"Headroom: {json.dumps(headroom)}")
    print(f"Written to {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="./data")
    parser.add_argument("--output", default="./output/analysis/statistics.json")
    args = parser.parse_args()
    compute(args.data, args.output)
