import requests
import pandas as pd
import time

# -----------------------------
# CONFIG
# -----------------------------
BASE_URL = "https://api.data.gov/ed/collegescorecard/v1/schools"

API_KEY = "OT8WjBQjlDxFl2hc3ipiYYDSCKOoauXsBC4rTFNM"

OUTPUT_FILE = "collegescorecard_results.csv"

PER_PAGE = 100
MAX_PAGES = 5  # increase if you want more data

# Example filter (you can change this)
PARAMS = {
    "school.state": "TX",
    "fields": "id,school.name,school.city,school.state,latest.student.size,latest.cost.tuition.in_state",
    "per_page": PER_PAGE,
    "page": 0,
    "api_key": API_KEY
}


# -----------------------------
# FETCH ONE PAGE
# -----------------------------
def fetch_page(page):
    params = PARAMS.copy()
    params["page"] = page

    response = requests.get(BASE_URL, params=params, timeout=30)

    if response.status_code != 200:
        print(f"Error {response.status_code}: {response.text}")
        return None

    return response.json()


# -----------------------------
# MAIN PROCESS
# -----------------------------
def run():
    all_results = []

    print("Starting College Scorecard download...")

    for page in range(MAX_PAGES):
        print(f"Fetching page {page}...")

        data = fetch_page(page)

        if not data or "results" not in data:
            print("No more data or request failed.")
            break

        results = data["results"]

        if not results:
            print("Empty page, stopping.")
            break

        all_results.extend(results)

        time.sleep(0.2)  # respect rate limits

    # Convert to DataFrame
    df = pd.DataFrame(all_results)

    print(f"Total records: {len(df)}")

    # Save to CSV
    df.to_csv(OUTPUT_FILE, index=False)

    print(f"Saved to {OUTPUT_FILE}")


# -----------------------------
# RUN
# -----------------------------
if __name__ == "__main__":
    run()