from concurrent.futures import ThreadPoolExecutor, as_completed
import requests

URLS = [
    "https://exoplanetarchive.ipac.caltech.edu/cgi-bin/nstedAPI/nph-nstedAPI?&table=exoplanets&format=ipac&where=pl_kepflag=1",

    "https://exoplanetarchive.ipac.caltech.edu/cgi-bin/nstedAPI/nph-nstedAPI?&table=exoplanets&format=ipac&where=pl_tranflag=1",

    "https://exoplanetarchive.ipac.caltech.edu/cgi-bin/nstedAPI/nph-nstedAPI?table=cumulative&where=koi_prad<2 and koi_teq>180 and koi_teq<303 and koi_disposition like 'CANDIDATE'"
]


def fetch_url(url):
    """
    Fetch data from a single URL.
    """
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        return {
            "url": url,
            "status_code": response.status_code,
            "content_length": len(response.text),
            "preview": response.text[:500]  # First 500 characters
        }

    except requests.exceptions.RequestException as e:
        return {
            "url": url,
            "error": str(e)
        }


def main():
    results = []

    # Create a thread pool
    with ThreadPoolExecutor(max_workers=3) as executor:

        # Submit all tasks
        future_to_url = {
            executor.submit(fetch_url, url): url
            for url in URLS
        }

        # Process results as they complete
        for future in as_completed(future_to_url):
            result = future.result()
            results.append(result)

    # Print results
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