from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
import os

URLS = [
    "https://exoplanetarchive.ipac.caltech.edu/cgi-bin/nstedAPI/nph-nstedAPI?&table=exoplanets&format=ipac&where=pl_kepflag=1",

    "https://exoplanetarchive.ipac.caltech.edu/cgi-bin/nstedAPI/nph-nstedAPI?&table=exoplanets&format=ipac&where=pl_tranflag=1",

    "https://exoplanetarchive.ipac.caltech.edu/cgi-bin/nstedAPI/nph-nstedAPI?table=cumulative&where=koi_prad<2 and koi_teq>180 and koi_teq<303 and koi_disposition like 'CANDIDATE'"
]


# Timeout settings (connect timeout, read timeout)
REQUEST_TIMEOUT = (5, 20)  # 5s to connect, 20s to read response


def fetch_url(url):
    """
    Fetch data from a single URL with timeout handling.
    """
    try:
        response = requests.get(url, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()

        return {
            "url": url,
            "status_code": response.status_code,
            "content_length": len(response.text),
            "preview": response.text[:500]
        }

    except requests.exceptions.Timeout:
        return {
            "url": url,
            "error": f"Request timed out after {REQUEST_TIMEOUT} seconds"
        }

    except requests.exceptions.HTTPError as e:
        return {
            "url": url,
            "error": f"HTTP error: {str(e)}"
        }

    except requests.exceptions.RequestException as e:
        return {
            "url": url,
            "error": f"Request failed: {str(e)}"
        }


def main():
    results = []

    # Dynamic thread pool sizing
    cpu_count = os.cpu_count() or 1
    max_workers = min(len(URLS), cpu_count * 5)

    print(f"CPU cores detected : {cpu_count}")
    print(f"Thread pool size   : {max_workers}")
    print(f"Request timeout    : connect={REQUEST_TIMEOUT[0]}s, read={REQUEST_TIMEOUT[1]}s\n")

    with ThreadPoolExecutor(max_workers=max_workers) as executor:

        future_to_url = {
            executor.submit(fetch_url, url): url
            for url in URLS
        }

        for future in as_completed(future_to_url):
            results.append(future.result())

    # Output results
    for result in results:
        print("=" * 80)
        print(f"URL: {result['url']}")

        if "error" in result:
            print(f"ERROR: {result['error']}")
        else:
            print(f"Status Code : {result['status_code']}")
            print(f"Content Size: {result['content_length']} characters")
            print("\nPreview:")
            print(result["preview"])

        print("=" * 80)
        print()


if __name__ == "__main__":
    main()