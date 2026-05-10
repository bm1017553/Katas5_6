import requests
import pandas as pd
import time
from multiprocessing import Pool, cpu_count

# -----------------------------
# CONFIG
# -----------------------------
BASE_URL = "https://api.data.gov/ed/collegescorecard/v1/schools"
API_KEY = "YOUR_API_KEY_HERE"

PER_PAGE = 100
MAX_PAGES = 5

FIELDS = [
    "school.name",
    "school.state",
    "school.city",
    "latest.student.size",
    "latest.cost.tuition.in_state"
]

# -----------------------------
# FETCH DATA
# -----------------------------
def fetch_page(page):
    params = {
        "api_key": API_KEY,
        "per_page": PER_PAGE,
        "page": page,
        "fields": ",".join(FIELDS),
        "school.state": "TX"
    }

    r = requests.get(BASE_URL, params=params, timeout=30)

    if r.status_code != 200:
        return []

    data = r.json()
    return data.get("results", [])


# -----------------------------
# CPU-BOUND FUNCTION
# (runs in parallel processes)
# -----------------------------
def compute_stats(group):
    state, df = group

    return {
        "state": state,
        "avg_size": df["latest.student.size"].mean(),
        "median_size": df["latest.student.size"].median(),
        "avg_tuition": df["latest.cost.tuition.in_state"].mean(),
        "school_count": len(df)
    }


# -----------------------------
# MAIN PIPELINE
# -----------------------------
def run():
    print("Fetching data...")

    all_data = []

    for page in range(MAX_PAGES):
        print(f"Page {page}")
        all_data.extend(fetch_page(page))
        time.sleep(0.2)

    df = pd.DataFrame(all_data)

    # -----------------------------
    # SAFE CLEANING (NO KEYERROR)
    # -----------------------------
    required_columns = [
    "school.state",
    "latest.student.size",
    "latest.cost.tuition.in_state"
    ]

    for col in required_columns:
        if col not in df.columns:
            print(f"Warning: missing column {col}")
            df[col] = None  # create empty column to avoid crash

    df["latest.student.size"] = pd.to_numeric(df["latest.student.size"], errors="coerce")
    df["latest.cost.tuition.in_state"] = pd.to_numeric(
    df["latest.cost.tuition.in_state"],
    errors="coerce"
    )

    df = df.dropna(subset=["school.state"])

    # -----------------------------
    # GROUP DATA (CPU WORK)
    # -----------------------------
    grouped = [(state, group.copy()) for state, group in df.groupby("school.state")]

    print("Running CPU-bound aggregation...")

    with Pool(cpu_count()) as pool:
        results = pool.map(compute_stats, grouped)

    stats_df = pd.DataFrame(results)

    # -----------------------------
    # OUTPUT
    # -----------------------------
    df.to_csv("raw_schools.csv", index=False)
    stats_df.to_csv("state_statistics.csv", index=False)

    print("\nDone.")
    print("Saved:")
    print("- raw_schools.csv")
    print("- state_statistics.csv")


# -----------------------------
# RUN
# -----------------------------
if __name__ == "__main__":
    run()