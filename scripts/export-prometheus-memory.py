#!/usr/bin/env python3
"""
Export memory metrics from Prometheus to create exact graphs.
Run this while Prometheus has data (or shortly after load tests).
Usage: python3 export-prometheus-memory.py [--prometheus-url http://localhost:9090]
Output: JSON files in results/prometheus-exports/ for use in graph generation.
"""

import json
import sys
import urllib.request
import urllib.parse
from pathlib import Path
from datetime import datetime
from time import time

PROJECT_DIR = Path(__file__).resolve().parent.parent
OUT_DIR = PROJECT_DIR / "results" / "prometheus-exports"
OUT_DIR.mkdir(parents=True, exist_ok=True)

PROMETHEUS_URL = "http://localhost:9090"

def query_prometheus(query: str, start_ts: int, end_ts: int, step: str = "10s") -> list:
    """Query Prometheus range API. Returns list of (timestamp, value) tuples."""
    params = {
        "query": query,
        "start": start_ts,
        "end": end_ts,
        "step": step,
    }
    url = f"{PROMETHEUS_URL}/api/v1/query_range?" + urllib.parse.urlencode(params)
    try:
        with urllib.request.urlopen(url, timeout=10) as r:
            data = json.loads(r.read().decode())
    except Exception as e:
        print(f"Error querying Prometheus: {e}")
        return []

    if data.get("status") != "success" or "data" not in data:
        return []

    result = data["data"]["result"]
    if not result:
        return []

    values = result[0].get("values", [])
    return [(int(ts), float(v)) for ts, v in values]

def main():
    global PROMETHEUS_URL
    url = PROMETHEUS_URL
    if len(sys.argv) > 2 and sys.argv[1] == "--prometheus-url":
        url = sys.argv[2]
        PROMETHEUS_URL = url

    # Default: last 30 minutes
    end_ts = int(time())
    start_ts = end_ts - 30 * 60

    spring_boot_query = 'sum(jvm_memory_used_bytes{area="heap"}) / 1024 / 1024'
    fastapi_query = 'process_resident_memory_bytes{job="fastapi"} / 1024 / 1024'

    print("Querying Prometheus...")
    sb_data = query_prometheus(spring_boot_query, start_ts, end_ts)
    fa_data = query_prometheus(fastapi_query, start_ts, end_ts)

    if sb_data:
        out = OUT_DIR / "spring_boot_memory.json"
        export = {"query": spring_boot_query, "data": [{"ts": ts, "value": v} for ts, v in sb_data]}
        out.write_text(json.dumps(export, indent=2))
        print(f"Exported {len(sb_data)} points: {out}")
    else:
        print("No Spring Boot data. Is Prometheus scraping spring-boot?")

    if fa_data:
        out = OUT_DIR / "fastapi_memory.json"
        export = {"query": fastapi_query, "data": [{"ts": ts, "value": v} for ts, v in fa_data]}
        out.write_text(json.dumps(export, indent=2))
        print(f"Exported {len(fa_data)} points: {out}")
    else:
        print("No FastAPI data. Is Prometheus scraping fastapi?")

    if not sb_data and not fa_data:
        print("\nUsing fallback; run load tests, then rerun this script while Prometheus has data.")

if __name__ == "__main__":
    main()