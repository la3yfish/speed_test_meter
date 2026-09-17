from __future__ import annotations

import argparse
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass


@dataclass
class Sample:
    elapsed_s: float
    bytes_downloaded: int


def fetch_once(url: str, timeout: float) -> Sample:
    start = time.perf_counter()
    downloaded = 0

    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        },
        method="GET",
    )

    with urllib.request.urlopen(request, timeout=timeout) as response:
        while True:
            chunk = response.read(64 * 1024)
            if not chunk:
                break
            downloaded += len(chunk)

    elapsed = time.perf_counter() - start
    return Sample(elapsed_s=elapsed, bytes_downloaded=downloaded)


def normalize_url(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme:
        return url
    return "https://" + url


def format_mbytes(value_bytes: int) -> float:
    return value_bytes / (1024 * 1024)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Measure download speed by fetching the same URL multiple times."
    )
    parser.add_argument("url", help="URL to request, for example https://example.com/image.jpg")
    parser.add_argument("-n", "--requests", type=int, default=10, help="Number of sequential requests (default: 10)")
    parser.add_argument(
        "--timeout",
        type=float,
        default=30.0,
        help="Per-request timeout in seconds (default: 30)",
    )
    args = parser.parse_args(argv)

    if args.requests <= 0:
        print("Error: --requests must be greater than 0", file=sys.stderr)
        return 2

    url = normalize_url(args.url)

    samples: list[Sample] = []
    total_bytes = 0
    total_elapsed = 0.0

    for index in range(1, args.requests + 1):
        try:
            sample = fetch_once(url, args.timeout)
        except (urllib.error.URLError, TimeoutError, ValueError) as exc:
            print(f"Request {index} failed: {exc}", file=sys.stderr)
            return 1

        samples.append(sample)
        total_bytes += sample.bytes_downloaded
        total_elapsed += sample.elapsed_s
        print(
            f"{index:02d}/{args.requests}: "
            f"{sample.bytes_downloaded} bytes in {sample.elapsed_s:.3f} s"
        )

    average_time = total_elapsed / len(samples)
    speed_mb_s = format_mbytes(total_bytes) / total_elapsed if total_elapsed > 0 else 0.0

    print()
    print(f"URL: {url}")
    print(f"Requests: {len(samples)}")
    print(f"Total downloaded: {total_bytes} bytes ({format_mbytes(total_bytes):.2f} MB)")
    print(f"Average request time: {average_time:.3f} s")
    print(f"Speed: {speed_mb_s:.2f} MB/s")

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
