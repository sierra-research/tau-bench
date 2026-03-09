#!/usr/bin/env python3
import os
import re
import glob
import pandas as pd

LOG_DIR = "logs"
DOMAINS = ["airline", "retail"]   # add more if you have: ["airline","retail","hotel",...]
KS = [1, 2, 3, 4, 5]              # adjust if you print more k's

# --- regex for metrics inside taubench log ---
avg_reward_re = re.compile(r"Average reward:\s*([0-9]*\.?[0-9]+)")
passk_re = re.compile(r"k\s*=\s*(\d+)\s*:\s*([0-9]*\.?[0-9]+)")

def parse_baseline_from_filename(fname: str):
    """
    Example filenames you showed:
      46631809_airline_act_2.log
      46647041_retail_tool-calling_2.log
    Returns: (jobid, domain, baseline_label)
    """
    base = os.path.basename(fname)
    m = re.match(r"^(\d+)_([a-zA-Z]+)_(.+)\.log$", base)
    if not m:
        return None
    jobid, domain, rest = m.group(1), m.group(2), m.group(3)

    # ignore internal logs like vllm_user / vllm_agent / taubench
    if rest in ("vllm_user", "vllm_agent", "taubench"):
        return None

    baseline_label = f"{domain}_{rest}"
    return jobid, domain.lower(), baseline_label

def extract_metrics(taubench_path: str):
    with open(taubench_path, "r", errors="ignore") as f:
        txt = f.read()

    m = avg_reward_re.search(txt)
    avg_reward = float(m.group(1)) if m else None

    pk = {int(k): float(v) for k, v in passk_re.findall(txt)}
    return avg_reward, pk

def main():
    # 1) collect candidate “baseline” logs (the ones that contain airline/retail etc.)
    driver_logs = []
    for fp in glob.glob(os.path.join(LOG_DIR, "*.log")):
        parsed = parse_baseline_from_filename(fp)
        if not parsed:
            continue
        jobid, domain, baseline = parsed
        if domain in DOMAINS:
            driver_logs.append((fp, jobid, domain, baseline))

    rows = []
    missing = []

    # 2) for each driver log, open the corresponding {jobid}_taubench.log
    for driver_fp, jobid, domain, baseline in sorted(driver_logs, key=lambda x: (x[2], x[3], x[1])):
        tb_fp = os.path.join(LOG_DIR, f"{jobid}_taubench.log")
        if not os.path.exists(tb_fp):
            missing.append((jobid, baseline, tb_fp))
            continue

        avg_reward, pk = extract_metrics(tb_fp)

        row = {
            "domain": domain,
            "baseline": baseline,
            "job_id": jobid,
            "taubench_log": tb_fp,
            "avg_reward": avg_reward,
        }
        for k in KS:
            row[f"pass^{k}"] = pk.get(k, None)

        rows.append(row)

    df = pd.DataFrame(rows)

    # 3) If multiple jobs exist for same baseline, keep the most recent taubench log (by mtime)
    if not df.empty:
        df["mtime"] = df["taubench_log"].apply(lambda p: os.path.getmtime(p))
        df = df.sort_values("mtime").groupby(["domain", "baseline"], as_index=False).tail(1)
        df = df.drop(columns=["mtime"]).sort_values(["domain", "baseline"])

    out_csv = "passk_summary.csv"
    df.to_csv(out_csv, index=False)

    pd.set_option("display.max_columns", None)
    print(df.to_string(index=False))
    print(f"\nWrote: {out_csv}")

    if missing:
        print("\nMissing taubench logs for some job ids:")
        for jobid, baseline, tb_fp in missing[:30]:
            print(f"  job_id={jobid} baseline={baseline} expected={tb_fp}")
        if len(missing) > 30:
            print(f"  ... and {len(missing)-30} more")

if __name__ == "__main__":
    main()
