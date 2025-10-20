#!/usr/bin/env bash
# ==============================================
# CURL POST Benchmark Tool
# Author: S3R
# Purpose: Benchmark POST requests with JSON payloads (Base64 file upload)
# Tested on: Ubuntu 25.04
# ==============================================

# --- Help & User Parameters ---
print_help() {
  cat <<'EOF'
Usage: benchmark_curl.sh [options] [URL] [FILE] [TYPE] [REQUESTS] [CONCURRENCY]

Benchmark POST requests to the Excel->CSV API.

Positional args (all optional, defaults shown):
  URL           Target endpoint (default: http://localhost:8500)
  FILE          File path to send (default: ./input.xlsx)
  TYPE          File type: xls|xlsx|xlsm (default: xlsx)
  REQUESTS      Total number of requests (default: 40)
  CONCURRENCY   Number of parallel jobs (default: 4)

Examples:
  ./benchmark_curl.sh
  ./benchmark_curl.sh http://localhost:8500 ./input.xlsx xlsx 100 8

Flags:
  -h, --help            Show this help and exit
  -c N, --concurrency=N Set parallel jobs (overrides positional)
EOF
}

# Parse flags first (-h/--help, -c/--concurrency)
CONCURRENCY=""
POSITIONALS=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help)
      print_help
      exit 0
      ;;
    -c)
      CONCURRENCY="$2"
      shift 2
      ;;
    --concurrency=*)
      CONCURRENCY="${1#*=}"
      shift
      ;;
    --concurrency)
      CONCURRENCY="$2"
      shift 2
      ;;
    --)
      shift
      break
      ;;
    -*)
      echo "Unknown option: $1" >&2
      exit 1
      ;;
    *)
      POSITIONALS+=("$1")
      shift
      ;;
  esac
done

# Restore remaining positionals
set -- "${POSITIONALS[@]}" "$@"

URL="${1:-http://localhost:8500}"              # Target endpoint
FILE="${2:-./input.xlsx}"                      # File to send
TYPE="${3:-xlsx}"                              # Type field in JSON
REQUESTS="${4:-40}"                            # Total number of requests
# If -c/--concurrency provided, use it; else positional fifth arg or default 4
CONCURRENCY="${CONCURRENCY:-${5:-4}}"          # Parallel jobs

# --- Dependency check ---
for cmd in curl parallel base64 bc; do
  if ! command -v "$cmd" &>/dev/null; then
    echo "❌ Missing dependency: $cmd"
    echo "Install it using: sudo apt install $cmd"
    exit 1
  fi
done

# --- Prepare Base64 payload once ---
if [[ ! -f "$FILE" ]]; then
  echo "❌ File not found: $FILE"
  exit 1
fi

B64_CONTENT=$(base64 -w0 "$FILE")
PAYLOAD="{\"content\":\"$B64_CONTENT\",\"type\":\"$TYPE\"}"

echo "=============================================="
echo "🔹 Benchmarking POST $URL"
echo "🔹 File: $FILE"
echo "🔹 Type: $TYPE"
echo "🔹 Requests: $REQUESTS"
echo "🔹 Concurrency: $CONCURRENCY"
echo "=============================================="

# --- Single Request Function ---
single_curl() {
  local start end duration code
  start=$(date +%s.%N)
  code=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$URL" \
    -H "Content-Type: application/json" \
    -d "$PAYLOAD")
  end=$(date +%s.%N)
  duration=$(echo "$end - $start" | bc)
  echo "$code,$duration"
}

export -f single_curl
export URL PAYLOAD

# --- Run Benchmark ---
bench_start=$(date +%s.%N)
results=$(seq 1 "$REQUESTS" | parallel -j "$CONCURRENCY" single_curl)
bench_end=$(date +%s.%N)
wall_elapsed=$(echo "$bench_end - $bench_start" | bc)

# --- Analyze Results ---
echo "$results" > /tmp/curl_post_bench.txt

total_time=0
count=0
success=0
while IFS=, read -r code time; do
  ((count++))
  total_time=$(echo "$total_time + $time" | bc)
  [[ "$code" == "200" ]] && ((success++))
done < /tmp/curl_post_bench.txt

avg_time=$(echo "scale=3; $total_time / $count" | bc)
success_rate=$(echo "scale=2; ($success / $count) * 100" | bc)
req_per_sec=$(echo "scale=2; $count / $total_time" | bc)

# --- Report ---
echo "=============================================="
echo "✅ Success Rate        : $success/$count ($success_rate%)"
echo "⏱️  Avg Response Time   : ${avg_time}s"
echo "📈 Requests/sec (est.)  : $req_per_sec"
echo "⏳ Elapsed (wall)        : $wall_elapsed s"
echo "=============================================="
