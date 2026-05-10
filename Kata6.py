import requests
import pandas as pd
import time
import multiprocessing as mp
from multiprocessing import Pool, cpu_count

# -----------------------------
# CONFIG
# -----------------------------
BASE_URL = "https://api.data.gov/ed/collegescorecard/v1/schools"
API_KEY = "OT8WjBQjlDxFl2hc3ipiYYDSCKOoauXsBC4rTFNM"

PER_PAGE = 100
MAX_PAGES = 5

FIELDS = [
    "school.name",
    "school.state",
    "school.city",
    "latest.student.size",
    "latest.cost.tuition.in_state"
]

ERROR_LOG_FILE = "error_log.txt"


# -----------------------------
# LOGGING
# -----------------------------
def log_error(msg):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(ERROR_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{ts}] {msg}\n")


# -----------------------------
# API FETCH (SAFE + RETRY)
# -----------------------------
def fetch_page(page, retries=3):
    params = {
        "api_key": API_KEY,
        "per_page": PER_PAGE,
        "page": page,
        "fields": ",".join(FIELDS),
        "school.state": "TX"
    }

    for attempt in range(retries):
        try:
            r = requests.get(BASE_URL, params=params, timeout=30)

            if r.status_code != 200:
                log_error(f"Page {page}: HTTP {r.status_code}")
                continue

            try:
                data = r.json()
                return data.get("results", [])
            except Exception as e:
                log_error(f"Page {page}: JSON error {e}")

        except Exception as e:
            log_error(f"Page {page}: request error {e}")

        time.sleep(1.5 * (attempt + 1))  # backoff

    return []


# -----------------------------
# CPU WORKER
# -----------------------------
def compute_stats(group):
    state, df = group

    try:
        return {
            "state": state,
            "avg_size": df["latest.student.size"].mean(),
            "median_size": df["latest.student.size"].median(),
            "avg_tuition": df["latest.cost.tuition.in_state"].mean(),
            "school_count": len(df)
        }
    except Exception as e:
        log_error(f"CPU error state={state}: {e}")
        return {
            "state": state,
            "avg_size": None,
            "median_size": None,
            "avg_tuition": None,
            "school_count": len(df)
        }


# -----------------------------
# MAIN PIPELINE
# -----------------------------
def run():
    print("\n=== FETCHING DATA ===\n")

    all_data = []

    # -------------------------
    # FETCH WITH PROGRESS
    # -------------------------
    for page in range(MAX_PAGES):
        print(f"Fetching page {page + 1}/{MAX_PAGES} ...", end=" ")

        data = fetch_page(page)

        if not data:
            print("FAILED or EMPTY")
        else:
            print(f"{len(data)} records")

        all_data.extend(data)
        time.sleep(0.2)

    print(f"\nTotal records fetched: {len(all_data)}\n")

    df = pd.DataFrame(all_data)

    # -----------------------------
    # SAFE CLEANING
    # -----------------------------
    required = [
        "school.state",
        "latest.student.size",
        "latest.cost.tuition.in_state"
    ]

    for col in required:
        if col not in df.columns:
            log_error(f"Missing column: {col}")
            df[col] = None

    df["latest.student.size"] = pd.to_numeric(df["latest.student.size"], errors="coerce")
    df["latest.cost.tuition.in_state"] = pd.to_numeric(df["latest.cost.tuition.in_state"], errors="coerce")

    df = df.dropna(subset=["school.state"])

    # -----------------------------
    # GROUP DATA
    # -----------------------------
    grouped = [(state, group.copy()) for state, group in df.groupby("school.state")]

    print(f"Running CPU aggregation on {len(grouped)} groups...\n")

    # -----------------------------
    # PARALLEL PROCESSING (RELIABLE)
    # -----------------------------
    results = []

    with Pool(cpu_count()) as pool:
        for i, result in enumerate(pool.imap_unordered(compute_stats, grouped), start=1):
            results.append(result)
            print(f"CPU progress: {i}/{len(grouped)}", end="\r")

    print("\nCPU processing complete.\n")

    stats_df = pd.DataFrame(results)

    # -----------------------------
    # OUTPUT
    # -----------------------------
    df.to_csv("raw_schools.csv", index=False)
    stats_df.to_csv("state_statistics.csv", index=False)

    print("Saved files:")
    print("- raw_schools.csv")
    print("- state_statistics.csv")
    print(f"- {ERROR_LOG_FILE}")


# -----------------------------
# ENTRY POINT
# -----------------------------
if __name__ == "__main__":
    run()