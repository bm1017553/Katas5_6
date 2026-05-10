from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
import os
import pandas as pd
from io import StringIO

URLS = [
    "https://exoplanetarchive.ipac.caltech.edu/cgi-bin/nstedAPI/nph-nstedAPI?&table=exoplanets&format=ipac&where=pl_kepflag=1",

    "https://exoplanetarchive.ipac.caltech.edu/cgi-bin/nstedAPI/nph-nstedAPI?&table=exoplanets&format=ipac&where=pl_tranflag=1",

    "https://exoplanetarchive.ipac.caltech.edu/cgi-bin/nstedAPI/nph-nstedAPI?table=cumulative&where=koi_prad<2 and koi_teq>180 and koi_teq<303 and koi_disposition like 'CANDIDATE'"
]

# Timeout: (connect timeout, read timeout)
REQUEST_TIMEOUT = (5, 15)


def fetch_and_parse(url):
    try:
        # --- REQUEST WITH TIMEOUT ---
        response = requests.get(url, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()

        text = response.text

        # --- PARSE DATAFRAME ---
        df = pd.read_csv(StringIO(text))

        return {
            "url": url,
            "status_code": response.status_code,
            "rows": len(df),
            "columns": list(df.columns),
            "dataframe": df
        }

    # --- TIMEOUT HANDLING ---
    except requests.exceptions.Timeout:
        return {
            "url": url,
            "error": f"Timeout: request exceeded {REQUEST_TIMEOUT} (connect, read)"
        }

    # --- HTTP ERRORS ---
    except requests.exceptions.HTTPError as e:
        return {
            "url": url,
            "error": f"HTTP error: {str(e)}"
        }

    # --- OTHER REQUEST FAILURES ---
    except requests.exceptions.RequestException as e:
        return {
            "url": url,
            "error": f"Request failed: {str(e)}"
        }

    # --- EMPTY OR BAD CSV ---
    except pd.errors.EmptyDataError:
        return {
            "url": url,
            "error": "Empty dataset returned"
        }

    # --- GENERIC FALLBACK ---
    except Exception as e:
        return {
            "url": url,
            "error": f"Unexpected error: {str(e)}"
        }


def main():
    cpu_count = os.cpu_count() or 1
    max_workers = min(len(URLS), cpu_count * 5)

    print(f"Thread pool size: {max_workers}")
    print(f"Timeout (connect, read): {REQUEST_TIMEOUT}\n")

    results = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(fetch_and_parse, url): url for url in URLS}

        for future in as_completed(futures):
            results.append(future.result())

    # --- OUTPUT ---
    for result in results:
        print("=" * 80)
        print(f"URL: {result['url']}")

        if "error" in result:
            print(f"ERROR: {result['error']}")
        else:
            df = result["dataframe"]
            print(f"Rows    : {result['rows']}")
            print(f"Columns : {len(result['columns'])}")
            print("\nPreview:")
            print(df.head())

        print("=" * 80 + "\n")


if __name__ == "__main__":
    main()