#!/usr/bin/env python3
"""
Concurrent POST benchmark tool (Python)

Mirrors the behavior of `curl_benchmark.sh`:
- Reads a local file, encodes as base64, sends JSON `{content, type}`
- Executes N total requests with configurable concurrency
- Reports success rate, average response time, and estimated requests/sec

Usage:
  python3 benchmark.py [URL] [FILE] [TYPE] [REQUESTS] [CONCURRENCY]
  python3 benchmark.py -c 10
  python3 benchmark.py --concurrency=10

Notes:
- Flags override positionals when both are provided
- Defaults (match bash script): URL=http://localhost:8500 FILE=./input.xlsx TYPE=xlsx REQUESTS=40 CONCURRENCY=4
"""

import argparse
import base64
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Tuple, Optional

try:
    # Prefer stdlib to avoid external dependencies
    from urllib.request import Request, urlopen
    from urllib.error import URLError, HTTPError
except Exception as import_error:  # pragma: no cover
    print(f"Failed to import urllib modules: {import_error}")
    sys.exit(1)


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Benchmark concurrent POST requests with JSON base64 payload",
        add_help=True,
    )

    # Optional flags (override positionals if provided)
    parser.add_argument("-u", "--url", dest="url", help="Target endpoint URL")
    parser.add_argument("-f", "--file", dest="file", help="Path to the file to encode and send")
    parser.add_argument("-t", "--type", dest="type", help="Type field to include in the JSON body (xlsx/xls/xlsm)")
    parser.add_argument("-n", "--requests", dest="requests", type=int, help="Total number of requests to send")
    parser.add_argument("-c", "--concurrency", dest="concurrency", type=int, help="Number of concurrent workers")

    # Positional fallbacks (kept for compatibility)
    parser.add_argument("url_pos", nargs="?", default="http://localhost:8500")
    parser.add_argument("file_pos", nargs="?", default=os.path.expanduser("./input.xlsx"))
    parser.add_argument("type_pos", nargs="?", default="xlsx")
    parser.add_argument("requests_pos", nargs="?", type=int, default=40)
    parser.add_argument("concurrency_pos", nargs="?", type=int, default=4)

    args = parser.parse_args(argv)

    # Compute final values with flags overriding positionals
    args.url = args.url or args.url_pos
    args.file = args.file or args.file_pos
    args.type = args.type or args.type_pos
    args.requests = args.requests if args.requests is not None else args.requests_pos
    args.concurrency = args.concurrency if args.concurrency is not None else args.concurrency_pos

    return args


def read_and_encode_file(path: str) -> str:
    if not os.path.isfile(path):
        print(f"❌ File not found: {path}")
        sys.exit(1)
    with open(path, "rb") as f:
        content = f.read()
    return base64.b64encode(content).decode("ascii")


def do_post(url: str, payload_json: str) -> Tuple[int, float, Optional[bytes]]:
    start = time.perf_counter()
    status_code = 0
    body: Optional[bytes] = None
    try:
        req = Request(url=url, data=payload_json.encode("utf-8"), method="POST")
        req.add_header("Content-Type", "application/json")
        with urlopen(req, timeout=300) as resp:
            status_code = getattr(resp, "status", 200)
            try:
                body = resp.read()
            except Exception:
                body = None
    except HTTPError as http_err:
        status_code = getattr(http_err, "code", 0)
    except URLError:
        status_code = 0
    except Exception:
        status_code = 0
    end = time.perf_counter()
    duration = end - start
    return status_code, duration, body


def main(argv: List[str]) -> int:
    args = parse_args(argv)

    b64_content = read_and_encode_file(args.file)
    payload = {"content": b64_content, "type": args.type}
    payload_json = json.dumps(payload, separators=(",", ":"))

    print("==============================================")
    print(f"🔹 Benchmarking POST {args.url}")
    print(f"🔹 File: {args.file}")
    print(f"🔹 Type: {args.type}")
    print(f"🔹 Requests: {args.requests}")
    print(f"🔹 Concurrency: {args.concurrency}")
    print("==============================================")

    results: List[Tuple[int, float, Optional[bytes]]] = []
    # Measure overall wall-clock elapsed time for the benchmark execution
    wall_start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=args.concurrency) as executor:
        futures = [executor.submit(do_post, args.url, payload_json) for _ in range(args.requests)]
        for fut in as_completed(futures):
            try:
                results.append(fut.result())
            except Exception:
                results.append((0, 0.0, None))
    wall_end = time.perf_counter()
    wall_elapsed = wall_end - wall_start

    # Write raw results to file in the same format as the bash script
    out_path = "./__post_benchmark_result.txt"
    try:
        with open(out_path, "w", encoding="utf-8") as f:
            for code, duration, _ in results:
                f.write(f"{code},{duration}\n")
    except Exception as e:
        print(f"⚠️  Failed to write results file: {e}")

    # Save first valid (HTTP 200) response body
    first_valid_path = "./__post_first_valid_response.txt"
    first_valid_saved = False
    # Aggregate all invalid responses (non-200 or missing body)
    invalid_agg_path = "./__post_invalid_responses.txt"
    invalid_count = 0
    try:
        with open(invalid_agg_path, "wb") as invalid_out:
            for code, _, body in results:
                if int(code) == 200 and not first_valid_saved and body is not None:
                    try:
                        with open(first_valid_path, "wb") as ok_out:
                            ok_out.write(body)
                        first_valid_saved = True
                    except Exception:
                        pass
                if int(code) != 200:
                    # Write a small header for traceability, then body if present
                    header = f"--- invalid status {code} ---\n".encode("utf-8")
                    invalid_out.write(header)
                    if body:
                        invalid_out.write(body)
                        invalid_out.write(b"\n")
                    else:
                        invalid_out.write(b"<no-body>\n")
                    invalid_count += 1
    except Exception as e:
        print(f"⚠️  Failed to write invalid responses file: {e}")

    count = len(results)
    total_time = sum(d for _, d, __ in results) if count > 0 else 0.0
    success = sum(1 for code, _, __ in results if int(code) == 200)

    avg_time = (total_time / count) if count else 0.0
    success_rate = (success / count * 100.0) if count else 0.0
    req_per_sec = (count / total_time) if total_time > 0 else 0.0

    print("==============================================")
    print(f"✅ Success Rate        : {success}/{count} ({success_rate:.2f}%)")
    print(f"⏱️  Avg Response Time   : {avg_time:.3f}s")
    print(f"📈 Requests/sec (est.)  : {req_per_sec:.2f}")
    print(f"⏳ Elapsed (wall)        : {wall_elapsed:.3f}s")
    if first_valid_saved:
        print(f"📝 First valid response : {first_valid_path}")
    else:
        print("📝 First valid response : <none saved>")
    print(f"🗂️  Invalid responses    : {invalid_agg_path} ({invalid_count} entries)")
    print("==============================================")

    # Non-zero exit if there were any failures
    return 0 if success == count and count > 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))


