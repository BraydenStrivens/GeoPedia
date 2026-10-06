"""
Downloads Cambodia administrative-name data from the MEF public dataset API.

The dataset provides Khmer and English administrative names and codes for
provinces, districts, communes, and villages. Requests are rate-limited and
automatically retried with exponential backoff when necessary.

Output:
    data/raw/countries/cambodia/mef-admin-data.json

Run from the GeoPedia project root:
    python scripts/countries/asia/cambodia/download/mef-admin-data.py
"""

import json
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


API_URL = (
    "https://data.mef.gov.kh/api/v1/public-datasets/"
    "pd_68e370856a965e00074a5e7b/json"
)

OUTPUT_PATH = Path(
    "data/raw/countries/cambodia/mef-admin-data.json"
)

PAGE_SIZE = 200

# Be conservative with the public API.
REQUEST_DELAY_SECONDS = 5.0

# Retry transient failures, especially HTTP 429.
MAX_RETRIES = 6
INITIAL_RETRY_DELAY_SECONDS = 5.0


def fetch_page(page: int) -> dict:
    query = urlencode(
        {
            "page": page,
            "page_size": PAGE_SIZE,
        }
    )

    url = f"{API_URL}?{query}"

    for attempt in range(MAX_RETRIES + 1):
        try:
            print(f"Fetching page {page}...")

            request = Request(
                url,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 GeoPedia administrative-data downloader"
                    ),
                    "Accept": "application/json",
                },
            )

            with urlopen(request, timeout=60) as response:
                return json.load(response)

        except HTTPError as error:
            if error.code != 429:
                raise

            if attempt >= MAX_RETRIES:
                raise RuntimeError(
                    f"Page {page} continued returning HTTP 429 "
                    f"after {MAX_RETRIES} retries."
                ) from error

            # Respect Retry-After when the server supplies one.
            retry_after = error.headers.get("Retry-After")

            if retry_after:
                try:
                    delay = float(retry_after)
                except ValueError:
                    delay = (
                        INITIAL_RETRY_DELAY_SECONDS
                        * (2 ** attempt)
                    )
            else:
                delay = (
                    INITIAL_RETRY_DELAY_SECONDS
                    * (2 ** attempt)
                )

            print(
                f"  HTTP 429: rate limited. "
                f"Waiting {delay:.1f} seconds before retrying..."
            )

            time.sleep(delay)

        except URLError as error:
            if attempt >= MAX_RETRIES:
                raise RuntimeError(
                    f"Page {page} failed after "
                    f"{MAX_RETRIES} retries."
                ) from error

            delay = (
                INITIAL_RETRY_DELAY_SECONDS
                * (2 ** attempt)
            )

            print(
                f"  Network error: {error.reason}. "
                f"Waiting {delay:.1f} seconds before retrying..."
            )

            time.sleep(delay)

    raise RuntimeError(
        f"Unable to download page {page}."
    )


def find_records(payload):
    """
    Extracts the record array from the MEF API response.
    """
    if not isinstance(payload, dict):
        raise RuntimeError(
            f"Unexpected API response type: "
            f"{type(payload).__name__}"
        )

    records = payload.get("items")

    if not isinstance(records, list):
        print("\nUnexpected response structure:")
        print(
            json.dumps(
                payload,
                ensure_ascii=False,
                indent=2,
            )[:5000]
        )

        raise RuntimeError(
            "Could not locate the 'items' array "
            "in the API response."
        )

    return records


def main() -> None:
    all_records = []
    page = 1
    expected_total = None

    while True:
        payload = fetch_page(page)
        records = find_records(payload)

        if expected_total is None:
            expected_total = payload.get("total_items")

            print(
                f"Dataset reports "
                f"{expected_total:,} total records."
            )

        print(
            f"  Received {len(records):,} records "
            f"({len(all_records) + len(records):,}"
            f"/{expected_total:,})."
        )

        if not records:
            break

        all_records.extend(records)

        total_pages = payload.get("total_pages")

        if total_pages is not None and page >= total_pages:
            break

        if len(records) < PAGE_SIZE:
            break

        page += 1

        # Avoid hammering the public API.
        time.sleep(REQUEST_DELAY_SECONDS)

    if not all_records:
        raise RuntimeError(
            "The API returned no records."
        )

    if (
        expected_total is not None
        and len(all_records) != expected_total
    ):
        raise RuntimeError(
            "Download finished with an unexpected "
            f"record count: got {len(all_records):,}, "
            f"expected {expected_total:,}."
        )

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with OUTPUT_PATH.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            all_records,
            file,
            ensure_ascii=False,
            indent=2,
        )

    print()
    print("Download complete.")
    print(f"Records: {len(all_records):,}")
    print(f"Output:  {OUTPUT_PATH}")

    print("\nFirst record:")
    print(
        json.dumps(
            all_records[0],
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()