#!/usr/bin/env python3
"""Summarize a trajectory.json into a condensed text for LLM consumption.

Usage: python3 scripts/summarize_trajectory.py <trajectory.json> [--max-tokens 1500]

Outputs condensed summary to stdout.
"""

import argparse
import json
import sys


def summarize(traj_path, max_tokens=1500):
    with open(traj_path) as f:
        data = json.load(f)

    steps = data.get("steps", [])
    agent_info = data.get("agent", {})
    metrics = data.get("final_metrics", {})

    model = agent_info.get("model_name", "unknown")
    total_steps = len(steps)

    # Separate agent steps
    agent_steps = []
    for s in steps:
        if s.get("source") == "agent":
            obs_raw = s.get("observation", {})
            obs_text = ""
            if isinstance(obs_raw, dict):
                for r in obs_raw.get("results", []):
                    obs_text += r.get("content", "")[:500] + "\n"
            elif isinstance(obs_raw, str):
                obs_text = obs_raw[:500]

            commands = []
            for tc in s.get("tool_calls", []):
                args = tc.get("arguments", {})
                if isinstance(args, dict):
                    for key in ("keystrokes", "command", "cmd"):
                        if key in args:
                            commands.append(str(args[key]).strip()[:200])

            agent_steps.append({
                "step_id": s.get("step_id", "?"),
                "message": s.get("message", "")[:500],
                "commands": commands[:5],
                "observation": obs_text[:500],
            })

    # Select steps: first 2 + last 3
    if len(agent_steps) <= 5:
        selected = agent_steps
    else:
        selected = agent_steps[:2] + agent_steps[-3:]

    # Build summary
    lines = [
        f"Model: {model}",
        f"Total steps: {total_steps} ({len(agent_steps)} agent turns)",
        f"Tokens: {metrics.get('total_prompt_tokens', '?')} prompt, {metrics.get('total_completion_tokens', '?')} completion",
        f"Cost: ${metrics.get('total_cost_usd', '?')}",
        "",
    ]

    for i, s in enumerate(selected):
        if i == 2 and len(agent_steps) > 5:
            lines.append(f"  ... ({len(agent_steps) - 5} steps omitted) ...")
            lines.append("")

        lines.append(f"--- Agent Step {s['step_id']} ---")
        if s["message"]:
            lines.append(f"Reasoning: {s['message'][:300]}")
        if s["commands"]:
            lines.append("Commands:")
            for cmd in s["commands"]:
                lines.append(f"  $ {cmd}")
        if s["observation"]:
            lines.append(f"Output: {s['observation'][:300]}")
        lines.append("")

    print("\n".join(lines))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("trajectory", help="Path to trajectory.json")
    parser.add_argument("--max-tokens", type=int, default=1500)
    args = parser.parse_args()
    summarize(args.trajectory, args.max_tokens)
