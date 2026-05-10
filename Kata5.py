from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
import os
import pandas as pd
from io import StringIO
import threading

# -----------------------------
# NASA API endpoints
# -----------------------------
URLS = [
    "https://exoplanetarchive.ipac.caltech.edu/cgi-bin/nstedAPI/nph-nstedAPI?&table=exoplanets&format=ipac&where=pl_kepflag=1",

    "https://exoplanetarchive.ipac.caltech.edu/cgi-bin/nstedAPI/nph-nstedAPI?&table=exoplanets&format=ipac&where=pl_tranflag=1",

    "https://exoplanetarchive.ipac.caltech.edu/cgi-bin/nstedAPI/nph-nstedAPI?table=cumulative&where=koi_prad<2 and koi_teq>180 and koi_teq<303 and koi_disposition like 'CANDIDATE'"
]

# -----------------------------
# Configuration
# -----------------------------
REQUEST_TIMEOUT = (5, 15)  # (connect timeout, read timeout)

# Shared thread-safe storage
results = []
results_lock = threading.Lock()


# -----------------------------
# Worker function
# -----------------------------
def fetch_and_parse(url):
    try:
        # --- HTTP request with timeout ---
        response = requests.get(url, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()

        # --- Parse into DataFrame ---
        df = pd.read_csv(StringIO(response.text))

        result = {
            "url": url,
            "status_code": response.status_code,
            "rows": len(df),
            "columns": list(df.columns),
            "dataframe": df
        }

    except requests.exceptions.Timeout:
        result = {
            "url": url,
            "error": f"Timeout after {REQUEST_TIMEOUT} (connect, read)"
        }

    except requests.exceptions.HTTPError as e:
        result = {
            "url": url,
            "error": f"HTTP error: {str(e)}"
        }

    except requests.exceptions.RequestException as e:
        result = {
            "url": url,
            "error": f"Request failed: {str(e)}"
        }

    except pd.errors.EmptyDataError:
        result = {
            "url": url,
            "error": "Empty dataset returned"
        }

    except Exception as e:
        result = {
            "url": url,
            "error": f"Unexpected error: {str(e)}"
        }

    # --- THREAD-SAFE WRITE ---
    with results_lock:
        results.append(result)


# -----------------------------
# Main execution
# -----------------------------
def main():
    cpu_count = os.cpu_count() or 1
    max_workers = min(len(URLS), cpu_count * 5)

    print("=" * 80)
    print(f"CPU cores detected : {cpu_count}")
    print(f"Thread pool size   : {max_workers}")
    print(f"Timeout settings   : connect={REQUEST_TIMEOUT[0]}s, read={REQUEST_TIMEOUT[1]}s")
    print("=" * 80 + "\n")

    # --- Run threaded fetch ---
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(fetch_and_parse, url) for url in URLS]

        # Ensure completion
        for future in as_completed(futures):
            pass

    # -----------------------------
    # Output results (single thread)
    # -----------------------------
    for result in results:
        print("=" * 80)
        print(f"URL: {result['url']}")

        if "error" in result:
            print(f"ERROR: {result['error']}")
        else:
            df = result["dataframe"]
            print(f"Status Code : {result['status_code']}")
            print(f"Rows        : {result['rows']}")
            print(f"Columns     : {len(result['columns'])}")

            print("\nPreview:")
            print(df.head())

        print("=" * 80 + "\n")


if __name__ == "__main__":
    main()