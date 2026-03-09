#!/usr/bin/env python3
import json
import os
import re
import argparse
from math import comb
from collections import defaultdict
from typing import Any, Dict, List, Tuple

SKIP_SUFFIXES = ("_ERRORED", "_TIMEOUT", "_FAILED", "_OLD")

def is_successful(reward: float) -> bool:
    # TauBench uses reward 1.0 as success
    return (1 - 1e-6) <= reward <= (1 + 1e-6)

def should_skip_file(filename: str) -> bool:
    """
    Skip files whose *stem* ends with _ERRORED/_TIMEOUT/_FAILED/_OLD
    Examples:
      foo_ERRORED.json -> skip
      foo_TIMEOUT.json -> skip
      foo_FAILED.json -> skip
      foo_OLD.json -> skip
    """
    base = os.path.basename(filename)
    if not base.lower().endswith(".json"):
        return True
    stem = base[:-5]  # remove ".json"
    return any(stem.endswith(suf) for suf in SKIP_SUFFIXES)

def load_robust_json(filepath: str) -> List[Dict[str, Any]]:
    """
    Handles standard JSON and 'smashed' JSON caused by restarting jobs
    e.g. [...][...] -> merge into one list.
    """
    try:
        with open(filepath, "r") as f:
            content = f.read().strip()
    except Exception as e:
        print(f"  ⚠️  Read error: {filepath}: {e}")
        return []

    if not content:
        return []

    # 1) Standard JSON
    try:
        data = json.loads(content)
        return data if isinstance(data, list) else []
    except json.JSONDecodeError:
        pass

    # 2) Fix list collisions
    fixed = content.replace("][", ",")
    try:
        data = json.loads(fixed)
        return data if isinstance(data, list) else []
    except json.JSONDecodeError:
        print(f"  ⚠️  Could not parse JSON (skipping): {filepath}")
        return []

def normalize_results(raw: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Normalize entries: ensure task_id + reward exist; keep everything else.
    """
    out = []
    for r in raw:
        if not isinstance(r, dict):
            continue
        if "task_id" not in r or "reward" not in r:
            continue
        out.append(r)
    return out

def dedupe_latest_only(results: List[Dict[str, Any]], num_trials: int) -> List[Dict[str, Any]]:
    """
    Keep latest-only per task_id, capped to last num_trials runs.
    Assumes chronological order within each file and across loaded files
    (we load files in sorted order; later files are treated as newer).
    """
    tasks_map: Dict[int, List[Dict[str, Any]]] = defaultdict(list)
    for r in results:
        tasks_map[int(r["task_id"])].append(r)

    cleaned = []
    for t_id, runs in tasks_map.items():
        # keep last num_trials
        cleaned.extend(runs[-num_trials:])
    return cleaned

def calculate_pass_k(cleaned_results: List[Dict[str, Any]], num_trials: int) -> Tuple[float, Dict[int, float], int, int]:
    """
    Returns: avg_reward, pass@k dict, num_cleaned_runs, num_tasks
    """
    # Count successes per task
    c_per_task: Dict[int, int] = defaultdict(int)
    for r in cleaned_results:
        task_id = int(r["task_id"])
        c_per_task[task_id] += 1 if is_successful(float(r["reward"])) else 0

    num_tasks = len(c_per_task)
    if num_tasks == 0 or len(cleaned_results) == 0:
        return 0.0, {}, 0, 0

    pass_ks: Dict[int, float] = {}
    for k in range(1, num_trials + 1):
        s = 0.0
        for c in c_per_task.values():
            if c >= k:
                # comb(c,k)/comb(n,k) where n=num_trials
                s += comb(c, k) / comb(num_trials, k)
        pass_ks[k] = s / num_tasks

    avg_reward = sum(float(r["reward"]) for r in cleaned_results) / len(cleaned_results)
    return avg_reward, pass_ks, len(cleaned_results), num_tasks

def find_json_files(results_root: str, subdir: str | None) -> List[str]:
    """
    Collect json files from results_root (optionally within a subdir).
    """
    base = os.path.join(results_root, subdir) if subdir else results_root
    if not os.path.isdir(base):
        raise FileNotFoundError(f"Directory not found: {base}")

    files = []
    for root, _, fnames in os.walk(base):
        for fn in fnames:
            if fn.endswith(".json"):
                fp = os.path.join(root, fn)
                if not should_skip_file(fp):
                    files.append(fp)

    files.sort()  # stable ordering; later files treated as newer in dedupe
    return files

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--results-root",
        default="results",
        help="Path to your tau-bench-agent007/results directory (default: results)"
    )
    ap.add_argument(
        "--subdir",
        default=None,
        help="Optional: specific results subfolder (e.g., airline_act_agent_...). If omitted, scans all subfolders."
    )
    ap.add_argument(
        "--trials",
        type=int,
        default=5,
        help="Expected number of trials per task (default: 5)"
    )
    ap.add_argument(
        "--write-clean",
        default=None,
        help="Optional: path to write cleaned merged JSON (for debugging/auditing)"
    )
    args = ap.parse_args()

    files = find_json_files(args.results_root, args.subdir)

    print("=" * 80)
    print("TauBench Pass@k Compilation")
    print(f"Experiment Subdir : {args.subdir if args.subdir else 'ALL'}")
    print(f"Results Root      : {args.results_root}")
    print(f"Trials            : {args.trials}")

    print("-" * 80)

    print(f"Total {len(files)} json files (after skipping *_ERRORED/_TIMEOUT/_FAILED/_OLD)")

    all_results: List[Dict[str, Any]] = []
    for fp in files:
        data = normalize_results(load_robust_json(fp))
        all_results.extend(data)

    unique_tasks = len(set(int(r["task_id"]) for r in all_results))
    
    print(f"Found {len(all_results)} runs across {unique_tasks} unique task_ids")

    cleaned = dedupe_latest_only(all_results, args.trials)
    cleaned_tasks = len(set(int(r["task_id"]) for r in cleaned))
    
    avg_reward, pass_ks, clean_runs, num_tasks = calculate_pass_k(cleaned, args.trials)

    print(f"Compiling Average & Pass@k from {clean_runs} runs across {num_tasks} tasks")
    print("-" * 80)

    print(f"🏆 Average Reward: {avg_reward:.4f}")
    print("📈 Pass^k:")
    for k in range(1, args.trials + 1):
        if k in pass_ks:
            print(f"  k={k}: {pass_ks[k]:.4f}")

    print("-" * 80)

    if args.write_clean:
        os.makedirs(os.path.dirname(args.write_clean) or ".", exist_ok=True)
        with open(args.write_clean, "w") as f:
            json.dump(cleaned, f)
        print(f"\n🧾 Wrote cleaned merged JSON to: {args.write_clean}")

    print("=" * 80)

if __name__ == "__main__":
    main()
